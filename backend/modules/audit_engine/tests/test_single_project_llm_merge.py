from modules.audit_engine.services.single_project_analysis_service import _build_customer_view, _dedupe_basis, merge_llm_fields


def test_merge_llm_fields_fills_missing_semantic_value():
    standard_fields = {
        "is_public_part": {
            "field_key": "is_public_part",
            "value": None,
            "status": "missing",
            "candidates": [],
            "selected_index": -1,
        }
    }
    llm_result = {
        "available": True,
        "fields": {"is_public_part": True},
        "evidence": {"is_public_part": "屋面瓦片塌落、渗水维修"},
    }

    merged = merge_llm_fields(standard_fields, llm_result)

    assert merged["final_fields"]["is_public_part"]["value"] is True
    assert merged["final_fields"]["is_public_part"]["status"] == "llm_classified"
    assert merged["field_conflicts"] == []


def test_merge_llm_fields_keeps_parser_value_on_conflict():
    standard_fields = {
        "is_public_part": {
            "field_key": "is_public_part",
            "value": True,
            "status": "inferred",
            "candidates": [],
            "selected_index": 0,
        }
    }
    llm_result = {
        "available": True,
        "fields": {"is_public_part": False},
        "evidence": {"is_public_part": "模型误判"},
    }

    merged = merge_llm_fields(standard_fields, llm_result)

    assert merged["final_fields"]["is_public_part"]["value"] is True
    assert merged["field_conflicts"][0]["final_value"] is True


def test_basis_dedupe_uses_document_and_article():
    documents = [
        {"title": "住宅专项维修资金管理办法", "document_no": "165号", "article": "第十八条", "basis_explanation": "说明1"},
        {"title": "住宅专项维修资金管理办法", "document_no": "165号", "article": "第十八条", "basis_explanation": "说明2"},
    ]

    assert len(_dedupe_basis(documents)) == 1


def test_mixed_scope_is_boundary_risk_not_problem_card():
    audit_result = {
        "project_name": "屋面及外墙维修",
        "overall_result": "compliant",
        "display_result": "初步符合",
        "manual_review_required": False,
        "sub_audits": {
            "entity_audit": {"result": "compliant", "display_result": "初步符合", "reasons": ["范围初步适配。"], "reason_codes": [], "basis_documents": []},
            "trace_audit": {"result": "compliant", "display_result": "初步符合", "reasons": ["资料齐备。"], "reason_codes": [], "basis_documents": []},
            "process_audit": {"result": "compliant", "display_result": "初步符合", "reasons": ["流程初步符合。"], "reason_codes": [], "basis_documents": []},
            "amount_info": {"result": "info_only", "display_result": "仅展示", "reasons": ["金额展示。"], "reason_codes": [], "basis_documents": []},
        },
    }

    view = _build_customer_view(
        audit_result=audit_result,
        final_fields={},
        llm_result={"fields": {"mixed_scope_detected": True}},
        structured_conflicts=[],
    )

    assert view["problem_count"] == 0
    assert view["boundary_risks"][0]["title"] == "存在合并立项边界风险"
    assert view["manual_review_required"] is True
