const TOP_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充材料',
  manual_review: '需复核',
  non_compliant: '不符合'
}

const SUB_STATUS_LABELS = {
  compliant: '通过',
  need_supplement: '需补充材料',
  manual_review: '需复核',
  non_compliant: '不符合',
  info_only: '仅展示'
}

const SUB_DEFAULT_BRIEF = {
  entity_audit: '项目使用范围需结合共用部位、专有部分和物业服务范围进行最终判断。',
  trace_audit: '当前资料/手续痕迹字段齐备，初步满足本轮展示要求。',
  process_audit: '当前流程字段初步满足本轮展示要求。',
  amount_info: '金额与造价信息仅用于展示，不影响审计结论'
}

const REASON_CODE_BRIEF = {
  ENTITY_PUBLIC_REPAIR_OBJECT: '项目属于共用部位或共用设施设备维修对象，符合专项维修资金使用范围。',
  ENTITY_PRIVATE_PART_NOT_ELIGIBLE: '项目属于业主专有部分，不属于专项维修资金使用范围。',
  ENTITY_PROPERTY_SERVICE_SCOPE: '项目属于物业日常服务或维保范围，不属于专项维修资金使用范围。',
  ENTITY_IN_WARRANTY: '保修状态展示提示',
  ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW: '项目维修对象或使用范围无法确认，需要补充材料后人工复核。',
  ENTITY_FIELD_CONFLICT_MANUAL_REVIEW: '项目目录语义与来源字段存在冲突，需要人工复核使用范围。',
  TRACE_MISSING_VOTE_TRACE: '当前资料/手续痕迹不完整，需补充业主表决材料后再核验。',
  TRACE_MISSING_CONSTRUCTION_CONTRACT: '当前资料/手续痕迹不完整，需补充施工合同材料后再核验。',
  TRACE_MISSING_APPRAISAL_CONTRACT: '当前资料/手续痕迹不完整，需补充审价合同材料后再核验。',
  TRACE_MISSING_APPRAISAL_REPORT: '当前资料/手续痕迹不完整，需补充审价报告材料后再核验。',
  TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED: '当前资料/手续痕迹不完整，需补充施工合同签署材料后再核验。',
  PROCESS_NORMAL_VOTE_MISSING: '当前普通维修项目缺少表决流程信息，流程合规性需补充材料后判断。',
  PROCESS_NORMAL_VOTE_NOT_LEGAL: '当前普通维修项目表决结果未达到展示口径或无法确认，流程合规性需复核。',
  PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW: '当前普通维修流程时序需要复核，需补充表决与开工时间材料。',
  PROCESS_VOTE_DATE_MISSING: '当前普通维修项目缺少表决日期，无法完成流程时序校验。',
  PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED: '当前普通维修项目存在先开工后表决的时序风险，流程合规性需复核。',
  PROCESS_VOTE_DATE_PROXY_USED: '当前表决日期使用代用日期，流程时序判断仅作为弱校验展示。',
  PROCESS_EMERGENCY_FLOW_EXEMPTED: '当前项目按紧急维修程序审查，普通表决流程可豁免；流程判断以事后资料痕迹为主。',
  PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED: '当前项目按紧急维修程序处理，普通表决流程可豁免；但事后资料痕迹不足，流程仍需补充。',
  PROCESS_PROPERTY_VALUE_UNSUPPORTED: '当前工程性质字段超出支持范围，普通维修或紧急维修路径需人工复核。',
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

export function toCustomerReason(text) {
  return String(text || '').trim()
}

export function getTopStatusLabel(overallResult, displayResult) {
  return TOP_STATUS_LABELS[overallResult] || displayResult || '需补充材料'
}

export function getTopReasons(result) {
  const values = result?.top_reasons?.length ? result.top_reasons : result?.reasons
  const reasons = dedupeStrings((values || []).map((item) => toCustomerReason(item)))
  if (reasons.length) return reasons.slice(0, 3)
  return ['暂无明确原因说明']
}

export function getBasisList(basisDocuments) {
  const documents = basisDocuments || []
  return dedupeStrings(documents.map((item) => item?.display_name || item?.title).filter(Boolean))
}

export function getTopBasisView(basisDocuments) {
  return {
    documents: getBasisList(basisDocuments || [])
  }
}

export function getSubBasisPairs(basisDocuments) {
  const documents = basisDocuments || []
  const seen = new Set()
  const pairs = []
  for (const item of documents) {
    const lawText = String(item?.display_name || item?.title || '').trim()
    if (!lawText) continue
    const basisExplanation = String(item?.basis_explanation || '当前依据用于本分项判断展示。').trim()
    const key = `${lawText}__${basisExplanation}`
    if (seen.has(key)) continue
    seen.add(key)
    pairs.push({ lawText, basisExplanation })
  }
  return pairs
}

export function getBasisView(basisDocuments) {
  return {
    documents: getBasisList(basisDocuments || []),
    pairs: getSubBasisPairs(basisDocuments || [])
  }
}

function getSubTone(item) {
  if (!item || item.applicable === false) return 'na'
  if (item.result === 'compliant') return 'success'
  if (item.result === 'info_only') return 'info'
  if (item.result === 'need_supplement') return 'warning'
  if (item.result === 'manual_review') return 'review'
  if (item.result === 'non_compliant') return 'error'
  return 'review'
}

function getSubStatus(item) {
  if (!item || item.applicable === false) return '不适用'
  return SUB_STATUS_LABELS[item.result] || item.display_result || '需补充材料'
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
  const basisView =
    key === 'amount_info'
      ? { documents: ['金额层仅展示，不绑定法规依据'], pairs: [] }
      : getBasisView(item?.basis_documents || [])
  return {
    key,
    title,
    tone: getSubTone(item),
    status: getSubStatus(item),
    brief: getSubBrief(key, item),
    basis: basisView.documents,
    basisPairs: basisView.pairs
  }
}
