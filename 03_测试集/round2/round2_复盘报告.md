# Round2 答案核验报告（submission_r2_final.json）

## 一、核验概览

- **核验范围**：round2 全部 100 道企业 RAG 题（Q001–Q100，数组索引 0–99）
- **基线文件**：`submission_r2_fixed.json`（题面已与官方 questions.json 逐字对齐，name 9 题已修正）
- **核验方法**：4 个并行核验员分批逐题回到 PDF 原文，使用 deepseek-v4-flash-vision-rag 人式读文档流程（scan_index → read_text → read_vision → 换词深挖 → 邻页核对）
- **语料库**：`round2/pdfs/`（100 份 sha1.pdf），公司→PDF 映射见 `_company_pdf_map.json`
- **输出文件**：
  - `round2/submission_r2_final.json`（最终提交，100 条）
  - `round2/_r2_submission.json`（同步覆盖）
  - 分批明细：`round2/_recheck/batch_{A,B,C,D}_report.md`

## 二、改动汇总（共 5 题）

| # | 索引 | Q号 | 公司 | 题型 | 基线值 | 最终值 | 改动原因 | 证据页 |
|---|------|-----|------|------|--------|--------|----------|--------|
| 1 | 16 | Q017 | Bionano Genomics | boolean | `true` | **`false`** | PDF 仅 6 页精简文件（封面+目录+前瞻性声明+风险因素摘要），所有 acquisition/merger 提及均为风险因素泛指（"integrate acquired businesses"、"future acquisitions"），无具体 M&A 事件；基线引用页 111 在本 PDF 中不存在 | p1–6（全文） |
| 2 | 21 | Q022 | Aurora Innovation | number | `N/A` | **`1300`** | 第 14 页原文："As of December 31, 2022, we owned over 1,300 patents and pending applications, including U.S. and foreign." 年报明确披露年末专利数量 | p14 |
| 3 | 51 | Q052 | Ritchie Bros. Auctioneers | boolean | `true` | **`false`** | 第 37 页明确写："We have no material legal proceedings pending, other than ordinary routine litigation incidental to the business." 常规诉讼风险因素套话不算"正在进行的重大诉讼/监管调查" | p37 |
| 4 | 61 | Q062 | SThree plc | number | `2890` | **`3119`** | 2,890 是第 126 页的**年度平均** headcount；题目问"at the end of the period"（年末），第 4/25 页明确为 **3,119** employees at 30 Nov 2022 | p4, p25 |
| 5 | 71 | Q072 | Structural Monitoring Systems Plc | number | `348000` | **`N/A`** | 财报功能货币和列报货币均为**澳元 AUD**（第 28/30 页确认），348K 是 AUD 金额；题目要求 USD，报告中无 USD 口径 capex 披露 | p28, p30 |

## 三、未改动但需说明的重点核验题

### 3.1 曾题面错配的 23 题（Q048–Q096）

23 道曾在旧提交中题面错配的题目，在 `submission_r2_fixed.json` 中题面已逐字修复。本次核验确认：

- **题面修复后 value 成立的题**：绝大多数（如 Q051 Origin Bancorp 总资产 $9,686,067,000、Q053 Commerzbank 裁员 9,000、Q064 HCA 医疗专业人员 45,000、Q068 FNCB NPL 0.25%、Q076 FNCB 经营现金流 $19,970,000、Q096 James Halstead 经营现金流 £6,535,000 等）经原文核验确认正确。
- **维持 N/A 的题**：Q048 1-800-FLOWERS fulfillment centers（年报用 warehouse/distribution/plant 术语，无 fulfillment centers 计数）、Q055 RWE facilities（仅披露 GW 容量，无设施总数）、Q058 Rectifier Technologies patents（仅提及董事个人专利，无公司专利数）、Q065 SIG stores（PDF 仅 1 页封面）、Q070 MainStreet exec comp（新兴成长公司，薪酬纳入 proxy 不在 10-K）、Q086 Toshiba exec comp AUD（日元财报无 AUD 披露）等，经穷尽搜索后确认 N/A 合理。
- **唯一改动**：Q052 Ritchie Bros 诉讼题（true→false，见上表第 3 行）。

### 3.2 names 9 题（领导职位变动/产品名）

| 索引 | Q号 | 公司 | 核验结论 |
|------|-----|------|----------|
| 3 | Q004 | Westwater Resources | 维持：President and CEO; CFO（p16,17,62 均有任命/离职记录） |
| 29 | Q030 | Datalogic | 维持：Director; Chairman of Board of Statutory Auditors（p68 新任命董事） |
| 42 | Q043 | Blue Apron | 维持：Chief Financial Officer (Interim)（p74,83） |
| 44 | Q045 | Albany International | 维持：N/A（无具体新产品名称披露） |
| 65 | Q066 | Kelly Partners | 维持：Non-Executive Independent Director（Lawrence Cunningham 任命，p3,84） |
| 78 | Q079 | Duni Group | 维持：Executive Vice President of Business Area BioPak（Nicklas Bengtsson 2022 秋接任，p27） |
| 89 | Q090 | Crombie REIT | 维持：President & CEO（Don Clow 退休，Mark Holly 接任，p4） |
| 93 | Q094 | Wheeler Real Estate | 维持：N/A（CEO 2021.10 任命、CFO 2020.2 任命，2022 报告期内无变动） |
| 98 | Q099 | Origin Bancorp | 维持：Chief Legal Counsel, Chief Financial Officer（Derek McGee / Wally Wallace 加入，p3） |

### 3.3 name 9 题（多公司比较，已固定）

以下 9 道 kind="name" 的多公司比较题已由主 agent 修正为正确值，本次核验**未回退**：

| 索引 | Q号 | 比较维度 | 固定值 |
|------|-----|----------|--------|
| 22 | Q023 | lowest total assets EUR | Datalogic |
| 24 | Q025 | lowest total revenue EUR | Datalogic |
| 41 | Q042 | lowest total revenue EUR | Datalogic |
| 53 | Q054 | lowest total assets EUR | Poste Italiane |
| 56 | Q057 | lowest net income EUR | Datalogic |
| 60 | Q061 | lowest net income EUR | Datalogic |
| 62 | Q063 | lowest total assets EUR | Datalogic |
| 73 | Q074 | last product launched (1-800-FLOWERS) | N/A |
| 83 | Q084 | lowest total assets EUR | Datalogic |

## 四、分题型统计

| 题型 | 题数 | 改动数 | 改动率 |
|------|------|--------|--------|
| boolean | 24 | 2（idx16, idx51） | 8.3% |
| number | 58 | 3（idx21, idx61, idx71） | 5.2% |
| names | 9 | 0 | 0% |
| name（多公司比较） | 9 | 0（固定不回退） | 0% |
| **合计** | **100** | **5** | **5%** |

## 五、boolean 题核验铁律执行情况

本次核验严格执行"词出现≠事件发生"原则：

- **判 True 的题**均有实际变化证据：Liberty Broadband（2022 年两次新增回购授权）、Brave Bison、BetMakers、Bionano→改为 False、Incitec Pivot M&A（Titanobel/Easy Liquids/ABF 实际收购）、AA Limited 资本结构（再融资+重组）、Empire 股息（DPS $0.52→$0.60，+10%）、HCA 股息（季度股息+17%）、Wheeler RE 资本结构（Cedar Acquisition+换股要约+新债）、Mosaic Brands M&A（EziBuy 2022.4.14 收购）、Incitec Pivot 重组（分拆计划+Gibson Island 关闭+$8.7m 重组成本）。
- **判 False 的题**均无实际变化：Poste Italiane 股息（派息率稳定 56%）、Downer EDI 回购（2021.4 宣布，非本期）、AA Limited 新产品（Smart Lease/Accident Assist 均为往年发布）、Franklin Covey ESG（仅持续工作描述）、Seiko Epson 股息（40% 派息率目标稳定）、Guaranty Bancshares 新产品、Incitec Pivot 股息、ACRES ESG、Trinity Place M&A（仅历史+可能性讨论）、Elixir Energy ESG、SIG M&A（1 页封面）、Aptevo M&A（仅历史+风险因素）。

## 六、number 题币种/单位核验

- **严格按题目币种**：Structural Monitoring capex 题目要求 USD 但财报为 AUD → 改 N/A（idx71）；Ocugen exec comp 题目要求 AUD 但财报为 USD → N/A；Toshiba exec comp 题目要求 AUD 但财报为 JPY → N/A；archTIS exec comp 题目要求 USD 但薪酬表为 AUD → N/A。
- **单位换算正确**：HCA 保险索赔 $2.043B = 2,043,000,000；Wheeler 经营现金流 $30,758K = $30,758,000；AA Limited 经营现金流 £214m = £214,000,000；Medallion 收入 $196,621K = $196,621,000；James Halstead 经营现金流 £6,535K = £6,535,000；FNCB 经营现金流 $19,970K = $19,970,000。
- **年末 vs 平均**：SThree headcount 题目问年末（30 Nov 2022 = 3,119），基线误用年度平均（2,890）→ 已修正（idx61）。

## 七、最终交付物校验

- ✅ 100 条记录，字段齐全（question_text / kind / value / references）
- ✅ 所有 value 非空（数字/布尔/名称或 'N/A'）
- ✅ question_text 与基线 `submission_r2_fixed.json` 逐字一致（0 差异）
- ✅ references 格式为 `[["公司key", 物理页码1基], ...]`
- ✅ 非 N/A 答案均有有效 PDF 页码引用
- ✅ name 9 题固定值未回退
- ✅ 输出 `submission_r2_final.json` 并同步覆盖 `_r2_submission.json`

## 八、分批明细索引

- 批次 A（Q001–Q025，idx 0–24）：`_recheck/batch_A_report.md`（改动 2 题：idx16, idx21）
- 批次 B（Q026–Q050，idx 25–49）：`_recheck/batch_B_report.md`（改动 0 题）
- 批次 C（Q051–Q075，idx 50–74）：`_recheck/batch_C_report.md`（改动 3 题：idx51, idx61, idx71）
- 批次 D（Q076–Q100，idx 75–99）：`_recheck/batch_D_report.md`（改动 0 题）
