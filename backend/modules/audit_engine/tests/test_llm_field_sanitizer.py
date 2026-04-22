from modules.audit_engine.services.llm_field_sanitizer import sanitize_llm_output
from modules.audit_engine.services.local_llm_client import _classify_request_error


def test_sanitizer_drops_unknown_fields_and_invalid_evidence():
    definitions = {
        "project_type": {
            "type": "enum|null",
            "llm_extractable": True,
            "enum": ["屋面维修", "其他"],
        }
    }
    result = sanitize_llm_output(
        {
            "fields": {"project_type": "屋面维修", "audit_result": "合规"},
            "evidence": {"project_type": "屋面瓦片塌落", "audit_result": "不应保留"},
        },
        definitions,
    )

    assert result["fields"] == {"project_type": "屋面维修"}
    assert result["evidence"] == {"project_type": "屋面瓦片塌落"}
    assert result["dropped_fields"] == ["audit_result"]


def test_sanitizer_nulls_invalid_enum_and_type_values():
    definitions = {
        "project_type": {
            "type": "enum|null",
            "llm_extractable": True,
            "enum": ["屋面维修", "其他"],
        },
        "is_public_part": {
            "type": "boolean|null",
            "llm_extractable": True,
        },
    }
    result = sanitize_llm_output(
        {"fields": {"project_type": "电梯维修", "is_public_part": "无法确定"}},
        definitions,
    )

    assert result["fields"]["project_type"] is None
    assert result["fields"]["is_public_part"] is None
    assert len(result["validation_errors"]) == 2


def test_local_llm_error_classifier_labels_refused_messages():
    import requests

    error = requests.ConnectionError("Failed to establish a new connection: [Errno 111] Connection refused")

    assert _classify_request_error(error) == "refused"
