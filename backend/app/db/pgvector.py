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
NEW_RULE_TABLE = "rule_db_new_pure"
NEW_RULE_VECTOR_TABLE = "rule_db_new_pure_vector"


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
            keywords, logic_rules, required_fields, embedding, updated_at
        )
        VALUES (
            %(rule_id)s, %(law_name)s, %(clause_label)s, %(full_title)s, %(content)s, %(category)s,
            %(keywords)s::jsonb, %(logic_rules)s::jsonb, %(required_fields)s::jsonb, %(embedding)s::vector, CURRENT_TIMESTAMP
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
            embedding = EXCLUDED.embedding,
            updated_at = CURRENT_TIMESTAMP
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

    def search_new_pure_rules(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        embedding = embed_text(query)
        sql = f"""
        SELECT
            rule_id, doc_id, parent_id, law_name, node_level, node_type,
            clause_label, item_label, subitem_label, sub_clause,
            full_title, title_text, content, clean_text, embedding_text,
            parent_context, path, category, logic_rules, required_fields,
            1 - (embedding <=> %(embedding)s::vector) AS score
        FROM {NEW_RULE_VECTOR_TABLE}
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
            logic_rules = row[18] or {}
            if logic_rules and not logic_rules.get("required_fields"):
                logic_rules["required_fields"] = row[19] or []
            results.append(
                {
                    "id": row[0],
                    "doc_id": row[1],
                    "parent_id": row[2],
                    "law_name": row[3],
                    "node_level": row[4],
                    "node_type": row[5],
                    "clause_label": row[6],
                    "item_label": row[7] or "",
                    "subitem_label": row[8] or "",
                    "sub_clause": row[9] or "",
                    "full_title": row[10] or "",
                    "title_text": row[11] or "",
                    "content": row[12] or "",
                    "clean_text": row[13] or "",
                    "embedding_text": row[14] or "",
                    "parent_context": row[15] or "",
                    "path": row[16] or [],
                    "category": row[17] or "",
                    "logic_rules": logic_rules,
                    "score": float(row[20] or 0),
                }
            )
        return results

    def list_new_pure_rules(
        self,
        offset: int = 1,
        limit: int = 20,
        keyword: str = "",
        category: str = "",
        law_name: str = "",
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
        if law_name:
            filters.append("law_name = %(law_name)s")
            payload["law_name"] = law_name

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        count_sql = f"SELECT COUNT(*) FROM {NEW_RULE_VECTOR_TABLE} {where_sql}"
        list_sql = f"""
        SELECT
            rule_id, doc_id, parent_id, law_name, node_level, node_type,
            clause_label, item_label, subitem_label, sub_clause,
            full_title, title_text, content, clean_text, embedding_text,
            parent_context, path, category, logic_rules
        FROM {NEW_RULE_VECTOR_TABLE}
        {where_sql}
        ORDER BY rule_id ASC
        OFFSET %(offset)s
        LIMIT %(limit)s
        """
        categories_sql = f"""
        SELECT DISTINCT category
        FROM {NEW_RULE_VECTOR_TABLE}
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category ASC
        """
        law_count_sql = f"SELECT COUNT(DISTINCT law_name) FROM {NEW_RULE_VECTOR_TABLE} {where_sql}"
        latest_updated_sql = f"SELECT MAX(updated_at) FROM {NEW_RULE_VECTOR_TABLE} {where_sql}"

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, payload)
                total = cur.fetchone()[0]
                cur.execute(list_sql, payload)
                rows = cur.fetchall()
                cur.execute(categories_sql)
                category_rows = cur.fetchall()
                cur.execute(law_count_sql, payload)
                law_count = cur.fetchone()[0] or 0
                cur.execute(latest_updated_sql, payload)
                latest_updated_at = cur.fetchone()[0]

        items = []
        for row in rows:
            items.append(
                {
                    "id": row[0],
                    "doc_id": row[1],
                    "parent_id": row[2],
                    "law_name": row[3],
                    "node_level": row[4],
                    "node_type": row[5],
                    "clause_label": row[6],
                    "item_label": row[7] or "",
                    "subitem_label": row[8] or "",
                    "sub_clause": row[9] or "",
                    "full_title": row[10] or "",
                    "title_text": row[11] or "",
                    "content": row[12] or "",
                    "clean_text": row[13] or "",
                    "embedding_text": row[14] or "",
                    "parent_context": row[15] or "",
                    "path": row[16] or [],
                    "index": None,
                    "category": row[17] or "",
                    "logic_rules": row[18] or {},
                }
            )

        return {
            "total": total,
            "items": items,
            "categories": [row[0] for row in category_rows],
            "law_count": law_count,
            "latest_updated_at": latest_updated_at.isoformat() if latest_updated_at else None,
        }

    def get_new_pure_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        sql = f"""
        SELECT
            rule_id, doc_id, parent_id, law_name, node_level, node_type,
            clause_label, item_label, subitem_label, sub_clause,
            full_title, title_text, content, clean_text, embedding_text,
            parent_context, path, category, logic_rules
        FROM {NEW_RULE_VECTOR_TABLE}
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
            "doc_id": row[1],
            "parent_id": row[2],
            "law_name": row[3],
            "node_level": row[4],
            "node_type": row[5],
            "clause_label": row[6],
            "item_label": row[7] or "",
            "subitem_label": row[8] or "",
            "sub_clause": row[9] or "",
            "full_title": row[10] or "",
            "title_text": row[11] or "",
            "content": row[12] or "",
            "clean_text": row[13] or "",
            "embedding_text": row[14] or "",
            "parent_context": row[15] or "",
            "path": row[16] or [],
            "index": None,
            "category": row[17] or "",
            "logic_rules": row[18] or {},
        }

    def count_new_pure_rules_by_law_names(self, law_names: List[str]) -> Dict[str, int]:
        names = [name for name in law_names if name]
        if not names:
            return {}
        sql = f"""
        SELECT law_name, COUNT(*)
        FROM {NEW_RULE_VECTOR_TABLE}
        WHERE law_name = ANY(%(law_names)s)
        GROUP BY law_name
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"law_names": names})
                rows = cur.fetchall()
        return {row[0]: int(row[1]) for row in rows}

    def upsert_new_pure_rule(self, rule: Dict[str, Any]) -> None:
        embedding_text = " ".join(
            [
                rule.get("law_name", ""),
                rule.get("full_title", ""),
                rule.get("parent_context", ""),
                rule.get("embedding_text", "") or rule.get("clean_text", "") or rule.get("content", ""),
            ]
        ).strip()
        sql = f"""
        INSERT INTO {NEW_RULE_TABLE} (
            id, doc_id, parent_id, law_name, node_level, node_type,
            clause_label, item_label, subitem_label, sub_clause,
            full_title, title_text, display_text, content, embedding_text, clean_text,
            parent_context, path, rule_index, category, logic_rules, raw_payload, updated_at
        )
        VALUES (
            %(id)s, %(doc_id)s, %(parent_id)s, %(law_name)s, %(node_level)s, %(node_type)s,
            %(clause_label)s, %(item_label)s, %(subitem_label)s, %(sub_clause)s,
            %(full_title)s, %(title_text)s, %(display_text)s, %(content)s, %(embedding_text)s, %(clean_text)s,
            %(parent_context)s, %(path)s::jsonb, %(rule_index)s, %(category)s, %(logic_rules)s::jsonb, %(raw_payload)s::jsonb, CURRENT_TIMESTAMP
        )
        ON CONFLICT (id) DO UPDATE SET
            doc_id = EXCLUDED.doc_id,
            parent_id = EXCLUDED.parent_id,
            law_name = EXCLUDED.law_name,
            node_level = EXCLUDED.node_level,
            node_type = EXCLUDED.node_type,
            clause_label = EXCLUDED.clause_label,
            item_label = EXCLUDED.item_label,
            subitem_label = EXCLUDED.subitem_label,
            sub_clause = EXCLUDED.sub_clause,
            full_title = EXCLUDED.full_title,
            title_text = EXCLUDED.title_text,
            display_text = EXCLUDED.display_text,
            content = EXCLUDED.content,
            embedding_text = EXCLUDED.embedding_text,
            clean_text = EXCLUDED.clean_text,
            parent_context = EXCLUDED.parent_context,
            path = EXCLUDED.path,
            rule_index = EXCLUDED.rule_index,
            category = EXCLUDED.category,
            logic_rules = EXCLUDED.logic_rules,
            raw_payload = EXCLUDED.raw_payload,
            updated_at = CURRENT_TIMESTAMP
        """
        payload = {
            "id": rule.get("id", ""),
            "doc_id": rule.get("doc_id", ""),
            "parent_id": rule.get("parent_id"),
            "law_name": rule.get("law_name", ""),
            "node_level": rule.get("node_level"),
            "node_type": rule.get("node_type", ""),
            "clause_label": rule.get("clause_label", ""),
            "item_label": rule.get("item_label", ""),
            "subitem_label": rule.get("subitem_label", ""),
            "sub_clause": rule.get("sub_clause", ""),
            "full_title": rule.get("full_title", ""),
            "title_text": rule.get("title_text", ""),
            "display_text": rule.get("content", ""),
            "content": rule.get("content", ""),
            "embedding_text": embedding_text,
            "clean_text": rule.get("clean_text", "") or embedding_text,
            "parent_context": rule.get("parent_context", ""),
            "path": json.dumps(rule.get("path", []), ensure_ascii=False),
            "rule_index": rule.get("index"),
            "category": rule.get("category", ""),
            "logic_rules": json.dumps(rule.get("logic_rules", {}), ensure_ascii=False),
            "raw_payload": json.dumps(rule, ensure_ascii=False),
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, payload)
            conn.commit()

        vector_sql = f"""
        INSERT INTO {NEW_RULE_VECTOR_TABLE} (
            rule_id, doc_id, parent_id, law_name, node_level, node_type,
            clause_label, item_label, subitem_label, sub_clause,
            full_title, title_text, content, clean_text, embedding_text,
            parent_context, path, category, logic_rules, required_fields, embedding, updated_at
        )
        VALUES (
            %(rule_id)s, %(doc_id)s, %(parent_id)s, %(law_name)s, %(node_level)s, %(node_type)s,
            %(clause_label)s, %(item_label)s, %(subitem_label)s, %(sub_clause)s,
            %(full_title)s, %(title_text)s, %(content)s, %(clean_text)s, %(embedding_text)s,
            %(parent_context)s, %(path)s::jsonb, %(category)s, %(logic_rules)s::jsonb, %(required_fields)s::jsonb, %(embedding)s::vector, CURRENT_TIMESTAMP
        )
        ON CONFLICT (rule_id) DO UPDATE SET
            doc_id = EXCLUDED.doc_id,
            parent_id = EXCLUDED.parent_id,
            law_name = EXCLUDED.law_name,
            node_level = EXCLUDED.node_level,
            node_type = EXCLUDED.node_type,
            clause_label = EXCLUDED.clause_label,
            item_label = EXCLUDED.item_label,
            subitem_label = EXCLUDED.subitem_label,
            sub_clause = EXCLUDED.sub_clause,
            full_title = EXCLUDED.full_title,
            title_text = EXCLUDED.title_text,
            content = EXCLUDED.content,
            clean_text = EXCLUDED.clean_text,
            embedding_text = EXCLUDED.embedding_text,
            parent_context = EXCLUDED.parent_context,
            path = EXCLUDED.path,
            category = EXCLUDED.category,
            logic_rules = EXCLUDED.logic_rules,
            required_fields = EXCLUDED.required_fields,
            embedding = EXCLUDED.embedding,
            updated_at = CURRENT_TIMESTAMP
        """
        vector_payload = {
            "rule_id": rule.get("id", ""),
            "doc_id": rule.get("doc_id", ""),
            "parent_id": rule.get("parent_id"),
            "law_name": rule.get("law_name", ""),
            "node_level": rule.get("node_level"),
            "node_type": rule.get("node_type", ""),
            "clause_label": rule.get("clause_label", ""),
            "item_label": rule.get("item_label", ""),
            "subitem_label": rule.get("subitem_label", ""),
            "sub_clause": rule.get("sub_clause", ""),
            "full_title": rule.get("full_title", ""),
            "title_text": rule.get("title_text", ""),
            "content": rule.get("content", ""),
            "clean_text": rule.get("clean_text", "") or embedding_text,
            "embedding_text": embedding_text,
            "parent_context": rule.get("parent_context", ""),
            "path": json.dumps(rule.get("path", []), ensure_ascii=False),
            "category": rule.get("category", ""),
            "logic_rules": json.dumps(rule.get("logic_rules", {}), ensure_ascii=False),
            "required_fields": json.dumps(rule.get("logic_rules", {}).get("required_fields", []), ensure_ascii=False),
            "embedding": self._vector_literal(embed_text(embedding_text)),
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(vector_sql, vector_payload)
            conn.commit()

    def delete_new_pure_rule(self, rule_id: str) -> int:
        full_sql = f"DELETE FROM {NEW_RULE_TABLE} WHERE id = %(rule_id)s"
        vector_sql = f"DELETE FROM {NEW_RULE_VECTOR_TABLE} WHERE rule_id = %(rule_id)s"
        deleted = 0
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(vector_sql, {"rule_id": rule_id})
                cur.execute(full_sql, {"rule_id": rule_id})
                deleted = cur.rowcount or 0
            conn.commit()
        return deleted

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
        law_name: str = "",
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

        if law_name:
            filters.append("law_name = %(law_name)s")
            payload["law_name"] = law_name

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
        law_count_sql = f"""
        SELECT COUNT(DISTINCT law_name)
        FROM knowledge_base
        {where_sql}
        """
        latest_updated_sql = f"""
        SELECT MAX(updated_at)
        FROM knowledge_base
        {where_sql}
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, payload)
                total = cur.fetchone()[0]

                cur.execute(list_sql, payload)
                rows = cur.fetchall()

                cur.execute(categories_sql)
                category_rows = cur.fetchall()

                cur.execute(law_count_sql, payload)
                law_count = cur.fetchone()[0] or 0

                cur.execute(latest_updated_sql, payload)
                latest_updated_at = cur.fetchone()[0]

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
            "law_count": law_count,
            "latest_updated_at": latest_updated_at.isoformat() if latest_updated_at else None,
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

    def delete_rules_by_prefix(self, prefix: str) -> int:
        sql = """
        DELETE FROM knowledge_base
        WHERE rule_id LIKE %(prefix)s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"prefix": f"{prefix}%"})
                deleted = cur.rowcount or 0
            conn.commit()
        return deleted

    def count_rules_by_law_names(self, law_names: List[str]) -> Dict[str, int]:
        names = [name for name in law_names if name]
        if not names:
            return {}

        sql = """
        SELECT law_name, COUNT(*)
        FROM knowledge_base
        WHERE law_name = ANY(%(law_names)s)
        GROUP BY law_name
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"law_names": names})
                rows = cur.fetchall()

        return {row[0]: int(row[1]) for row in rows}

    def delete_rule(self, rule_id: str) -> int:
        sql = """
        DELETE FROM knowledge_base
        WHERE rule_id = %(rule_id)s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"rule_id": rule_id})
                deleted = cur.rowcount or 0
            conn.commit()
        return deleted

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
