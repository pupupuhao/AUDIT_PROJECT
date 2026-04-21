import csv
import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.core.config import EMBEDDING_DIMENSION, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER
from app.core.embedding import embed_text


INPUT_PATH = BASE_DIR / "data" / "rules" / "rules_db_new_pure_with_logic.json"
CSV_PATH = BASE_DIR / "data" / "rules" / "rules_db_new_pure_vector.csv"
TABLE_NAME = "rule_db_new_pure_vector"

COLUMNS = [
    "rule_id",
    "doc_id",
    "parent_id",
    "law_name",
    "node_level",
    "node_type",
    "clause_label",
    "item_label",
    "subitem_label",
    "sub_clause",
    "full_title",
    "title_text",
    "content",
    "clean_text",
    "embedding_text",
    "parent_context",
    "path",
    "category",
    "logic_rules",
    "required_fields",
    "embedding",
]


CREATE_TABLE_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(64) UNIQUE NOT NULL,
    doc_id VARCHAR(64) NOT NULL,
    parent_id VARCHAR(64),
    law_name VARCHAR(255) NOT NULL,
    node_level INTEGER NOT NULL,
    node_type VARCHAR(32) NOT NULL,
    clause_label VARCHAR(100) DEFAULT '',
    item_label VARCHAR(100) DEFAULT '',
    subitem_label VARCHAR(100) DEFAULT '',
    sub_clause VARCHAR(100) DEFAULT '',
    full_title TEXT DEFAULT '',
    title_text TEXT DEFAULT '',
    content TEXT DEFAULT '',
    clean_text TEXT DEFAULT '',
    embedding_text TEXT DEFAULT '',
    parent_context TEXT DEFAULT '',
    path JSONB DEFAULT '[]'::jsonb,
    category VARCHAR(100) DEFAULT '',
    logic_rules JSONB DEFAULT '{{}}'::jsonb,
    required_fields JSONB DEFAULT '[]'::jsonb,
    embedding VECTOR({EMBEDDING_DIMENSION}),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_category ON {TABLE_NAME}(category);
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_law_name ON {TABLE_NAME}(law_name);
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_rule_id ON {TABLE_NAME}(rule_id);
"""


def _vector_literal(vector: list[float]) -> str:
    clipped = vector[:EMBEDDING_DIMENSION]
    if len(clipped) < EMBEDDING_DIMENSION:
        clipped.extend([0.0] * (EMBEDDING_DIMENSION - len(clipped)))
    return "[" + ",".join(f"{value:.8f}" for value in clipped) + "]"


def _load_rules() -> list[dict]:
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"输入文件格式错误: {INPUT_PATH}")
    return payload


def _normalize_row(item: dict) -> dict:
    logic_rules = item.get("logic_rules", {}) or {}
    embedding_source = item.get("embedding_text") or item.get("clean_text") or item.get("content") or ""
    vector = embed_text(embedding_source)
    return {
        "rule_id": item.get("id", ""),
        "doc_id": item.get("doc_id", ""),
        "parent_id": item.get("parent_id") or "",
        "law_name": item.get("law_name", ""),
        "node_level": int(item.get("node_level", 0) or 0),
        "node_type": item.get("node_type", ""),
        "clause_label": item.get("clause_label", ""),
        "item_label": item.get("item_label", ""),
        "subitem_label": item.get("subitem_label", ""),
        "sub_clause": item.get("sub_clause", ""),
        "full_title": item.get("full_title", ""),
        "title_text": item.get("title_text", ""),
        "content": item.get("content", ""),
        "clean_text": item.get("clean_text", ""),
        "embedding_text": embedding_source,
        "parent_context": item.get("parent_context", ""),
        "path": json.dumps(item.get("path", []), ensure_ascii=False),
        "category": item.get("category", ""),
        "logic_rules": json.dumps(logic_rules, ensure_ascii=False),
        "required_fields": json.dumps(logic_rules.get("required_fields", []), ensure_ascii=False),
        "embedding": _vector_literal(vector),
    }


def _write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        for item in rows:
            writer.writerow(_normalize_row(item))


def _run_psql(sql: str) -> None:
    subprocess.run(
        [
            "psql",
            "-h",
            POSTGRES_HOST,
            "-p",
            str(POSTGRES_PORT),
            "-U",
            POSTGRES_USER,
            "-d",
            POSTGRES_DB,
            "-c",
            sql,
        ],
        check=True,
    )


def _copy_csv() -> None:
    columns = ", ".join(COLUMNS)
    _run_psql(f"TRUNCATE TABLE {TABLE_NAME}")
    _run_psql(
        f"\\copy {TABLE_NAME} ({columns}) "
        f"FROM '{CSV_PATH.resolve()}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"
    )


def run() -> None:
    rows = _load_rules()
    _write_csv(rows)
    _run_psql(CREATE_TABLE_SQL)
    _copy_csv()
    print(f"向量化入库完成：{TABLE_NAME} {len(rows)} 条。")


if __name__ == "__main__":
    run()
