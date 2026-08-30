# Round 4 视觉 RAG 挑战 — 答题报告

- 模型：DeepSeek V4-Flash-Vision（deepseek-v4-flash-vision-exp）
- 方法：**deepseek-v4-flash-vision-rag skill「人式读文档」流程**
  `scan_index 查目录 → read_text 快速瞄 → 换词深挖 → 语义搜索 → 物理页核对 → 收敛`
- 题目数：33（number 16 / boolean 10 / name 4 / names 3）
- 语料：复用 round2/pdfs 索引库（100 份年报，与 round3 同一批）
- 提交文件：`submission_r4.json`（33 条，question_text/kind/value/references 齐全）
- 说明：round4 无本机真值，得分需在官方环境评分

---

## 一、number 题（16）

| # | 公司 | 指标 | 答案 | 证据（1基页码） | 备注 |
|---|---|---|---|---|---|
| 1 | CoreCard | Total revenue 2022 (USD) | 69765 | p46 | 损益表 "Total net revenue 69,765"（千）；⚠️ 题目标 in USD，按 raw 数 |
| 2 | Franklin Covey | Net sales FY22 (千 USD) | 262841 | p111 | "Net sales $262,841" |
| 3 | FNCB | Total revenue 2022 (千 USD) | 62025 | p2 | "Total revenue 62,025" |
| 4 | Ritchie Bros | Total revenue 2022 (千 USD) | 1733808 | 物理页76 | Service 1,050,583 + Inventory 683,225 |
| 5 | Albany Intl | Net sales 2022 (千 USD) | 1034887 | p15 | 分部合计 1,034,887 |
| 6 | Seiko Epson | Revenue FY结束2022-03-31 (百万 JPY) | 1128914 | p6 | 五年表 Revenue 1,128,914 |
| 7 | SIG plc | Revenue 2022 (百万 GBP) | 2744.5 | p3 | "Revenue £2,744.5m" |
| 8 | FNCB | Total assets 2022 (千 USD) | 1745530 | p2 | "Total assets $1,745,530" |
| 9 | 1-800-FLOWERS | Net revenues FY2022 (千 USD) | 2207885 | 物理页38 | "Total net revenues 2,207,885" |
| 10 | BetMakers | Total revenue FY22 (千 AUD) | 91682 | p8 | "Revenue 91,682" |
| 11 | James Halstead | Revenue FY22 (千 GBP) | 291860 | 物理页33 | 损益表 "Revenue 291,860" |
| 12 | Elixir Energy | Total revenue FY22 (AUD) | 0 | 物理页30 | 损益表 Revenue（continuing operations）为空，无营收 |
| 13 | abrdn Japan IT | 期末员工数 | N/A | p20 | "has no employees"（投资信托无员工披露） |
| 14 | Armadale Capital | Total revenue 2022 (GBP) | 0 | p9 | "did not earn any revenues" |
| 15 | Ocugen | Total revenue 2022 (USD) | 0 | 物理页117 | 损益表无 Revenue 行，无营收 |
| 16 | Kiniksa | Gross margin (%) | 89.6 | p130 | (220,180-22,895)/220,180 计算，年报未直接披露 |

## 二、boolean 题（10）

| # | 公司 | 判定 | 证据（1基页码） | 判断要点 |
|---|---|---|---|---|
| 17 | Medallion Financial | True | p36 | 2022-04-29 董事会**授权新回购计划**（$35M→$40M）并回购 2,650,911 股 |
| 18 | Ritchie Bros | True | p4 | 明确提及**拟议收购 IAA** 及多项并购 |
| 19 | Ziff Davis | True | p54 | Stock Repurchase Program（2012 Program）持续，2022 执行 10b5-1 计划 |
| 20 | Franklin Covey | True | p85 | 2019-11-15 董事会批准 $40M 回购计划，2022 回购 585,000 股（$23.9M） |
| 21 | Downer EDI | True | p20 | 新 ESG：Net Zero 2050、Scope3 减排 30% by 2032、中央脱碳基金 |
| 22 | James Halstead | False | p21 | 仅通用会计政策提及，无实际并购交易 |
| 23 | Toshiba | False | — | 无 buyback/repurchase 计划宣布（仅 TSR 倡议提及） |
| 24 | Peako | False | p24 | 仅环境法规合规声明，无 ESG 倡议 |
| 25 | BetMakers | False | p1 | 无分红支付/建议/宣布，分红政策无变化 |
| 26 | 1-800-FLOWERS | False | p33 | 从未分红，政策无变化 |

## 三、name 题（4）

| # | 公司 | 变动职位 | 证据（1基页码） | 判断要点 |
|---|---|---|---|---|
| 27 | BetMakers | Non-Executive Director | p14 | Rebekah Giles（2022-02-08）、Anna Massion 任命 NED；Matt Davey 辞职 |
| 28 | Franklin Covey | Chief Executive Officer | p22 | 2021-09-01 Paul S. Walker 任命 CEO（Whitman 任 Executive Chairman） |
| 29 | CoreCard | Director | p10 | Kathryn Petralia 2022-10 当选新董事 |
| 30 | Brave Bison | Non-Executive Director | p7 | Gordon Brough 报告期内任命 NED |

## 四、names 比较题（3）— 员工数

| 公司 | 员工数 | 来源 |
|---|---|---|
| Poste Italiane | ~120,000 | p20 |
| Commerzbank | 42,378 | 物理页273 |
| RWE | 18,310 | p3 |
| Playtech | ≈7,000 | p6 |
| AA Limited | 6,890 | 物理页11 |
| SThree | 3,119 | p4 |
| Brave Bison | 162 | 物理页49（附注12） |
| James Halstead | 22 | 物理页66（附注2） |
| Armadale Capital | 无员工数披露 | 承包商为主 |

| # | 问题 | 答案 |
|---|---|---|
| 31 | 最高（Poste/Commerzbank/RWE/Playtech） | **Poste Italiane**（~120,000） |
| 32 | 最低（SThree/Brave Bison/Halstead/Armadale） | **James Halstead**（22；Armadale 无数据被排除） |
| 33 | 最高（AA/SThree/Brave Bison/Halstead） | **AA Limited**（6,890） |

---

## 五、高风险项与说明（供评审）

1. **Q1（CoreCard=69,765）**：题目单位标 "(in USD)"，但财报损益表为 "(in thousands)"。按财报 raw 数字作答；若官方按完整美元（69,765,000）计分则失分——该题单位标注与财报不一致，属生成器异常。
2. **Q12/Q14/Q15（Elixir/Armadale/Ocugen=0）**：三家均无营收（损益表 Revenue 为空/无行）。与 round3 Terns（0）口径一致。
3. **Q13（abrdn=N/A）**：投资信托无员工数披露（仅"has no employees"文字），提取不到数字按 N/A。
4. **Q16（Kiniksa=89.6）**：年报未直接披露毛利率，按 Total revenue 220,180 与 COGS 22,895 计算。
5. **Q28（Franklin Covey=Chief Executive Officer）**：报告期初 CEO 与 Chairman 同时变动（2021-09-01），官方可能记 CEO 或 Chairman，取最核心的 CEO。
6. **Q32（Halstead=22）**：Armadale 无员工数被排除；Halstead 附注平均月员工仅 22，为四家中最低。
7. **页码引用**：部分 PDF（Ritchie/AA/Halstead 等）有封面页偏移，引用一律用 PyMuPDF 物理页号核对。
