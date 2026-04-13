from modules.audit.models.law_clause import LawClauseModel
from modules.audit.services.rule_service import load_rules


class LawDocumentService:
    async def list_documents(self, offset: int = 1, limit: int = 20, keyword: str = ""):
        query = LawClauseModel.filter(status__not=9)
        if keyword:
            query = query.filter(law_name__contains=keyword)

        clauses = await query.order_by("law_name", "id").all()
        grouped_docs = self._group_documents(clauses)

        start = max(offset - 1, 0) * limit
        end = start + limit
        return {
            "total": len(grouped_docs),
            "items": grouped_docs[start:end],
        }

    async def get_document(self, law_name: str):
        clauses = await LawClauseModel.filter(
            status__not=9,
            law_name=law_name,
        ).order_by("id").all()

        if not clauses:
            return None

        documents = self._group_documents(clauses)
        return documents[0] if documents else None

    def _group_documents(self, clauses):
        grouped_docs: list[dict] = []
        current_doc: dict | None = None
        rule_counter = self._build_rule_counter()

        for clause in clauses:
            if current_doc is None or current_doc["title"] != clause.law_name:
                current_doc = {
                    "id": f"LAW_{len(grouped_docs) + 1:03d}",
                    "title": clause.law_name,
                    "sections": [],
                    "section_count": 0,
                    "rule_count": 0,
                }
                grouped_docs.append(current_doc)

            current_doc["sections"].append(
                {
                    "title": clause.full_title or clause.clause_label,
                    "content": clause.content,
                }
            )

        for doc in grouped_docs:
            doc["section_count"] = len(doc["sections"])
            doc["rule_count"] = rule_counter.get(doc["title"], 0)

        return grouped_docs

    @staticmethod
    def _build_rule_counter() -> dict[str, int]:
        rule_counter: dict[str, int] = {}
        for rule in load_rules():
            rule_counter[rule.law_name] = rule_counter.get(rule.law_name, 0) + 1
        return rule_counter


service = LawDocumentService()
