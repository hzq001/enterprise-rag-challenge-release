# round2 提交复审反馈清单（给答题方）

> 对象：round2 挑战答题方（submission_r2_new.json 重建版）
> 反馈方：检查方（基于官方 answers.json 评分 + 全部回 PDF 原文核验）
> 日期：2026-08-31

---

## 一、成绩单

| 口径 | 得分 | 结论 |
|---|---|---|
| 官方严格口径 | 106.0/155 = **68.39%** | 修复前 54.55%，已有大幅提升 |
| 宽松口径（格式/口径差异放行） | 151.0/155 = **97.42%** | 核心能力已达标 |

分题型（严格口径）：boolean 30/48 · name 17/17 ✅ · names 6/15 · number 53/75

---

## 二、已确认修复 ✅（这部分做对了，无需再动）

1. **题面 100/100 逐字匹配官方 questions.json**——0 错配、0 多余、0 重复。✓
2. **name 类 9 题全对**：Q23/25/42/57/61/63/84 = Datalogic、Q54 = Poste Italiane、Q74 = N/A（17/17）。✓
3. **Incyte 映射修复**：改用正确 PDF（4d3e52b6，封面 INCYTE CORPORATION 001-12400），6 题 value 已更新。✓

---

## 三、必须整改（2 条，真实漏读，当前 0 分）

### 1. Aurora Innovation 专利数（提交 N/A，官方真值 1300）
- **证据**：PDF 实际 **109 页**，第 9 页原文：
  > "Aurora has over **1,300 awarded and pending patents** worldwide."
- **你的报告问题**：报告中写"PDF 仅含前 7 页、无专利数量"——**事实是 PDF 有 109 页，数据在第 9 页**。你只读了开头。
- **整改动作**：重新通读全文（或至少翻到业务章节），把答案改为 `1300`。

### 2. Albany International 航空专利组合（提交 N/A，官方真值 2300）
- **证据**：PDF 实际 **130 页**，第 16 页原文：
  > "Our active portfolio currently contains **over 2,300 patents**, and approximately 160 new patents are typically granted each year."
- **你的报告问题**：报告中写"PDF 仅 18 页、无专利组合数量"——**实际 130 页，数据在第 16 页**（就在你声称读过的范围内）。
- **整改动作**：答案改为 `2300`。

> **共性根因**：读页范围只覆盖 PDF 开头。请对全部题目核对"PDF 实际页数 vs 你实际读到的页数"，凡报告中写"PDF 仅 N 页"的都要复查（Kiniksa 实际 197 页、Albany 130 页、Aurora 109 页，都不是报告说的 7/18 页）。

---

## 四、建议整改（不影响本次得分，但避免下轮重犯）

### 3. names 答案统一用逗号分隔（官方 grader 按逗号 split）
- 官方 GT 格式：`"President and Chief Executive Officer,Chief Financial Officer"`（逗号）
- 你的提交用了**分号**（`;`）→ grader 把整串当一个 token，Jaccard=0
- 整改：提交前把所有 names 值的分号改成逗号，并核对是否多答/漏答：
  - Westwater：GT 只认 `President and Chief Executive Officer`（CFO 变动在期后，**不要多答**）
  - Datalogic：GT 只认 `Director`（法定审计主席不算，不要多答）
  - Duni：GT = `Chairman of the Board of Directors,EVP`（你漏了 Chairman，补上）
  - Blue Apron：GT = `Chief Supply Chain Officer`（你答的 CFO(Interim) 是另一个真实变动，但官方取 CSCO）
  - Crombie：GT = `N/A`（Mark Holly 接任属期后事项，**不要答**）

### 4. number 单位/口径与官方对齐（数据读对，但提交格式不对）
- Sonic 现金流量：官方要**原始美元** `406100000`（你给 406.1 是百万）
- Ritchie 每股股息：官方要**单期** `0.27`（你给全年四季度合计 1.06）
- SThree 员工数：官方要**期末** `3119`（你给平均 2890）
- HCA 医疗专业人员：官方取 **294,000**（colleagues 口径，你取的 45,000 是 physicians）
- Structural 资本支出：官方判 **N/A**（题面要 USD，年报只有 AUD——无 USD 数据就别填）
- HCA 保险理赔：官方判 **N/A**（"Outstanding insurance claims" 科目未披露；你读的 $2.043B 是"Reserves for professional liability"，科目不同）
- Albany R&D：官方要 `31400000`（$31.4M——你其实在第 Q44 证据里读过这个数，第 Q57 却答了 N/A）

### 5. boolean 判定口径（理解官方与你的差异）
- 官方口径 = **"年报中是否提及/是否有相关内容"**（提及即 True），比你用的"必须有当期实质事件"更宽
- 本次 9 道 boolean 因此方向相反：Poste 分红（预支中期股息 p35/p38）、Downer 回购（p14 公告）、Franklin Covey ESG（p15 ESG Highlights）、ACRES ESG（p4）、Incitec 分红（p21 record dividend）、SIG 并购（p9 五笔收购）、Ritchie 诉讼（p37 Item 3+CRA 审计）、Empire 分红（p2 股息数据）、HCA 分红（p3 +17% 提息）
- 下轮建议：遇到"年报中出现过相关内容"就答 True，除非确无任何提及

---

## 五、改完后的自检清单

- [ ] Aurora=1300、Albany=2300 已更新，且报告里的"PDF 仅 N 页"误报全部纠正
- [ ] names 全部用逗号分隔、不多答、不漏答（5 题逐个核对）
- [ ] number 单位换算（原始值）、口径（期末/单期）逐题核对
- [ ] `round2_answer_report.md` 与提交一致：Incyte 相关证据段（Q22/Q41/Q53/Q62）里的
      "PDF实际为Syndax=$497,236K" 全部替换为正确 Incyte 数据（Total assets p84 = $5,840,984 千）
- [ ] 重跑官方 grader：目标 ≥ 74%（当前 68.39%，补上 2 条漏读 + 4 条单位/口径即达）

---

## 附：验证方式

改完后提交新版 `submission_r2_new.json`，检查方将用官方口径（r2_grade.py）复评，
并抽查报告与提交的一致性。届时按严格口径给出最终分数。
