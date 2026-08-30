# Round5 答案键说明（全部经原文核实）

- 方法：每题答案回到 `round2/pdfs/<sha>.pdf` 原文核实（fitz 文本层）
- 题型：number 16（13 取数 + 3 N/A）/ boolean 10（5 True + 5 False）/ names 7（4 领导职位 + 3 员工比较）= 33 题
- 自测：63.0/63 = 100%（官方口径）；与 r2/r3/r4 题面零重复
- 应用 round4 教训：
  · 题面单位写死（"in millions of CAD" / "in thousands of USD" 等，杜绝千元/USD 歧义）
  · N/A 判定以"利润表是否有该行/是否披露"为准（禁止自算、禁止从 prose 推断 0）
  · 领导职位键用**报告原词**，多值键一律 kind="names"（Jaccard 部分分，官方惯例）
  · 全部核对 2022/2021 列序与财年截止日（Incitec 财年截至 9/30 等）

## 一、number（16）

| # | 公司 | 指标 | 答案 | 证据（1基页） |
|---|---|---|---|---|
| 1 | Empire | Sales FY 至 2022-05-07 (百万 CAD) | 30162.4 | p49 "Sales $30,162.4 (in millions of Canadian dollars)" |
| 2 | ACRES | Total revenues 2022 (千 USD) | 75170 | p94 "Total revenues 75,170" |
| 3 | HCA | Revenues 2022 (百万 USD) | 60233 | p101 "Revenues $60,233 (Dollars in millions)" |
| 4 | Incitec | Total revenue FY 至 2022-09-30 (百万 AUD) | 6315.3 | p94 "Total revenue 6,315.3"（FS 以 AUD 列报，p91） |
| 5 | NZME | Revenue 2022 (千 NZD) | 355433 | p52 "Revenue 355,433" |
| 6 | Blue Apron | Net revenue 2022 (千 USD) | 458467 | p90 利润表 "Net revenue $458,467"（p48 的 458,457 为孤立数字） |
| 7 | Playtech | Revenue 2022 (百万 EUR) | 1601.8 | p80 "Total reported revenue from continuing operations was €1,601.8 million" |
| 8 | Structural | Sales revenue FY 至 2022-06-30 (千 AUD) | 15701 | p20 "Sales revenue 15,701" |
| 9 | Mosaic | Total assets 至 2022-07-02 (千 AUD) | 342466 | p54 "TOTAL ASSETS 342,466" |
| 10 | Kelly | Total assets 至 2022-06-30 (AUD) | 106642496 | p29 "Total assets 106,642,496"（原始 AUD） |
| 11 | Incyte | Total revenues 2022 (百万 USD) | 3394.6 | p74 "Total revenues $3,394.6" |
| 12 | Duni | Net sales 2022 (百万 SEK) | 6976 | p4 "Net sales 6,976 (SEK m)" |
| 13 | INMUNE | Total revenue 2022 (千 USD) | 374 | p49 利润表 "REVENUE $374"（⚠️ 有营收行，非 N/A） |
| 14 | Atreca | Total revenue 2022 (USD) | N/A | p73 利润表直接以 Operating expenses 开头，无营收行 |
| 15 | NuCana | Total revenue 2022 (USD) | N/A | p166 利润表以 R&D 开头，无营收行 |
| 16 | Westwater | Total revenue 2022 (USD) | N/A | p44 利润表以 Operating Expenses 开头，无营收行 |

## 二、boolean（10）

| # | 公司 | 判定 | 证据（1基页） |
|---|---|---|---|
| 17 | Empire 回购 | True | p12 "plans to repurchase for cancellation … under the normal course issuer bid" + p25 实际回购 |
| 18 | HCA 回购 | True | p3 "We repurchased $7 billion, or over 30 million shares" |
| 19 | NZME 回购 | True | p10 "$17.6m repurchase of shares" + p55 "Repurchase of shares (17,599)" |
| 20 | Playtech 新品 | True | p23 "In August 2022, Playtech launched The Walking Dead™ 2"（游戏产品） |
| 21 | Poste 并购 | True | p20/p35 "acquisition of Plurima / Agile Lab / Sourcesense" + Net Insurance 要约收购 |
| 22 | HCA 新品 | False | 仅内部试点/DEI 战略（"launched a pilot"），无产品发布 |
| 23 | Blue Apron 并购 | False | 仅风险因素/常规措辞（customer acquisition 为营销含义） |
| 24 | RWE 回购 | False | 仅 2018 年股东大会的历史授权（p75），无 2022 回购计划/执行 |
| 25 | Structural ESG | False | p74 仅"environmental … legislation"合规声明，无 ESG 举措 |
| 26 | Kelly ESG | False | p15 明说 "not subject to any particular [ESG] risks"，无举措 |

## 三、names — 领导职位（4，kind=names Jaccard，报告原词）

| # | 公司 | 答案 | 证据（1基页） |
|---|---|---|---|
| 27 | Incitec | Chief Financial Officer,President | p65 "Mr Victor commenced as CFO … 1 July 2022"；"Mr Titze ceased … From that date, Mr Hayne began acting as Interim President" |
| 28 | Playtech | Chief Financial Officer,Chief Sustainability and Corporate Affairs Officer | p96 "Chis McGinnis was appointed as CFO … November 2022"；p50/p69 "appointed a new Chief Sustainability and Corporate Affairs Officer" |
| 29 | Structural | Non-Executive Director | p5 "Bryant McLarty, Hendrik Deurloo and Brian Wall were all appointed as Non-executive Directors during the year" |
| 30 | Downer | Chairman,Non-Executive Director | p28 "Chellew … (commenced 1 September 2021)"、"Harding … (retired 30 September 2021)"、"Binns/Menhinnitt … (commenced 1 March 2022)"、"Howse … (commenced 1 April 2022)" |

## 四、names — 员工比较（3）

| 公司 | 员工数 | 证据 |
|---|---|---|
| HCA | ≈294,000 | p35 "approximately 294,000 employees (as of December 31, 2022)" |
| Empire | ≈130,000 | p2 "employ approximately 130,000 people" |
| Poste | ≈120,000 | p20 "120 thousand employees" |
| RWE | 18,310 | p3 |
| Blue Apron | 1,541 | p19 "to 1,541 at December 31, 2022" |
| Incyte | 2,324 | p36 |
| Duni | 2,231 | p4 |
| Structural | 98 | p42 "Production 63 + Research 24 + Selling 11 = 98" |
| Incitec | 5,822 | p7 "employees worldwide 5,822" |
| Playtech | ≈7,000 | p6 |
| Datalogic | 3,069 | p32 |

| # | 问题 | 答案 |
|---|---|---|
| 31 | 最高（HCA/Empire/Poste/RWE） | **HCA Healthcare, Inc.**（≈294,000） |
| 32 | 最低（Blue Apron/Structural/Incyte/Duni） | **Structural Monitoring Systems Plc**（98） |
| 33 | 最高（Empire/Incitec/Playtech/Datalogic） | **Empire Company Limited**（≈130,000） |

## 五、使用说明

1. 把 `new_questions.json` + 61 份 vision 缓存 PDF（或 deepseek-v4-flash-vision-rag skill）交给另一 AI
2. 另一 AI 按 `submission_template.json` 格式作答
3. 评分：官方 rank.py 或 round4 的评分脚本（改答案路径为 `round5/new_answers.json`）
   —— 注意 27-30 题为 names 口径（Jaccard 部分分），勿按 name 精确匹配
