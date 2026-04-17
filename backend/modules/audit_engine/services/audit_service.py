from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Iterable, List, Sequence

from modules.audit_engine.services.basis_resolver import build_from_reason_codes
from modules.audit_engine.services.rule_loader import load_rule_json


DISPLAY_MAPPING = {
    "compliant": "初步符合",
    "non_compliant": "疑似违规",
    "need_supplement": "需补充材料",
    "manual_review": "建议人工复核",
    "info_only": "仅展示",
}
ENTITY_FIELDS = [
    "project_name",
    "is_public_part",
    "is_private_part",
    "is_property_service_scope",
    "warranty_status",
    "repair_nature",
]
TRACE_FIELDS = [
    "has_vote_trace",
    "need_construction_contract",
    "has_construction_contract",
    "has_appraisal_contract",
    "has_appraisal_report",
]
PROCESS_FIELDS = [
    "property_raw_value",
    "property_value_valid",
    "repair_nature",
    "is_emergency_repair",
    "has_vote_trace",
    "vote_pass_rate_by_household",
    "vote_pass_rate_by_area",
    "vote_legal",
    "construction_start_date",
]
AMOUNT_FIELDS = ["budget_amount", "contract_amount"]
ENTITY_CODES = {
    "ENTITY_PUBLIC_REPAIR_OBJECT",
    "ENTITY_PRIVATE_PART_NOT_ELIGIBLE",
    "ENTITY_PROPERTY_SERVICE_SCOPE",
    "ENTITY_IN_WARRANTY",
    "ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW",
    "ENTITY_FIELD_CONFLICT_MANUAL_REVIEW",
}
TRACE_CODES = {
    "TRACE_MISSING_VOTE_TRACE",
    "TRACE_MISSING_CONSTRUCTION_CONTRACT",
    "TRACE_MISSING_APPRAISAL_CONTRACT",
    "TRACE_MISSING_APPRAISAL_REPORT",
    "TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED",
}
PROCESS_CODES = {
    "PROCESS_NORMAL_VOTE_MISSING",
    "PROCESS_NORMAL_VOTE_NOT_LEGAL",
    "PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW",
    "PROCESS_EMERGENCY_FLOW_EXEMPTED",
    "PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED",
    "PROCESS_PROPERTY_VALUE_UNSUPPORTED",
}
AMOUNT_CODES = {"AMOUNT_BUDGET_DISPLAY", "AMOUNT_CONTRACT_DISPLAY", "AMOUNT_INFO_MISSING"}


@lru_cache(maxsize=1)
def load_reason_code_definitions() -> Dict[str, Any]:
    return load_rule_json("audit_reason_codes.json")


def _append_unique(items: List[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in items:
            items.append(value)


def _display(result: str | None) -> str | None:
    if result is None:
        return None
    return DISPLAY_MAPPING.get(result, result)


def _result(
    result: str,
    reason_codes: Sequence[str],
    reasons: Sequence[str],
    missing_items: Sequence[str],
    audit_path: Sequence[str],
    used_fields: Sequence[str],
    applicable: bool = True,
) -> Dict[str, Any]:
    return {
        "applicable": applicable,
        "result": result,
        "display_result": _display(result),
        "reason_codes": list(reason_codes),
        "reasons": list(reasons),
        "missing_items": list(missing_items),
        "basis_documents": build_from_reason_codes(reason_codes),
        "audit_path": list(audit_path),
        "used_standard_fields": list(used_fields),
    }


def _validate_code_categories(sub_audits: Dict[str, Dict[str, Any]]) -> None:
    expected = {
        "entity_audit": ENTITY_CODES,
        "trace_audit": TRACE_CODES,
        "process_audit": PROCESS_CODES,
        "amount_info": AMOUNT_CODES,
    }
    for key, allowed_codes in expected.items():
        for code in sub_audits.get(key, {}).get("reason_codes", []):
            if code not in allowed_codes:
                raise ValueError(f"{key} 使用了非本层 reason_code: {code}")


def _audit_entity(fields: Dict[str, Any], mapping_layer: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    codes: List[str] = []
    missing: List[str] = []
    tags = set(mapping_layer.get("normalized_tags", []))
    public_part = fields.get("is_public_part")
    private_part = fields.get("is_private_part")
    property_scope = fields.get("is_property_service_scope")
    warranty_status = fields.get("warranty_status")

    if public_part is True and (private_part is True or property_scope is True):
        return _result(
            "manual_review",
            ["ENTITY_FIELD_CONFLICT_MANUAL_REVIEW"],
            ["目录映射显示为共用维修对象，但来源字段或项目语义存在专有部分/物业维保冲突，需人工复核。"],
            [],
            ["field_mapping_layer", "entity_audit", "field_conflict"],
            ENTITY_FIELDS,
        )
    if private_part is True:
        return _result(
            "non_compliant",
            ["ENTITY_PRIVATE_PART_NOT_ELIGIBLE"],
            ["项目属于业主专有部分，不符合维修资金使用条件。"],
            [],
            ["field_mapping_layer", "entity_audit", "private_part"],
            ENTITY_FIELDS,
        )
    if property_scope is True:
        return _result(
            "non_compliant",
            ["ENTITY_PROPERTY_SERVICE_SCOPE"],
            ["项目属于物业日常服务或维保范围，不符合维修资金使用条件。"],
            [],
            ["field_mapping_layer", "entity_audit", "property_service_scope"],
            ENTITY_FIELDS,
        )
    if warranty_status == "in_warranty":
        return _result(
            "manual_review",
            ["ENTITY_IN_WARRANTY"],
            ["当前展示口径下项目可能处于保修期内，需人工确认保修责任后再判断是否可使用维修资金。"],
            [],
            ["field_mapping_layer", "entity_audit", "warranty_status"],
            ENTITY_FIELDS,
        )
    if public_part is True:
        return _result(
            "compliant",
            ["ENTITY_PUBLIC_REPAIR_OBJECT"],
            ["项目属于共用部位或共用设施设备维修对象，本体合规初步通过。"],
            [],
            ["field_mapping_layer", "entity_audit", "public_repair_object"],
            ENTITY_FIELDS,
        )

    if "unknown_object" in tags:
        missing.append("project_name")
    else:
        missing.extend(["is_public_part", "is_private_part", "is_property_service_scope"])
    return _result(
        "manual_review",
        ["ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW"],
        ["项目本体对象或维修范围无法通过标准字段确认，需人工复核。"],
        missing,
        ["field_mapping_layer", "entity_audit", "object_unknown"],
        ENTITY_FIELDS,
    )


def _audit_trace(fields: Dict[str, Any]) -> Dict[str, Any]:
    codes: List[str] = []
    reasons: List[str] = []
    missing: List[str] = []

    if fields.get("has_vote_trace") is not True:
        codes.append("TRACE_MISSING_VOTE_TRACE")
        reasons.append("缺少业主表决痕迹，需补充表决汇总或相关材料。")
        missing.append("has_vote_trace")
    if fields.get("need_construction_contract") is True and fields.get("has_construction_contract") is not True:
        codes.append("TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED")
        reasons.append("当前项目需要施工合同，但未见施工合同签署痕迹。")
        missing.append("has_construction_contract")
    elif fields.get("has_construction_contract") is not True:
        codes.append("TRACE_MISSING_CONSTRUCTION_CONTRACT")
        reasons.append("缺少施工合同签署痕迹，需补充施工合同材料。")
        missing.append("has_construction_contract")
    if fields.get("has_appraisal_contract") is not True:
        codes.append("TRACE_MISSING_APPRAISAL_CONTRACT")
        reasons.append("缺少审价合同签署痕迹，需补充审价合同材料。")
        missing.append("has_appraisal_contract")
    if fields.get("has_appraisal_report") is not True:
        codes.append("TRACE_MISSING_APPRAISAL_REPORT")
        reasons.append("缺少审价报告痕迹，需补充审价报告材料。")
        missing.append("has_appraisal_report")

    if codes:
        return _result(
            "need_supplement",
            codes,
            reasons,
            missing,
            ["field_mapping_layer", "trace_audit", "trace_missing"],
            TRACE_FIELDS,
        )
    return _result(
        "compliant",
        [],
        ["资料/手续痕迹字段齐备。"],
        [],
        ["field_mapping_layer", "trace_audit", "trace_complete"],
        TRACE_FIELDS,
    )


def _audit_process(fields: Dict[str, Any], trace_result: Dict[str, Any]) -> Dict[str, Any]:
    if fields.get("property_value_valid") is False:
        return _result(
            "manual_review",
            ["PROCESS_PROPERTY_VALUE_UNSUPPORTED"],
            ["工程性质 property 值不在当前支持范围内（仅支持 1=一般维修、2=急修），未按普通维修静默处理。"],
            ["property"],
            ["field_mapping_layer", "process_audit", "property_value_unsupported"],
            PROCESS_FIELDS,
        )

    if fields.get("repair_nature") == "emergency" or fields.get("is_emergency_repair") is True:
        codes = ["PROCESS_EMERGENCY_FLOW_EXEMPTED"]
        reasons = ["紧急维修仅豁免普通维修流程，不豁免项目本体合规。"]
        missing: List[str] = []
        if trace_result.get("result") in {"need_supplement", "manual_review"}:
            codes.append("PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED")
            reasons.append("紧急维修仍需补充资料/手续痕迹以支撑事后复核。")
            missing.extend(trace_result.get("missing_items", []))
        return _result(
            "manual_review" if len(codes) > 1 else "compliant",
            codes,
            reasons,
            missing,
            ["field_mapping_layer", "process_audit", "emergency_flow"],
            PROCESS_FIELDS,
        )

    codes: List[str] = []
    reasons: List[str] = []
    missing: List[str] = []
    if fields.get("has_vote_trace") is not True:
        codes.append("PROCESS_NORMAL_VOTE_MISSING")
        reasons.append("普通维修缺少业主表决流程信息。")
        missing.append("has_vote_trace")
    elif fields.get("vote_legal") is not True:
        codes.append("PROCESS_NORMAL_VOTE_NOT_LEGAL")
        reasons.append("普通维修表决通过率未达到当前口径或无法确认，建议人工复核。")
        if fields.get("vote_legal") is None:
            missing.extend(["vote_pass_rate_by_household", "vote_pass_rate_by_area"])
    if fields.get("construction_start_date") and fields.get("vote_legal") is not True:
        codes.append("PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW")
        reasons.append("已有开工日期但普通维修表决合法性未确认，需复核流程时序。")

    if codes:
        result = "need_supplement" if codes == ["PROCESS_NORMAL_VOTE_MISSING"] else "manual_review"
        return _result(
            result,
            codes,
            reasons,
            missing,
            ["field_mapping_layer", "process_audit", "normal_flow"],
            PROCESS_FIELDS,
        )
    return _result(
        "compliant",
        [],
        ["普通维修流程字段初步符合当前审计口径。"],
        [],
        ["field_mapping_layer", "process_audit", "normal_flow"],
        PROCESS_FIELDS,
    )


def _audit_amount(fields: Dict[str, Any]) -> Dict[str, Any]:
    codes: List[str] = []
    reasons: List[str] = []
    missing: List[str] = []
    budget_amount = fields.get("budget_amount")
    contract_amount = fields.get("contract_amount")
    if budget_amount is not None:
        codes.append("AMOUNT_BUDGET_DISPLAY")
        reasons.append(f"预算金额：{budget_amount:g}。")
    else:
        missing.append("budget_amount")
    if contract_amount is not None:
        codes.append("AMOUNT_CONTRACT_DISPLAY")
        reasons.append(f"合同金额：{contract_amount:g}。")
    else:
        missing.append("contract_amount")
    if not codes:
        codes.append("AMOUNT_INFO_MISSING")
        reasons.append("缺少预算金额和合同金额，金额层仅提示展示信息缺失。")
    return _result(
        "info_only",
        codes,
        reasons,
        missing,
        ["field_mapping_layer", "amount_info", "display_only"],
        AMOUNT_FIELDS,
    )


def _aggregate(sub_audits: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    entity = sub_audits["entity_audit"]
    trace = sub_audits["trace_audit"]
    process = sub_audits["process_audit"]
    if "PROCESS_PROPERTY_VALUE_UNSUPPORTED" in process.get("reason_codes", []):
        overall = "manual_review"
        primary = process
    elif entity["result"] == "non_compliant":
        overall = "non_compliant"
        primary = entity
    elif entity["result"] == "manual_review":
        overall = "manual_review"
        primary = entity
    elif trace["result"] == "need_supplement":
        overall = "need_supplement"
        primary = trace
    elif process["result"] in {"manual_review", "non_compliant", "need_supplement"}:
        overall = process["result"]
        primary = process
    else:
        overall = "compliant"
        primary = entity

    reason_codes = list(primary.get("reason_codes", []))
    reasons = list(primary.get("reasons", []))
    missing_items = list(primary.get("missing_items", []))
    manual_review_required = overall == "manual_review" or any(
        sub.get("result") == "manual_review" for sub in sub_audits.values()
    )
    gap_categories = []
    if trace.get("result") == "need_supplement":
        gap_categories.append("资料/手续痕迹")
    if process.get("result") in {"need_supplement", "manual_review", "non_compliant"}:
        gap_categories.append("流程")
    summary_type = overall
    base_message = DISPLAY_MAPPING.get(overall, overall)
    if overall == "compliant":
        display_summary = "项目本体、资料痕迹和流程合规初步通过；金额层仅作展示。"
    elif gap_categories:
        display_summary = f"{base_message}（当前主要缺口：{'/'.join(gap_categories)}）"
    else:
        display_summary = reasons[0] if reasons else base_message
    return {
        "overall_result": overall,
        "display_result": DISPLAY_MAPPING[overall],
        "reason_codes": reason_codes,
        "reasons": reasons,
        "missing_items": missing_items,
        "basis_documents": build_from_reason_codes(reason_codes),
        "manual_review_required": manual_review_required,
        "summary_conclusion": {
            "type": summary_type,
            "entity_pass": entity.get("result") == "compliant",
            "conflict_detected": "ENTITY_FIELD_CONFLICT_MANUAL_REVIEW" in entity.get("reason_codes", []),
            "gap_categories": gap_categories,
            "primary_message": reasons[0] if reasons else base_message,
            "display_summary": display_summary,
        },
        "display_summary": display_summary,
    }


def audit_project(field_mapping_layer: Dict[str, Any]) -> Dict[str, Any]:
    fields = dict(field_mapping_layer.get("standard_fields", {}))
    entity = _audit_entity(fields, field_mapping_layer)
    trace = _audit_trace(fields)
    process = _audit_process(fields, trace)
    amount = _audit_amount(fields)
    sub_audits = {
        "entity_audit": entity,
        "trace_audit": trace,
        "process_audit": process,
        "amount_info": amount,
    }
    _validate_code_categories(sub_audits)
    aggregate = _aggregate(sub_audits)
    return {
        "project_name": fields.get("project_name") or "",
        "mapped_objects": field_mapping_layer.get("mapped_objects", []),
        "matched_object_ids": field_mapping_layer.get("matched_object_ids", []),
        "normalized_tags": field_mapping_layer.get("normalized_tags", []),
        "audit_path": ["field_mapping_layer", "entity_audit", "trace_audit", "process_audit", "amount_info"],
        "sub_audits": sub_audits,
        "field_mapping_layer": {
            "standard_fields": field_mapping_layer.get("standard_fields", {}),
            "field_mappings": field_mapping_layer.get("field_mappings", []),
            "unmapped_sources": field_mapping_layer.get("unmapped_sources", []),
            "warnings": field_mapping_layer.get("warnings", []),
        },
        **aggregate,
    }
