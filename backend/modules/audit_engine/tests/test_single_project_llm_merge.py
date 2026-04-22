from modules.audit_engine.services.single_project_analysis_service import merge_llm_fields


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
