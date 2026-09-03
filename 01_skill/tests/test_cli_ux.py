"""show.py / router.py 的 CLI 失败模式回归测试。"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import fitz

import router

SHOW = SCRIPT_DIR / "show.py"


def make_pdf(path: Path, pages: int = 2) -> Path:
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page()
        page.insert_text((72, 72), f"page {i}")
    doc.save(str(path))
    doc.close()
    return path


class ShowCliTest(unittest.TestCase):
    def run_show(self, pdf: Path, pages: str, out: Path):
        return subprocess.run(
            [sys.executable, str(SHOW), str(pdf), "--pages", pages, "--out", str(out)],
            capture_output=True,
            text=True,
        )

    def test_valid_pages_render_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            r = self.run_show(make_pdf(tmp / "mini.pdf"), "1-2", tmp / "out")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(sorted(p.name for p in (tmp / "out").glob("*.png")),
                             ["mini_p1.png", "mini_p2.png"])

    def test_all_pages_out_of_range_exits_nonzero_with_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out = tmp / "out"
            r = self.run_show(make_pdf(tmp / "mini.pdf"), "99", out)
            self.assertEqual(r.returncode, 1)
            self.assertIn("没有渲染任何页面", r.stderr)
            self.assertEqual(list((tmp / "out").glob("*.png")), [])

    def test_encrypted_pdf_exits_with_friendly_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pdf = tmp / "enc.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "secret")
            doc.save(str(pdf), encryption=fitz.PDF_ENCRYPT_AES_256,
                     owner_pw="owner", user_pw="user")
            doc.close()
            r = self.run_show(pdf, "1", tmp / "out")
            self.assertEqual(r.returncode, 1)
            self.assertIn("加密", r.stderr)

    def test_malformed_pages_argument_uses_argparse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            r = self.run_show(make_pdf(tmp / "mini.pdf"), "6-", tmp / "out")
            self.assertEqual(r.returncode, 2)
            self.assertIn("无法解析页码", r.stderr)


class RouterFallbackTest(unittest.TestCase):
    def test_classify_falls_back_without_pdf_inspector(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = make_pdf(Path(tmp) / "mini.pdf")
            # 把 pdf_inspector 标记为不可导入，走纯 PyMuPDF 回退路径。
            with patch.dict(sys.modules, {"pdf_inspector": None}):
                labels, _, _ = router.classify_pdf(pdf, 0)
        self.assertEqual(set(labels), {1, 2})


if __name__ == "__main__":
    unittest.main()
