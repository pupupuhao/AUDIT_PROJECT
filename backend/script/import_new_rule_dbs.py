import csv
import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.core.config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER


FULL_RULE_PATH = BASE_DIR / "data" / "chunks" / "rule_db(new).json"
PURE_RULE_PATH = BASE_DIR / "data" / "chunks" / "rule_db_pure(new).json"
FULL_CSV_PATH = BASE_DIR / "data" / "chunks" / "rule_db(new).csv"
PURE_CSV_PATH = BASE_DIR / "data" / "chunks" / "rule_db_pure(new).csv"

FULL_TABLE = "rule_db_new_full"
PURE_TABLE = "rule_db_new_pure"

COLUMNS = [
    "id",
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
    "display_text",
    "content",
    "embedding_text",
    "clean_text",
    "parent_context",
    "path",
    "rule_index",
    "category",
    "logic_rules",
    "raw_payload",
]


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id VARCHAR(64) PRIMARY KEY,
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
    display_text TEXT DEFAULT '',
    content TEXT DEFAULT '',
    embedding_text TEXT DEFAULT '',
    clean_text TEXT DEFAULT '',
    parent_context TEXT DEFAULT '',
    path JSONB DEFAULT '[]'::jsonb,
    rule_index INTEGER DEFAULT 0,
    category VARCHAR(100) DEFAULT '',
    logic_rules JSONB DEFAULT '{{}}'::jsonb,
    raw_payload JSONB DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_doc_id ON {table_name}(doc_id);
CREATE INDEX IF NOT EXISTS idx_{table_name}_law_name ON {table_name}(law_name);
CREATE INDEX IF NOT EXISTS idx_{table_name}_node_type ON {table_name}(node_type);
CREATE INDEX IF NOT EXISTS idx_{table_name}_parent_id ON {table_name}(parent_id);
CREATE INDEX IF NOT EXISTS idx_{table_name}_rule_index ON {table_name}(rule_index);
"""


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"{path} 内容格式错误，预期为 JSON 数组")
    return payload


def _normalize_row(item: dict) -> dict:
    return {
        "id": item.get("id", ""),
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
        "display_text": item.get("display_text", ""),
        "content": item.get("content", ""),
        "embedding_text": item.get("embedding_text", ""),
        "clean_text": item.get("clean_text", ""),
        "parent_context": item.get("parent_context", ""),
        "path": json.dumps(item.get("path", []), ensure_ascii=False),
        "rule_index": int(item.get("index", 0) or 0),
        "category": item.get("category", ""),
        "logic_rules": json.dumps(item.get("logic_rules", {}), ensure_ascii=False),
        "raw_payload": json.dumps(item, ensure_ascii=False),
    }


def _write_csv(rows: list[dict], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as file:
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


def _copy_csv(table_name: str, csv_path: Path) -> None:
    columns = ", ".join(COLUMNS)
    _run_psql(f"TRUNCATE TABLE {table_name}")
    _run_psql(
        f"\\copy {table_name} ({columns}) "
        f"FROM '{csv_path.resolve()}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"
    )


def run() -> None:
    full_rows = _load_json(FULL_RULE_PATH)
    pure_rows = _load_json(PURE_RULE_PATH)

    _write_csv(full_rows, FULL_CSV_PATH)
    _write_csv(pure_rows, PURE_CSV_PATH)

    _run_psql(CREATE_TABLE_SQL.format(table_name=FULL_TABLE))
    _run_psql(CREATE_TABLE_SQL.format(table_name=PURE_TABLE))

    _copy_csv(FULL_TABLE, FULL_CSV_PATH)
    _copy_csv(PURE_TABLE, PURE_CSV_PATH)

    print(
        f"入库完成：{FULL_TABLE} {len(full_rows)} 条，"
        f"{PURE_TABLE} {len(pure_rows)} 条。"
    )


if __name__ == "__main__":
    run()
