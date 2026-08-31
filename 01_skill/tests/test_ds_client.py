import base64
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from ds_client import DSClient, SUPPORTED_INPUT_MODES, resolve_input_mode


class DSClientInputModeTest(unittest.TestCase):
    def setUp(self):
        self.image = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        self.addCleanup(self._remove_image)
        self.image.write(b"fake-png")
        self.image.close()

    def _remove_image(self):
        try:
            os.unlink(self.image.name)
        except FileNotFoundError:
            pass

    def test_file_mode_builds_file_block_without_inline_data(self):
        client = DSClient(
            api_key="test-key",
            base_url="http://example.test/v1",
            model="file-model",
            input_mode="file",
        )
        uploaded = []
        client.upload_image = lambda path: uploaded.append(path) or "file-test-123"

        block = client.build_image_block(self.image.name)

        self.assertEqual(block, {"type": "file", "file_id": "file-test-123"})
        self.assertEqual(uploaded, [self.image.name])
        self.assertNotIn("image_url", block)

    def test_image_url_mode_builds_base64_data_url_without_upload(self):
        client = DSClient(
            api_key="test-key",
            base_url="http://example.test/v1",
            model="image-model",
            input_mode="image_url",
        )
        client.upload_image = lambda _: self.fail("image_url 模式不应调用 Files API")

        block = client.build_image_block(self.image.name)

        self.assertEqual(block["type"], "image_url")
        self.assertEqual(block["image_url"]["detail"], "high")
        self.assertTrue(block["image_url"]["url"].startswith("data:image/png;base64,"))
        encoded = block["image_url"]["url"].split(",", 1)[1]
        self.assertEqual(base64.b64decode(encoded), b"fake-png")

    def test_image_url_mode_accepts_remote_url(self):
        client = DSClient(api_key="test-key", input_mode="image_url")

        block = client.build_image_block("https://example.test/page.png")

        self.assertEqual(
            block,
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.test/page.png",
                    "detail": "high",
                },
            },
        )

    def test_invalid_input_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_input_mode("multipart")
        self.assertEqual(SUPPORTED_INPUT_MODES, ("file", "image_url"))

    def test_model_and_input_mode_can_be_selected_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "VISION_BASE_URL": "http://localhost:8317/v1",
                "VISION_MODEL": "gpt-5.6-luna",
                "VISION_INPUT_MODE": "image_url",
            },
            clear=False,
        ):
            client = DSClient(api_key="test-key")

        self.assertEqual(client.base_url, "http://localhost:8317/v1")
        self.assertEqual(client.model, "gpt-5.6-luna")
        self.assertEqual(client.input_mode, "image_url")

    def test_chat_sends_selected_model(self):
        client = DSClient(
            api_key="test-key",
            base_url="http://example.test/v1",
            model="gpt-5.6-luna",
            input_mode="image_url",
        )
        captured = {}

        def create(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                choices=[
                    types.SimpleNamespace(
                        message=types.SimpleNamespace(content="ok"),
                        finish_reason="stop",
                    )
                ]
            )

        client.client = types.SimpleNamespace(
            chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
        )

        text, finish = client.chat(
            [{"type": "text", "text": "hello"}], retries=1, max_tokens=16
        )

        self.assertEqual(text, "ok")
        self.assertEqual(finish, "stop")
        self.assertEqual(captured["model"], "gpt-5.6-luna")


class ImageBlockFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPT_DIR))
        import ingest
        import transcribe

        cls.ingest = ingest
        cls.transcribe = transcribe

    def test_ingest_uses_image_url_block_when_selected(self):
        client = types.SimpleNamespace(
            input_mode="image_url",
            build_image_block=lambda source: {
                "type": "image_url",
                "image_url": {"url": source, "detail": "high"},
            },
        )

        blocks = self.ingest.batch_blocks(client, [1], {"1": "data:image/png;base64,abc"})

        self.assertEqual(blocks[1]["type"], "image_url")
        self.assertEqual(blocks[1]["image_url"]["url"], "data:image/png;base64,abc")

    def test_ingest_uses_file_block_when_selected(self):
        client = types.SimpleNamespace(
            input_mode="file",
            build_file_block=lambda file_id: {"type": "file", "file_id": file_id},
        )

        blocks = self.ingest.batch_blocks(client, [1], {"1": "file-test-123"})

        self.assertEqual(blocks[1], {"type": "file", "file_id": "file-test-123"})

    def test_transcribe_image_url_mode_skips_upload_and_files_cache(self):
        client = types.SimpleNamespace(
            input_mode="image_url",
            upload_image=lambda _: self.fail("image_url 模式不应调用 Files API"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            files_json = Path(tmp) / "files.json"
            page_pngs = {3: Path(tmp) / "page-3.png"}
            result = self.transcribe._upload(client, page_pngs, files_json)

        self.assertEqual(result, {"3": str(page_pngs[3])})
        self.assertFalse(files_json.exists())


class ReadVisionFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import agentic_tools

        cls.agentic_tools = agentic_tools

    def setUp(self):
        import fitz

        self.temp_dir = Path(tempfile.mkdtemp(prefix="enterprise-rag-read-vision-"))
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        self.pdf_path = self.temp_dir / "report.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "test financial report")
        doc.save(str(self.pdf_path))
        doc.close()

    def test_read_vision_passes_image_url_block_and_detail(self):
        captured = {}

        class FakeClient:
            def build_image_block(self, source, input_mode=None, detail="high"):
                captured["source"] = source
                captured["input_mode"] = input_mode
                captured["detail"] = detail
                return {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,test", "detail": detail},
                }

            def chat(self, blocks, **kwargs):
                captured["blocks"] = blocks
                captured["chat_kwargs"] = kwargs
                return "vision answer", "stop"

        answer = self.agentic_tools.read_vision(
            self.pdf_path,
            0,
            "读取页面内容",
            cache_dir=self.temp_dir / "cache",
            dpi=72,
            client=FakeClient(),
            input_mode="image_url",
            detail="low",
        )

        self.assertEqual(answer, "vision answer")
        self.assertEqual(captured["input_mode"], "image_url")
        self.assertEqual(captured["detail"], "low")
        self.assertTrue(Path(captured["source"]).is_file())
        self.assertEqual(captured["blocks"][0], {"type": "text", "text": "读取页面内容"})
        self.assertEqual(captured["blocks"][1]["type"], "image_url")
        self.assertEqual(captured["chat_kwargs"]["thinking"], False)

    def test_read_vision_constructs_client_with_selected_model_and_base_url(self):
        captured = {}

        class FakeClient:
            def __init__(self, **kwargs):
                captured["client_kwargs"] = kwargs

            def build_image_block(self, source, input_mode=None, detail="high"):
                return {"type": "file", "file_id": "file-test-123"}

            def chat(self, blocks, **kwargs):
                captured["blocks"] = blocks
                return "file answer", "stop"

        with patch("ds_client.DSClient", FakeClient):
            answer = self.agentic_tools.read_vision(
                self.pdf_path,
                0,
                "读取页面内容",
                cache_dir=self.temp_dir / "cache",
                dpi=72,
                model="gpt-5.6-luna",
                base_url="http://localhost:8317/v1",
                input_mode="file",
            )

        self.assertEqual(answer, "file answer")
        self.assertEqual(
            captured["client_kwargs"],
            {
                "model": "gpt-5.6-luna",
                "base_url": "http://localhost:8317/v1",
                "input_mode": "file",
            },
        )
        self.assertEqual(captured["blocks"][1], {"type": "file", "file_id": "file-test-123"})


if __name__ == "__main__":
    unittest.main()
