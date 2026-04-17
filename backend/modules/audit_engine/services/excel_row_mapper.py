from __future__ import annotations

from typing import Any, Dict, Tuple


COLUMN_ALIASES: Dict[str, Tuple[str, str]] = {
    "project_name": ("text", "project_name"),
    "工程名称": ("text", "project_name"),
    "项目名称": ("text", "project_name"),
    "property": ("t_workspace", "property"),
    "工程性质": ("t_workspace", "property"),
    "expirer_remark": ("blueprint_draft", "expirer_remark"),
    "保修备注": ("blueprint_draft", "expirer_remark"),
    "is_signed_pc": ("ws_project", "is_signed_pc"),
    "是否已签订施工合同": ("ws_project", "is_signed_pc"),
    "is_signed_esc": ("ws_project", "is_signed_esc"),
    "是否已签订审价合同": ("ws_project", "is_signed_esc"),
    "is_signed_esr": ("ws_project", "is_signed_esr"),
    "是否已出具审价报告": ("ws_project", "is_signed_esr"),
    "need_con": ("ws_project", "need_con"),
    "是否需要签订施工合同": ("ws_project", "need_con"),
    "count_hou": ("hou_notion_sum", "count_hou"),
    "总户数": ("hou_notion_sum", "count_hou"),
    "agree_hou": ("hou_notion_sum", "agree_hou"),
    "同意户数": ("hou_notion_sum", "agree_hou"),
    "sum_area": ("hou_notion_sum", "sum_area"),
    "总面积": ("hou_notion_sum", "sum_area"),
    "agree_area": ("hou_notion_sum", "agree_area"),
    "同意面积": ("hou_notion_sum", "agree_area"),
    "request_enddate": ("hou_notion_sum", "request_enddate"),
    "征询结束日期": ("hou_notion_sum", "request_enddate"),
    "表决结束日期": ("hou_notion_sum", "request_enddate"),
    "request_startdate": ("hou_notion_sum", "request_startdate"),
    "征询开始日期": ("hou_notion_sum", "request_startdate"),
    "表决开始日期": ("hou_notion_sum", "request_startdate"),
    "reg_date": ("hou_notion_sum", "reg_date"),
    "录入日期": ("hou_notion_sum", "reg_date"),
    "startup_date": ("project_contract", "startup_date"),
    "开工日期": ("project_contract", "startup_date"),
    "orgn_amt": ("project_contract", "orgn_amt"),
    "预算金额": ("project_contract", "orgn_amt"),
    "contract_amt": ("project_contract", "contract_amt"),
    "合同金额": ("project_contract", "contract_amt"),
}


def _normalize_column(value: Any) -> str:
    return str(value or "").strip()


def _is_present(value: Any) -> bool:
    return value is not None and value != ""


def map_excel_row_to_audit_request(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map one parsed Excel row dict into the unified audit request shape.

    This helper intentionally does not parse xlsx files. The future upload API can
    parse rows with any Excel library and call this function row by row.
    """
    sources: Dict[str, Dict[str, Any]] = {
        "t_workspace": {},
        "ws_project": {},
        "blueprint_draft": {},
        "hou_notion_sum": {},
        "project_contract": {},
        "text": {},
    }
    unmapped_columns = []

    for column_name, value in (row or {}).items():
        normalized = _normalize_column(column_name)
        target = COLUMN_ALIASES.get(normalized)
        if not target:
            if _is_present(value):
                unmapped_columns.append(normalized)
            continue
        source_name, source_field = target
        sources.setdefault(source_name, {})[source_field] = value

    project_name = str(sources.get("text", {}).get("project_name") or "").strip()
    if project_name:
        sources["t_workspace"].setdefault("wsname", project_name)
        sources["blueprint_draft"].setdefault("wsname", project_name)
        sources["project_contract"].setdefault("name", project_name)

    return {
        "project_name": project_name,
        "sources": {source: values for source, values in sources.items() if values},
        "unmapped_columns": sorted(set(unmapped_columns)),
    }
