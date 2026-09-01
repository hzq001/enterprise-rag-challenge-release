# 可切换视觉模型 Vision RAG（人式读文档）

> 让 AI **像人一样翻开一份 PDF**：先翻目录定位，再亲眼去看那一页，找不到就深挖，
> 最后带物理页码引用给出答案，并把那一页原图展示给你核对。

基于 OpenAI 兼容视觉接口的 PDF 深度问答（vision RAG），默认模型为 `deepseek-v4-flash-vision-exp`，模型、Base URL 和图片输入模式均可切换。
支持文字版、扫描版、图表、表格、代码、公式的视觉理解；回答带物理页码引用。

---

## 一、核心原则：你就是那个读文档的人

**不要写程序、不要跑流水线、不要写批量脚本。** 你是一个专业的文档阅读者，手里有一套
工具，像人一样翻开文档、看目录、看页、找到答案：

```
查目录 → 视觉看页 → 没找到就深挖 → 给答案（一次一次来，务必得到答案）
```

- 每一步（看哪页、看什么、要不要深挖）由你当下判断，没有预定义流程
- 工具只提供能力：查目录、看图、读文本、自检
- 真实使用是一次一题，每题认真做完，绝不敷衍

---

## 二、工具集（`scripts/agentic_tools.py`，你自主调用）

| 工具 | 用途 | 什么时候用 |
|---|---|---|
| `scan_index(pdf, keywords)` | **查目录**：优先查预建索引（秒回+带页标题/类型），无索引降级即时扫描 | 第 1 步，定位大概位置 |
| `read_vision(pdf, page0, instr)` | **看图（你的眼睛）**：渲染该页，按你的指令提取 | 第 2 步，视觉查看 |
| `read_text(pdf, page0)` | 快速瞄一眼文本层（零成本） | 先看文字再决定要不要看图 |
| `search_pages(pdf, query)` | 辅助检索（带词干匹配） | 目录扫不到时兜底 |
| `verify_quote(quote, evidence, kind, value, ...)` | 校验引用、数字符号与换算 | 细粒度核验 |
| `verify_answer(answer, evidence)` | 校验结构化答案契约与页面证据 | 出答案前强制核验 |

`read_vision` 内部通过 `scripts/ds_client.py`（可切换的视觉模型客户端）渲染并调用视觉模型。

---

## 三、工作流（像人一样读文档）

1. **查目录（`scan_index`）**——像人先翻目录页：**优先查预建索引**（`.cache/<sha>/index.json`，
   每页转录文本 + 页标题/类型/摘要，秒回、覆盖乱码/扫描页）；无索引自动降级即时扫描
   （会话内每个 PDF 只全量解析一次）。题目说 "employees let go"，你想年报可能写
   "headcount reduction / job cuts / restructuring"；主动换词扫，看命中页与上下文，
   判断大概在第几页。
2. **视觉看页（`read_vision`）**——翻开那一页，按你构造的指令逐字读出相关内容、表格数字、图注。
   也可先用 `read_text` 瞄一眼文本层，再决定要不要看图。
3. **深度查看**——没找到就换关键词再扫、翻邻页、找动词（appointed/resigned/effective）。
4. **收敛与核验**——找到了记录答案、raw_value、scale、单位、币种、期间、quote 和页码；
   穷尽目录与邻页仍无，记录 `N/A`、`not_disclosed`、已检索关键词和页码，再调用
   `verify_answer`。没有指标行不能填 0，只有明确出现 `0` 或 `—` 才能填 0。

> boolean 题型最易失分：词出现 ≠ 事件发生。判定标尺——**必须有"变化"的证据**
> （与去年对比的数字、报告期内实际完成的并购、明确发布的新产品、新设目标、股权注入），
> 仅有描述/常规声明/集成第三方/历史引用/可能性讨论/提案 → False。拿不准按 False。

详情见 `SKILL.md`（含 3 个实测示范与决策规则）。

---

## 四、环境要求

```bash
pip install openai pymupdf pdf-inspector   # VLM/文本路由依赖
```

Mac 原生 OCR 还需要 macOS 的 `Vision.framework` 和 Swift（安装 Xcode Command Line Tools
即可），不需要额外下载 OCR 模型。当前本机已验证支持 `zh-Hans`、`zh-Hant`、`en-US`。

API key 不内置在代码里（skill 可公开分发）。优先设置 `VISION_API_KEY`；也兼容
`DEEPSEEK_API_KEY`、`CLIPROXY_API_KEY`、`LOCAL_OPENAI_API_KEY`、`OPENAI_API_KEY`，
或把 DeepSeek key 写入 `~/.deepseek_api_key` 文件首行（仅存在于本机）。

默认配置与切换示例：

```bash
# 默认值
export VISION_BASE_URL=https://api.deepseek.com
export VISION_MODEL=deepseek-v4-flash-vision-exp
export VISION_INPUT_MODE=file

# 切换到本地 OpenAI 兼容网关和 image_url
export VISION_BASE_URL=http://localhost:8317/v1
export VISION_MODEL=gpt-5.6-luna
export VISION_INPUT_MODE=image_url
export VISION_API_KEY='...'

# auto 路由默认使用 Mac Vision OCR 处理 SCAN/GARBLED 页
export OCR_ENGINE=mac
```

图片输入模式说明：`file` 使用 Files API 并复用 `files.json`；`image_url` 接受远程 URL、data URL，
本地图片会自动转换为 Base64 data URL，因此不会访问或生成 `files.json`。不设置自动 fallback。

---

## 五、建索引（人式流程的标准前置步骤）

`scan_index` 是**索引优先**的：有预建索引（`.cache/<sha>/index.json`）就秒查索引（不打开 PDF、
带页标题/类型、转录让乱码/扫描页也可检索）；没有才降级即时扫描。因此**新 PDF 建议先建索引**：

```bash
python scripts/ingest.py "你的文件.pdf" --route auto \
  [--ocr-engine mac|vlm] [--model MODEL] [--base-url URL] [--input-mode file|image_url]
#   → router.py 页分类（TEXT/TABLE/GARBLED/SCAN/GRAPHIC）
#   → TEXT 直接取文本层；SCAN/GARBLED 默认用 Mac OCR
#   → TABLE/GRAPHIC 用 VLM 保留表格行列或图形语义
#   → 落盘 .cache/<sha>/index.json（含 page_texts 目录 + pages/ 渲染图）
#   → file 模式额外保存 files.json；image_url 模式不使用 Files API
```

如需把扫描/乱码页也交给视觉模型做对照实验，显式指定：

```bash
python scripts/ingest.py "你的文件.pdf" --route auto --ocr-engine vlm \
  --model gpt-5.6-luna --base-url http://localhost:8317/v1 --input-mode image_url
```

`--ocr-engine mac` 只处理 `SCAN/GARBLED`；`TABLE/GRAPHIC` 无论该选项如何设置都使用 VLM，
因为财务表格需要行列、单位和期间信息。两种引擎之间不做隐藏式自动回退，失败会明确报错。

- 重复运行命中缓存，瞬间返回；`--force` 重建、`--clean` 清缓存
- 不建索引也能用（`scan_index` 自动降级即时扫描），但慢且乱码/扫描页检索不到
- 61 份已建索引的 round2 PDF 缓存可复用（见 `02_语料/已建视觉索引的61家公司.txt`）

展示指定页原图（无需建索引）：

```bash
python scripts/show.py "你的文件.pdf" --pages 6,33 [--dpi 220]
```

---

## 六、目录结构

```
deepseek-v4-flash-vision-rag/
├── SKILL.md                  # skill 入口：触发条件 + 人式工作流 + 决策规则 + 实测示范
├── README.md                # 本文件
├── scripts/
│   ├── agentic_tools.py     # 人式工具集：scan_index / read_vision / read_text / search_pages / verify_answer
│   ├── answer_quality.py     # 数字解析、披露状态与答案契约校验
│   ├── ds_client.py         # 可切换模型和图片输入模式的 VLM 客户端
│   ├── file_cache.py         # Files API ID 与本地 PNG 摘要校验/断点缓存
│   ├── rendering.py         # 带 DPI 清单的 PDF 页面 PNG 缓存
│   ├── mac_ocr.py            # Mac Vision OCR 的 Python 适配层
│   ├── mac_ocr.swift         # Vision.framework OCR CLI
│   ├── ingest.py            # 建索引（→ router + transcribe）；scan_index 的索引来源
│   ├── router.py            # 页分类器（ingest 依赖）
│   ├── transcribe.py        # Mac OCR/VLM 转录（ingest 依赖）
│   ├── show.py              # 指定页高清渲染（展示用）
│   └── _inspect_cache.py    # 缓存检查小工具
├── references/
│   ├── api-notes.md         # 视觉 API 实测要点与坑（改代码前必读）
│   └── index-schema.md      # .cache 索引 JSON 结构、提示词、缓存机制
└── .cache/                  # 预建索引（按 PDF 内容哈希分目录；scan_index 第 1 步优先查这里）
    └── <sha256前16位>/
        ├── index.json        # 每页转录文本、页目录、大纲与处理链指纹
        ├── files.json        # 仅 file 模式：页码 → Files API file_id 映射
        ├── .files-manifest.json # file_id 对应 PNG 的 SHA-256
        ├── pages/.render-manifest.json # PNG 的请求/实际 DPI 与尺寸
        └── pages/p0001.png   # 每页渲染图
```

---

## 七、已知局限

- 超长跨页内容（如一张表横跨 3 页）深读时只带 ±1 邻页，极端情况用 `show.py` 看全
- 纯语音/视频型 PDF 不支持；加密 PDF 需先解密
- 页码统一按**物理页码**（第 1 张图 = 第 1 页），与书的印刷页码可能差一个前言偏移
- Mac OCR 返回识别行和坐标，不负责还原复杂财务表格的单元格关系；表格/图表页由 VLM 处理
- Mac OCR 只在 macOS 上可用；非 macOS 环境需显式使用 `--ocr-engine vlm` 或 `--route vision`
