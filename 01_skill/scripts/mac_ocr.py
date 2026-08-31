"""macOS 原生 OCR 适配层。

通过同目录的 ``mac_ocr.swift`` 调用 Apple Vision.framework，专门处理扫描页和
文本层损坏页。该模块不调用远程模型，也不会在 OCR 失败时偷偷改走 VLM。
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


SWIFT_SCRIPT = Path(__file__).with_name("mac_ocr.swift")
SUPPORTED_OCR_ENGINES = ("mac", "vlm")
DEFAULT_OCR_ENGINE = "mac"


class MacOCRError(RuntimeError):
    """Mac 原生 OCR 执行或结果解析失败。"""


class MacOCRUnavailable(MacOCRError):
    """当前环境没有可用的 macOS Vision OCR 运行时。"""


def resolve_ocr_engine(value=None) -> str:
    """解析 OCR 引擎，默认使用 Mac Vision。

    参数：
        value: 显式引擎名；为空时读取 ``OCR_ENGINE``，再使用 ``mac``。
    返回值：
        规范化后的 ``mac`` 或 ``vlm``。
    异常：
        ``ValueError``：引擎名不受支持。
    """
    candidate = value
    if candidate is None or not str(candidate).strip():
        candidate = os.environ.get("OCR_ENGINE", DEFAULT_OCR_ENGINE)
    aliases = {
        "mac": "mac",
        "apple": "mac",
        "vision": "mac",
        "mac_vision": "mac",
        "vlm": "vlm",
        "model": "vlm",
    }
    engine = aliases.get(str(candidate).strip().lower().replace("-", "_"))
    if engine is None:
        supported = ", ".join(SUPPORTED_OCR_ENGINES)
        raise ValueError(f"不支持的 OCR 引擎 {value!r}，可选：{supported}")
    return engine


def _resolve_swift_executable(swift_executable=None) -> str:
    """解析 Swift 命令路径；允许测试或本机环境显式指定。"""
    executable = swift_executable or os.environ.get("MAC_OCR_SWIFT")
    if executable:
        return str(executable)
    executable = shutil.which("swift")
    if not executable:
        raise MacOCRUnavailable("未找到 swift；Mac OCR 需要 Xcode Command Line Tools")
    return executable


def _parse_results(stdout: str, page_by_path: dict[str, int]) -> dict[int, str]:
    """解析 Swift 输出，并按规范化路径映射回 PDF 页码。"""
    try:
        payload = json.loads(stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise MacOCRError(f"Mac OCR 输出不是有效 JSON: {exc}") from exc

    records = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise MacOCRError("Mac OCR 输出缺少 pages 数组")

    result = {}
    for record in records:
        if not isinstance(record, dict):
            raise MacOCRError("Mac OCR pages 中存在无效记录")
        raw_path = str(record.get("path", ""))
        key = str(Path(raw_path).expanduser().resolve())
        page = page_by_path.get(key)
        if page is None:
            raise MacOCRError(f"Mac OCR 返回了未请求的图片: {raw_path!r}")
        error = str(record.get("error", "") or "").strip()
        if error:
            raise MacOCRError(f"第 {page} 页 Mac OCR 失败: {error}")
        result[page] = str(record.get("text", "") or "").strip()

    missing = sorted(set(page_by_path.values()) - set(result))
    if missing:
        raise MacOCRError(f"Mac OCR 未返回第 {missing[0]} 页结果")
    return result


def ocr_pages(page_pngs: dict[int, str | Path], swift_executable=None,
              timeout: int = 300, runner=None) -> dict[int, str]:
    """批量识别 PNG 页面。

    参数：
        page_pngs: ``{1: Path("p0001.png")}`` 形式的页码到图片映射。
        swift_executable: 可选 Swift 可执行文件路径，默认查找 ``swift``。
        timeout: 单批 OCR 超时时间（秒）。
        runner: subprocess runner，供单元测试注入。
    返回值：
        ``{页码: OCR 文本}``，包含每个请求页，即使文本为空。
    异常：
        ``MacOCRUnavailable``：非 macOS 或找不到 Swift。
        ``MacOCRError``：图片、进程或输出结果异常。
    """
    if platform.system() != "Darwin":
        raise MacOCRUnavailable("Mac Vision OCR 只能在 macOS 上运行")
    if not page_pngs:
        return {}
    if not SWIFT_SCRIPT.is_file():
        raise MacOCRUnavailable(f"找不到 OCR 脚本: {SWIFT_SCRIPT}")

    ordered = []
    page_by_path = {}
    for page, source in sorted(page_pngs.items(), key=lambda item: int(item[0])):
        path = Path(source).expanduser()
        if not path.is_file():
            raise MacOCRError(f"OCR 图片不存在: {path}")
        resolved = path.resolve()
        key = str(resolved)
        if key in page_by_path:
            raise MacOCRError(f"OCR 图片路径重复: {resolved}")
        page_by_path[key] = int(page)
        ordered.append(resolved)

    executable = _resolve_swift_executable(swift_executable)
    command = [executable, str(SWIFT_SCRIPT), *(str(path) for path in ordered)]
    runner = runner or subprocess.run
    try:
        completed = runner(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise MacOCRError(f"Mac OCR 超时（>{timeout} 秒）") from exc
    except OSError as exc:
        raise MacOCRUnavailable(f"无法启动 Swift OCR: {exc}") from exc

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        detail = stderr[-500:] if stderr else f"exit code {completed.returncode}"
        raise MacOCRError(f"Swift OCR 执行失败: {detail}")
    return _parse_results(completed.stdout or "", page_by_path)
