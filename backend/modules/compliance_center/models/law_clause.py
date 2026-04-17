from tortoise import fields

from modules.system.models.common import Table


class LawClauseModel(Table):
    law_name = fields.CharField(max_length=255, description="法规名称")
    clause_label = fields.CharField(max_length=100, description="条款编号")
    full_title = fields.TextField(description="完整标题", null=True)
    content = fields.TextField(description="条款内容")

    class Meta:
        table = "law_clauses"
        table_description = "法规条款表"
        indexes = ("status", "law_name", "clause_label")
