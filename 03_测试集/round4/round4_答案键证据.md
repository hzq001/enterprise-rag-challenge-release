# Round4 答案键说明（全部经原文核实）

- 方法：与 round3 相同——每题的答案都回到 `round2/pdfs/<sha>.pdf` 原文核实（fitz 文本层 + 必要时视觉）
- 题型：number 16（12 取数 + 4 N/A）/ boolean 10（5 True + 5 False）/ name 4 / names 3，共 33 题
- 自测：62.0/62 = 100%（官方 rank.py 同口径）；题面与 round2/round3 零重复
- 应用 round3 教训：number 题均核对 2022/2021 列序；boolean 键与"必须有变化证据"校准规则自洽；
  name/names 键使用报告原词全称；N/A 题穷尽确认（数据确实未披露）

## 一、number（16）

| # | 公司 | 指标 | 答案 | 证据（1基页） |
|---|---|---|---|---|
| 1 | CoreCard | Total revenue 2022 (USD) | 69765000 | p31 "Total revenue … was $69,765,000" |
| 2 | Franklin Covey | Net sales FY2022 至 2022-08-31 (千 USD) | 262841 | p7/p111 "Net sales 262,841" |
| 3 | FNCB | Total revenue 2022 (千 USD) | 62025 | p2 "Total revenue 62,025" |
| 4 | Ritchie Bros | Total revenue 2022 (千 USD) | 1733808 | p76 "Total revenue 1,733,808" |
| 5 | Albany Intl | Net sales 2022 (千 USD) | 1034887 | p35/p58 "Net sales 1,034,887" |
| 6 | Seiko Epson | Total revenue FY2022 至 2022-03-31 (百万 JPY) | 1128914 | p108 "Revenue 995,940 1,128,914 9,231,449"(2022=1,128,914) |
| 7 | SIG plc | Revenue 2022 (百万 GBP) | 2744.5 | p3 "Revenue £2,744.5m (2021: £2,291.4m)" |
| 8 | FNCB | Total assets 2022-12-31 (千 USD) | 1745530 | p2 "Total assets 1,745,530 1,664,323" |
| 9 | 1-800-FLOWERS | Net revenues FY2022 至 2022-07-03 (千 USD) | 2207885 | p66 "Net revenues 2,207,885" |
| 10 | BetMakers | Total revenue FY2022 至 2022-06-30 (千 AUD) | 91682 | p29/p39 "Revenue 91,682" |
| 11 | James Halstead | Revenue FY2022 至 2022-06-30 (千 GBP) | 291860 | p5/p73 "£291.9m" / "Revenue 291,860" |
| 12 | Elixir Energy | Total revenue FY2022 (AUD) | 38926 | p30 "Revenue from continuing operations: Interest income 38,926" |
| 13 | abrdn Japan | 员工数 | N/A | p20 "The Company … has no employees" |
| 14 | Armadale | Total revenue 2022 (GBP) | N/A | p9 "did not earn any revenues"；利润表无营收行 |
| 15 | Ocugen | Total revenue 2022 (USD) | N/A | p117 利润表直接以 Operating expenses 开头，无 Revenue 行 |
| 16 | Kiniksa | Gross margin (%) | N/A | 全文无 "gross margin/gross profit" 任何披露 |

## 二、boolean（10）

| # | 公司 | 判定 | 证据（1基页） |
|---|---|---|---|
| 17 | Medallion | True | p36 "On April 29, 2022 … authorized a new stock repurchase program, up to $35 million" + p74 "Treasury stock repurchased (20,619)" |
| 18 | Ritchie Bros | True | p7 "On November 7, 2022 … entered into an Agreement and Plan of [Merger] … proposed acquisition of IAA, Inc." |
| 19 | Ziff Davis | True | p54 "2012 Program … repurchase of up to five million shares" + p62 "Repurchase of common stock (78,291)" |
| 20 | Franklin Covey | True | p98/p131 "2019 … repurchase up to $40.0 million" + p4 "investing $23.9 million to repurchase 585,000 shares" |
| 21 | Downer | True | p20 "creation of a centralised decarbonisation fund"；p130 "establishing a standalone Climate Change Report" |
| 22 | James Halstead | False | 仅会计政策/个人履历/常规措辞，无当期并购事件 |
| 23 | Toshiba | False | 全文无 repurchase/buyback |
| 24 | Peako | False | p24 仅 "subject to significant environmental legal regulation" 例行声明 |
| 25 | BetMakers | False | p12/p60 "There were no dividends paid, recommended or declared" |
| 26 | 1-800-FLOWERS | False | p33 "We have never declared or paid cash dividends on our common stock" |

## 三、name（4）— 职位全称（报告原词）

| # | 公司 | 答案 | 证据（1基页） |
|---|---|---|---|
| 27 | BetMakers | Chief Executive Officer of North America,Non-Executive Director | p6/p9 "appointed … Christian Stuart to the key role of Chief Executive Officer of North America"；"Appointed Rebekah Giles as an independent non-executive director / Anna Massion" |
| 28 | Franklin Covey | Executive Chairman,Chief Executive Officer | p22 "September 1, 2021 appointment of Robert A. Whitman as Executive Chairman and Chairman of the Board and Paul S. Walker as Chief Executive Officer, these roles are no longer combined" |
| 29 | CoreCard | Director | p10 "Ms. Petralia was elected by the Board as a new director in October 2022" |
| 30 | Brave Bison | Director | p20/p67 "Gordon Brough (appointed 11 July 2022)" |

## 四、names（3）— 员工数比较（货币无关）

| 公司 | 员工数 | 证据 |
|---|---|---|
| Poste Italiane | ≈120,000 | p20 "120 thousand employees" |
| Commerzbank | 37,852 | p273 平均员工数 |
| RWE | 18,310 | p3 |
| Playtech | ≈7,000 | p6 |
| AA Limited | 6,890 | p11 KPI "Employees at the AA 6,890" |
| SThree | 3,119 | p4 "Employees 3,119" |
| James Halstead | 819 | p47 "average monthly number of employees … 819" |
| Brave Bison | 162 | p50 "average number of persons … 162" |
| Armadale | 3 | p40 "average monthly number … Management 3" |

| # | 问题 | 答案 |
|---|---|---|
| 31 | 最高（Poste/Commerzbank/RWE/Playtech） | **Poste Italiane**（≈120,000） |
| 32 | 最低（SThree/Brave Bison/James Halstead/Armadale） | **Armadale Capital Plc**（3） |
| 33 | 最高（AA/SThree/Brave Bison/James Halstead） | **AA Limited**（6,890） |

## 五、使用说明

1. 把 `new_questions.json` + 61 份 vision 缓存 PDF（或 deepseek-v4-flash-vision-rag skill）交给另一 AI
2. 另一 AI 按 `submission_template.json` 格式作答（`question_text/kind/value/references`）
3. 用 round3 的 `r3_grade_check.py`（改答案路径为 `round4/new_answers.json`）或官方 rank.py 评分
