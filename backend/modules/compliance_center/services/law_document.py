from modules.compliance_center.models.law_clause import LawClauseModel
from modules.compliance_center.services.rule_service import count_rules_by_law_names


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

        rule_counter = count_rules_by_law_names([doc["title"] for doc in grouped_docs])
        for doc in grouped_docs:
            doc["section_count"] = len(doc["sections"])
            doc["rule_count"] = rule_counter.get(doc["title"], 0)

        return grouped_docs


service = LawDocumentService()
