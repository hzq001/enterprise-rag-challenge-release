#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通用评分器 —— 严格镜像官方 rank.py 的 compare()，可评任意轮次。

为什么独立成脚本
----------------
评分口径若有偏差，所有优化方向都会被带偏（本项目踩过两次：
把 names 当精确匹配、给 number 发 0.5 部分分，都与官方不符）。
本脚本不依赖任何轮次专用路径，随发布包一起分发。

官方口径要点
------------
  number  : abs(pred - gt) < 0.01 * gt      （1% 相对容差，无部分分）
  boolean : str(gt).lower() == str(pred).lower()
  name    : 精确字符串比较（小写、trim）
  names   : Jaccard = |交集| / |并集|，GT 侧按逗号 split（有部分分）
  权重    : GT 为 N/A 的题 1 分，其余（检索题）2 分

用法
----
  python grade.py --questions round5_questions.json ^
                  --key round5_answers_key.json ^
                  --submission round5_被测方提交.json [--show-wrong]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_NONES = ("N/A", "n/a", None, "")


def is_na(v):
    if isinstance(v, list):
        return len(v) == 0
    return v is None or (isinstance(v, str) and v.strip().lower() in ("n/a", "na", ""))


def compare(kind, gt, pred):
    """镜像 rank.py::compare(schema, actual, predicted)。gt=actual, pred=predicted。"""
    gt_na, pred_na = is_na(gt), is_na(pred)
    if gt_na and pred_na:
        return 1.0
    if gt_na or pred_na:
        return 0.0

    if kind == "number":
        try:
            a, p = float(gt), float(pred)
        except (TypeError, ValueError):
            return 0.0
        return 1.0 if abs(p - a) < 0.01 * abs(a) else 0.0

    if kind == "boolean":
        return 1.0 if str(gt).strip().lower() == str(pred).strip().lower() else 0.0

    if kind == "name":
        return 1.0 if str(gt).strip().lower() == str(pred).strip().lower() else 0.0

    if kind == "names":
        gts = [x.strip().lower() for x in str(gt).split(",") if x.strip()]
        if isinstance(pred, str):
            ps = [x.strip().lower() for x in pred.split(",") if x.strip()]
        else:
            ps = [str(x).strip().lower() for x in (pred or [])]
        union = len(set(gts) | set(ps))
        return (len(set(gts) & set(ps)) / union) if union else 0.0

    return 0.0


def weight(gt_answers):
    return 1 if any(is_na(a) for a in gt_answers) else 2


def score(key: dict, sub: list):
    """按官方口径评分：缺题计 0 分，但权重仍计入满分（与 rank.py 一致）。"""
    ours = {r["question_text"]: r for r in sub}
    total = ideal = 0.0
    per, detail = {}, []
    missing = [q for q in key if q not in ours]
    for q, v in key.items():
        w = weight(v["answers"])
        ideal += w
        d = per.setdefault(v["kind"], [0.0, 0.0, 0])
        d[1] += w
        d[2] += 1
        if q not in ours:
            continue
        g = max(compare(v["kind"], gt, ours[q]["value"]) for gt in v["answers"])
        total += g * w
        d[0] += g * w
        detail.append((q, v["kind"], v["answers"], ours[q]["value"], g, w))
    return total, ideal, per, detail, missing


def load_json(path: Path, label: str):
    """读取 JSON 输入，文件缺失或格式错误时给出可读错误并退出。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        sys.exit(f"无法读取{label}文件: {path}（{e}）")
    except json.JSONDecodeError as e:
        sys.exit(f"{label}文件不是有效 JSON: {path}（第 {e.lineno} 行）")


def main():
    ap = argparse.ArgumentParser(description="官方口径评分器（任意轮次）")
    ap.add_argument("--questions", required=True, help="题集 JSON（用于核对题数/题型）")
    ap.add_argument("--key", required=True, help="答案键 JSON")
    ap.add_argument("--submission", required=True, help="被测方提交 JSON")
    ap.add_argument("--show-wrong", action="store_true", help="列出所有未满分的题")
    args = ap.parse_args()

    key = load_json(Path(args.key), "答案键")
    if not isinstance(key, dict) or not key:
        sys.exit(f"答案键文件应为非空对象: {args.key}")
    sub = load_json(Path(args.submission), "提交")
    if isinstance(sub, dict):                      # 兼容 {"answers": [...]} 提交格式
        sub = sub.get("answers")
    if not isinstance(sub, list):
        sys.exit(f"提交文件应为数组或 {{'answers': [...]}}: {args.submission}")
    qs = load_json(Path(args.questions), "题集")

    total, ideal, per, detail, missing = score(key, sub)
    print(f"=== {Path(args.submission).name} ===")
    print(f"题数: {len(qs)} | 提交: {len(sub)} | 键: {len(key)}")
    if missing:
        print(f"⚠️ 提交缺失 {len(missing)} 题")
    print(f"\n{'kind':<10}{'题数':>5}{'得分':>10}{'满分':>7}{'占比':>8}")
    for k, (s, m, n) in sorted(per.items()):
        print(f"{k:<10}{n:>5}{s:>10.2f}{m:>7.0f}{100*s/m:>7.1f}%")
    print(f"{'总计':<10}{sum(v[2] for v in per.values()):>5}{total:>10.2f}{ideal:>7.0f}"
          f"{100*total/ideal:>7.2f}%" if ideal else "（无题目）")

    if args.show_wrong:
        print("\n=== 未满分的题 ===")
        for i, (q, k, gt, pv, g, w) in enumerate(detail, 1):
            if g < 1:
                print(f"Q{i} [{k:<7}] {g:.2f}x{w}  期望={str(gt)[:46]:<46} 提交={str(pv)[:34]}")
                print(f"        {q[:96]}")


if __name__ == "__main__":
    main()
