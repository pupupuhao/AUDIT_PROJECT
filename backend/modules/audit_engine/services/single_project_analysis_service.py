from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

from fastapi import UploadFile

from modules.audit_engine.services.audit_pipeline_service import run_audit_pipeline
from modules.audit_engine.services.llm_field_classifier import classify_fields_with_local_llm
from modules.audit_engine.services.uploaded_file_parser import parse_uploaded_files


SEMANTIC_LLM_FIELDS = {
    "project_name",
    "project_type",
    "repair_object",
    "repair_scope",
    "repair_reason",
    "is_public_part",
    "is_private_part",
    "is_property_service_scope",
    "mixed_scope_detected",
}

FIELD_LABELS = {
    "project_name": "项目名称",
    "project_item_code": "工程编号",
    "warranty_status": "保修状态",
    "is_public_part": "共用部位/设施",
    "is_private_part": "专有部分",
    "is_property_service_scope": "物业服务范围",
    "has_vote_trace": "业主表决材料",
    "vote_date": "表决日期",
    "need_construction_contract": "是否需要施工合同",
    "has_construction_contract": "施工合同",
    "has_appraisal_contract": "审价合同 / 造价咨询合同",
    "has_appraisal_report": "审价报告 / 预算审核报告",
    "budget_amount": "预算金额",
    "contract_amount": "合同金额",
    "repair_scope": "维修范围",
    "repair_reason": "维修原因",
    "project_type": "项目类型",
    "repair_object": "维修对象",
    "mixed_scope_detected": "边界风险",
}

SUB_AUDIT_TITLES = {
    "entity_audit": "使用范围适配性",
    "trace_audit": "资料/手续完整性",
    "process_audit": "流程合规性",
    "amount_info": "金额与造价信息",
}

STATUS_LABELS = {
    "compliant": "初步通过",
    "non_compliant": "不符合",
    "need_supplement": "需补充材料",
    "manual_review": "建议人工复核",
    "info_only": "仅展示",
}

PROBLEM_TITLES = {
    "ENTITY_IN_WARRANTY_NOT_ELIGIBLE": "保修期条件不满足",
    "ENTITY_WARRANTY_UNKNOWN_NEED_REVIEW": "缺少保修期满依据",
    "ENTITY_PRIVATE_PART_NOT_ELIGIBLE": "维修对象疑似专有部分",
    "ENTITY_PROPERTY_SERVICE_SCOPE": "维修事项疑似物业服务范围",
    "ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW": "维修对象范围无法确认",
    "ENTITY_FIELD_CONFLICT_MANUAL_REVIEW": "维修范围字段存在冲突",
    "TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED": "缺少施工合同签署痕迹",
    "TRACE_MISSING_CONSTRUCTION_CONTRACT": "缺少施工合同材料",
    "TRACE_MISSING_APPRAISAL_CONTRACT": "缺少审价合同材料",
    "TRACE_MISSING_APPRAISAL_REPORT": "缺少审价报告材料",
    "TRACE_MISSING_VOTE_TRACE": "缺少业主表决材料",
    "PROCESS_NORMAL_VOTE_MISSING": "缺少普通维修表决流程",
    "PROCESS_NORMAL_VOTE_NOT_LEGAL": "表决结果未达到当前口径",
    "PROCESS_VOTE_DATE_MISSING": "缺少表决日期",
    "PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED": "存在先施工后表决风险",
    "PROCESS_VOTE_DATE_PROXY_USED": "表决日期为代理日期",
}

MISSING_ITEM_LABELS = {
    "warranty_status": "保修期满依据",
    "has_construction_contract": "施工合同",
    "has_appraisal_contract": "审价合同 / 造价咨询合同",
    "has_appraisal_report": "审价报告 / 预算审核报告",
    "has_vote_trace": "业主表决材料",
    "vote_date": "表决日期",
    "vote_pass_rate_by_household": "按户数表决通过率",
    "vote_pass_rate_by_area": "按面积表决通过率",
}


def _runtime_value(runtime: Any) -> Any:
    if isinstance(runtime, dict):
        return runtime.get("value")
    return runtime


def _display_value(value: Any) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    if value is None or value == "":
        return "未知"
    if value == "in_warranty":
        return "保修期内"
    if value == "out_of_warranty":
        return "已过保/保修期外"
    if value == "unknown":
        return "未知"
    return str(value)


def _runtime_source(runtime: Dict[str, Any]) -> str:
    candidates = runtime.get("candidates") or []
    selected_index = runtime.get("selected_index", -1)
    if not isinstance(selected_index, int) or selected_index < 0 or selected_index >= len(candidates):
        return ""
    candidate = candidates[selected_index] if isinstance(candidates[selected_index], dict) else {}
    sheet = str(candidate.get("source_sheet") or candidate.get("source_type") or "")
    column = str(candidate.get("source_column") or "")
    return " / ".join(item for item in (sheet, column) if item)


def _dedupe_basis(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in documents or []:
        key = (
            str(item.get("title") or item.get("display_name") or ""),
            str(item.get("document_no") or ""),
            str(item.get("article") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "title": item.get("title") or item.get("display_name") or "",
                "article": item.get("article") or "",
                "display_text": item.get("display_text") or item.get("display_name") or item.get("title") or "",
                "basis_explanation": item.get("basis_explanation") or item.get("section") or "",
            }
        )
    return output


def _raw_fields_from_standard_fields(standard_fields: Dict[str, Any]) -> Dict[str, Any]:
    return {
        field_key: _runtime_value(runtime)
        for field_key, runtime in (standard_fields or {}).items()
        if _runtime_value(runtime) is not None
    }


def _raw_text_from_row(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    if row.get("project_name"):
        parts.append(f"项目名称：{row.get('project_name')}")
    if row.get("project_key"):
        parts.append(f"项目主键：{row.get('project_key')}")
    for item in row.get("business_summary") or []:
        parts.append(str(item))
    for field_key, runtime in (row.get("standard_fields") or {}).items():
        if not isinstance(runtime, dict):
            continue
        value = runtime.get("value")
        if value is not None:
            parts.append(f"{field_key}: {value}")
        for candidate in runtime.get("candidates") or []:
            if not isinstance(candidate, dict):
                continue
            raw_value = candidate.get("raw_value")
            if raw_value is None or raw_value == "":
                continue
            source = ".".join(
                item
                for item in [
                    str(candidate.get("source_sheet") or ""),
                    str(candidate.get("source_column") or ""),
                ]
                if item
            )
            parts.append(f"{field_key} 来源 {source}: {raw_value}")
    return "\n".join(parts)


def _llm_candidate(field_key: str, value: Any, evidence: Optional[str]) -> Dict[str, Any]:
    return {
        "source_type": "llm",
        "source_file": "",
        "source_sheet": "llm",
        "source_column": field_key,
        "raw_value": evidence or value,
        "normalized_value": value,
        "confidence": 0.6,
    }


def _empty_runtime(field_key: str) -> Dict[str, Any]:
    return {
        "field_key": field_key,
        "value": None,
        "status": "missing",
        "candidates": [],
        "selected_index": -1,
    }


def merge_llm_fields(
    standard_fields: Dict[str, Any],
    llm_result: Dict[str, Any],
) -> Dict[str, Any]:
    final_fields = deepcopy(standard_fields or {})
    conflicts: List[Dict[str, Any]] = []
    if llm_result.get("available") is not True:
        return {"final_fields": final_fields, "field_conflicts": conflicts}

    evidence = llm_result.get("evidence") or {}
    for field_key, llm_value in (llm_result.get("fields") or {}).items():
        if field_key not in SEMANTIC_LLM_FIELDS:
            continue
        runtime = final_fields.setdefault(field_key, _empty_runtime(field_key))
        if not isinstance(runtime, dict):
            runtime = _empty_runtime(field_key)
            final_fields[field_key] = runtime

        candidate = _llm_candidate(field_key, llm_value, evidence.get(field_key))
        runtime.setdefault("candidates", []).append(candidate)
        llm_index = len(runtime["candidates"]) - 1
        current_value = runtime.get("value")

        if current_value is None and llm_value is not None:
            runtime["value"] = llm_value
            runtime["status"] = "llm_classified"
            runtime["selected_index"] = llm_index
            continue
        if current_value is not None and llm_value is not None and current_value != llm_value:
            conflicts.append(
                {
                    "field": field_key,
                    "parser_value": current_value,
                    "llm_value": llm_value,
                    "final_value": current_value,
                    "evidence": evidence.get(field_key),
                }
            )
            if runtime.get("status") != "conflicting":
                runtime["status"] = "conflicting"

    return {"final_fields": final_fields, "field_conflicts": conflicts}


def _structured_conflicts(raw_conflicts: List[Any], final_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for item in raw_conflicts or []:
        if isinstance(item, dict):
            field_key = str(item.get("field") or "")
            output.append(
                {
                    "field": field_key,
                    "field_label": FIELD_LABELS.get(field_key, field_key or "字段"),
                    "parser_value": _display_value(item.get("parser_value")),
                    "llm_value": _display_value(item.get("llm_value")),
                    "final_value": _display_value(item.get("final_value")),
                    "reason": "保守采用 parser / 规则字段作为最终值。",
                    "evidence": item.get("evidence") or "",
                }
            )
            continue
        field_key = str(item or "")
        runtime = final_fields.get(field_key, {}) if isinstance(final_fields, dict) else {}
        output.append(
            {
                "field": field_key,
                "field_label": FIELD_LABELS.get(field_key, field_key),
                "parser_value": "多来源不一致",
                "llm_value": "无",
                "final_value": _display_value(_runtime_value(runtime)),
                "reason": "parser 多来源字段存在冲突，按字段优先级保守采用最终值。",
                "evidence": _runtime_source(runtime) if isinstance(runtime, dict) else "",
            }
        )
    return output


def _public_private_summary(fields: Dict[str, Any]) -> List[Dict[str, str]]:
    public_part = _runtime_value(fields.get("is_public_part"))
    private_part = _runtime_value(fields.get("is_private_part"))
    if public_part is True and private_part is not True:
        return [
            {"label": "共用部位/设施", "value": "是"},
            {"label": "专有部分", "value": "否"},
        ]
    if private_part is True and public_part is not True:
        return [
            {"label": "共用部位/设施", "value": "否"},
            {"label": "专有部分", "value": "是"},
        ]
    if public_part is True and private_part is True:
        return [{"label": "维修对象属性", "value": "存在混合/冲突"}]
    return [{"label": "维修对象属性", "value": "未知"}]


def _risk_level(result: str, has_conflicts: bool = False) -> str:
    if result == "non_compliant":
        return "高"
    if result in {"manual_review", "need_supplement"} or has_conflicts:
        return "中"
    return "低"


def _build_boundary_risks(llm_result: Dict[str, Any]) -> List[Dict[str, str]]:
    fields = llm_result.get("fields") or {}
    if fields.get("mixed_scope_detected") is True:
        return [
            {
                "title": "存在合并立项边界风险",
                "description": "项目描述涉及多个维修对象/部位，存在合并立项迹象，建议人工核验是否属于同一维修事项。",
                "risk_level": "中",
            }
        ]
    return []


def _build_dimension_cards(audit_result: Dict[str, Any], boundary_risks: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for key, title in SUB_AUDIT_TITLES.items():
        sub = (audit_result.get("sub_audits") or {}).get(key, {})
        result = sub.get("result") or "manual_review"
        cards.append(
            {
                "key": key,
                "title": title,
                "result": STATUS_LABELS.get(result, result),
                "risk_level": _risk_level(result),
                "summary": (sub.get("reasons") or ["暂无异常提示。"])[0],
            }
        )
    if boundary_risks:
        cards.append(
            {
                "key": "boundary_risk",
                "title": "边界风险提示",
                "result": "建议复核",
                "risk_level": "中",
                "summary": boundary_risks[0]["description"],
            }
        )
    return cards


def _suggestion(missing_items: List[str]) -> str:
    labels = [MISSING_ITEM_LABELS.get(item, item) for item in missing_items or []]
    if labels:
        return "请补充或核验：" + "、".join(labels) + "。"
    return "请结合项目原始材料进行人工复核。"


def _build_problem_cards(audit_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for sub in (audit_result.get("sub_audits") or {}).values():
        if not isinstance(sub, dict) or sub.get("result") in {"compliant", "info_only"}:
            continue
        codes = sub.get("reason_codes") or ["NEED_REVIEW"]
        for index, code in enumerate(codes):
            cards.append(
                {
                    "title": PROBLEM_TITLES.get(code, "审计问题提示"),
                    "description": (sub.get("reasons") or ["规则引擎提示该项需要处理。"])[min(index, len(sub.get("reasons") or []) - 1)],
                    "suggestion": _suggestion(sub.get("missing_items") or []),
                    "basis": _dedupe_basis(sub.get("basis_documents") or []),
                    "reason_code": code,
                }
            )
    return cards


def _build_key_evidence(final_fields: Dict[str, Any]) -> List[Dict[str, str]]:
    keys = [
        "project_name",
        "warranty_status",
        "repair_scope",
        "repair_reason",
        "vote_date",
        "has_construction_contract",
        "has_appraisal_contract",
        "has_appraisal_report",
        "budget_amount",
        "contract_amount",
    ]
    evidence: List[Dict[str, str]] = []
    for item in _public_private_summary(final_fields):
        evidence.append({"label": item["label"], "value": item["value"], "source": "规则字段归一化", "review_hint": ""})
    for key in keys:
        runtime = final_fields.get(key, {})
        value = _runtime_value(runtime)
        if value is None and key not in {"has_construction_contract", "has_appraisal_contract", "has_appraisal_report", "warranty_status"}:
            continue
        evidence.append(
            {
                "label": FIELD_LABELS.get(key, key),
                "value": _display_value(value),
                "source": _runtime_source(runtime) if isinstance(runtime, dict) else "",
                "review_hint": "需补充材料" if value in (None, "unknown", False) and key.startswith("has_") else "",
            }
        )
    return evidence


def _build_customer_view(
    *,
    audit_result: Dict[str, Any],
    final_fields: Dict[str, Any],
    llm_result: Dict[str, Any],
    structured_conflicts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    boundary_risks = _build_boundary_risks(llm_result)
    problem_cards = _build_problem_cards(audit_result)
    overall = audit_result.get("overall_result") or "manual_review"
    range_result = (audit_result.get("sub_audits") or {}).get("entity_audit", {}).get("display_result") or "需复核"
    trace_result = (audit_result.get("sub_audits") or {}).get("trace_audit", {}).get("display_result") or "需复核"
    process_result = (audit_result.get("sub_audits") or {}).get("process_audit", {}).get("display_result") or "需复核"
    summary = (
        f"使用范围：{range_result}；资料手续：{trace_result}；流程合规：{process_result}。"
        f"总体结论为“{audit_result.get('display_result') or STATUS_LABELS.get(overall, overall)}”，"
        "当前暂不能直接作为完整合规材料流转，建议补充材料并复核边界问题。"
        if overall != "compliant"
        else "使用范围、资料手续与流程字段初步满足当前审计口径，可进入后续业务复核。"
    )
    return {
        "project_name": audit_result.get("project_name") or "",
        "overall_result": audit_result.get("display_result") or STATUS_LABELS.get(overall, overall),
        "risk_level": _risk_level(overall, bool(structured_conflicts)),
        "problem_count": len(problem_cards),
        "manual_review_required": audit_result.get("manual_review_required") or bool(structured_conflicts) or bool(boundary_risks),
        "summary": summary,
        "dimension_cards": _build_dimension_cards(audit_result, boundary_risks),
        "problem_cards": problem_cards,
        "boundary_risks": boundary_risks,
        "key_evidence": _build_key_evidence(final_fields),
    }


def _build_report_summary(audit_result: Dict[str, Any], field_conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues = audit_result.get("reason_codes") or []
    result = audit_result.get("display_result") or audit_result.get("overall_result") or "未知"
    project_name = audit_result.get("project_name") or "未识别项目"
    manual_review = audit_result.get("manual_review_required") or bool(field_conflicts)
    summary = (
        f"{project_name} 的规则审计结论为“{result}”。"
        f"当前识别到 {len(issues)} 个规则提示，"
        f"{'建议人工复核字段冲突或混合范围。' if manual_review else '暂未发现必须人工复核的字段冲突。'}"
    )
    return {
        "title": "审计报告摘要",
        "summary": summary,
        "conclusion": result,
        "issue_count": len(issues),
        "manual_review_required": manual_review,
    }


async def analyze_single_project_file(files: Iterable[UploadFile]) -> Dict[str, Any]:
    parsed = await parse_uploaded_files(files)
    parsed_files = parsed.get("files") or []
    warnings: List[str] = []

    if len(parsed_files) != 1:
        return {
            "status": "unsupported",
            "single_project_supported": False,
            "message": "当前阶段仅支持一次上传一个工程合同文件。",
            "files": parsed_files,
            "warnings": ["当前阶段仅支持一次上传一个工程合同文件。"],
        }

    file_result = parsed_files[0]
    if file_result.get("status") != "parsed":
        return {
            "status": file_result.get("status") or "failed",
            "single_project_supported": False,
            "filename": file_result.get("filename"),
            "message": file_result.get("message") or "文件未完成解析。",
            "files": parsed_files,
            "warnings": file_result.get("warnings") or [],
        }

    rows = file_result.get("rows") or []
    if len(rows) != 1:
        message = f"当前阶段仅支持单个维修项目，解析到 {len(rows)} 个项目，需人工选择或复核。"
        return {
            "status": "manual_review",
            "single_project_supported": False,
            "filename": file_result.get("filename"),
            "parse_mode": file_result.get("parse_mode"),
            "message": message,
            "files": parsed_files,
            "warnings": [message],
        }

    row = rows[0]
    raw_fields = _raw_fields_from_standard_fields(row.get("standard_fields") or {})
    raw_text = _raw_text_from_row(row)
    llm_result = classify_fields_with_local_llm(raw_fields, raw_text)
    merged = merge_llm_fields(row.get("standard_fields") or {}, llm_result)
    field_conflicts = list(row.get("conflicting_fields") or []) + merged["field_conflicts"]
    structured_conflicts = _structured_conflicts(field_conflicts, merged["final_fields"])
    final_request = dict(row.get("audit_request") or {})
    final_request["standard_fields"] = merged["final_fields"]
    final_request["warnings"] = list(final_request.get("warnings") or []) + [
        "本地 LLM 字段归类仅作辅助，最终审计结论由规则引擎输出。"
    ]
    if llm_result.get("available") is not True:
        warnings.append("本地 LLM 不可用，已跳过 AI 字段归类。")
    if field_conflicts:
        warnings.append("存在 parser 与 LLM 或多来源字段冲突，建议人工复核。")

    audit_result = run_audit_pipeline(final_request)
    report_summary = _build_report_summary(audit_result, merged["field_conflicts"])
    customer_view = _build_customer_view(
        audit_result=audit_result,
        final_fields=merged["final_fields"],
        llm_result=llm_result,
        structured_conflicts=structured_conflicts,
    )
    return {
        "status": "analyzed",
        "single_project_supported": True,
        "filename": file_result.get("filename"),
        "parse_mode": file_result.get("parse_mode"),
        "project_key": row.get("project_key"),
        "project_name": row.get("project_name"),
        "source_sheets": row.get("source_sheets") or [],
        "business_summary": row.get("business_summary") or [],
        "raw_fields": raw_fields,
        "llm_result": llm_result,
        "sanitized_fields": llm_result.get("fields") or {},
        "final_fields": merged["final_fields"],
        "field_conflicts": structured_conflicts,
        "audit_result": audit_result,
        "report_summary": report_summary,
        "customer_view": customer_view,
        "warnings": warnings + list(row.get("warnings") or []),
    }
