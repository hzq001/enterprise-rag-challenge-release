# Round4 交叉检查报告 — 另一AI 提交 vs 我方答案键

- 提交：`round4/submission_r4.json`（33 条，含 `_note` 证据）
- 答案键：`round4/new_answers.json`（我方制作，逐题读原文核实）
- 评分口径：官方 rank.py（number 1% 容差 / boolean+name 精确 / names Jaccard / N-A 权重1、其余2）
- 复核方式：每题争议均回到 `round2/pdfs/<sha>.pdf` 原文重新核读

---

## 一、总评分

### 按我方原键（机械评分）
| kind | 题数 | 得分 | 满分 | 占比 |
|---|---|---|---|---|
| boolean | 10 | 20.0 | 20 | 100.0% |
| number | 16 | 21.0 | 28 | 75.0% |
| names | 3 | 4.0 | 6 | 66.7% |
| name | 4 | 2.0 | 8 | 25.0% |
| **总计** | **33** | **47.0** | **62** | **75.81%** |

### 修正我方键错误（Q30）+ 按官方"names 部分分"口径（Q27/Q28）后
→ **51.0 / 62 ≈ 82.26%**（boolean 满分、number 命中率高，方法与 round3 相当、整体可复现）

---

## 二、逐题裁定（9 处失分）

### 我方键错误 / 题设歧义（3 处，另一AI 基本无辜或对）
| # | 我方键 | 另一AI | 原文证据 | 裁定 |
|---|---|---|---|---|
| Q30 Brave Bison 职位 | Director | **Non-Executive Director** | p21/p23 "Gordon Brough (Committee Chair and **Independent Non-Executive Director**)"、"Matthew and I are **Non-Executive Directors**" | **我键错**（重复 round3 SThree 教训：未用报告原词），另一AI 对 |
| Q12 Elixir 营收 | 38926 | 0 | p30 营收段 "Interest income 38,926 / Foreign exchange gain 431,446 / Other –" | **题设歧义**（38,926 或含 FX 合计 470,372 皆可）；另一AI 答 0 明显错（报告确有营收行） |
| Q1 CoreCard 营收 | 69765000 | 69765 | p31 MD&A "Total revenue … was **$69,765,000**"；FS 为千元口径 | 键与 MD&A 一致；另一AI 把千元数当 USD（其 note 自称 "keep raw figure"）→ **单位换算错** |

### 另一AI 错误（我方键正确，4 处 N/A 纪律 + 2 处漏答 + 1 处员工数误读）
| # | 我方键 | 另一AI | 原文证据 | 裁定 |
|---|---|---|---|---|
| Q14 Armadale 营收 | N/A | 0 | p22 利润表无营收行（Admin exp→Operating loss→Loss），p9 明说 "did not earn any revenues" | **另一AI 错**：无营收行=数据不可得→N/A（对照 Terns 有 "$—" 行才答 0） |
| Q15 Ocugen 营收 | N/A | 0 | p117 利润表直接以 Operating expenses 开头，无 Revenue 行 | **另一AI 错**：同上，无营收行→N/A |
| Q16 Kiniksa 毛利率 | N/A | 89.6 | 全文无 gross margin 披露；**round2 官方口径：Ritchie（有营收有COGS）毛利率 GT 也是 N/A**，不认自算 | **另一AI 错**：自算 (220,180−22,895)/220,180，违反"按年报披露"口径 |
| Q27 BetMakers 职位 | CEO of North America,Non-Executive Director | Non-Executive Director | p6/p9 "appointed … Christian Stuart to the **key role of Chief Executive Officer of North America**"；"Appointed Rebekah Giles / Anna Massion as independent non-executive director" | **另一AI 漏答**：只答 NED，漏 CEO of North America（官方口径为多值 names，部分分见下） |
| Q28 Franklin Covey 职位 | Executive Chairman,Chief Executive Officer | Chief Executive Officer | p22 "appointment of Robert A. Whitman as **Executive Chairman** and Chairman of the Board and Paul S. Walker as **Chief Executive Officer**, roles no longer combined" | **另一AI 漏答**：只答 CEO（其 note 已见 Whitman 但未写入 value） |
| Q32 names 最低员工 | Armadale Capital Plc | James Halstead | Armadale p40 "average monthly number … **Management 3**"；James Halstead p47 集团 **819**（p67 母公司仅 22） | **另一AI 双重错**：用母公司口径 22 而非集团 819，且漏了 Armadale 的 3 人 |

---

## 三、结论

### 另一AI 的亮点（较 round3 明显进步）
- **boolean 10/10 = 100% 满分**（round3 有 1 处校准错误，本轮零失误——Medallion/Ritchie/Ziff/Franklin Covey/Downer 全部判对，5 个 False 陷阱全部识破）
- number 11/16 命中，**多币种多单位全部正确**（Seiko JPY 百万、SIG GBP 百万、FNCB/Ritchie/Albany 千元、BetMakers AUD）
- N/A 中的 abrdn 员工判对（"has no employees"）；names 中 Poste 最高、AA 最高判对

### 另一AI 的系统性弱点（本轮失分主因）
1. **N/A 纪律（-3 题）**：Ocugen/Armadale 把"无营收行"推断成 0、Kiniksa 自算毛利率——正确做法是"数据未披露→N/A"（round2 官方对 Ritchie 毛利率同样答 N/A）
2. **多值 name 漏答（-2 题）**：BetMakers 漏 CEO of North America、Franklin Covey 漏 Executive Chairman（官方 names 口径下有部分分）
3. **单位/口径**：CoreCard 千元未换算成 USD；Q32 误用母公司员工数 22（应为集团 819）

### 我方答案键的 3 处问题（下轮修正）
1. **Q30 键错**：Brave Bison 应为 "Non-Executive Director"（报告原词），重蹈 round3 SThree 覆辙
2. **Q1/Q12 题设模糊**："(in USD)" 未说明报告口径；Elixir 营收段含 FX gain 未限定
3. **Q27/Q28 用 name 精确匹配**承载多值答案，比官方 names（Jaccard 部分分）更苛刻——多值答案应归为 names kind

---

## 四、建议动作
1. 修正 `new_answers.json`：Q30 → "Non-Executive Director"；Q12 键补注（38,926 为利息收入口径）
2. 若重新评分，建议按官方惯例将 Q27/Q28 视为 names（Jaccard），可给另一AI 部分分
3. 下轮建键：多值职位键用 names kind；N/A 判定以"利润表是否有该行/是否披露"为准，禁止自算
