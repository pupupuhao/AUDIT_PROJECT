from modules.audit_engine.core.field_resolver import make_candidate, resolve_all_fields, resolve_field


def test_resolve_field_prefers_source_priority_when_values_match():
    candidates = [
        make_candidate(
            field_type="boolean|null",
            source_type="excel",
            source_file="demo.xlsx",
            source_sheet="维修预案",
            source_column="NEED_CHECK_AMT",
            raw_value="1",
        ),
        make_candidate(
            field_type="boolean|null",
            source_type="excel",
            source_file="demo.xlsx",
            source_sheet="维修工程信息",
            source_column="NEED_CHECK_AMT",
            raw_value=1,
        ),
    ]

    runtime = resolve_field(
        "need_cost_review",
        candidates,
        {"source_priority": ["维修工程信息", "维修预案"]},
    )

    assert runtime.status == "resolved"
    assert runtime.value is True
    assert runtime.candidates[runtime.selected_index].source_sheet == "维修工程信息"


def test_resolve_field_marks_conflict_but_keeps_priority_value():
    candidates = [
        make_candidate(
            field_type="boolean|null",
            source_type="excel",
            source_file="demo.xlsx",
            source_sheet="维修工程信息",
            source_column="NEED_PRO_CONTRACT",
            raw_value="1",
        ),
        make_candidate(
            field_type="boolean|null",
            source_type="excel",
            source_file="demo.xlsx",
            source_sheet="维修预案",
            source_column="NEED_PRO_CONTRACT",
            raw_value="0",
        ),
    ]

    runtime = resolve_field(
        "need_construction_contract",
        candidates,
        {"source_priority": ["维修工程信息", "维修预案"]},
    )

    assert runtime.status == "conflicting"
    assert runtime.value is True
    assert runtime.candidates[runtime.selected_index].source_sheet == "维修工程信息"


def test_resolve_all_fields_reports_missing_required_raw_fact():
    resolved = resolve_all_fields({})

    assert resolved["standard_fields"]["property_raw_value"]["status"] == "missing"
    assert "property_raw_value" in resolved["missing_fields"]


def test_warranty_status_uses_three_state_policy():
    unknown = resolve_all_fields({})
    assert unknown["standard_fields"]["warranty_status"]["value"] == "unknown"

    out = resolve_all_fields(
        {
            "warranty_status": [
                make_candidate(
                    field_type="enum|null",
                    source_type="excel",
                    source_file="demo.xlsx",
                    source_sheet="维修决案",
                    source_column="EXPIRER_REMARK",
                    raw_value="已过保",
                )
            ]
        }
    )
    assert out["standard_fields"]["warranty_status"]["value"] == "out_of_warranty"

    inside = resolve_all_fields(
        {
            "warranty_status": [
                make_candidate(
                    field_type="enum|null",
                    source_type="excel",
                    source_file="demo.xlsx",
                    source_sheet="维修决案",
                    source_column="EXPIRER_REMARK",
                    raw_value="保修期内",
                )
            ]
        }
    )
    assert inside["standard_fields"]["warranty_status"]["value"] == "in_warranty"


def test_vote_end_date_is_marked_as_proxy_date():
    resolved = resolve_all_fields(
        {
            "vote_date": [
                make_candidate(
                    field_type="date|null",
                    source_type="excel",
                    source_file="demo.xlsx",
                    source_sheet="业主表决汇总",
                    source_column="REQUEST_ENDDATE",
                    raw_value="20240301",
                )
            ]
        }
    )

    assert resolved["standard_fields"]["vote_date"]["value"] == "2024-03-01"
    assert resolved["standard_fields"]["vote_date_is_proxy"]["value"] is True
