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


def _runtime_value(runtime: Any) -> Any:
    if isinstance(runtime, dict):
        return runtime.get("value")
    return runtime


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
        "field_conflicts": field_conflicts,
        "audit_result": audit_result,
        "report_summary": report_summary,
        "warnings": warnings + list(row.get("warnings") or []),
    }
