import json
import re
from typing import Any, Dict, List

from app.core.llm_client import call_llm
from app.models.request_model import AuditRequest
from app.models.rule_model import JudgeResult, RetrievalResult
from app.services.retrieval_service import search_rules


NEGATIVE_PATTERNS = [
    ("室内装修", "维修资金不得用于业主室内装修"),
    ("个人", "个人专有部分通常不属于维修资金共用维修范围"),
    ("开发商", "应由开发建设单位承担的责任，不应动用维修资金"),
    ("人为损坏", "人为损坏导致的维修费用应由责任人承担"),
]

PROCESS_DOC_KEYWORDS = ["审批", "同意", "签字", "表决", "业主大会", "业主小组", "申请", "报价", "合同"]


def _request_text(req: AuditRequest) -> str:
    parts = [
        req.application_text,
        req.project_name or "",
        req.applicant or "",
        req.use_case or "",
        " ".join(req.docs),
    ]
    if req.amount is not None:
        parts.append(f"申请金额 {req.amount}")
    return " ".join(part for part in parts if part)


def _serialize_rule(result: RetrievalResult) -> Dict[str, Any]:
    rule = result.rule
    return {
        "id": rule.id,
        "law_name": rule.law_name,
        "clause_label": rule.clause_label,
        "full_title": rule.full_title,
        "content": rule.content,
        "keywords": rule.keywords,
        "category": rule.category,
        "logic_rules": rule.logic_rules.model_dump(),
        "score": result.score,
        "match_reasons": result.match_reasons,
    }


def _extract_basis(results: List[RetrievalResult]) -> List[str]:
    basis = []
    for item in results:
        label = item.rule.clause_label or item.rule.sub_clause or item.rule.id
        if label not in basis:
            basis.append(label)
    return basis[:5]


def _heuristic_judge(req: AuditRequest, results: List[RetrievalResult]) -> JudgeResult:
    request_text = _request_text(req)
    reasons: List[str] = []
    negative_reasons: List[str] = []

    for keyword, reason in NEGATIVE_PATTERNS:
        if keyword in request_text:
            negative_reasons.append(reason)

    doc_text = " ".join(req.docs)
    missing_process_docs = []
    if results:
        needs_approval = any(
            any(token in " ".join(item.rule.logic_rules.condition) or token in " ".join(item.rule.keywords) for token in ["审批", "同意", "业主大会", "业主小组"])
            for item in results
        )
        if needs_approval and not any(token in doc_text or token in request_text for token in PROCESS_DOC_KEYWORDS):
            missing_process_docs.append("审批/同意类材料未体现")

    high_risk_rules = []
    for item in results:
        forbidden = item.rule.logic_rules.forbidden
        if any(term and term in request_text for term in forbidden):
            high_risk_rules.append(item)
            negative_reasons.append(f"{item.rule.clause_label} 命中禁止事项: {', '.join(forbidden[:3])}")

    if negative_reasons:
        reasons.extend(negative_reasons)
    if missing_process_docs:
        reasons.extend(missing_process_docs)

    compliant = not reasons
    if compliant and results:
        reasons.append("申请描述与召回规则整体一致，未发现明显禁止事项")
    elif compliant:
        reasons.append("未召回到足够规则，当前仅能给出低置信度初判")

    risk_level = "low" if compliant else "high" if high_risk_rules else "medium"
    return JudgeResult(
        合规=compliant,
        原因="；".join(reasons),
        依据=_extract_basis(results),
        命中规则=results,
        风险等级=risk_level,
        结构化摘要={
            "amount": req.amount,
            "docs": req.docs,
            "matched_rule_count": len(results),
            "negative_hits": negative_reasons,
            "missing_docs": missing_process_docs,
        },
    )


def _build_judge_prompt(req: AuditRequest, results: List[RetrievalResult]) -> str:
    rules = [_serialize_rule(item) for item in results]
    return f"""
你是维修资金合规审核助手。请结合申请文本和召回规则，输出严格 JSON。

审核要求：
1. 判断申请是否合规。
2. 给出简短、可解释的原因。
3. 只引用召回规则中的条款作为依据。
4. 若材料不足，也要在原因中说明。

输出字段：
{{
  "合规": true,
  "原因": "一句到两句中文解释",
  "依据": ["第十三条", "第十四条"],
  "风险等级": "low|medium|high"
}}

申请信息：
{json.dumps(req.model_dump(), ensure_ascii=False)}

召回规则：
{json.dumps(rules, ensure_ascii=False)}
"""


def _parse_llm_result(raw: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def judge_application(req: AuditRequest, use_llm: bool = True) -> JudgeResult:
    results = search_rules(_request_text(req), top_k=req.top_k)
    heuristic = _heuristic_judge(req, results)

    if not use_llm or not results:
        return heuristic

    raw = call_llm(_build_judge_prompt(req, results))
    parsed = _parse_llm_result(raw)
    if not parsed:
        return heuristic

    return JudgeResult(
        合规=bool(parsed.get("合规", heuristic.compliant)),
        原因=parsed.get("原因", heuristic.reason),
        依据=parsed.get("依据", heuristic.basis),
        命中规则=results,
        风险等级=parsed.get("风险等级", heuristic.risk_level),
        结构化摘要=heuristic.summary,
    )
