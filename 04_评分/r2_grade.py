#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立评分器：严格镜像官方 rank.py 的 compare()，逐行核对过源码。

为什么要独立成脚本
------------------
评分口径若有偏差，所有优化方向都会被带偏（本项目已踩过两次：
把 names 当精确匹配、给 number 发 0.5 部分分，都与官方不符）。
独立脚本可随时对任意提交文件复算，且不受主模块加载时机影响。

官方口径要点
------------
  number  : abs(pred - gt) < 0.01 * gt      （1% 相对容差，无部分分）
  boolean : str(gt).lower() == str(pred).lower()
  name    : 精确字符串比较（小写、trim）
  names   : Jaccard = |交集| / |并集|，GT 侧按逗号 split（有部分分）
  权重    : GT 为 N/A 的题 1 分，其余（检索题）2 分

用法
----
  python r2_grade.py submission_r2_text.json
  python r2_grade.py submission_r2_retry.json --diff submission_r2_text.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import r2paths  # noqa: E402
ROUND2 = Path(__file__).parent
ANSWERS_FILE = r2paths.file_of(__file__, "answers.json")
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


def score_file(path):
    an = json.loads(ANSWERS_FILE.read_text(encoding="utf-8"))
    sub = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(sub, dict):                       # 兼容 {"answers": [...]} 提交格式
        sub = sub.get("answers", [])
    ours = {r["question_text"]: r for r in sub}
    total = ideal = 0.0
    per, detail = {}, []
    for q, v in an.items():
        if q not in ours:
            continue
        w = weight(v["answers"])
        g = max(compare(v["kind"], gt, ours[q]["value"]) for gt in v["answers"])
        total += g * w
        ideal += w
        d = per.setdefault(v["kind"], [0.0, 0.0, 0])
        d[0] += g * w
        d[1] += w
        d[2] += 1
        detail.append((q, v["kind"], v["answers"], ours[q]["value"], g, w))
    return total, ideal, per, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sub")
    ap.add_argument("--diff", help="与该基线文件逐题对比，列出变好/变差的题")
    ap.add_argument("--show-wrong", action="store_true", help="列出所有未满分的题")
    args = ap.parse_args()

    total, ideal, per, detail = score_file(args.sub)
    print(f"=== {args.sub} ===")
    print(f"{'kind':<9}{'题数':>5}{'得分':>9}{'满分':>7}{'占比':>8}")
    for k, (s, m, n) in sorted(per.items()):
        print(f"{k:<9}{n:>5}{s:>9.2f}{m:>7.0f}{100*s/m:>7.1f}%")
    print(f"{'总计':<9}{sum(v[2] for v in per.values()):>5}{total:>9.2f}{ideal:>7.0f}"
          f"{100*total/ideal:>7.2f}%")
    print(f"\n参考: 全 N/A 基线 45(29.0%) | 榜首 122.2(78.8%)")

    if args.diff:
        t2, i2, p2, d2 = score_file(args.diff)
        base = {q: g for q, _, _, _, g, _ in d2}
        better = [(q, k, gt, pv, base[q], g) for q, k, gt, pv, g, w in detail
                  if q in base and g > base[q]]
        worse = [(q, k, gt, pv, base[q], g) for q, k, gt, pv, g, w in detail
                 if q in base and g < base[q]]
        print(f"\n=== 相对 {args.diff}（{t2:.2f} → {total:.2f}，"
              f"{'+' if total>=t2 else ''}{total-t2:.2f}）===")
        print(f"变好 {len(better)} 题 / 变差 {len(worse)} 题")
        for lbl, rows in (("✓ 变好", better), ("✗ 变差", worse)):
            for q, k, gt, pv, og, ng in rows:
                print(f"{lbl} [{k}] {og:.2f}→{ng:.2f}  期望={str(gt)[:40]}  我们={str(pv)[:40]}")
                print(f"        {q[:96]}")

    if args.show_wrong:
        print("\n=== 未满分的题 ===")
        for q, k, gt, pv, g, w in detail:
            if g < 1:
                print(f"[{k:<7}] {g:.2f}×{w}  期望={str(gt)[:40]:<40} 我们={str(pv)[:36]}")
                print(f"          {q[:98]}")


if __name__ == "__main__":
    main()
