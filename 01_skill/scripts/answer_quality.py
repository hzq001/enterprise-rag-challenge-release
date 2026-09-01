"""财务答案的结构化契约与确定性校验。

模型负责从页面中找出证据；本模块负责检查答案有没有把“未披露”“明确为零”、
单位换算、负号和报告期混在一起。它不替模型判断页面内容，也不调用远程 API。
"""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
import math
import re


SUPPORTED_KINDS = ("number", "boolean", "name", "names")
DISCLOSURE_STATUSES = ("reported", "explicit_zero", "not_disclosed")
NA_MARKERS = frozenset(
    {
        "",
        "n/a",
        "na",
        "not available",
        "not disclosed",
        "not applicable",
        "none",
        "null",
    }
)
ZERO_DASH_MARKERS = frozenset({"-", "–", "—", "−", "﹣"})
_NUMBER_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:\(\s*[$€£¥￥₹]?\s*[+-]?\s*\d[\d,\s]*(?:\.\d+)?\s*%?\s*\)"
    r"|[+\-−]?\s*[$€£¥￥₹]?\s*\d[\d,\s]*(?:\.\d+)?\s*%?)"
)
_CONTEXT_ALIASES = {
    "usd": ("usd", "u.s. dollar", "us dollar", "美元", "美金", "$"),
    "cny": ("cny", "rmb", "renminbi", "yuan", "人民币", "元"),
    "eur": ("eur", "euro", "欧元", "€"),
    "gbp": ("gbp", "pound", "pounds", "英镑", "£"),
    "aud": ("aud", "australian dollar", "澳元"),
    "thousand": ("thousand", "thousands", "千", "千元", "000"),
    "million": ("million", "millions", "百万", "百万美元"),
    "percent": ("%", "percent", "percentage", "百分比", "百分率"),
}


def is_na_value(value) -> bool:
    """判断答案或单元格值是否表示未披露。

    参数：
        value: 答案值或财务表格原始单元格值。
    返回值：
        是未披露标记时返回 ``True``，否则返回 ``False``。
    约束：
        只把明确的 N/A 类标记视为未披露，不把数字零视为未披露。
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NA_MARKERS
    return False


def _clean_number_text(value) -> str:
    """清理一个原始数字单元格，保留括号和正负号语义。"""
    text = str(value).strip()
    text = text.replace("\u00a0", " ").replace("−", "-").replace("﹣", "-")
    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"^[\$€£¥￥₹]", "", text)
    text = re.sub(r"%$", "", text)
    return text


def is_explicit_zero(value) -> bool:
    """判断报告中的原始值是否明确表示零。

    参数：
        value: 原始单元格值，例如 ``0``、``0.00`` 或财报常用的 ``—``。
    返回值：
        明确为零时返回 ``True``。
    异常：
        不抛出异常；无法解析的文本返回 ``False``。
    """
    if value is None or isinstance(value, bool):
        return False
    text = _clean_number_text(value)
    if text in ZERO_DASH_MARKERS:
        return True
    number = parse_reported_number(value)
    return number == 0 if number is not None else False


def parse_reported_number(value) -> Decimal | None:
    """解析财报原始数值，并保留括号负数语义。

    参数：
        value: 数字、数字字符串、带逗号/货币符号/百分号的字符串，或括号负数。
    返回值：
        可解析时返回 ``Decimal``；N/A、破折号或非数字文本返回 ``None``。
    约束：
        不从包含多个数字的句子中猜测数值；调用方应传入单元格或单个数字 token。
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return Decimal(str(value))

    raw = str(value).strip()
    if raw.lower() in NA_MARKERS:
        return None
    parenthesized = raw.startswith("(") and raw.endswith(")")
    if parenthesized:
        raw = raw[1:-1].strip()
    text = _clean_number_text(raw)
    if text in ZERO_DASH_MARKERS or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return -abs(number) if parenthesized else number


def numbers_match(expected, actual, tolerance: Decimal | str = Decimal("0.01")) -> bool:
    """按财务答案的相对容差比较两个数值，并严格检查正负号。

    参数：
        expected: 期望值。
        actual: 证据中的值。
        tolerance: 相对容差，默认 1%。
    返回值：
        数值相等或在容差内且符号一致时返回 ``True``。
    异常：
        输入无法解析或容差非正时返回 ``False``。
    """
    left = parse_reported_number(expected)
    right = parse_reported_number(actual)
    if left is None or right is None:
        return False
    try:
        margin = Decimal(str(tolerance))
    except (InvalidOperation, ValueError):
        return False
    if margin < 0:
        return False
    if left == 0:
        return right == 0
    if left * right < 0:
        return False
    return abs(right - left) <= abs(left) * margin


def extract_reported_numbers(text: str) -> list[Decimal]:
    """从一段引用中提取单个数字 token，保留括号负数。

    参数：
        text: 页面引用或表格文本。
    返回值：
        按文本出现顺序返回可解析的 ``Decimal`` 数值列表。
    约束：
        年份、页码等数字也会被返回；调用方仍需结合 raw_value、期间和单位判断。
    """
    if not text:
        return []
    values = []
    for match in _NUMBER_TOKEN.finditer(str(text)):
        number = parse_reported_number(match.group(0))
        if number is not None:
            values.append(number)
    return values


def explicit_zero_matches(raw_value, evidence_text: str) -> bool:
    """判断引用中是否出现了与原始零值对应的显式标记。

    参数：
        raw_value: 原始单元格的 ``0``、``0.00`` 或破折号。
        evidence_text: 原文引用。
    返回值：
        引用包含对应数字零或独立破折号时返回 ``True``。
    约束：
        Markdown 表格分隔线 ``---`` 不算破折号零值，避免把表格格式误当成数据。
    """
    if not is_explicit_zero(raw_value):
        return False
    text = str(evidence_text or "")
    normalized = _clean_number_text(raw_value)
    if normalized not in ZERO_DASH_MARKERS:
        return any(numbers_match(0, number) for number in extract_reported_numbers(text))

    for marker in ZERO_DASH_MARKERS:
        if re.search(
            rf"(?<![-\d]){re.escape(marker)}(?![-\d])",
            text,
        ):
            return True
    return False


def context_matches(expected, evidence_text: str) -> bool:
    """判断单位、币种或报告期是否出现在同一页证据中。

    参数：
        expected: 调用方要求的上下文，例如 ``USD``、``in thousands`` 或 ``2022``。
        evidence_text: 该页的原文或视觉转录文本。
    返回值：
        原文包含标准文本或已知同义表达时返回 ``True``。
    约束：
        这是页级必要条件，不替代对表格列和目标单元格的精确定位。
    """
    if expected is None or not str(expected).strip():
        return True
    expected_text = str(expected).strip().lower()
    evidence = str(evidence_text or "").lower()
    compact_expected = re.sub(r"\s+", "", expected_text)
    compact_evidence = re.sub(r"\s+", "", evidence)
    if expected_text in evidence or compact_expected in compact_evidence:
        return True
    for aliases in _CONTEXT_ALIASES.values():
        if compact_expected in {re.sub(r"\s+", "", alias) for alias in aliases}:
            return any(alias.lower() in evidence or re.sub(r"\s+", "", alias.lower()) in compact_evidence
                       for alias in aliases)
    return False


def resolve_reported_value(has_metric_row: bool, raw_value) -> dict:
    """按财报披露状态把原始单元格归类为数值、明确零或 N/A。

    参数：
        has_metric_row: 利润表/指标表是否确实存在目标指标行。
        raw_value: 目标单元格的原始内容。
    返回值：
        ``{"value": ..., "disclosure_status": ...}``，状态为
        ``reported``、``explicit_zero`` 或 ``not_disclosed``。
    异常：
        ``ValueError``：无指标行却提供数字/零，或有指标行但值无法解释。
    """
    if not has_metric_row:
        if is_na_value(raw_value):
            return {"value": "N/A", "disclosure_status": "not_disclosed"}
        raise ValueError("没有该指标行时不能把缺失数据填成 0 或其它数字")

    if is_na_value(raw_value):
        return {"value": "N/A", "disclosure_status": "not_disclosed"}
    if is_explicit_zero(raw_value):
        return {"value": Decimal("0"), "disclosure_status": "explicit_zero"}
    number = parse_reported_number(raw_value)
    if number is None:
        raise ValueError(f"指标行存在，但原始值无法解析: {raw_value!r}")
    return {"value": number, "disclosure_status": "reported"}


def _valid_references(references) -> bool:
    """检查引用是否至少包含一个可识别的 1 基物理页码。"""
    if not isinstance(references, list) or not references:
        return False
    for reference in references:
        page = None
        if isinstance(reference, Mapping):
            page = reference.get("page")
        elif isinstance(reference, (list, tuple)) and len(reference) >= 2:
            page = reference[1]
        if isinstance(page, bool):
            return False
        try:
            if int(page) <= 0:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _required_text(answer: Mapping, key: str, errors: list[str]) -> str:
    """读取契约中的非空文本字段并记录错误。"""
    value = answer.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} 必须是非空文本")
        return ""
    return value.strip()


def validate_answer_payload(answer: Mapping) -> list[str]:
    """校验一个带证据的财务答案对象。

    参数：
        answer: 至少包含 ``question_text/kind/value/references`` 的答案对象。
    返回值：
        空列表表示通过；否则返回所有可修复的契约错误。
    约束：
        number 答案必须同时提供 raw_value、scale、unit、currency、period、quote；
        N/A 必须声明未披露且已穷尽检索，不能以数字或显式零作为依据。
    """
    errors: list[str] = []
    if not isinstance(answer, Mapping):
        return ["答案必须是对象"]
    _required_text(answer, "question_text", errors)
    kind = answer.get("kind")
    if kind not in SUPPORTED_KINDS:
        errors.append(f"kind 必须是 {SUPPORTED_KINDS}")
    if not _valid_references(answer.get("references")):
        errors.append("references 必须包含至少一个有效的 1 基物理页码")

    value = answer.get("value")
    if is_na_value(value):
        if answer.get("disclosure_status") != "not_disclosed":
            errors.append("N/A 必须声明 disclosure_status=not_disclosed")
        if answer.get("search_exhausted") is not True:
            errors.append("N/A 必须确认已穷尽检索")
        terms = answer.get("searched_terms")
        if not isinstance(terms, list) or not any(str(term).strip() for term in terms):
            errors.append("N/A 必须记录已检索的关键词")
        raw_value = answer.get("raw_value")
        if raw_value is not None and (parse_reported_number(raw_value) is not None or is_explicit_zero(raw_value)):
            errors.append("N/A 不能同时带有数字或显式零原始值")
        return errors

    quote = _required_text(answer, "quote", errors)
    if kind == "number":
        expected = parse_reported_number(value)
        if expected is None:
            errors.append("number 的 value 必须是数值或 N/A")
        raw_value = answer.get("raw_value")
        raw_number = parse_reported_number(raw_value)
        explicit_zero = is_explicit_zero(raw_value)
        if raw_number is None and not explicit_zero:
            errors.append("number 必须提供可解析的 raw_value")
        scale = parse_reported_number(answer.get("scale", 1))
        if scale is None or scale <= 0:
            errors.append("scale 必须是正数")
        elif expected is not None and raw_number is not None and not numbers_match(expected, raw_number * scale):
            errors.append("value 与 raw_value*scale 不一致")
        if answer.get("disclosure_status") not in ("reported", "explicit_zero"):
            errors.append("number 必须声明 reported 或 explicit_zero")
        if answer.get("disclosure_status") == "explicit_zero" and (not explicit_zero or expected != 0):
            errors.append("explicit_zero 必须对应原始零值和 value=0")
        _required_text(answer, "unit", errors)
        _required_text(answer, "currency", errors)
        _required_text(answer, "period", errors)
        if not quote:
            errors.append("number 必须提供原文 quote")
    elif kind == "boolean":
        if not isinstance(value, bool):
            errors.append("boolean 的 value 必须是布尔值")
        if answer.get("rubric") not in ("mentioned", "actual_change"):
            errors.append("boolean 必须声明 rubric=mentioned 或 actual_change")
        if not _required_text(answer, "boolean_basis", errors):
            errors.append("boolean 必须记录判定依据")
    elif kind in ("name", "names"):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{kind} 的 value 必须是非空文本")
        if not quote:
            errors.append(f"{kind} 必须提供原文 quote")
    return errors
