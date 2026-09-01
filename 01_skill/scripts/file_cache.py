"""Files API 图片缓存。

``files.json`` 只保存页码到 ``file_id`` 的兼容映射；旁边的隐藏清单保存本地 PNG
摘要。这样强制重建或 DPI 变化时，不会把旧图片或失效的 Files API ID 送给模型。
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path


MANIFEST_NAME = ".files-manifest.json"


def _manifest_path(files_json: Path) -> Path:
    return files_json.parent / MANIFEST_NAME


def _load_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return default.copy()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default.copy()
    return value if isinstance(value, dict) else default.copy()


def _save_json(path: Path, data: dict) -> None:
    """原子写入缓存文件，避免上传中断留下损坏映射。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    temp.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_id_exists(client, file_id: str) -> bool:
    """调用客户端的免费存在性检查；测试替身没有该方法时保持旧兼容性。"""
    checker = getattr(client, "file_exists", None)
    if not callable(checker):
        return True
    try:
        return bool(checker(file_id))
    except Exception:
        return False


def prepare_file_sources(client, page_files, files_json: Path, workers: int = 4) -> dict:
    """校验并准备 Files API 图片来源。

    参数：
        client: 具有 ``input_mode``、``upload_image`` 的客户端；若提供
            ``file_exists``，会在复用前校验远端文件。
        page_files: 按物理页码顺序排列的本地 PNG 路径，或 ``{页码: 路径}`` 映射。
        files_json: 页码到 Files API ID 的兼容映射路径。
        workers: 校验/上传并发数，必须大于 0。
    返回值：
        ``{"1": "file-api-..."}``，覆盖传入页面的有效映射。
    异常：
        ``ValueError``：并发数非法或上传未返回 ID。
        ``OSError`` 或客户端异常：本地文件读取或上传失败时向上抛出。
    """
    if isinstance(workers, bool) or workers <= 0:
        raise ValueError("workers 必须大于 0")
    files_json = Path(files_json)
    files_json.parent.mkdir(parents=True, exist_ok=True)
    files_map = {
        str(page): str(file_id).strip()
        for page, file_id in _load_json(files_json, {}).items()
        if str(file_id).strip()
    }
    manifest_path = _manifest_path(files_json)
    manifest = _load_json(manifest_path, {"version": 1, "pages": {}})
    manifest["version"] = 1
    page_records = manifest.get("pages")
    if not isinstance(page_records, dict):
        page_records = {}
        manifest["pages"] = page_records

    if isinstance(page_files, Mapping):
        source_by_page = {
            str(page): Path(source) for page, source in page_files.items()
        }
    else:
        source_by_page = {
            str(index + 1): Path(source)
            for index, source in enumerate(page_files)
        }
    digest_by_page = {
        page: _sha256(source) for page, source in source_by_page.items()
    }

    candidate_pages = []
    for page in source_by_page:
        file_id = files_map.get(page)
        cached = page_records.get(page) or {}
        same_source = cached.get("sha256") == digest_by_page[page]
        if not file_id or not same_source:
            candidate_pages.append(page)

    # 只有本地 PNG 没变时才查询远端 ID；查询并发与上传并发保持一致。
    check_pages = [
        page for page in source_by_page
        if page not in candidate_pages and files_map.get(page)
    ]
    if check_pages:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = executor.map(
                lambda page: (page, _file_id_exists(client, files_map[page])),
                check_pages,
            )
            for page, exists in results:
                if not exists:
                    candidate_pages.append(page)

    candidate_pages = sorted(set(candidate_pages), key=int)
    if not candidate_pages:
        return {page: files_map[page] for page in source_by_page}

    def persist() -> None:
        _save_json(files_json, files_map)
        _save_json(manifest_path, manifest)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(client.upload_image, str(source_by_page[page])): page
            for page in candidate_pages
        }
        for future in concurrent.futures.as_completed(futures):
            page = futures[future]
            file_id = str(future.result() or "").strip()
            if not file_id:
                raise ValueError(f"第 {page} 页上传未返回 file_id")
            files_map[page] = file_id
            page_records[page] = {"sha256": digest_by_page[page]}
            persist()

    return {page: files_map[page] for page in source_by_page}
