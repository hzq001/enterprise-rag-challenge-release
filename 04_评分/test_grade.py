"""grade.py 评分口径回归测试：缺题计 0 分但权重仍进分母（官方 rank.py 口径）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_评分"))

import grade


class ScoringDenominatorTest(unittest.TestCase):
    def key(self):
        return {
            "Q1": {"kind": "number", "answers": [100]},
            "Q2": {"kind": "number", "answers": [200]},
        }

    def full(self, extra=None):
        sub = [
            {"question_text": "Q1", "kind": "number", "value": 100},
            {"question_text": "Q2", "kind": "number", "value": 200},
        ]
        if extra:
            sub.extend(extra)
        return sub

    def test_missing_question_counts_zero_with_full_denominator(self):
        sub = [{"question_text": "Q1", "kind": "number", "value": 100}]
        total, ideal, per, detail, missing = grade.score(self.key(), sub)
        self.assertEqual((total, ideal), (2.0, 4.0))
        self.assertEqual(missing, ["Q2"])
        self.assertEqual(per["number"], [2.0, 4.0, 2])     # 得分/满分/题数

    def test_complete_submission_keeps_identical_scores(self):
        total, ideal, per, detail, missing = grade.score(self.key(), self.full())
        self.assertEqual((total, ideal), (4.0, 4.0))
        self.assertEqual(per["number"], [4.0, 4.0, 2])
        self.assertEqual(missing, [])

    def test_wrong_value_scores_zero_but_keeps_weight(self):
        sub = [
            {"question_text": "Q1", "kind": "number", "value": 100},
            {"question_text": "Q2", "kind": "number", "value": 999},
        ]
        total, ideal, _, _, _ = grade.score(self.key(), sub)
        self.assertEqual((total, ideal), (2.0, 4.0))


class InputValidationTest(unittest.TestCase):
    def test_malformed_json_exits_with_clear_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("not json", encoding="utf-8")
            with self.assertRaises(SystemExit):
                grade.load_json(bad, "提交")

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            grade.load_json(Path("/nonexistent/x.json"), "答案键")


if __name__ == "__main__":
    unittest.main()
