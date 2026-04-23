from pathlib import Path

from modules.audit_engine.services.audit_pipeline_service import run_audit_pipeline
from modules.audit_engine.services.excel_upload_service import parse_xlsx_bytes
from modules.audit_engine.services.field_mapping_layer import build_field_mapping_layer
from modules.audit_engine.services.audit_service import audit_project
from modules.audit_engine.services.standard_field_payload_builder import build_standard_field_payload_from_flat_fields


def test_sample_business_package_requires_warranty_review_and_missing_materials():
    path = Path("backend/modules/audit_engine/xlsx/辰弘佳苑小区联排及多层共13户屋面瓦片塌落、渗水维修.xlsx")
    parsed = parse_xlsx_bytes(path.read_bytes(), filename=path.name)
    result = run_audit_pipeline(parsed["rows"][0]["audit_request"])

    assert result["overall_result"] == "manual_review"
    assert result["display_result"] == "建议人工复核"
    assert result["reason_codes"] == [
        "ENTITY_WARRANTY_UNKNOWN_NEED_REVIEW",
        "TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED",
        "TRACE_MISSING_APPRAISAL_CONTRACT",
        "TRACE_MISSING_APPRAISAL_REPORT",
        "PROCESS_VOTE_DATE_PROXY_USED",
    ]
    assert result["missing_items"] == [
        "warranty_status",
        "has_construction_contract",
        "has_appraisal_contract",
        "has_appraisal_report",
    ]
    assert result["summary_conclusion"]["type"] == "manual_review"


def test_manual_demo_case_keeps_legacy_result_after_runtime_conversion():
    flat_fields = {
        "project_name": "3号楼电梯主机维修",
        "property": 1,
        "is_signed_pc": True,
        "is_signed_esc": True,
        "is_signed_esr": True,
        "need_con": True,
        "has_hou_notion_sum": True,
        "count_hou": 100,
        "agree_hou": 80,
        "sum_area": 1000,
        "agree_area": 800,
        "request_enddate": "20240301",
        "orgn_amt": 120000,
        "contract_amt": 118000,
        "expirer_remark": "已过保",
    }
    legacy_payload = {
        "project_name": flat_fields["project_name"],
        "sources": {
            "t_workspace": {
                "wsname": flat_fields["project_name"],
                "property": flat_fields["property"],
            },
            "blueprint_draft": {
                "wsname": flat_fields["project_name"],
                "property": flat_fields["property"],
                "expirer_remark": flat_fields["expirer_remark"],
            },
            "ws_project": {
                "is_signed_pc": flat_fields["is_signed_pc"],
                "is_signed_esc": flat_fields["is_signed_esc"],
                "is_signed_esr": flat_fields["is_signed_esr"],
                "need_con": flat_fields["need_con"],
                "orgn_amt": flat_fields["orgn_amt"],
            },
            "project_contract": {
                "name": flat_fields["project_name"],
                "orgn_amt": flat_fields["orgn_amt"],
                "contract_amt": flat_fields["contract_amt"],
            },
            "hou_notion_sum": {
                "__row_exists__": True,
                "count_hou": flat_fields["count_hou"],
                "agree_hou": flat_fields["agree_hou"],
                "sum_area": flat_fields["sum_area"],
                "agree_area": flat_fields["agree_area"],
                "request_enddate": flat_fields["request_enddate"],
            },
        },
    }

    legacy = audit_project(build_field_mapping_layer(legacy_payload))
    runtime_payload = build_standard_field_payload_from_flat_fields(
        {
            "project_name": flat_fields["project_name"],
            "flat_fields": flat_fields,
        }
    )
    current = run_audit_pipeline(runtime_payload)

    assert current["overall_result"] == legacy["overall_result"] == "compliant"
    assert current["display_result"] == legacy["display_result"] == "初步符合"
    assert current["reason_codes"] == legacy["reason_codes"] == [
        "ENTITY_PUBLIC_REPAIR_OBJECT",
        "PROCESS_VOTE_DATE_PROXY_USED",
    ]
    assert current["missing_items"] == legacy["missing_items"] == []


def test_warranty_status_participates_in_entity_audit():
    base = {
        "project_name": "3号楼电梯主机维修",
        "property": 1,
        "is_signed_pc": True,
        "is_signed_esc": True,
        "is_signed_esr": True,
        "need_con": True,
        "has_hou_notion_sum": True,
        "count_hou": 100,
        "agree_hou": 80,
        "sum_area": 1000,
        "agree_area": 800,
        "request_enddate": "20240301",
        "orgn_amt": 120000,
        "contract_amt": 118000,
    }

    in_warranty = dict(base, expirer_remark="保修期内")
    unknown = dict(base, expirer_remark="")
    out_of_warranty = dict(base, expirer_remark="已过保")

    assert run_audit_pipeline(build_standard_field_payload_from_flat_fields({"flat_fields": in_warranty}))["overall_result"] == "non_compliant"
    assert run_audit_pipeline(build_standard_field_payload_from_flat_fields({"flat_fields": unknown}))["overall_result"] == "manual_review"
    assert run_audit_pipeline(build_standard_field_payload_from_flat_fields({"flat_fields": out_of_warranty}))["overall_result"] == "compliant"
