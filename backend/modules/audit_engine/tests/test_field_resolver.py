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

