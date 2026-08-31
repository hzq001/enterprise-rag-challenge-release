import json
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

import fitz

import ingest
import mac_ocr
import router
import transcribe


class MacOCRRoutingTest(unittest.TestCase):
    def test_resolve_ocr_engine_defaults_to_mac_and_accepts_vlm(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mac_ocr.resolve_ocr_engine(), "mac")
        self.assertEqual(mac_ocr.resolve_ocr_engine("vision"), "mac")
        self.assertEqual(mac_ocr.resolve_ocr_engine("vlm"), "vlm")

    def test_invalid_ocr_engine_is_rejected(self):
        with self.assertRaises(ValueError):
            mac_ocr.resolve_ocr_engine("tesseract")

    def test_auto_routes_scan_to_mac_and_tables_to_vlm(self):
        native, vision = ingest.split_auto_labels(
            {1: "SCAN", 2: "GARBLED", 3: "TABLE", 4: "GRAPHIC", 5: "TEXT"},
            "mac",
        )
        self.assertEqual(native, {1: "SCAN", 2: "GARBLED"})
        self.assertEqual(vision, {3: "TABLE", 4: "GRAPHIC"})

    def test_auto_can_explicitly_route_scan_to_vlm(self):
        native, vision = ingest.split_auto_labels({1: "SCAN", 2: "TABLE"}, "vlm")
        self.assertEqual(native, {})
        self.assertEqual(vision, {1: "SCAN", 2: "TABLE"})

    def test_auto_cache_requires_matching_ocr_engine(self):
        old = {"pages_indexed": 3, "total_pages": 3}
        self.assertFalse(ingest.cache_is_usable(old, "auto", 3, "mac"))
        old["ocr_engine"] = "mac"
        self.assertTrue(ingest.cache_is_usable(old, "auto", 3, "mac"))
        self.assertTrue(ingest.cache_is_usable({"pages_indexed": 3}, "text", 3))


class RouterClassificationTest(unittest.TestCase):
    def test_chinese_text_is_not_misclassified_as_garbled(self):
        text = "生益科技主营业务包括覆铜板、电子材料和其他业务，报告期内收入持续增长。" * 2
        self.assertFalse(router._is_garbled(text))

    def test_table_page_wins_over_short_english_garbled_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "table.pdf"
            doc = fitz.open()
            page = doc.new_page()
            rows = [
                ["Segment", "2025 Revenue", "2024 Revenue", "YoY"],
                ["Copper Clad", "100.00", "80.00", "25.00%"],
                ["Materials", "60.00", "50.00", "20.00%"],
            ]
            widths = [150, 110, 110, 90]
            for row_index, row in enumerate(rows):
                x = 72
                for col_index, value in enumerate(row):
                    rect = fitz.Rect(x, 100 + row_index * 34,
                                     x + widths[col_index], 134 + row_index * 34)
                    page.draw_rect(rect, color=(0, 0, 0), width=0.7)
                    page.insert_textbox(rect, value, fontsize=11, align=1)
                    x += widths[col_index]
            doc.save(str(pdf_path))
            doc.close()

            labels, _, _ = router.classify_pdf(pdf_path, limit=1)

        self.assertEqual(labels[1], "TABLE")

    def test_full_page_scanned_image_is_not_misclassified_as_graphic(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "scanned.pdf"
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            page.insert_image(page.rect, filename=str(
                Path(__file__).resolve().parents[1] / "scripts/_human_demo/q30_p35.png"
            ))
            doc.save(str(pdf_path))
            doc.close()

            labels, _, _ = router.classify_pdf(pdf_path, limit=1)

        self.assertEqual(labels[1], "SCAN")


class MacOCRProcessTest(unittest.TestCase):
    def test_ocr_pages_calls_swift_and_maps_results_by_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page1 = root / "p0001.png"
            page2 = root / "p0002.png"
            page1.write_bytes(b"png-1")
            page2.write_bytes(b"png-2")
            stdout = json.dumps(
                {
                    "pages": [
                        {"path": str(page2.resolve()), "text": "第二页"},
                        {"path": str(page1.resolve()), "text": "第一页"},
                    ]
                },
                ensure_ascii=False,
            )
            completed = types.SimpleNamespace(returncode=0, stdout=stdout, stderr="")
            with patch("mac_ocr.platform.system", return_value="Darwin"), \
                    patch("mac_ocr.subprocess.run", return_value=completed) as run:
                result = mac_ocr.ocr_pages(
                    {2: page2, 1: page1},
                    swift_executable="/usr/bin/swift",
                )

        self.assertEqual(result, {1: "第一页", 2: "第二页"})
        command = run.call_args.args[0]
        self.assertEqual(command[0:2], ["/usr/bin/swift", str(mac_ocr.SWIFT_SCRIPT)])
        self.assertEqual(command[2:], [str(page1.resolve()), str(page2.resolve())])

    def test_ocr_pages_fails_loudly_when_swift_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "p0001.png"
            page.write_bytes(b"png")
            completed = types.SimpleNamespace(returncode=1, stdout="", stderr="Vision failed")
            with patch("mac_ocr.platform.system", return_value="Darwin"), \
                    patch("mac_ocr.subprocess.run", return_value=completed):
                with self.assertRaises(mac_ocr.MacOCRError):
                    mac_ocr.ocr_pages({1: page}, swift_executable="swift")


class TranscribeRoutingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="enterprise-rag-mac-ocr-"))
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        self.pdf_path = self.temp_dir / "report.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "test financial report")
        doc.save(str(self.pdf_path))
        doc.close()

    def test_mac_engine_uses_local_ocr_without_upload(self):
        with patch("transcribe.mac_ocr.ocr_pages", return_value={1: "本地 OCR 文本"}) as ocr:
            with patch.object(transcribe, "_upload", side_effect=AssertionError("不应上传")):
                result = transcribe.transcribe_pages(
                    None,
                    self.pdf_path,
                    {1: "SCAN"},
                    self.temp_dir / "cache",
                    dpi=72,
                    ocr_engine="mac",
                )

        self.assertEqual(result, {1: "本地 OCR 文本"})
        ocr.assert_called_once()

    def test_mac_engine_routes_table_pages_to_vlm(self):
        calls = []
        client = types.SimpleNamespace(
            input_mode="image_url",
            build_image_block=lambda source: {"type": "image_url", "image_url": {"url": str(source)}},
            chat=lambda blocks, **kwargs: calls.append(kwargs["system"]) or (
                "[第1页]\n| Segment | Revenue |\n| --- | --- |\n| Copper Clad | 100 |",
                "stop",
            ),
        )
        result = transcribe.transcribe_pages(
            client,
            self.pdf_path,
            {1: "TABLE"},
            self.temp_dir / "cache",
            dpi=72,
            ocr_engine="mac",
        )

        self.assertEqual(len(calls), 1)
        self.assertIn("表头", calls[0])
        self.assertIn("Copper Clad", result[1])

    def test_vlm_engine_uses_table_prompt_for_table_pages(self):
        captured = {}

        def chat(blocks, **kwargs):
            captured["system"] = kwargs["system"]
            return "【第1页】\n| 业务 | 收入 |\n| --- | --- |\n| 覆铜板 | 100 |", "stop"

        client = types.SimpleNamespace(
            input_mode="image_url",
            build_image_block=lambda source: {
                "type": "image_url",
                "image_url": {"url": str(source), "detail": "high"},
            },
            chat=chat,
        )
        result = transcribe.transcribe_pages(
            client,
            self.pdf_path,
            {1: "TABLE"},
            self.temp_dir / "cache",
            dpi=72,
            ocr_engine="vlm",
        )

        self.assertIn("表头", captured["system"])
        self.assertIn("覆铜板", result[1])
        self.assertNotIn("【第1页】", result[1])


if __name__ == "__main__":
    unittest.main()
