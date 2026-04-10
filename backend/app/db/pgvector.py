import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import (
    EMBEDDING_DIMENSION,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from app.core.embedding import embed_text

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"


class PgVectorStore:
    def __init__(self):
        self.enabled = psycopg is not None

    def _ensure_driver(self) -> None:
        if psycopg is None:
            raise RuntimeError(
                "未安装 psycopg。请先执行: pip install psycopg[binary]"
            )

    def _connect(self):
        self._ensure_driver()
        return psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

    @staticmethod
    def _vector_literal(vector: List[float]) -> str:
        clipped = vector[:EMBEDDING_DIMENSION]
        if len(clipped) < EMBEDDING_DIMENSION:
            clipped = clipped + [0.0] * (EMBEDDING_DIMENSION - len(clipped))
        return "[" + ",".join(f"{value:.8f}" for value in clipped) + "]"

    def init_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
            conn.commit()

    def upsert_rule(self, rule: Dict[str, Any]) -> None:
        text = " ".join([
            rule.get("law_name", ""),
            rule.get("clause_label", ""),
            rule.get("full_title", ""),
            rule.get("content", ""),
            " ".join(rule.get("keywords", [])),
        ])
        embedding = embed_text(text)
        required_fields = rule.get("required_fields") or rule.get("logic_rules", {}).get("condition") or []

        sql = """
        INSERT INTO knowledge_base (
            rule_id, law_name, clause_label, full_title, content, category,
            keywords, logic_rules, required_fields, embedding
        )
        VALUES (
            %(rule_id)s, %(law_name)s, %(clause_label)s, %(full_title)s, %(content)s, %(category)s,
            %(keywords)s::jsonb, %(logic_rules)s::jsonb, %(required_fields)s::jsonb, %(embedding)s::vector
        )
        ON CONFLICT (rule_id) DO UPDATE SET
            law_name = EXCLUDED.law_name,
            clause_label = EXCLUDED.clause_label,
            full_title = EXCLUDED.full_title,
            content = EXCLUDED.content,
            category = EXCLUDED.category,
            keywords = EXCLUDED.keywords,
            logic_rules = EXCLUDED.logic_rules,
            required_fields = EXCLUDED.required_fields,
            embedding = EXCLUDED.embedding
        """

        payload = {
            "rule_id": rule.get("id", ""),
            "law_name": rule.get("law_name", ""),
            "clause_label": rule.get("clause_label", ""),
            "full_title": rule.get("full_title", ""),
            "content": rule.get("content", ""),
            "category": rule.get("category", ""),
            "keywords": json.dumps(rule.get("keywords", []), ensure_ascii=False),
            "logic_rules": json.dumps(rule.get("logic_rules", {}), ensure_ascii=False),
            "required_fields": json.dumps(required_fields, ensure_ascii=False),
            "embedding": self._vector_literal(embedding),
        }

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, payload)
            conn.commit()

    def search_rules(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        embedding = embed_text(query)
        sql = """
        SELECT
            rule_id, law_name, clause_label, full_title, content,
            category, keywords, logic_rules, required_fields,
            1 - (embedding <=> %(embedding)s::vector) AS score
        FROM knowledge_base
        ORDER BY embedding <=> %(embedding)s::vector
        LIMIT %(top_k)s
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "embedding": self._vector_literal(embedding),
                        "top_k": top_k,
                    },
                )
                rows = cur.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "law_name": row[1],
                    "clause_label": row[2],
                    "full_title": row[3],
                    "content": row[4],
                    "category": row[5],
                    "keywords": row[6] or [],
                    "logic_rules": row[7] or {},
                    "required_fields": row[8] or [],
                    "score": float(row[9] or 0),
                }
            )
        return results

    def list_rules(
        self,
        offset: int = 1,
        limit: int = 20,
        keyword: str = "",
        category: str = "",
    ) -> Dict[str, Any]:
        filters = []
        payload: Dict[str, Any] = {
            "offset": max(offset - 1, 0) * limit,
            "limit": limit,
        }

        if keyword:
            filters.append(
                """
                (
                    rule_id ILIKE %(keyword)s
                    OR law_name ILIKE %(keyword)s
                    OR clause_label ILIKE %(keyword)s
                    OR full_title ILIKE %(keyword)s
                    OR content ILIKE %(keyword)s
                )
                """
            )
            payload["keyword"] = f"%{keyword}%"

        if category:
            filters.append("category = %(category)s")
            payload["category"] = category

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_sql = f"""
        SELECT COUNT(*)
        FROM knowledge_base
        {where_sql}
        """
        list_sql = f"""
        SELECT
            rule_id, law_name, clause_label, full_title, content,
            category, keywords, logic_rules, required_fields
        FROM knowledge_base
        {where_sql}
        ORDER BY rule_id ASC
        OFFSET %(offset)s
        LIMIT %(limit)s
        """
        categories_sql = """
        SELECT DISTINCT category
        FROM knowledge_base
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category ASC
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, payload)
                total = cur.fetchone()[0]

                cur.execute(list_sql, payload)
                rows = cur.fetchall()

                cur.execute(categories_sql)
                category_rows = cur.fetchall()

        items = []
        for row in rows:
            items.append(
                {
                    "id": row[0],
                    "law_name": row[1],
                    "clause_label": row[2],
                    "full_title": row[3],
                    "content": row[4],
                    "category": row[5],
                    "keywords": row[6] or [],
                    "logic_rules": row[7] or {},
                    "required_docs": row[8] or [],
                }
            )

        return {
            "total": total,
            "items": items,
            "categories": [row[0] for row in category_rows],
        }

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
            rule_id, law_name, clause_label, full_title, content,
            category, keywords, logic_rules, required_fields
        FROM knowledge_base
        WHERE rule_id = %(rule_id)s
        LIMIT 1
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"rule_id": rule_id})
                row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "law_name": row[1],
            "clause_label": row[2],
            "full_title": row[3],
            "content": row[4],
            "category": row[5],
            "keywords": row[6] or [],
            "logic_rules": row[7] or {},
            "required_docs": row[8] or [],
        }

    def insert_project(self, project_name: str, raw_data: Dict[str, Any]) -> int:
        sql = """
        INSERT INTO project_data (project_name, raw_data)
        VALUES (%(project_name)s, %(raw_data)s::jsonb)
        RETURNING id
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "project_name": project_name,
                        "raw_data": json.dumps(raw_data, ensure_ascii=False),
                    },
                )
                project_id = cur.fetchone()[0]
            conn.commit()
        return project_id

    def insert_audit_result(
        self,
        project_id: int,
        rule_id: str,
        compliance: bool,
        audit_opinion: str,
        evidence: str,
    ) -> None:
        sql = """
        INSERT INTO audit_results (project_id, rule_id, compliance, audit_opinion, evidence)
        VALUES (%(project_id)s, %(rule_id)s, %(compliance)s, %(audit_opinion)s, %(evidence)s)
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "project_id": project_id,
                        "rule_id": rule_id,
                        "compliance": compliance,
                        "audit_opinion": audit_opinion,
                        "evidence": evidence,
                    },
                )
            conn.commit()


def get_pgvector_store() -> Optional[PgVectorStore]:
    store = PgVectorStore()
    return store if store.enabled else None
