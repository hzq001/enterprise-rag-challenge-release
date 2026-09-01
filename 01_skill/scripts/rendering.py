"""PDF 页面 PNG 缓存。

渲染结果与请求 DPI 一起记录。索引因为模型或提示词变化而重建时可以复用同一批
图片；只有 DPI、页面尺寸或 PNG 本身变化时才重新渲染，避免把旧分辨率静默送给视觉模型。
"""
from __future__ import annotations

import json
from pathlib import Path

import fitz


MAX_SIDE_PX = 3600
MANIFEST_NAME = ".render-manifest.json"


def effective_dpi(page, dpi: int) -> int:
    """计算页面实际使用的 DPI，并限制渲染图最长边。

    参数：
        page: PyMuPDF 页面对象。
        dpi: 请求的正整数 DPI。
    返回值：
        实际传给 ``get_pixmap`` 的 DPI，最低为 72。
    异常：
        ``ValueError``：DPI 不是正数。
    """
    if isinstance(dpi, bool) or int(dpi) <= 0:
        raise ValueError("dpi 必须是正数")
    long_side_in = max(page.rect.width, page.rect.height) / 72
    return max(72, min(int(dpi), int(MAX_SIDE_PX / max(long_side_in, 1e-6))))


def _manifest_path(out_dir: Path) -> Path:
    return out_dir / MANIFEST_NAME


def _load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {"version": 1, "pages": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "pages": {}}
    if not isinstance(data, dict) or not isinstance(data.get("pages"), dict):
        return {"version": 1, "pages": {}}
    return data


def _save_manifest(path: Path, manifest: dict) -> None:
    """原子写入渲染清单，避免中断留下半个 JSON。"""
    temp = path.with_name(f"{path.name}.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    temp.replace(path)


def _rendered_file_is_current(png: Path, record: dict, requested_dpi: int,
                             actual_dpi: int) -> bool:
    if not png.is_file():
        return False
    if record.get("requested_dpi") != int(requested_dpi):
        return False
    if record.get("effective_dpi") != int(actual_dpi):
        return False
    try:
        pix = fitz.Pixmap(str(png))
    except Exception:
        return False
    return (
        record.get("width") == pix.width
        and record.get("height") == pix.height
    )


def _render_one(page, page_number: int, png: Path, requested_dpi: int,
                manifest: dict) -> None:
    actual_dpi = effective_dpi(page, requested_dpi)
    record = manifest["pages"].get(str(page_number), {})
    if _rendered_file_is_current(png, record, requested_dpi, actual_dpi):
        return

    pix = page.get_pixmap(dpi=actual_dpi)
    pix.save(str(png))
    manifest["pages"][str(page_number)] = {
        "requested_dpi": int(requested_dpi),
        "effective_dpi": int(actual_dpi),
        "width": pix.width,
        "height": pix.height,
    }


def render_pages(doc, out_dir: Path, dpi: int) -> list[Path]:
    """渲染 PDF 全部页面，并按 DPI/PNG 状态复用或更新缓存。

    参数：
        doc: 已打开的 PyMuPDF 文档。
        out_dir: 页面 PNG 输出目录。
        dpi: 请求的正整数 DPI。
    返回值：
        按物理页码排序的 PNG 路径列表。
    异常：
        ``ValueError``：DPI 非正数。
    """
    int(dpi)  # 先让无效输入尽早暴露，再创建目录。
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = _manifest_path(out_dir)
    manifest = _load_manifest(manifest_path)
    manifest["version"] = 1
    files = []
    for index, page in enumerate(doc):
        png = out_dir / f"p{index + 1:04d}.png"
        _render_one(page, index + 1, png, dpi, manifest)
        files.append(png)
    _save_manifest(manifest_path, manifest)
    return files


def render_selected(pdf: Path, pages: list[int], out_dir: Path,
                    dpi: int = 150) -> dict[int, Path]:
    """渲染指定物理页，并按 DPI/PNG 状态复用或更新缓存。

    参数：
        pdf: PDF 文件路径。
        pages: 1 基物理页码列表。
        out_dir: 页面 PNG 输出目录。
        dpi: 请求的正整数 DPI。
    返回值：
        ``{页码: PNG 路径}``。
    异常：
        ``ValueError``：DPI 非正数或页码越界。
    """
    int(dpi)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = _manifest_path(out_dir)
    manifest = _load_manifest(manifest_path)
    manifest["version"] = 1
    doc = fitz.open(str(pdf))
    result = {}
    try:
        for page_number in pages:
            if not isinstance(page_number, int) or isinstance(page_number, bool):
                raise ValueError(f"页码必须是整数: {page_number!r}")
            if not 1 <= page_number <= len(doc):
                raise ValueError(f"页号越界: {page_number}")
            png = out_dir / f"p{page_number:04d}.png"
            _render_one(doc[page_number - 1], page_number, png, dpi, manifest)
            result[page_number] = png
    finally:
        doc.close()
    _save_manifest(manifest_path, manifest)
    return result
