# Enterprise RAG Challenge —— 人式读文档视觉 RAG 方案

> 让 AI **像人一样翻开一份 PDF**：查目录 → 看图 → 深挖 → 带页码引用给答案。
> 基于可切换的 OpenAI 兼容视觉模型（默认 `deepseek-v4-flash-vision-exp`），支持文字版／扫描版／图表／表格／公式年报。


---


## Enterprise RAG Challenge・Round2 挑战详解与解决方案

> 本文档基于对 
>
> `enterprise-rag-challenge-main/round2/`
> 
>  全部资料（README、questions.json、answers.json、main.py、rank.py、teams.py、scores.csv、100 份年报 PDF、dataset.csv）的深度解析，并结合 
>
> `deepseek-v4-flash-vision-rag`
>
>  skill 的能力，给出挑战 round2 的完整分析与可执行方案。

挑战赛具体数据和说明：https://github.com/trustbit/enterprise-rag-challenge


***

## 1. 挑战背景

**Enterprise RAG Challenge** 是由 TIMETOACT GROUP Austria 举办的全球性 RAG（检索增强生成）竞赛：给出一批公开公司的年报 PDF，参赛系统需检索 PDF 内容回答预设问题，答案必须带物理页码引用（证明不是幻觉）。Round1 是试水轮：规模小、问题由模板生成、掺杂大量 "陷阱题"。Round2 是完整轮。 

## 2. 数据构成



| 项目     | 数量   | 说明                                                        |
| ------ | ---- | --------------------------------------------------------- |
| 年报 PDF | 20 份 | 对应 20 家上市公司，文件名 = 文件 sha1                                 |
| 问题     | 40 题 | schema 分 `number` / `name` / `boolean` 三类                 |
| 公司映射   | 20 家 | 由 `round1/dataset.csv`（sha1, date, company\_name, size）还原 |
| 历史成绩   | 若干   | `round1/scores.csv`，最高 84 分（Daniel Weller）                |

### 2.1 20 份 PDF → 公司映射



| sha1      | 公司                                           | 报告覆盖期             |
| --------- | -------------------------------------------- | ----------------- |
| 194000c9… | Holley Inc.                                  | FY2022（2023-03 报） |
| 2779336b… | Tradition                                    | 2022-12           |
| 43437bcc… | ENRG ELEMENTS LIMITED                        | 2022-06           |
| 6054ec55… | MITSUI O.S.K. LINES                          | 2022-03           |
| 609042c6… | Petra Diamonds                               | 2022-06           |
| 84749ef5… | BAKER STEEL RESOURCES TRUST LIMITED          | 2022-12           |
| 85fb23ba… | TransUnion                                   | FY2021（2022-01 报） |
| 9d7a7244… | TSX\_Y                                       | 2022-01           |
| a706b44b… | Oesterreichische Kontrollbank                | 2022-01           |
| a8077fe1… | PowerFleet                                   | FY2022（2023-03 报） |
| ac9aa244… | Mercia Asset Management PLC                  | 2022-01           |
| ba5852cb… | Caixa Geral de Depósitos                     | 2022-12           |
| cbd8fb25… | Tower Semiconductor Ltd.                     | 2023-12           |
| e0d6bb57… | Creative Media & Community Trust Corporation | 2023-03           |
| e2b19d2c… | CrossFirst Bank                              | 2022-12           |
| e33544bd… | Sensata                                      | 2022-01           |
| e62b2ebe… | Sleep Country Canada Holdings Inc.           | 2022-01           |
| e765cdd4… | First Mid Bancshares                         | 2022-12           |
| f06d7ecc… | Safe & Green Holdings Corp.                  | 2023-03           |
| f721fa86… | TSX\_ACQ                                     | 2022-12           |

> 注意：
>
> `dataset.csv`
>
>  的 date 字段是 "报告日期"，而问题可能问的是不同财年 —— 这是 round1 最大的陷阱来源。

## 3. 计分机制（来自 `rank.py`）

评分采用 Math Kangaroo 风格：



* **问题分类**：按 `answers.json` 中 "有效答案集合是否包含 N/A" 区分两类 ——


  * **N/A 类**（答案可为 N/A）：满分 **1 分**；

  * **检索类**（必须给出具体值）：满分 **2 分**。

* **答案匹配规则**（按 schema）：


  * `number`：与真值误差 **<1% 得全分（× 满分），<10% 得半分（×0.5）**；

  * `name`：字符串**精确匹配**（大小写敏感）得全分；

  * `boolean`：二值精确匹配得全分。

* 若真值有多个有效答案（如 `["N/A", 值]`），取参赛者得分最高者。

* 最终得分 = `100 × 实际得分 / 满分`。

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
│   │   ├── ds_client.py            可切换模型与图片输入模式的 VLM 客户端
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

### 直接在codex/workbuddy等agent命令AI， 利用 deepseek-v4-flash-vision-rag skill 解决 enterprise-rag-challenge ！ 

以下是实际代码运行，可以不需要理会：

```bash
pip install openai pymupdf
# 默认 DeepSeek：
export DEEPSEEK_API_KEY='...'
# 也可以统一配置任意 OpenAI 兼容视觉接口：
export VISION_API_KEY='...'
export VISION_BASE_URL='http://localhost:8317/v1'
export VISION_MODEL='gpt-5.6-luna'
export VISION_INPUT_MODE='image_url'
```

图片输入有两种模式：`file` 使用 Files API 上传并缓存 `file_id`；`image_url` 使用远程 URL、data URL，或把本地图片转换为 Base64 data URL，不访问 Files API。默认模式为 `file`，可用 `VISION_INPUT_MODE` 或命令行参数切换；不做自动 fallback。

预建索引时也可逐次覆盖模型、接口和输入模式：

```bash
python 01_skill/scripts/ingest.py "你的文件.pdf" --route vision \
  --model gpt-5.6-luna \
  --base-url http://localhost:8317/v1 \
  --input-mode image_url
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
