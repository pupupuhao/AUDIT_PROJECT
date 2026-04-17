from typing import Any, Dict

from modules.audit_engine.services.audit_service import audit_project
from modules.audit_engine.services.field_mapping_layer import build_field_mapping_layer


def run_audit_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    field_mapping_layer = build_field_mapping_layer(payload)
    return audit_project(field_mapping_layer)
