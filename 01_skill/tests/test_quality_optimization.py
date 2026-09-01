import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from decimal import Decimal
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import fitz

import agentic_tools
import answer_quality
import ingest
import transcribe


class FinancialDisclosureRulesTest(unittest.TestCase):
    def test_parenthetical_number_preserves_negative_sign(self):
        self.assertEqual(
            answer_quality.parse_reported_number("($1,234.50)"),
            Decimal("-1234.50"),
        )

    def test_missing_row_is_na_but_explicit_dash_is_zero(self):
        missing = answer_quality.resolve_reported_value(False, None)
        self.assertEqual(missing["value"], "N/A")
        self.assertEqual(missing["disclosure_status"], "not_disclosed")

        explicit_zero = answer_quality.resolve_reported_value(True, "—")
        self.assertEqual(explicit_zero["value"], Decimal("0"))
        self.assertEqual(explicit_zero["disclosure_status"], "explicit_zero")

    def test_numeric_value_without_a_reported_row_is_rejected(self):
        with self.assertRaises(ValueError):
            answer_quality.resolve_reported_value(False, "0")


class ImportCompatibilityTest(unittest.TestCase):
    def test_documented_package_import_works_from_skill_directory(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from scripts.agentic_tools import verify_answer; print('ok')",
            ],
            cwd=SCRIPT_DIR.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("ok", completed.stdout)


class AnswerContractTest(unittest.TestCase):
    def number_answer(self):
        return {
            "question_text": "What was total revenue in 2022?",
            "kind": "number",
            "value": 69765000,
            "raw_value": "69,765",
            "scale": 1000,
            "unit": "in thousands",
            "currency": "USD",
            "period": "2022",
            "quote": "Total revenue 69,765 (in thousands of USD) for 2022",
            "disclosure_status": "reported",
            "references": [["Example Corp", 31]],
        }

    def test_number_answer_requires_context_and_validates_conversion(self):
        self.assertEqual(answer_quality.validate_answer_payload(self.number_answer()), [])

        invalid = self.number_answer()
        invalid.pop("currency")
        self.assertTrue(answer_quality.validate_answer_payload(invalid))

        invalid = self.number_answer()
        invalid["scale"] = 1
        self.assertTrue(answer_quality.validate_answer_payload(invalid))

    def test_na_answer_requires_exhaustive_disclosure_basis(self):
        answer = {
            "question_text": "What was gross margin?",
            "kind": "number",
            "value": "N/A",
            "disclosure_status": "not_disclosed",
            "search_exhausted": True,
            "searched_terms": ["gross margin", "gross profit"],
            "references": [["Example Corp", 31]],
        }
        self.assertEqual(answer_quality.validate_answer_payload(answer), [])

        invalid = dict(answer)
        invalid["search_exhausted"] = False
        self.assertTrue(answer_quality.validate_answer_payload(invalid))

        invalid = dict(answer)
        invalid["disclosure_status"] = "reported"
        self.assertTrue(answer_quality.validate_answer_payload(invalid))

    def test_boolean_answer_requires_a_real_boolean_value(self):
        answer = {
            "question_text": "Did the company announce a buyback?",
            "kind": "boolean",
            "value": 1,
            "rubric": "mentioned",
            "boolean_basis": "The report mentions a buyback.",
            "quote": "The report mentions a buyback plan.",
            "references": [["Example Corp", 31]],
        }
        errors = answer_quality.validate_answer_payload(answer)
        self.assertIn("boolean 的 value 必须是布尔值", errors)


class EvidenceVerificationTest(unittest.TestCase):
    def test_verify_quote_rejects_wrong_sign(self):
        quote = "Net loss (1,234)"
        evidence = [(12, quote)]

        ok, _ = agentic_tools.verify_quote(quote, evidence, "number", -1234)
        self.assertTrue(ok)

        ok, reason = agentic_tools.verify_quote(quote, evidence, "number", 1234)
        self.assertFalse(ok)
        self.assertIn("数字", reason)

    def test_verify_quote_requires_explicit_scale_and_context(self):
        quote = "Total revenue 69,765 (in thousands of USD) for 2022"
        evidence = [(31, quote)]

        ok, _ = agentic_tools.verify_quote(
            quote,
            evidence,
            "number",
            69765000,
            raw_value="69,765",
            scale=1000,
            unit="in thousands",
            currency="USD",
            period="2022",
        )
        self.assertTrue(ok)

        ok, _ = agentic_tools.verify_quote(
            quote,
            evidence,
            "number",
            69765000,
            raw_value="69,765",
            scale=1,
            unit="in thousands",
            currency="USD",
            period="2022",
        )
        self.assertFalse(ok)

    def test_verify_quote_rejects_unknown_kind_and_bad_evidence_shape(self):
        quote = "A valid reported value is 10"
        ok, reason = agentic_tools.verify_quote(
            quote, [(1, quote)], "unsupported", 10
        )
        self.assertFalse(ok)
        self.assertIn("kind", reason)

        ok, reason = agentic_tools.verify_quote(quote, ["not-a-page"], "name", "x")
        self.assertFalse(ok)
        self.assertIn("证据", reason)

    def test_verify_quote_accepts_numeric_zero_and_rejects_markdown_separator(self):
        numeric_zero = "Revenue 0 (in thousands of USD) for 2022"
        ok, _ = agentic_tools.verify_quote(
            numeric_zero,
            [(31, numeric_zero)],
            "number",
            0,
            raw_value=0,
            scale=1000,
            unit="in thousands",
            currency="USD",
            period="2022",
        )
        self.assertTrue(ok)

        dash_without_value = "Revenue 100 (in thousands of USD) for 2022\n| --- | --- |"
        ok, reason = agentic_tools.verify_quote(
            dash_without_value,
            [(31, dash_without_value)],
            "number",
            0,
            raw_value="—",
            scale=1000,
            unit="in thousands",
            currency="USD",
            period="2022",
        )
        self.assertFalse(ok)
        self.assertIn("零值", reason)

    def test_verify_answer_combines_contract_and_evidence_checks(self):
        answer = {
            "question_text": "What was total revenue in 2022?",
            "kind": "number",
            "value": 69765000,
            "raw_value": "69,765",
            "scale": 1000,
            "unit": "in thousands",
            "currency": "USD",
            "period": "2022",
            "quote": "Total revenue 69,765 (in thousands of USD) for 2022",
            "disclosure_status": "reported",
            "references": [["Example Corp", 31]],
        }
        ok, _ = agentic_tools.verify_answer(answer, [(31, answer["quote"])])
        self.assertTrue(ok)

        answer["search_exhausted"] = False
        answer["value"] = "N/A"
        answer["disclosure_status"] = "not_disclosed"
        ok, reason = agentic_tools.verify_answer(answer, [(31, answer["quote"])])
        self.assertFalse(ok)
        self.assertIn("穷尽", reason)


class CacheAndTableRoutingTest(unittest.TestCase):
    def test_render_pages_recreates_png_when_dpi_changes(self):
        with tempfile.TemporaryDirectory(prefix="enterprise-rag-render-") as tmp:
            output_dir = Path(tmp) / "pages"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "DPI-sensitive financial table")

            ingest.render_pages(doc, output_dir, 72)
            first = fitz.Pixmap(str(output_dir / "p0001.png"))
            first_size = (first.width, first.height)

            ingest.render_pages(doc, output_dir, 144)
            second = fitz.Pixmap(str(output_dir / "p0001.png"))
            second_size = (second.width, second.height)
            doc.close()

        self.assertNotEqual(first_size, second_size)
        self.assertGreater(second_size[0], first_size[0])
        self.assertGreater(second_size[1], first_size[1])

    def test_file_cache_reuploads_missing_file_or_changed_png(self):
        with tempfile.TemporaryDirectory(prefix="enterprise-rag-file-cache-") as tmp:
            root = Path(tmp)
            image = root / "p0001.png"
            image.write_bytes(b"first-image")
            files_json = root / "files.json"
            uploaded = []
            valid_ids = set()

            class FakeFileClient:
                input_mode = "file"

                def file_exists(self, file_id):
                    return file_id in valid_ids

                def upload_image(self, path):
                    uploaded.append(Path(path).read_bytes())
                    file_id = f"file-new-{len(uploaded)}"
                    valid_ids.add(file_id)
                    return file_id

            client = FakeFileClient()
            first = ingest.upload_all(client, [image], files_json, workers=1)
            self.assertEqual(first, {"1": "file-new-1"})

            valid_ids.remove("file-new-1")
            missing_remote = ingest.upload_all(client, [image], files_json, workers=1)
            self.assertEqual(missing_remote, {"1": "file-new-2"})

            image.write_bytes(b"second-image")
            second = ingest.upload_all(client, [image], files_json, workers=1)
            self.assertEqual(second, {"1": "file-new-3"})
            self.assertEqual(
                uploaded,
                [b"first-image", b"first-image", b"second-image"],
            )

    def test_cache_signature_invalidates_model_and_route_changes(self):
        signature = ingest.build_pipeline_signature(
            "auto",
            "mac",
            150,
            model="gpt-5.6-luna",
            base_url="http://localhost:8317/v1",
            input_mode="image_url",
        )
        old = {
            "pages_indexed": 3,
            "route": "auto",
            "ocr_engine": "mac",
            "pipeline": signature,
        }
        self.assertTrue(ingest.cache_is_usable(old, "auto", 3, "mac", signature))

        changed_model = dict(signature, model="deepseek-v4-flash-vision-exp")
        self.assertFalse(ingest.cache_is_usable(old, "auto", 3, "mac", changed_model))
        self.assertFalse(ingest.cache_is_usable(old, "vision", 3, None, signature))

    def test_table_pages_are_sent_one_page_per_vlm_call(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="enterprise-rag-table-batch-"))
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        pdf = temp_dir / "table.pdf"
        doc = fitz.open()
        for page_number in range(1, 3):
            page = doc.new_page()
            page.insert_text((72, 72), f"Revenue table page {page_number}")
        doc.save(str(pdf))
        doc.close()

        calls = []

        def chat(blocks, **kwargs):
            calls.append(blocks)
            marker = next(
                block["text"]
                for block in blocks
                if block.get("type") == "text" and "[第" in block.get("text", "")
            )
            page_number = re.search(r"第(\d+)页", marker).group(1)
            return f"[第{page_number}页]\n| 业务 | 收入 |\n| --- | --- |\n| A | 100 |", "stop"

        client = types.SimpleNamespace(
            input_mode="image_url",
            build_image_block=lambda source: {
                "type": "image_url",
                "image_url": {"url": str(source)},
            },
            chat=chat,
        )
        result = transcribe.transcribe_pages(
            client,
            pdf,
            {1: "TABLE", 2: "TABLE"},
            temp_dir / "cache",
            batch=10,
            dpi=72,
            ocr_engine="mac",
        )

        self.assertEqual(len(calls), 2)
        self.assertEqual(sorted(result), [1, 2])


if __name__ == "__main__":
    unittest.main()
