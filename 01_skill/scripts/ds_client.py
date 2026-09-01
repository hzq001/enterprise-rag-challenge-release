"""Shared vision client for the enterprise-rag-challenge skill.

封装了实测验证过的 API 细节与坑（详见 references/api-notes.md）：
- 默认模型仍是 DeepSeek 视觉模型，但可按调用或环境变量切换模型；
- 图片输入支持 Files API（``file``）和 Chat Completions 的 ``image_url`` 两种模式；
- JSON Output 偶发空 content，必须重试。
"""
import base64
import json
import mimetypes
import os
import random
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash-vision-exp"
DEFAULT_INPUT_MODE = "file"
SUPPORTED_INPUT_MODES = ("file", "image_url")


def _env_first(names, default):
    """按顺序读取第一个非空环境变量。"""
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return default


# 保留旧环境变量，同时提供不绑定具体厂商的短名称。
BASE_URL = _env_first(("VISION_BASE_URL", "DEEPSEEK_BASE_URL"), DEFAULT_BASE_URL)
MODEL = _env_first(("VISION_MODEL", "DEEPSEEK_VISION_MODEL"), DEFAULT_MODEL)
INPUT_MODE = _env_first(
    ("VISION_INPUT_MODE", "DEEPSEEK_VISION_INPUT_MODE"), DEFAULT_INPUT_MODE
)

THINKING_OFF = {"thinking": {"type": "disabled"}}


def resolve_input_mode(value=None) -> str:
    """解析图片输入模式，统一返回 ``file`` 或 ``image_url``。

    参数：
        value: 显式模式；为空时读取 ``VISION_INPUT_MODE`` 等环境变量。
    返回：
        规范化后的输入模式。
    异常：
        ``ValueError``：模式不受支持。
    """
    candidate = (
        value
        if value is not None and str(value).strip()
        else _env_first(("VISION_INPUT_MODE", "DEEPSEEK_VISION_INPUT_MODE"), INPUT_MODE)
    )
    candidate = str(candidate).strip().lower().replace("-", "_")
    aliases = {
        "file": "file",
        "files": "file",
        "file_api": "file",
        "image_url": "image_url",
        "imageurl": "image_url",
    }
    mode = aliases.get(candidate)
    if mode is None:
        supported = ", ".join(SUPPORTED_INPUT_MODES)
        raise ValueError(f"不支持的图片输入模式 {value!r}，可选：{supported}")
    return mode


def _configured_base_url() -> str:
    """读取当前进程的接口地址配置。"""
    return _env_first(("VISION_BASE_URL", "DEEPSEEK_BASE_URL"), BASE_URL)


def _configured_model() -> str:
    """读取当前进程的模型配置。"""
    return _env_first(("VISION_MODEL", "DEEPSEEK_VISION_MODEL"), MODEL)


def resolve_base_url(value=None) -> str:
    """解析本次调用使用的 OpenAI 兼容接口地址。

    参数：
        value: 显式接口地址；为空时读取环境变量和默认值。
    返回值：
        去除首尾空白后的接口地址。
    约束：
        不在此处发起网络请求，也不校验接口是否可用。
    """
    candidate = value if value is not None and str(value).strip() else _configured_base_url()
    return str(candidate).strip()


def resolve_model(value=None) -> str:
    """解析本次调用使用的视觉模型名称。

    参数：
        value: 显式模型名称；为空时读取环境变量和默认值。
    返回值：
        去除首尾空白后的模型名称。
    约束：
        只解析配置，不证明模型支持视觉输入；可用性仍需真实请求验证。
    """
    candidate = value if value is not None and str(value).strip() else _configured_model()
    return str(candidate).strip()


def _load_api_key() -> str:
    """从环境变量或本机文件读取 API key，绝不在代码中硬编码。"""
    # VISION_API_KEY 用于统一配置；其余名称保持既有本机/DeepSeek 兼容性。
    for name in (
        "VISION_API_KEY",
        "DEEPSEEK_API_KEY",
        "CLIPROXY_API_KEY",
        "LOCAL_OPENAI_API_KEY",
        "OPENAI_API_KEY",
    ):
        key = os.environ.get(name, "").strip()
        if key:
            return key

    key_file = Path.home() / ".deepseek_api_key"
    if key_file.is_file():
        key = key_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if key:
            return key

    sys.exit(
        "[error] 未找到 API key，请设置 VISION_API_KEY、DEEPSEEK_API_KEY、"
        "CLIPROXY_API_KEY 或 OPENAI_API_KEY，或把 key 写入 ~/.deepseek_api_key 首行"
    )


class ChatError(RuntimeError):
    pass


def parse_json_lenient(text):
    """解析模型返回的 JSON，容忍代码围栏、None、尾逗号等常见毛病。"""
    if not text or not text.strip():
        raise ChatError("no content to parse")
    s = text.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.DOTALL)
    if m:
        s = m.group(1)
    s = s.strip()
    # 截掉围栏外多余文字：取第一个 { 或 [ 到最后一个 } 或 ]
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    if starts:
        s = s[min(starts):]
        for closer in (s.rfind("}"), s.rfind("]")):
            if closer != -1:
                s = s[: closer + 1]
                break
    s = re.sub(r"\bNone\b", "null", s)
    s = re.sub(r",\s*([\]}])", r"\1", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ChatError(f"unparseable JSON: {e}; head={s[:120]!r}")


class DSClient:
    def __init__(self, api_key=None, base_url=None, model=None, input_mode=None):
        """创建可配置的视觉模型客户端。

        参数：
            api_key: 显式 API key；为空时按环境变量和本机文件读取。
            base_url: OpenAI 兼容接口地址；为空时读取 ``VISION_BASE_URL``。
            model: 模型 ID；为空时读取 ``VISION_MODEL``。
            input_mode: ``file`` 或 ``image_url``；为空时读取环境变量。
        返回值：
            ``DSClient`` 实例。
        约束：
            ``input_mode`` 必须是支持的图片输入模式。
        """
        self.base_url = resolve_base_url(base_url)
        self.model = resolve_model(model)
        self.input_mode = resolve_input_mode(input_mode)
        self.client = OpenAI(
            api_key=api_key or _load_api_key(),
            base_url=self.base_url,
            max_retries=0,  # 重试与退避由本类统一控制
        )

    def chat(self, blocks, system=None, thinking=False, json_mode=False,
             max_tokens=8192, temperature=0.1, retries=4, timeout=600):
        """调用 vision 模型，返回 (text, finish_reason)。自动重试空 content 与网络错误。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": blocks})
        kwargs = dict(model=self.model, messages=messages, max_tokens=max_tokens, timeout=timeout)
        if not thinking:
            kwargs["temperature"] = temperature
            kwargs["extra_body"] = THINKING_OFF
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        delay = 2.0
        last = None
        for attempt in range(1, retries + 1):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                text = (resp.choices[0].message.content or "").strip()
                if not text:
                    last = ChatError(f"empty content (attempt {attempt})")
                else:
                    return text, (resp.choices[0].finish_reason or "stop")
            except Exception as e:  # 网络 / 429 / 5xx / 超时
                last = e
            if attempt < retries:
                time.sleep(delay + random.random())
                delay = min(delay * 2, 30)
        raise ChatError(f"chat failed after {retries} attempts: {last}")

    def chat_json(self, blocks, **kw):
        text, finish = self.chat(blocks, json_mode=True, **kw)
        return parse_json_lenient(text), finish

    def build_file_block(self, file_id):
        """把 Files API 返回的 ID 构造成消息图片块。

        参数：
            file_id: Files API 返回的文件 ID。
        返回值：
            ``{"type": "file", "file_id": ...}`` 消息块。
        异常：
            ``ChatError``：file_id 为空。
        """
        value = str(file_id or "").strip()
        if not value:
            raise ChatError("file_id cannot be empty")
        return {"type": "file", "file_id": value}

    def _image_data_url(self, source):
        """将本地图片转换为 data URL；远程 URL/data URL 原样返回。"""
        value = os.fspath(source)
        if value.startswith(("http://", "https://", "data:")):
            return value

        image_path = Path(value)
        if not image_path.is_file():
            raise ChatError(f"image file not found: {image_path}")
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
        if not mime_type.startswith("image/"):
            raise ChatError(f"not an image file: {image_path}")
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def build_image_url_block(self, source, detail="high"):
        """构造 ``image_url`` 消息块。

        参数：
            source: 远程图片 URL、data URL 或本地图片路径。
            detail: 视觉细节级别，默认 ``high``。
        返回值：
            OpenAI Chat Completions 兼容的 ``image_url`` 消息块。
        异常：
            ``ChatError``：本地图片不存在或不是图片文件。
        """
        return {
            "type": "image_url",
            "image_url": {"url": self._image_data_url(source), "detail": detail},
        }

    def build_image_block(self, source, input_mode=None, detail="high"):
        """按选择的输入模式构造图片消息块。

        参数：
            source: ``file`` 模式下为本地图片路径，``image_url`` 模式下也可为 URL/data URL。
            input_mode: 本次调用的模式；为空时使用客户端模式。
            detail: ``image_url`` 模式的视觉细节级别。
        返回值：
            ``file`` 模式返回 file block；``image_url`` 模式返回 image_url block。
        异常：
            ``ChatError``：上传失败、图片不存在或格式不支持。
        """
        mode = resolve_input_mode(input_mode or self.input_mode)
        if mode == "file":
            return self.build_file_block(self.upload_image(os.fspath(source)))
        return self.build_image_url_block(source, detail=detail)

    def upload_image(self, path):
        """上传图片到 Files API，返回 file_id。带指数退避重试。"""
        delay = 2.0
        last = None
        for attempt in range(1, 5):
            try:
                with open(path, "rb") as f:
                    return self.client.files.create(file=f, purpose="user_data").id
            except Exception as e:
                last = e
            if attempt < 4:
                time.sleep(delay + random.random())
                delay = min(delay * 2, 30)
        raise ChatError(f"upload failed for {path}: {last}")

    def file_exists(self, file_id):
        try:
            self.client.files.retrieve(file_id)
            return True
        except Exception:
            return False
