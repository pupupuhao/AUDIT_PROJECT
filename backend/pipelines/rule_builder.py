import re
from typing import Any, Dict, List


CATEGORIES = [
    "使用范围合规审计",
    "流程合规审计",
    "资料完整性审计",
    "时序合规审计",
    "金额合理性审计",
    "应急维修审计",
]

FIELD_ALIASES = {
    "is_public_part",
    "is_private_part",
    "is_property_service_scope",
    "is_emergency_repair",
    "repair_nature",
    "has_vote_trace",
    "vote_pass_rate_by_household",
    "vote_pass_rate_by_area",
    "vote_legal",
    "vote_date",
    "need_construction_contract",
    "has_construction_contract",
    "has_appraisal_contract",
    "has_appraisal_report",
    "construction_start_date",
    "is_before_vote_construct",
    "budget_amount",
    "contract_amount",
}

DOCUMENT_KEYWORDS = [
    "业主大会书面同意",
    "业主小组书面同意",
    "书面同意",
    "施工承包合同",
    "施工合同",
    "支付凭证",
    "费用清单",
    "维修方案",
    "报价单",
    "审价合同",
    "审价报告",
    "鉴定报告",
    "鉴定证明",
    "整改通知书",
    "申请材料",
    "有关材料",
    "证明",
]

OBJECT_KEYWORDS = {
    "common_part": ["共用部位", "共有部分", "屋面", "屋顶", "外墙", "楼道"],
    "common_facility": ["共用设备", "共用设施", "电梯", "消防", "水泵", "排水", "供水"],
    "public_facility": ["公共设施", "物业管理区域公共设施", "道路", "照明设施", "排水设施"],
    "private_part": ["专有部分", "室内", "户内", "自用部位", "业主专有"],
}

PROJECT_TYPE_KEYWORDS = {
    "elevator": ["电梯", "曳引机", "层门", "轿厢"],
    "facade": ["外墙", "外立面", "墙面", "脱落"],
    "roof": ["屋面", "屋顶", "渗漏"],
    "fire_system": ["消防", "消火栓", "喷淋", "火灾自动报警"],
    "drainage": ["排水", "排污", "堵塞", "爆裂"],
    "water_supply": ["给水", "供水", "水泵", "水箱"],
    "public_facility": ["道路", "照明", "门禁", "助老设施", "公共设施"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def default_logic_rules(old_logic: Dict[str, Any] | None = None) -> Dict[str, Any]:
    old_logic = old_logic or {}
    apply_scope = old_logic.get("apply_scope") or {}
    output_hint = old_logic.get("output_hint") or {}
    return {
        "rule_nature": old_logic.get("rule_nature", ""),
        "audit_stage": old_logic.get("audit_stage", ""),
        "audit_dimension": old_logic.get("audit_dimension", ""),
        "apply_scope": {
            "project_types": _listify(apply_scope.get("project_types")),
            "repair_modes": _listify(apply_scope.get("repair_modes")),
            "applicable_objects": _listify(apply_scope.get("applicable_objects")),
        },
        "judgement_mode": old_logic.get("judgement_mode", ""),
        "required_fields": _filter_known_fields(_listify(old_logic.get("required_fields"))),
        "required_documents": _listify(old_logic.get("required_documents")),
        "field_expectations": _normalize_field_expectations(old_logic.get("field_expectations")),
        "risk_points": _listify(old_logic.get("risk_points")),
        "output_hint": {
            "conclusion_type": output_hint.get("conclusion_type", ""),
            "risk_level": output_hint.get("risk_level", ""),
            "message_template": output_hint.get("message_template", ""),
        },
    }


def _listify(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _dedupe(items: List[str]) -> List[str]:
    seen: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.append(item)
    return seen


def _filter_known_fields(fields: List[str]) -> List[str]:
    return [field for field in _dedupe(fields) if field in FIELD_ALIASES]


def _normalize_field_expectations(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field", "")).strip()
        operator = str(item.get("operator", "")).strip()
        if not field or not operator:
            continue
        normalized.append(
            {
                "field": field,
                "operator": operator,
                "value": item.get("value"),
                "message": str(item.get("message", "")).strip(),
            }
        )
    return normalized


def _extract_required_documents(text: str) -> List[str]:
    docs: List[str] = []
    for keyword in DOCUMENT_KEYWORDS:
        if keyword in text and keyword not in docs:
            docs.append(keyword)
    return docs


def _infer_project_types(text: str) -> List[str]:
    matched: List[str] = []
    for project_type, keywords in PROJECT_TYPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched.append(project_type)
    return matched or ["general"]


def _infer_repair_modes(text: str) -> List[str]:
    if "应急" in text or "紧急" in text:
        return ["emergency"]
    return ["normal"]


def _infer_applicable_objects(text: str) -> List[str]:
    matched: List[str] = []
    for object_type, keywords in OBJECT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched.append(object_type)
    return matched or ["unknown"]


def _infer_category(text: str, logic_rules: Dict[str, Any]) -> str:
    if logic_rules["audit_dimension"] == "entity":
        return "使用范围合规审计"
    if logic_rules["audit_dimension"] == "trace":
        return "资料完整性审计"
    if logic_rules["audit_dimension"] == "amount":
        return "金额合理性审计"
    if "应急" in text or "紧急" in text:
        return "应急维修审计"
    if "开工" in text or "日期" in text or "先" in text and "后" in text:
        return "时序合规审计"
    return "流程合规审计"


def _infer_rule_nature(text: str) -> str:
    if re.search(r"不得|禁止|不应", text):
        return "prohibition"
    if any(keyword in text for keyword in ["资料", "材料", "报告", "合同", "凭证", "证明"]):
        return "document"
    if any(keyword in text for keyword in ["金额", "费用", "审价", "报价", "预算", "合同金额", "%", "万元", "元"]):
        return "amount"
    if any(keyword in text for keyword in ["责任人承担", "由业主承担", "由建设单位承担", "由责任人", "承担责任"]):
        return "responsibility"
    if any(keyword in text for keyword in ["范围", "不得挪作他用", "共用部位", "共用设备", "公共设施", "专有部分"]):
        return "eligibility"
    return "process"


def _infer_audit_stage(text: str) -> str:
    if any(keyword in text for keyword in ["结算", "审价", "工程量", "造价"]):
        return "settlement"
    if any(keyword in text for keyword in ["拨付", "支取", "列支", "付款", "支付"]):
        return "payment"
    if any(keyword in text for keyword in ["施工", "开工", "验收", "整改"]):
        return "construction"
    if any(keyword in text for keyword in ["表决", "同意", "公示", "申请", "启动", "立项", "实施程序"]):
        return "initiation"
    return "general"


def _infer_audit_dimension(text: str, rule_nature: str) -> str:
    if rule_nature in {"eligibility", "responsibility", "prohibition"}:
        return "entity"
    if rule_nature == "document":
        return "trace"
    if rule_nature == "amount":
        return "amount"
    return "process"


def _infer_judgement_mode(text: str, required_documents: List[str]) -> str:
    if required_documents:
        return "document_presence"
    if any(pattern in text for pattern in ["三分之二", "2/3", "50%", "30%", "15 年", "15年", "5 万元", "5万元", "元", "万元", "%"]):
        return "threshold"
    if any(keyword in text for keyword in ["应当", "必须", "应先", "事先", "不得", "禁止"]):
        return "boolean"
    return "manual_review"


def _append_expectation(expectations: List[Dict[str, Any]], field: str, operator: str, value: Any, message: str) -> None:
    for item in expectations:
        if item["field"] == field and item["operator"] == operator and item.get("value") == value:
            return
    expectations.append(
        {
            "field": field,
            "operator": operator,
            "value": value,
            "message": message,
        }
    )


def _infer_required_fields_and_expectations(text: str, judgement_mode: str) -> tuple[List[str], List[Dict[str, Any]], List[str]]:
    required_fields: List[str] = []
    expectations: List[Dict[str, Any]] = []
    risk_points: List[str] = []

    if any(keyword in text for keyword in ["共用部位", "共用设备", "公共设施", "专有部分", "物业服务"]):
        required_fields.extend(["is_public_part", "is_private_part", "is_property_service_scope"])
        if "专有部分" in text:
            risk_points.append("维修对象可能属于业主专有部分")
        if "物业服务" in text:
            risk_points.append("项目可能属于物业日常维保范围")

    if any(keyword in text for keyword in ["表决", "同意", "业主大会", "业主小组", "书面同意"]):
        required_fields.append("has_vote_trace")
        _append_expectation(expectations, "has_vote_trace", "==", True, "应存在业主表决痕迹")
        risk_points.append("缺少业主表决痕迹")

        if any(keyword in text for keyword in ["三分之二", "2/3"]):
            required_fields.extend(["vote_pass_rate_by_household", "vote_pass_rate_by_area"])
            _append_expectation(
                expectations,
                "vote_pass_rate_by_household",
                ">=",
                0.6667,
                "表决同意户数占比应达到三分之二以上",
            )
            _append_expectation(
                expectations,
                "vote_pass_rate_by_area",
                ">=",
                0.6667,
                "表决同意面积占比应达到三分之二以上",
            )
            risk_points.append("表决比例不足")

    if any(keyword in text for keyword in ["事先", "表决日期", "征询日期", "开工", "先开工后表决"]):
        required_fields.extend(["vote_date", "construction_start_date", "is_before_vote_construct"])
        _append_expectation(
            expectations,
            "is_before_vote_construct",
            "!=",
            True,
            "普通维修不应存在先开工后表决的情形",
        )
        risk_points.append("流程时序异常")

    if any(keyword in text for keyword in ["施工合同", "施工承包合同"]):
        required_fields.extend(["need_construction_contract", "has_construction_contract"])
        _append_expectation(
            expectations,
            "has_construction_contract",
            "==",
            True,
            "应具备施工合同签署痕迹",
        )
        risk_points.append("缺少施工合同")

    if "审价合同" in text:
        required_fields.append("has_appraisal_contract")
        _append_expectation(
            expectations,
            "has_appraisal_contract",
            "==",
            True,
            "应具备审价合同签署痕迹",
        )
        risk_points.append("缺少审价合同")

    if "审价报告" in text:
        required_fields.append("has_appraisal_report")
        _append_expectation(
            expectations,
            "has_appraisal_report",
            "==",
            True,
            "应具备审价报告或结算审核痕迹",
        )
        risk_points.append("缺少审价报告")

    if any(keyword in text for keyword in ["预算", "预算金额", "工程款总额", "预付款", "费用", "金额", "报价", "单价", "合同金额", "审价"]):
        if "合同" in text:
            required_fields.append("contract_amount")
        required_fields.append("budget_amount")
        if "预付款最高不得超过工程款总额的 30%" in text or "预付款最高不得超过工程款总额的30%" in text:
            _append_expectation(
                expectations,
                "budget_amount",
                "exists",
                None,
                "应核验预算或工程款金额，以判断预付款比例是否超限",
            )
        risk_points.append("金额或造价异常")

    if any(keyword in text for keyword in ["应急", "紧急"]):
        required_fields.extend(["is_emergency_repair", "repair_nature"])
        _append_expectation(
            expectations,
            "is_emergency_repair",
            "==",
            True,
            "该规则适用于应急维修场景",
        )
        risk_points.append("应急维修流程需事后复核")

    if judgement_mode == "manual_review" and not expectations:
        _append_expectation(
            expectations,
            "project_name",
            "exists",
            None,
            "当前规则需结合项目实际情况人工复核",
        )

    return _filter_known_fields(required_fields), expectations, _dedupe(risk_points)


def _infer_output_hint(rule_nature: str, audit_dimension: str, judgement_mode: str, text: str) -> Dict[str, str]:
    if rule_nature == "prohibition":
        return {
            "conclusion_type": "non_compliant",
            "risk_level": "high",
            "message_template": "项目触发禁止性规定，存在明显合规风险。",
        }
    if "应急" in text or "紧急" in text:
        return {
            "conclusion_type": "manual_review",
            "risk_level": "high",
            "message_template": "项目涉及应急维修规则，建议结合事后资料人工复核。",
        }
    if judgement_mode == "document_presence" or audit_dimension == "trace":
        return {
            "conclusion_type": "need_supplement",
            "risk_level": "medium",
            "message_template": "项目资料或手续可能不完整，需补充相关证明材料。",
        }
    if judgement_mode == "threshold":
        return {
            "conclusion_type": "manual_review",
            "risk_level": "high",
            "message_template": "项目存在阈值型校验要求，需结合实际字段结果判断是否合规。",
        }
    return {
        "conclusion_type": "manual_review",
        "risk_level": "medium",
        "message_template": "项目需结合规则和业务字段进一步复核。",
    }


def _infer_logic_rules(rule: Dict[str, Any]) -> Dict[str, Any]:
    text = normalize_text(
        " ".join(
            [
                rule.get("full_title", ""),
                rule.get("content", ""),
                rule.get("parent_context", ""),
            ]
        )
    )

    logic = default_logic_rules(rule.get("logic_rules"))
    logic["rule_nature"] = _infer_rule_nature(text)
    logic["audit_stage"] = _infer_audit_stage(text)
    logic["audit_dimension"] = _infer_audit_dimension(text, logic["rule_nature"])
    logic["apply_scope"] = {
        "project_types": _infer_project_types(text),
        "repair_modes": _infer_repair_modes(text),
        "applicable_objects": _infer_applicable_objects(text),
    }
    logic["required_documents"] = _extract_required_documents(text)
    logic["judgement_mode"] = _infer_judgement_mode(text, logic["required_documents"])
    required_fields, field_expectations, risk_points = _infer_required_fields_and_expectations(
        text,
        logic["judgement_mode"],
    )
    logic["required_fields"] = required_fields
    logic["field_expectations"] = field_expectations
    logic["risk_points"] = risk_points
    logic["output_hint"] = _infer_output_hint(
        logic["rule_nature"],
        logic["audit_dimension"],
        logic["judgement_mode"],
        text,
    )
    return logic


def enhance_rule(rule: dict) -> dict:
    logic_rules = _infer_logic_rules(rule)
    category = _infer_category(
        normalize_text(
            " ".join(
                [
                    rule.get("full_title", ""),
                    rule.get("content", ""),
                    rule.get("parent_context", ""),
                ]
            )
        ),
        logic_rules,
    )

    enhanced = dict(rule)
    enhanced["clean_text"] = rule.get("clean_text") or rule.get("embedding_text") or rule.get("content", "")
    enhanced["logic_rules"] = logic_rules
    enhanced["category"] = category if category in CATEGORIES else "流程合规审计"
    return enhanced
