# Round3 交叉检查报告 — 另一AI 提交 vs 我方答案键

- 提交：`round3/submission_r3.json`（33 条，含 `_note` 证据）
- 答案键：`round3/new_answers.json`（我方制作，已逐题读原文核实）
- 评分口径：与官方 rank.py 一致（number 1% 容差 / boolean+name 精确匹配 / names Jaccard / N-A 权重1、其余2）
- 复核方式：每题争议均回到 `round2/pdfs/<sha>.pdf` 原文重新核读

---

## 一、总评分

### 按我方原答案键（机械评分）
| kind | 题数 | 得分 | 满分 | 占比 |
|---|---|---|---|---|
| number | 16 | 25.0 | 28 | 89.3% |
| boolean | 10 | 14.0 | 20 | 70.0% |
| name | 4 | 2.0 | 8 | 25.0% |
| names | 3 | 2.0 | 6 | 33.3% |
| **总计** | **33** | **43.0** | **62** | **69.35%** |

### 答案键自我审查后（修正我键中 4 处错误）
→ **51.0 / 63 ≈ 80.95%**（Q9/Q14/Q17/Q26 按原文修正键后，另一AI 在这 4 题上全对）

---

## 二、失分题逐题裁定（10 题）

| # | 我方键 | 另一AI | 原文证据（1基页） | 裁定 |
|---|---|---|---|---|
| Q9 Downer 借款 | 1481.6 | **1361.7** | p98 "Total borrowings **1,361.7** 1,481.6"（2022=1361.7，2021=1481.6）；p82 期初1,481.6→期末1,361.7 | **我键错误**（取了2021列），另一AI 正确 |
| Q14 Terns 营收 | N/A | **0** | p127/p138 利润表 "Revenue: License revenue $— $1,000"（2022 明确披露为 $0） | **我键存疑**：数据有披露（=0），另一AI 的 0 更忠实 |
| Q17 Duni 分红政策 | True | **False** | p35 "long-term intention ≥40%"（长期意图，非变化）；无任何"revised/changed/new"政策声明；round2 同类 Seiko/Empire/HCA 均 False | **我键错误**（提案≠政策变化），另一AI 符合校准规则 |
| Q21 Guaranty 回购 | **True** | False | p3 CEO信 "In 2022, we repurchased 2% of our common shares outstanding"（实际完成事件） | **另一AI 错**（过度要求"计划授权"；round2 Q12 Downer 回购=实际完成→True 同款先例） |
| Q26 Playtech 并购 | False | **True** | p85 "payment for the acquisition of LSports"；p151 "Acquisition of Eyecon Limited 3.6 / Statscore NCI 1.6"（2022 当年真实并购） | **我键错误**（只看到2018 Snaitech 历史），另一AI 正确（其 Finalto 理由偏弱但结论对） |
| Q27 AA 职位 | Chief Executive Officer | Non-Executive Director | p28 变更清单：Pfaudler 任 CEO(2021-04-14)、Mackay 任 CFO(2021-11-15)、Breakwell 辞任、Sorenson 任 NED(2022-02-01) | **键不完整**：4 处变更都真实；我键取期内在任 CEO，另一AI 取被主席强调的 NED（略偏期末后）；机械上另一AI 失分 |
| Q28 Sonic 职位 | Chairman of the Board | Chairman | p11 "David Bruton Smith was elected as **Chairman of the Board** in July 2022" | **另一AI 错**（简写失配精确匹配；其自报风险第3条已预判） |
| Q30 SThree 职位 | Director | Non-Executive Director | p81 "Anne Fahy stepped down as a **Non-Executive Director** on 19 Apr 2022"；p65 "Mark Dorman stepped down as a **Director** on 31 Dec 2021" | **键不完整**：两类变更都有；双方各取一半，机械上另一AI 失分 |
| Q32 names 最低 | Duni Group | Duni | 题目公司名即 "Duni Group" | **另一AI 错**（简写，Jaccard=0） |
| Q33 names 最高 | Playtech plc | Playtech | 题目公司名即 "Playtech plc" | **另一AI 错**（简写，Jaccard=0） |

---

## 三、结论分层

### 我方答案键的问题（4 处，需修正）
1. **Q9 Downer**：键值 1481.6 是 2021 年（期初）余额，2022 年末应为 **1361.7** —— 键错误（确认）
2. **Q26 Playtech**：年报确有 2022 当年并购（Eyecon/LSports/Statscore NCI），应为 **True** —— 键错误（确认）
3. **Q14 Terns**：利润表明确披露 License revenue $0，应为 **0** 而非 N/A —— 键存疑（倾向 0）
4. **Q17 Duni**：分红政策仅"长期意图 ≥40%"描述 + 年度提案，无政策变化声明，应为 **False** —— 键错误（与我校准规则自相矛盾）

### 另一AI 的真正失误（键修正后仍失分，6 题 12 分）
- **Q21**：校准执行错误——有"实际完成事件"（2022 回购 2%）却判 False，违背"报告期内实际完成 → True"规则
- **Q28 / Q32 / Q33**：字符串精度——职位/公司名用简写（Chairman / Duni / Playtech），官方精确匹配/Jaccard 全失分
- **Q27 / Q30**：单选题里各取了一个真实变更，但键本身也是单值（键不完整，属题设局限，不算它的硬错）

### 方法可复刻性结论
另一AI 完整复刻了人式流程（scan_index 查目录 → read_text/read_vision 读页 → 换词深挖 → 收敛）：
- MGM 乱码文档用 read_vision 视觉朗读出净利 206,731 ✓（与键一致）
- 3 个 N/A 全部穷尽确认 ✓；boolean 8/10 正确，且我键错的 2 题（Q17/Q26）它反而判对
- **修正键后 ≈81%**，证明该方案可被另一 AI 复现；失分集中在字符串精度与 1 处校准执行

---

## 四、建议动作
1. 修正 `new_answers.json` 中 Q9→1361.7、Q14→0、Q17→False、Q26→True（4 处）
2. 若需重新评分，用 `r3_grade_check.py` 对修正后的键复算
3. 若再测一轮，可把 Q27/Q30 改为多值键（逗号分隔）以容纳全部真实变更
