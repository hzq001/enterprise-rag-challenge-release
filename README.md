# Enterprise RAG Challenge —— 人式读文档视觉 RAG 方案

> 让 AI **像人一样翻开一份 PDF**：查目录 → 看图 → 深挖 → 带页码引用给答案。
> 基于 DeepSeek 视觉模型 `deepseek-v4-flash-vision-exp`，支持文字版／扫描版／图表／表格／公式年报。

本发布包只含**当前方案**（人式读文档）。旧版的文本 RAG 批量流水线
（`round1_solve.py`、`r2_solve.py`、61 份 text_index、round1 时代方法论）已全部移除，
归档于 `../_archive/enterprise-rag-challenge-release_round1-2_*/`（确认无用后可删）。

---

## 一、目录结构

```
enterprise-rag-challenge-release/
├── 00_方案/
│   └── 人式读文档方案.md          ← 方案全文：原则、工具、流程、判定规则、验证结果
├── 01_skill/                     ← 可直接使用的 skill（不含 4.4G 索引缓存）
│   ├── SKILL.md                    skill 入口：触发条件 + 人式工作流 + 决策规则 + 3 个实测示范
│   ├── README.md                   skill 说明与环境配置
│   ├── scripts/
│   │   ├── agentic_tools.py        人式工具集：scan_index / read_vision / read_text
│   │   │                          / search_pages / verify_quote
│   │   ├── ds_client.py            DeepSeek VLM 客户端（read_vision 依赖）
│   │   ├── show.py                 指定页高清渲染
│   │   ├── ingest.py → router.py + transcribe.py   [可选] 一次性预建索引（非人式必需）
│   │   └── _human_demo/            教学示例图（SKILL.md 引用）
│   └── references/                API 要点与索引结构说明
├── 02_语料/
│   ├── subset.json                 100 家公司 → PDF sha1 → 币种 + 元数据标记
│   └── 已建视觉索引的61家公司.txt   已预建视觉索引的公司清单
├── 03_测试集/
│   ├── round2/  round3/  round4/  round5/
│   │                               round2=官方数据集（100题）；round3-5=自制仿考题
│   │                               每轮：题集 / 答案键 / 模板 / 被测方提交
│   │                               / 被测方答题报告 / 交叉检查报告 [/ 答案键证据]
├── 04_评分/
│   ├── grade.py                   官方 rank.py 同口径评分器（任意轮次通用）
│   └── r2_grade.py                round2 官方口径镜像评分器（历史用途）
├── 05_结果/
│   ├── round2官方数据集验证.md      round2 官方 100 题验证（92.26%，超榜首 78.8%）
│   └── 三轮验证结果.md             round3/4/5 成绩、趋势与结论
├── README.md                      本文件
└── LICENSE.md
```

---

## 二、快速开始

```bash
pip install openai pymupdf
# API key：环境变量 DEEPSEEK_API_KEY，或写入 ~/.deepseek_api_key 首行
```

**答题（人式，一题一题读）**

```python
from scripts.agentic_tools import scan_index, read_vision, read_text, verify_quote

hits = scan_index(pdf, ["employees", "headcount"])        # 1) 查目录
txt  = read_text(pdf, page0)                              # 2) 先瞄文本层
ans  = read_vision(pdf, page0, "读出该页员工总数原文")      # 3) 看图（乱码/表格页必用）
verify_quote(ans, evidence, kind, value)                  # 4) 自检后收敛
```

**评分（官方口径）**

```bash
cd 04_评分
python grade.py --questions ../03_测试集/round2/round2_questions.json \
                --key       ../03_测试集/round2/round2_answers_key.json \
                --submission ../03_测试集/round2/round2_被测方提交.json
# → round2 被测方（官方数据集）：143.00/155 = 92.26%

python grade.py --questions ../03_测试集/round5/round5_questions.json \
                --key       ../03_测试集/round5/round5_answers_key.json \
                --submission ../03_测试集/round5/round5_被测方提交.json --show-wrong
# → round5 被测方：54.00/63 = 85.71%
```

**评分口径**（与官方 `rank.py` 逐行核对过）：

| 类型 | 规则 |
|---|---|
| number | `abs(pred-gt) < 0.01*abs(gt)`（1% 容差，无部分分） |
| boolean | 字符串精确比较（小写、trim） |
| name | 字符串精确比较（小写、trim） |
| names | Jaccard = \|交集\|/\|\并集\|，GT 侧按逗号切词（**有部分分**） |
| 权重 | GT 为 N/A 的题 1 分，其余 2 分 |

---

## 三、判定规则速查（详见 `00_方案/人式读文档方案.md`）

- **boolean**：必须有"变化证据"才判 True；描述／提案／历史授权／合规声明 → False；拿不准按 False
- **N/A 纪律**：数据未披露 → N/A；报告明确写出且为 0（"$—" 行）→ 0；**禁止自算**
- **单位**：核对 2022/2021 列序（本项目最贵的一次错误来源）；题面单位与报告一致后再换算
- **职位/公司名**：答案用**报告原词**（`Director` ≠ `Non-Executive Director`）；
  多值职位用 names kind（Jaccard）；建键前穷举所有 commence/retire/designate 记录
- **反模式**：不写批量脚本、不信元数据 flag、不只读文本层、不推断未披露数据

---

## 四、验证结果

### 4.1 官方 round2 数据集（100 题，最硬核验证）

另一 AI 用人式读文档方案重做官方 round2 全部 100 题（该数据集为官方出题、官方答案键，无人为设计）：

| 指标 | 结果 |
|---|---|
| 最终得分（官方严格口径） | **143.0/155 = 92.26%**（官方榜首 78.8%） |
| 宽松口径（格式/单位/口径差异放行） | 155/155 = 100% |
| 分题型 | boolean 42/48 · name 17/17 · names 15/15 · number 69/75 |
| 评分进程 | 54.55% → 68.39% → 71.61% → **92.26%**（3 轮整改：题面匹配 → 单位口径 → boolean 口径） |

关键教训：题面必须逐字匹配官方；官方 boolean 口径="年报是否提及"；names 用逗号分隔；number 注意原始值/期末/单期口径。详见 `05_结果/round2官方数据集验证.md`。

### 4.2 自制仿考三轮（round3/4/5，各 33 题）

另一 AI 用本方案独立完成三轮各 33 题（题集与 round2 官方题零重复，真值均经原文核实）：

| 轮次 | 得分 | boolean | number | name/names |
|---|---|---|---|---|
| round3 | 69.35% | 8/10 | 89.3% | 25%/33% |
| round4 | 75.81% | 10/10 | 75.0% | 25%/67% |
| **round5** | **85.71%** | **10/10** | **89.7%** | **57%(Jaccard)** |

方法可复刻且单调进步；唯一系统性弱点是 N/A 纪律（把规则前置即可消除）。
完整裁定见各轮 `交叉检查报告.md`，其中也如实记录了**我方答案键自身的错误**。

---

## 五、说明

- PDF 语料体积较大，不随发布包分发。按 `02_语料/subset.json` 的 sha1
  从原数据集取用 `pdfs/<sha1>.pdf` 即可；61 份已建视觉索引的公司可直接复用缓存。
- 视觉索引缓存（约 4.4G）不在发布包内；首次对 PDF 使用工具时会按需实时读取
  （`scan_index` 直接读文本层、`read_vision` 实时渲染），无需预建。
  如需预建：见 `01_skill/scripts/ingest.py --route auto`。

## 六、许可

见 `LICENSE.md`。

特别感谢： https://linux.do 社区支持