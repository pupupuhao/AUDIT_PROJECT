const TOP_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充',
  manual_review: '需复核',
  non_compliant: '不符合'
}

const SUB_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充',
  manual_review: '需复核',
  non_compliant: '不符合',
  info_only: '仅展示'
}

const SUB_DEFAULT_BRIEF = {
  entity_audit: '项目本体合规范围需进一步确认',
  trace_audit: '资料/手续痕迹暂不完整，建议补充后复核',
  process_audit: '流程合规信息暂不完整，建议补充后复核',
  amount_info: '金额与造价信息仅用于展示，不影响审计结论'
}

const REASON_CODE_BRIEF = {
  ENTITY_PUBLIC_REPAIR_OBJECT: '属于共用部位或共用设施设备维修对象',
  ENTITY_PRIVATE_PART_NOT_ELIGIBLE: '属于业主专有部分',
  ENTITY_PROPERTY_SERVICE_SCOPE: '属于物业日常服务或维保范围',
  ENTITY_IN_WARRANTY: '保修状态需要人工确认',
  ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW: '维修对象或范围无法确认',
  ENTITY_FIELD_CONFLICT_MANUAL_REVIEW: '字段与目录语义存在冲突',
  TRACE_MISSING_VOTE_TRACE: '缺少业主表决痕迹',
  TRACE_MISSING_CONSTRUCTION_CONTRACT: '缺少施工合同痕迹',
  TRACE_MISSING_APPRAISAL_CONTRACT: '缺少审价合同痕迹',
  TRACE_MISSING_APPRAISAL_REPORT: '缺少审价报告痕迹',
  TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED: '需要施工合同但未见签署痕迹',
  PROCESS_NORMAL_VOTE_MISSING: '普通维修缺少表决流程信息',
  PROCESS_NORMAL_VOTE_NOT_LEGAL: '普通维修表决合法性需复核',
  PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW: '普通维修流程时序需复核',
  PROCESS_EMERGENCY_FLOW_EXEMPTED: '紧急维修豁免普通流程',
  PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED: '紧急维修仍需补充事后资料',
  AMOUNT_BUDGET_DISPLAY: '预算金额展示',
  AMOUNT_CONTRACT_DISPLAY: '合同金额展示',
  AMOUNT_INFO_MISSING: '金额信息缺失'
}

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
  return String(text || '').trim()
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
  return deduped.length ? deduped : ['系统审计规则（基于四层审计结构）']
}

function getSubTone(item) {
  if (!item || item.applicable === false) return 'na'
  if (item.result === 'compliant') return 'success'
  if (item.result === 'info_only') return 'info'
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
