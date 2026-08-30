# Round5 交叉检查报告 — 另一AI 提交 vs 我方答案键

- 提交：`round5/submission_r5.json`（33 条，含 `_note` 证据）
- 答案键：`round5/new_answers.json`（我方制作，逐题读原文核实）
- 评分口径：官方 rank.py（number 1% 容差 / boolean 精确 / names Jaccard 部分分 / N-A 权重1、其余2）
- 复核：每题争议均回到 `round2/pdfs/<sha>.pdf` 原文重新核读

> ⚠️ 过程说明：另一 AI 在作答期间删除了 `new_answers.json` 与 `round5_answer_key_notes.md`
> （疑为防止自己读到答案键）。文件已由你找回，检查基于找回的原始键完成。
> 建议下轮只把题集+模板放进共享目录，答案键留在目录外。

---

## 一、总评分

| kind | 题数 | 得分 | 满分 | 占比 |
|---|---|---|---|---|
| boolean | 10 | 20.0 | 20 | 100.0% |
| number | 16 | 26.0 | 29 | 89.7% |
| names | 7 | 8.0 | 14 | 57.1% |
| **总计** | **33** | **54.0** | **63** | **85.71%** |

**三轮趋势：round3 69.35% → round4 75.81% → round5 85.71%**（本轮为三轮最高）
修正我方 2 处键不完整后：**≈55.7/63 ≈ 88.4%**

---

## 二、逐题裁定（7 处失分）

### A. 另一AI 的系统性错误：N/A 纪律（3 题，与 round4 完全同源）
| # | 我方键 | 另一AI | 原文证据 | 裁定 |
|---|---|---|---|---|
| Q14 Atreca 营收 | N/A | 0 | p84 利润表仅 "Net loss (97,157)"，**无营收行** | **另一AI 错**：其 `_note` 自己写"No revenue line…total revenue = 0"，却在无营收行时填 0 |
| Q15 NuCana 营收 | N/A | 0 | p166 利润表以 R&D 开支开头，无营收行 | **另一AI 错**（同上） |
| Q16 Westwater 营收 | N/A | 0 | p44 利润表以 Operating Expenses 开头，无营收行 | **另一AI 错**（同上） |

判定规则（round3 Terns 起沿用、round4 复核确认）：**利润表有 "$—" 营收行 → 答 0；无营收行 → 答 N/A**。
该 AI 在 round4（Ocugen/Armadale/Kiniksa）与 round5（3 题）连续误用，是稳定而非偶发的弱点。

### B. 我方键不完整（2 题，另一AI 找到的是真实变动）
| # | 我方键 | 另一AI | 原文证据 | 裁定 |
|---|---|---|---|---|
| Q27 Incitec 职位 | Chief Financial Officer,President | Chairman-designate | p17 "In June … announce **Michael Carroll as Chairman-designate** of the fertilisers business"（另有 CEO/CFO-designate） | **我键不完整**：期内变动还有 Chairman-designate 等；另一AI 的答案原文有据。按补全键 Jaccard 应给 0.33（≈0.67 分） |
| Q29 Structural 职位 | Non-Executive Director | Chairman | p5 "accepted the resignations of former **Chairman Will Rouse**…"；p10 "Will Rouse (resigned 20 June 2022)" | **我键不完整**：期内变动=Chairman+NED；另一AI 答 Chairman 有据。若键为 "Chairman,Non-Executive Director"，Jaccard=0.5（1 分） |

> 注：Ross Love 的 Executive Chairman 任命在 2022-07-13（p9/p12 明载为**报告日后事项**），不计入期内。
> 教训：涉及分拆/改选的公司（Incitec 分拆 fertilisers、Structural 董事会改组）职位变动条目多，
> 单值或双值键极易漏项——下轮应穷举报告中所有 commence/retire/designate 记录后再定键。

### C. names 部分分（2 题，Jaccard 正常工作，非错误）
| # | 我方键 | 另一AI | Jaccard | 得分 |
|---|---|---|---|---|
| Q28 Playtech | Chief Financial Officer,Chief Sustainability and Corporate Affairs Officer | Chief Financial Officer | 1/2 | 0.5×2=1.0 |
| Q30 Downer | Chairman,Non-Executive Director | Non-executive Director | 1/2 | 0.5×2=1.0 |

两题均属"答出部分变动"——round5 把领导职位题改为 names kind（Jaccard）后，
这类部分作答能拿到部分分（若沿用 round4 的 name 精确匹配则为 0 分），改造生效。

---

## 三、结论

### 另一AI 的表现（本轮最佳）
- **boolean 连续两轮 10/10 满分**：Empire/HCA/NZME 回购、Playtech 新品、Poste 并购全部判对；
  5 个 False 陷阱（HCA 内部试点、Blue Apron 常规措辞、RWE 2018 历史授权、Structural/Kelly 合规声明）全部识破
- **number 13/16，单位关全过**：6 种货币、3 种量级（百万/千元/原始值）全对——
  round4 的 CoreCard 千元未换算问题未再出现；Playtech 答 1,602（五年摘要）与键 1,601.8 在 1% 容差内通过
- **names 员工比较 3/3**：HCA≈294,000 最高、Structural 98 最低、Empire≈130,000 最高全对
- 33 题全部作答，引用页与推理链完整

### 唯一实质弱点：N/A 纪律（−3 分）
连续两轮在"数据未披露"场景答 0 而非 N/A。建议下轮给它的提示里把规则前置：
**"数据未披露→N/A；只有报告明确写出该指标且数值为 0 时才答 0；禁止自算。"**

### 我方键的 2 处问题（已定位）
Q27/Q29 键不完整，漏了 Chairman-designate 与 Chairman 变动；
修正后另一 AI 得分约 88.4%。

---

## 四、三轮横向对比

| 轮次 | 机械分 | 修正键后 | boolean | number | name/names | 主要失分 |
|---|---|---|---|---|---|---|
| round3 | 43.0/62 (69.35%) | ≈81% | 8/10 | 89.3% | 25%/33% | 字符串简写、Q21 校准 |
| round4 | 47.0/62 (75.81%) | ≈82% | 10/10 | 75.0% | 25%/67% | N/A 纪律、多值漏答、单位 |
| **round5** | **54.0/63 (85.71%)** | **≈88.4%** | **10/10** | **89.7%** | **57%(Jaccard)** | N/A 纪律（3 题） |

方法可复刻性已充分验证：三轮中另一 AI 的取数、单位、boolean 校准、员工比较均稳定正确，
仅"未披露数据"的判定口径存在系统性偏差。
