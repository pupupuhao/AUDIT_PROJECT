import json
import re
from typing import Any, Dict, List

from app.core.llm_client import call_llm


CATEGORIES = [
    "使用范围合规审计",
    "流程合规审计",
    "资料完整性审计",
    "时序合规审计",
    "金额合理性审计",
    "应急维修审计",
]

CATEGORY_ALIASES = {
    "使用范围审计": "使用范围合规审计",
}


def build_prompt(rule: Dict[str, Any]) -> str:
    return f"""
你是维修资金法规结构化助手。请从下面的法规文本中提取可检索、可判定的规则信息，并输出严格 JSON。

要求：
1. keywords 输出 4-6 个短语，不要输出整句。
2. logic_rules 用于审核判断。
3. category 必须从给定列表中选择一个。
4. threshold 表示金额、比例、数量等门槛，没有则为 null。
5. required_docs 表示法规明确要求提交的材料，没有则为 []。
6. is_emergency 表示是否属于应急维修场景。
4. 只输出 JSON，不要解释。

分类列表：
{json.dumps(CATEGORIES, ensure_ascii=False)}

输出结构：
{{
  "keywords": ["关键词1", "关键词2"],
  "logic_rules": {{
    "action": "允许/禁止/必须审批/责任归属/应急",
    "target": ["适用对象"],
    "condition": ["触发条件"],
    "forbidden": ["禁止事项"],
    "responsibility": "责任主体",
    "threshold": null,
    "required_docs": [],
    "is_emergency": false
  }},
  "category": "使用范围合规审计"
}}

法规信息：
法条：{rule.get("clause_label", "")}
标题：{rule.get("full_title", "")}
正文：{rule.get("content", "")}
上下文：{rule.get("parent_context", "")}
"""


def clean_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.S)
    return match.group() if match else text


def default_logic_rules(old_logic: Dict[str, Any] | None = None) -> Dict[str, Any]:
    old_logic = old_logic or {}
    return {
        "action": "",
        "target": [],
        "condition": [],
        "forbidden": [],
        "responsibility": "",
        "threshold": old_logic.get("threshold"),
        "required_docs": old_logic.get("required_docs", []),
        "is_emergency": bool(old_logic.get("is_emergency", False)),
    }


def safe_parse(raw: str) -> dict:
    try:
        return json.loads(clean_json(raw))
    except Exception:
        print("LLM 结果解析失败，改用本地规则。")
        return {}


def normalize_category(category: str) -> str:
    category = CATEGORY_ALIASES.get(category, category)
    return category if category in CATEGORIES else "使用范围合规审计"


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _boolify(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return default


def _extract_keywords_locally(text: str) -> List[str]:
    candidates = re.findall(r"[\u4e00-\u9fa5]{2,12}", text)
    deduped = []
    for item in candidates:
        if item not in deduped:
            deduped.append(item)
    preferred = [
        item for item in deduped
        if any(token in item for token in ["维修资金", "共用", "公共", "业主", "物业", "审批", "同意", "更新", "维修", "应急"])
    ]
    merged = preferred + [item for item in deduped if item not in preferred]
    return merged[:6]


def _extract_threshold_locally(text: str) -> Any:
    normalized = " ".join((text or "").split())
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(万元|元|%|平方米|户)",
        r"超过\s*(\d+(?:\.\d+)?)\s*(万元|元|%|平方米|户)",
        r"不少于\s*(\d+(?:\.\d+)?)\s*(万元|元|%|平方米|户)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return "".join(group for group in match.groups() if group)
    return None


def _extract_required_docs_locally(text: str) -> List[str]:
    normalized = " ".join((text or "").split())
    doc_keywords = [
        "业主大会书面同意",
        "业主小组书面同意",
        "书面同意",
        "维修方案",
        "报价单",
        "审价报告",
        "鉴定报告",
        "鉴定证明",
        "整改通知书",
        "申请材料",
        "有关材料",
        "证明",
    ]
    docs = []
    for keyword in doc_keywords:
        if keyword in normalized and keyword not in docs:
            docs.append(keyword)
    return docs


def _infer_logic_rules(rule: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join([
        rule.get("full_title", ""),
        rule.get("content", ""),
        rule.get("parent_context", ""),
    ])

    logic = default_logic_rules(rule.get("logic_rules"))

    if re.search(r"不得|禁止|不应", text):
        logic["action"] = "禁止"
    elif re.search(r"应当|必须|应先|事先", text):
        logic["action"] = "必须审批"
    elif "应急" in text or "紧急" in text:
        logic["action"] = "应急"

    target_keywords = []
    for keyword in ["屋面", "外墙", "电梯", "消防", "共用部位", "共用设施", "公共设施", "物业管理区域", "维修资金"]:
        if keyword in text:
            target_keywords.append(keyword)
    logic["target"] = target_keywords[:5]

    conditions = []
    for keyword in ["书面同意", "审批", "业主大会", "业主小组", "紧急情况", "应急", "人为损坏"]:
        if keyword in text:
            conditions.append(keyword)
    logic["condition"] = conditions[:5]

    forbidden = []
    for keyword in ["室内装修", "挪作他用", "人为损坏", "开发建设单位承担", "个人承担"]:
        if keyword in text:
            forbidden.append(keyword)
    logic["forbidden"] = forbidden[:5]

    for actor in ["开发建设单位", "开发商", "责任人", "物业服务企业", "业主", "物业"]:
        if actor in text:
            logic["responsibility"] = actor
            break

    if "应急" in text or "紧急" in text:
        logic["is_emergency"] = True

    logic["threshold"] = _extract_threshold_locally(text) or logic.get("threshold")
    logic["required_docs"] = _extract_required_docs_locally(text) or logic.get("required_docs", [])

    return logic


def _infer_category(rule: Dict[str, Any], logic_rules: Dict[str, Any]) -> str:
    text = " ".join([
        rule.get("full_title", ""),
        rule.get("content", ""),
        " ".join(logic_rules.get("condition", [])),
        " ".join(logic_rules.get("forbidden", [])),
    ])

    if any(keyword in text for keyword in ["审批", "同意", "业主大会", "业主小组"]):
        return "流程合规审计"
    if any(keyword in text for keyword in ["材料", "资料", "证明"]):
        return "资料完整性审计"
    if any(keyword in text for keyword in ["应急", "紧急"]):
        return "应急维修审计"
    if any(keyword in text for keyword in ["金额", "费用", "标准"]):
        return "金额合理性审计"
    return "使用范围合规审计"


def enhance_rule(rule: dict) -> dict:
    old_logic = rule.get("logic_rules", {}) or {}

    prompt = build_prompt(rule)
    raw = call_llm(prompt)
    result = safe_parse(raw)

    local_logic = _infer_logic_rules(rule)
    llm_logic = result.get("logic_rules", {}) if isinstance(result, dict) else {}

    logic_rules = default_logic_rules(old_logic)
    logic_rules.update(
        {
            "action": llm_logic.get("action") or local_logic["action"],
            "target": _listify(llm_logic.get("target")) or local_logic["target"],
            "condition": _listify(llm_logic.get("condition")) or local_logic["condition"],
            "forbidden": _listify(llm_logic.get("forbidden")) or local_logic["forbidden"],
            "responsibility": llm_logic.get("responsibility") or local_logic["responsibility"],
            "threshold": llm_logic.get("threshold") or local_logic.get("threshold") or old_logic.get("threshold"),
            "required_docs": _listify(llm_logic.get("required_docs")) or local_logic.get("required_docs", []) or _listify(old_logic.get("required_docs")),
            "is_emergency": _boolify(
                llm_logic.get("is_emergency"),
                default=bool(local_logic.get("is_emergency") or old_logic.get("is_emergency", False)),
            ),
        }
    )

    keywords = result.get("keywords", []) if isinstance(result, dict) else []
    if not isinstance(keywords, list) or not keywords:
        keywords = _extract_keywords_locally(rule.get("content", ""))
    else:
        keywords = [str(item).strip() for item in keywords if str(item).strip()][:6]

    category = normalize_category(result.get("category", "")) if isinstance(result, dict) else ""
    if not category or category == "使用范围合规审计":
        category = _infer_category(rule, logic_rules)

    enhanced = dict(rule)
    enhanced["clean_text"] = rule.get("clean_text") or rule.get("content", "")
    enhanced["keywords"] = keywords
    enhanced["logic_rules"] = logic_rules
    enhanced["category"] = category
    return enhanced
