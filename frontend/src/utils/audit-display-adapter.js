const TOP_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充',
  manual_review: '存在风险',
  non_compliant: '存在风险'
}

const SUB_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充',
  manual_review: '存在风险',
  non_compliant: '存在风险'
}

const SUB_DEFAULT_BRIEF = {
  scope_audit: '当前场景的使用范围需进一步确认',
  process_audit: '流程材料暂不完整，建议补充后复核',
  document_completeness_audit: '资料链暂不完整，建议补充关键材料',
  timeline_audit: '时序信息暂不完整，建议补充关键时间节点',
  amount_audit: '金额信息暂不完整，建议补充预算与审批依据',
  emergency_audit: '应急信息暂不完整，建议补充应急证明材料'
}

const REASON_CODE_BRIEF = {
  MISSING_VOTE: '缺少业主表决相关材料',
  MISSING_CONTRACT: '缺少施工合同相关材料',
  MISSING_INVOICE: '缺少发票相关材料',
  MISSING_ANNOUNCEMENT: '缺少公示相关材料',
  MISSING_BUDGET_REVIEW: '缺少审价相关材料',
  MISSING_PAYMENT_PROOF: '缺少付款凭证相关材料',
  MISSING_SETTLEMENT_REPORT: '缺少结算相关材料',
  MISSING_COMPLETION_REPORT: '缺少完工或验收相关材料'
}

const PHRASE_REPLACEMENTS = [
  ['正向维修对象', '属于维修对象目录范围'],
  ['需继续走完整审计链', '建议补充关键材料后继续审核'],
  ['目录语义显示项目属于共用设施设备维修范围', '属于维修对象目录范围（共用设施）'],
  ['目录语义显示项目属于共用部位维修范围', '属于维修对象目录范围（共用部位）']
]

function dedupeStrings(values) {
  const seen = new Set()
  const output = []
  for (const value of values || []) {
    const text = String(value || '').trim()
    if (!text || seen.has(text)) continue
    seen.add(text)
    output.push(text)
  }
  return output
}

function isFormalBasisSourceType(sourceType) {
  const normalized = String(sourceType || '').toLowerCase()
  return (
    normalized.includes('regulation') ||
    normalized.includes('law') ||
    normalized.includes('standard') ||
    normalized.includes('statute')
  )
}

export function toCustomerReason(text) {
  let normalized = String(text || '').trim()
  if (!normalized) return ''
  for (const [from, to] of PHRASE_REPLACEMENTS) {
    normalized = normalized.replaceAll(from, to)
  }
  return normalized
}

export function getTopStatusLabel(overallResult, displayResult) {
  return TOP_STATUS_LABELS[overallResult] || displayResult || '需补充'
}

export function getTopReasons(result) {
  const reasons = dedupeStrings((result?.reasons || []).map((item) => toCustomerReason(item)))
  if (reasons.length) return reasons.slice(0, 2)
  return ['暂无明确原因说明']
}

export function getTopGapText(summaryConclusion = {}) {
  const categories = Array.isArray(summaryConclusion.gap_categories) ? summaryConclusion.gap_categories : []
  return categories.length ? categories.join(' / ') : '暂无明显缺口'
}

export function getBasisList(basisDocuments) {
  const values = (basisDocuments || [])
    .filter((item) => isFormalBasisSourceType(item?.source_type))
    .map((item) => item?.display_name || item?.title)
    .filter(Boolean)
  const deduped = dedupeStrings(values)
  return deduped.length ? deduped : ['系统审计规则（基于工程审计经验）']
}

export function isHighFreqDirectReject(auditPath) {
  const list = Array.isArray(auditPath) ? auditPath.map((item) => String(item || '').toLowerCase()) : []
  return list.includes('direct_reject')
}

function getSubTone(item) {
  if (!item || item.applicable === false) return 'na'
  if (item.result === 'compliant') return 'success'
  if (item.result === 'need_supplement') return 'warning'
  return 'risk'
}

function getSubStatus(item) {
  if (!item || item.applicable === false) return '不适用'
  return SUB_STATUS_LABELS[item.result] || item.display_result || '需补充'
}

function getSubBrief(key, item) {
  if (!item || item.applicable === false) {
    return '当前场景暂不适用'
  }

  if (key === 'scope_audit' && item.result === 'compliant') {
    return '属于维修对象目录范围（初步判断）'
  }

  const codes = Array.isArray(item.reason_codes) ? item.reason_codes : []
  for (const code of codes) {
    if (REASON_CODE_BRIEF[code]) return REASON_CODE_BRIEF[code]
  }

  const firstReason = toCustomerReason((item.reasons || [])[0] || '')
  if (firstReason) return firstReason

  return SUB_DEFAULT_BRIEF[key] || '建议补充相关信息后复核'
}

export function buildSubAuditView(key, title, item) {
  return {
    key,
    title,
    tone: getSubTone(item),
    status: getSubStatus(item),
    brief: getSubBrief(key, item),
    basis: getBasisList(item?.basis_documents || [])
  }
}
