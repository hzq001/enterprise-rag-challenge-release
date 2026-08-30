# Round 3 视觉 RAG 挑战 — 答题报告

- 模型：DeepSeek V4-Flash-Vision（deepseek-v4-flash-vision-exp）
- 方法：**deepseek-v4-flash-vision-rag skill 的「人式读文档」流程**
  `scan_index 查目录 → read_text 快速瞄 → read_vision 视觉看页 → 换词深挖 → verify_quote 自检 → 收敛`
- 题目数：33（number 16 / boolean 10 / name 4 / names 3）
- 语料：29 份公司年报 PDF（已建视觉索引），全部在被引用 61 份之内
- 提交文件：`submission_r3.json`（33 条，question_text/kind/value/references 齐全）
- 说明：round3 无本机真值，得分需在官方环境评分

---

## 一、number 题（16）

| # | 公司 | 指标 | 答案 | 证据（1基页码） | 备注 |
|---|---|---|---|---|---|
| 1 | Ziff Davis | 员工数 | 4400 | p10 | "approximately 4,400 employees" |
| 2 | Aurora Innovation | 员工数 | 1700 | p16 | "approximately 1,700 employees" |
| 3 | Bionano Genomics | 员工数 | 405 | p26 | "we had 405 employees" |
| 4 | MainStreet Bancshares | EPS basic+diluted 2022 | 3.26 | p41 | Per share data 表，2022 列 $3.26 |
| 5 | Kelly Partners | FY22 Revenue (AUD) | 64862110 | p10 | "FY22 Revenue 64,862,110" |
| 6 | Mosaic Brands | Total revenue+other income (千 AUD) | 619651 | p61 | 表：Revenue 571,362 + Other 48,289 |
| 7 | Brave Bison | Total equity (千 GBP) | 10022 | p37 | "Total equity 10,022" |
| 8 | MGM Resorts | Net income (loss) 2022 (千 USD) | 206731 | p64 | **乱码页，read_vision 视觉读出** "Net income (loss) 2022: 206,731" |
| 9 | Downer EDI | Total borrowings (百万 AUD) | 1361.7 | p98 | "Total borrowings 1,361.7" |
| 10 | AA Limited | Group revenue (百万 GBP) | 989 | p12 | "Revenue 989" |
| 11 | Trinity Place | Cloud storage capacity (TB) | N/A | p19 | 地产公司无该数据；"cloud" 仅指楼盘 "Cloud Club" 设施 |
| 12 | Atreca | Gross margin (%) | N/A | p26 | pre-revenue 生物科技，无毛利率披露 |
| 13 | Pintec | Dividend per share (AUD) | N/A | p12 | "none ... has paid any dividends" |
| 14 | Terns Pharma | Total revenue 2022 (USD) | 0 | p127 | License revenue 2022 = $—（明确披露为 0）；⚠️ 见风险说明 |
| 15 | Commerzbank | Total assets (十亿 EUR) | 477.4 | p2 | "Total assets (€bn) 477.4" |
| 16 | Datalogic | Total revenue (千 EUR) | 654632 | p44 | "Total revenue 654,632" |

## 二、boolean 题（10）

| # | 公司 | 判定 | 证据（1基页码） | 判断要点 |
|---|---|---|---|---|
| 17 | Duni | False | p35 | 分红政策为长期意图描述（≥40%），**无政策变化**声明，仅年度分红提议 |
| 18 | Structural Monitoring | True | p7/p12 | 报告期内**实际完成** Rights Issue（$4.91m）+ Placement（$1.93m）→ 资本结构变化 |
| 19 | Poste Italiane | True | p38 | AGM 2022-05-27 **授权**回购计划（2.6m 股/€40m）并已执行 |
| 20 | RWE | True | p7/p38 | 明确提及并购：收购 Con Edison Clean Energy Businesses（US$6.8bn）、Alpha Solar、JBM Solar、Magnum |
| 21 | Guaranty Bancshares | False | p3 | 仅 CEO 信描述"回购 2%股份"，**无明确的回购计划授权/宣布** |
| 22 | archTIS | False | p21 | 无任何 ESG 举措，仅例行声明不受重大环境监管 |
| 23 | INMUNE BIO | False | p3 | 临床阶段公司，无产品发布（仅"目标"描述） |
| 24 | NuCana | False | p55 | 仅风险因素/行业描述/未来可能性/历史提及（Bioenvision 2007 被收购），无实质并购 |
| 25 | Incyte | False | p60 | 无任何回购计划（仅 Treasury 证券投资） |
| 26 | Playtech | True | p21/p80 | **2022-07 完成 Finalto 出售（$228.1m）**，涉及收购协议，明确的并购交易提及 |

## 三、name 题（4）

| # | 公司 | 变动职位 | 证据（1基页码） | 判断要点 |
|---|---|---|---|---|
| 27 | AA Limited | Non-Executive Director | p28 | Kory Sorenson 任命为 NED，2022-02-01 加入 Topco Board |
| 28 | Sonic Automotive | Chairman | p11 | David Bruton Smith 2022-07 当选 Chairman of the Board |
| 29 | Rectifier Technologies | Company Secretary | p8 | Nova Taylor 2022-02-03 任命；Stedwell 同日辞职 |
| 30 | SThree | Non-Executive Director | p12/p25 | Elaine O'Donnell 2022-10 任命（ARC Chair + NED）；Imogen Joss 2022-12-01 生效 NED |

## 四、names 比较题（3）— 6 家公司员工数

| 公司 | 员工数 | 来源（1基页码） |
|---|---|---|
| Datalogic | 3,069 | p32 |
| Duni | 2,231 | p4 |
| Incyte | 2,324 | p36 |
| Playtech | ≈7,000 | p6 |
| RWE | 18,310 | p3 |
| Commerzbank | 42,378 | p273（物理页，平均员工数） |

| # | 问题 | 答案 |
|---|---|---|
| 31 | 最高（6 家） | **Commerzbank**（42,378） |
| 32 | 最低（Datalogic/Duni/Incyte/Playtech/RWE） | **Duni**（2,231） |
| 33 | 最高（Datalogic/Duni/Incyte/Playtech） | **Playtech**（≈7,000） |

---

## 五、高风险项与说明（供评审）

1. **Q14（Terns revenue = 0）**：报表明确披露 License revenue 2022 = $—（0）。若官方将"零收入生物科技"标为 N/A，此答案可能失分；但忠实数据即 0，已按最字面口径作答。
2. **Q21（Guaranty = False）**：公司确有实际回购（2%），但年报无明确的"buyback plan 授权/宣布"声明，按 skill 规则「词出现 ≠ 事件」「无实质证据按 False」判 False。
3. **Q28（Sonic = Chairman）**：name 精确匹配，官方可能用 "Chairman" 或 "Chairman of the Board"，取最简职位名。
4. **Q4（MainStreet = 3.26）**：EPS 取 2022 列（2021 = 2.65），已核对列序。
5. **Commerzbank 页码**：该 PDF 存在打印页码/物理页偏移，员工数取自物理页 273（(61) Average number of staff，Group 2022 Total = 42,378）。

## 六、方法说明

- 每题先 `scan_index` 用多个同义词定位（如 employees/headcount/colleagues；merger/acquisition；appointed/resigned），再用 `read_text` 读文本层确认，页码存疑时用 PyMuPDF 直接核对物理页。
- 乱码文档（MGM）走 `read_vision` 视觉朗读，读出利润表净利 206,731。
- N/A 题均先穷尽 2-3 组关键词确认无数据（Trinity Place、Atreca、Pintec）。
- boolean 题以「必须有变化/实质事件证据」为判据，拿不准按 False。
