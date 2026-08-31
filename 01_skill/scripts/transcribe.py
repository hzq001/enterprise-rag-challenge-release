"""transcribe.py —— 本地 OCR / VLM 视觉转录（补盲区核心）

对 router 标出的 GARBLED / SCAN / TABLE / GRAPHIC 页，渲染后按页面类型和显式引擎
转录，产出完整可检索文本，回填索引的 page_texts（原始文本层不可用的页从此可被检索）。

按页类型切换提示词：
    GARBLED  乱码页：Mac OCR 或 VLM 朗读整页
    SCAN     扫描页：Mac OCR 或 VLM OCR 整页
    TABLE    表格页：VLM 按行列和单位转录
    GRAPHIC  图纸页：VLM 提取标注文字/尺寸数值/图例/内容描述 → 结构化

用法（库函数，供 ingest.py 调用）：
    from transcribe import transcribe_pages
    text_map = transcribe_pages(client, pdf_path, {page: label}, cache_dir)
"""
import json
import argparse
import sys
import time
from pathlib import Path

import fitz

import mac_ocr
from ds_client import DSClient, ChatError, SUPPORTED_INPUT_MODES

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- 转录提示词
PROMPT_GARBLED = """你是一台 PDF 页面阅读器。你会收到一页或多页 PDF 的渲染图（这些页的文本层损坏，但渲染正常）。
请把每一页内容【逐字、完整】读出来，包括正文、表格数字。
要求：
1. 完整转录，不要总结、不要遗漏数字和表格内容
2. 表格用 Markdown 表格格式输出
3. 多页时每页输出前加一行【[第N页]】标记（N 为给出的页码）
4. 只输出转录文本，不要任何解释"""

PROMPT_SCAN = """你是一台 OCR 引擎。这是一页或多页扫描件/图片型 PDF 页。
请把每一页内容【逐字、完整】转录出来，包括标题、正文、表格数字、标注。
要求：表格用 Markdown 表格格式输出；多页时每页输出前加一行【[第N页]】标记（N 为给出的页码）；
只输出转录文本，不要任何解释"""

PROMPT_TABLE = """你是一名财务报表表格转录器。你会收到一页或多页包含财务表格的 PDF 页面图像。
请逐页、逐格转录与问题相关的完整表格，严格保留：表头层级、行名、列名、单位、币种、期间、同比/环比标记、正负号、小数和百分号。
要求：
1. 表格使用 Markdown 表格输出，无法确定的单元格写 [无法辨认]，不要猜测
2. 多级表头用合并后的完整列名表达，并在表格前写明单位/币种
3. 多页时每页输出前加一行【[第N页]】标记（N 为给出的页码）
4. 只输出转录文本，不要分析或解释"""

PROMPT_GRAPHIC = """你看到的是工程图纸 / 示意图 / 图表页面。请仔细看图并结构化转录：
1. texts:  图中所有文字标注（标题、部件名、标签、图例文字），逐字列出
2. numbers: 图中所有数字/尺寸/参数（数值+单位），逐一列出
3. desc:   用一句话描述这张图的内容（这是什么图/表/示意图）
输出 JSON：{"texts": ["..."], "numbers": ["...", "..."], "desc": "..."}
只输出 JSON。【图片】"""

PROMPTS = {
    "GARBLED": PROMPT_GARBLED,
    "SCAN": PROMPT_SCAN,
    "TABLE": PROMPT_TABLE,
    "GRAPHIC": PROMPT_GRAPHIC,
}


def _render_missing(pdf: Path, pages: list, pages_dir: Path, dpi: int = 150):
    """只渲染缺失的 PNG（沿用 ingest 的渲染参数，单边≤3600px）。"""
    pages_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    out = {}
    for p in pages:
        png = pages_dir / f"p{p:04d}.png"
        if not png.exists():
            page = doc[p - 1]
            long_side_in = max(page.rect.width, page.rect.height) / 72
            d = max(72, min(dpi, int(3600 / long_side_in)))
            page.get_pixmap(dpi=d).save(str(png))
        out[p] = png
    doc.close()
    return out


def _upload(client: DSClient, page_pngs: dict, files_json: Path, workers: int = 4):
    """准备缺失页图，返回 ``{页码str: file_id或本地路径}``。

    ``file`` 模式使用 files.json 断点续传；``image_url`` 模式跳过上传，
    直接把本地路径交给 DSClient 转成 data URL。
    """
    if client.input_mode == "image_url":
        print("  [upload] input_mode=image_url; skip Files API", flush=True)
        return {str(p): str(png) for p, png in page_pngs.items()}

    import concurrent.futures
    files_map = json.loads(files_json.read_text("utf-8")) if files_json.exists() else {}
    todo = {p: png for p, png in page_pngs.items() if str(p) not in files_map}
    if todo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(client.upload_image, str(png)): p for p, png in todo.items()}
            for fut in concurrent.futures.as_completed(futs):
                files_map[str(futs[fut])] = fut.result()
        files_json.write_text(json.dumps(files_map), "utf-8")
    return files_map


def _normalize_graphic(raw) -> str:
    """GRAPHIC 转录 JSON → 可检索文本。"""
    if not isinstance(raw, dict):
        return str(raw or "")
    parts = []
    if raw.get("texts"):
        parts.append("标注文字: " + " | ".join(str(t) for t in raw["texts"]))
    if raw.get("numbers"):
        parts.append("尺寸数值: " + " | ".join(str(n) for n in raw["numbers"]))
    if raw.get("desc"):
        parts.append("内容描述: " + str(raw["desc"]))
    return "；".join(parts)


def transcribe_pages(client: DSClient | None, pdf: Path, labels: dict,
                     cache_dir: Path, batch: int = 10, dpi: int = 150,
                     workers: int = 4, ocr_engine=None) -> dict:
    """转录指定页面。

    参数：
        client: VLM 引擎使用的客户端；Mac OCR 模式传 ``None``。
        pdf: 待转录 PDF。
        labels: ``{page: GARBLED|SCAN|TABLE|GRAPHIC}``，页码从 1 开始。
        cache_dir: PNG 和 Files API 映射的缓存目录。
        batch: VLM 每批页数；Mac OCR 一次处理所有输入页。
        dpi: PDF 渲染分辨率。
        workers: Files API 上传并发数。
        ocr_engine: ``mac`` 或 ``vlm``；为空时读取 ``OCR_ENGINE``，默认 ``mac``。
    返回值：
        ``{page: 转录文本}``。空结果页会记入日志但不写入返回值。
    异常：
        ``ValueError``：引擎与页面类型不匹配或缺少 VLM client。
        ``MacOCRError``：Mac OCR 进程失败；不会自动切换到 VLM。
    """
    if not labels:
        return {}
    if batch <= 0:
        raise ValueError("batch 必须大于 0")
    unsupported = sorted(set(labels.values()) - set(PROMPTS))
    if unsupported:
        raise ValueError(f"不支持的转录页类型: {unsupported}")

    engine = mac_ocr.resolve_ocr_engine(ocr_engine)
    mac_labels = (
        {p: lab for p, lab in labels.items() if lab in ("GARBLED", "SCAN")}
        if engine == "mac" else {}
    )
    # 表格/图形始终需要 VLM；ocr_engine=mac 只控制扫描/乱码页。
    vlm_labels = {
        p: lab for p, lab in labels.items()
        if p not in mac_labels
    }
    out, failed = {}, []
    if mac_labels:
        pages_dir = cache_dir / "pages"
        pngs = _render_missing(pdf, sorted(mac_labels), pages_dir, dpi)
        t0 = time.time()
        text_map = mac_ocr.ocr_pages(pngs)
        out, failed = {}, []
        for page in sorted(mac_labels):
            text = str(text_map.get(page, "") or "").strip()
            if text:
                out[page] = text
            else:
                failed.append(page)
        if failed:
            print(f"  [transcribe] Mac OCR 空结果 {len(failed)} 页: {failed[:10]}", flush=True)
        print(f"  [transcribe] Mac OCR p{min(mac_labels)}-{max(mac_labels)} "
              f"ok ({time.time()-t0:.0f}s)", flush=True)
    if not vlm_labels:
        return out

    if client is None:
        raise ValueError("TABLE/GRAPHIC 的 VLM 转录需要 client；SCAN/GARBLED 才可使用 Mac OCR")

    pages_dir = cache_dir / "pages"
    pngs = _render_missing(pdf, sorted(vlm_labels), pages_dir, dpi)
    image_sources = _upload(client, pngs, cache_dir / "files.json", workers)

    # 不把 TABLE/GRAPHIC 混在同一批里，确保各自使用正确的输出协议和提示词。
    groups = {}
    for page, label in sorted(vlm_labels.items()):
        groups.setdefault(label, []).append((page, label))
    t0 = time.time()
    for label in ("GRAPHIC", "TABLE", "GARBLED", "SCAN"):
        ordered = groups.get(label, [])
        for i in range(0, len(ordered), batch):
            chunk = ordered[i:i + batch]
            blocks = []
            for page, page_label in chunk:
                blocks.append({"type": "text", "text": f"[第{page}页] {page_label}"})
                source = image_sources[str(page)]
                if client.input_mode == "file":
                    blocks.append(client.build_file_block(source))
                else:
                    blocks.append(client.build_image_block(source))
            blocks.append({"type": "text",
                           "text": f"请处理第{chunk[0][0]}页到第{chunk[-1][0]}页。"})
            try:
                if label == "GRAPHIC":
                    # GRAPHIC：JSON 结构化（json_mode 可用，提示词含 json 字样）
                    data, _ = client.chat_json(blocks, system=PROMPTS["GRAPHIC"],
                                               thinking=False, max_tokens=8192)
                    # 可能是 {页: {...}} 或 {"pages":[...]} 结构
                    recs = data.get("pages") if isinstance(data, dict) else data
                    for page, _ in chunk:
                        rec = None
                        if isinstance(data, dict):
                            rec = data.get(str(page)) or data.get(page)
                        if rec is None and isinstance(recs, dict):
                            rec = recs.get(str(page))
                        if rec is None and isinstance(recs, list):
                            rec = next(
                                (item for item in recs
                                 if isinstance(item, dict)
                                 and str(item.get("page", "")) == str(page)),
                                None,
                            )
                        if isinstance(rec, dict):
                            out[page] = _normalize_graphic(rec)
                        elif isinstance(rec, str):
                            out[page] = rec
                        else:
                            failed.append(page)
                else:
                    # TABLE/ GARBLED/ SCAN：纯文本转录（不能用 json_mode）
                    text, _ = client.chat(blocks, system=PROMPTS[label],
                                          thinking=False, max_tokens=8192)
                    # 按 [第N页] 拆分，页码来自输入标签而不是模型猜测。
                    import re
                    segs = re.split(r"(?:\[|【)第(\d+)页(?:\]|】)", text)
                    # segs: [前缀, 页码, 内容, 页码, 内容, ...]
                    for j in range(1, len(segs), 2):
                        try:
                            page_no = int(segs[j])
                        except ValueError:
                            continue
                        content = (
                            segs[j + 1].strip().lstrip("【】").strip()
                            if j + 1 < len(segs) else ""
                        )
                        if content:
                            out[page_no] = content
                        else:
                            failed.append(page_no)
                    # 单页且模型未带标记：整体当作该页文本。
                    if len(chunk) == 1 and chunk[0][0] not in out and text.strip():
                        out[chunk[0][0]] = text.strip()
            except ChatError as e:
                failed.extend(page for page, _ in chunk)
                print(f"  [transcribe] {label} 批 p{chunk[0][0]}-{chunk[-1][0]} 失败: {e}",
                      flush=True)
                continue
            print(f"  [transcribe] {label} p{chunk[0][0]}-{chunk[-1][0]} ok "
                  f"({time.time()-t0:.0f}s)", flush=True)

    if failed:
        print(f"  [transcribe] 失败 {len(failed)} 页: {failed[:10]}", flush=True)
    return out


if __name__ == "__main__":
    # 自检用法：python transcribe.py <pdf> p1,p2,p3 SCAN [--ocr-engine mac]
    ap = argparse.ArgumentParser(description="Transcribe selected PDF pages with Mac OCR or VLM")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("pages", help="页码，逗号分隔，例如 1,2,3")
    ap.add_argument("label", nargs="?", default="GARBLED")
    ap.add_argument("--model", default=None, help="视觉模型 ID，默认读取 VISION_MODEL")
    ap.add_argument("--base-url", default=None, help="OpenAI 兼容接口地址，默认读取 VISION_BASE_URL")
    ap.add_argument("--input-mode", choices=SUPPORTED_INPUT_MODES, default=None,
                    help="图片输入模式：file 或 image_url，默认读取 VISION_INPUT_MODE")
    ap.add_argument("--ocr-engine", choices=mac_ocr.SUPPORTED_OCR_ENGINES, default=None,
                    help="OCR 引擎：mac（默认）或 vlm；默认读取 OCR_ENGINE")
    args = ap.parse_args()
    pdf = args.pdf
    pages = {int(x) for x in args.pages.split(",")}
    engine = mac_ocr.resolve_ocr_engine(args.ocr_engine)
    client = None if engine == "mac" else DSClient(
        base_url=args.base_url, model=args.model, input_mode=args.input_mode
    )
    cache = Path(__file__).resolve().parent / ".cache" / "transcribe_test"
    text_map = transcribe_pages(
        client, pdf, {p: args.label for p in pages}, cache, ocr_engine=engine
    )
    for p, t in text_map.items():
        print(f"=== p{p} 转录前 300 字 ===")
        print(t[:300])
