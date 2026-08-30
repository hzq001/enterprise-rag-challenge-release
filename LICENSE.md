# License & 数据归属说明

## 本发布包中的自有内容（MIT License）

以下内容由作者创作，以 MIT License 发布，可自由使用、修改、分发（保留版权声明）：

- `00_方案/` 下的方案文档（人式读文档流程、判定规则、验证结果）
- `01_skill/` 下的全部代码与文档（`agentic_tools.py`、`ds_client.py`、`SKILL.md`、
  `README.md`、`references/`、`scripts/` 下工具与教学示例图）
- `03_测试集/` 下**由作者制作**的内容：题集（`roundN_questions.json`）、
  答案键（`roundN_answers_key.json`）、提交模板、答案键证据、交叉检查报告
- `04_评分/grade.py` 评分器
- `05_结果/` 验证结果汇总
- `README.md` 与本文件

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 第三方数据（版权归原所有者，仅供研究复现）

| 数据 | 所有者 | 说明 |
|---|---|---|
| 年报 PDF 语料 | Enterprise RAG Challenge 主办方（TIMETOACT）及各上市公司 | **未随包分发**，请从官方渠道获取；按 `02_语料/subset.json` 的 sha1 取用 |
| `02_语料/subset.json` | 比赛官方 | 公司清单 → PDF sha1 映射、币种与元数据标记（原样随附，便于复现） |
| round2 官方题集与真值 | 比赛官方 | 仅用于校准口径（如"未披露→N/A"惯例），本包测试集与之零重复 |

## 被测方提交与报告的署名

`03_测试集/roundN/roundN_被测方提交.json` 与 `roundN_被测方答题报告.md`
由参与验证的**另一个 AI** 生成，用于展示方案的可复刻性，版权归其生成方；
随包分发仅作验证证据，引用请注明来源。

## 参考项目

- 比赛仓库：Enterprise RAG Challenge（TIMETOACT）
- DeepSeek 视觉模型 `deepseek-v4-flash-vision-exp`（API 调用，模型权重不属于本包）

> 注：旧版发布包（round1/round2 文本 RAG 批量流水线）已弃用并归档于
> `../_archive/`，不在本包范围内。
