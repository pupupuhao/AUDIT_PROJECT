<script setup>
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import {
  analyzeSingleAuditFile,
  judgeAuditEngine,
  judgeAuditFiles,
  parseAuditFiles
} from '@/service/audit-engine'
import {
  buildSubAuditView,
  getTopBasisView,
  getTopReasons,
  getTopStatusLabel
} from '@/utils/audit-display-adapter'

const loading = ref(false)
const result = ref(null)
const summaryBasisExpanded = ref(false)
const expandedSubBasisKeys = ref([])
const uploadFileList = ref([])
const fileLoading = ref(false)
const parseResult = ref(null)
const fileJudgeResult = ref(null)
const singleAnalysisResult = ref(null)

const form = reactive({
  project_name: '',
  property: undefined,
  expirer_remark: '',
  is_signed_pc: undefined,
  is_signed_esc: undefined,
  is_signed_esr: undefined,
  need_con: undefined,
  has_hou_notion_sum: undefined,
  count_hou: undefined,
  agree_hou: undefined,
  sum_area: undefined,
  agree_area: undefined,
  request_startdate: '',
  request_enddate: '',
  reg_date: '',
  startup_date: '',
  orgn_amt: undefined,
  contract_amt: undefined
})

const boolSelectOptions = [
  { label: '未填写', value: undefined },
  { label: '是', value: true },
  { label: '否', value: false }
]

const propertySelectOptions = [
  { label: '未填写', value: undefined },
  { label: '一般维修（1）', value: 1 },
  { label: '急修（2）', value: 2 }
]

const optionalFieldGroups = [
  {
    title: '工程主表 / 预案',
    fields: [
      { key: 'property', label: '工程性质 property', type: 'property' },
      { key: 'expirer_remark', label: '保修备注', type: 'text' }
    ]
  },
  {
    title: '业务痕迹',
    fields: [
      { key: 'is_signed_pc', label: '施工合同已签' },
      { key: 'is_signed_esc', label: '审价合同已签' },
      { key: 'is_signed_esr', label: '审价报告已有' },
      { key: 'need_con', label: '需要施工合同' }
    ]
  },
  {
    title: '表决汇总',
    fields: [
      { key: 'has_hou_notion_sum', label: '存在表决汇总' },
      { key: 'count_hou', label: '总户数', type: 'number' },
      { key: 'agree_hou', label: '同意户数', type: 'number' },
      { key: 'sum_area', label: '总面积', type: 'number' },
      { key: 'agree_area', label: '同意面积', type: 'number' },
      { key: 'request_enddate', label: '征询结束日期 YYYYMMDD', type: 'text' },
      { key: 'request_startdate', label: '征询开始日期 YYYYMMDD', type: 'text' },
      { key: 'reg_date', label: '录入日期 YYYYMMDD', type: 'text' }
    ]
  },
  {
    title: '合同与金额',
    fields: [
      { key: 'startup_date', label: '开工日期 YYYYMMDD', type: 'text' },
      { key: 'orgn_amt', label: '预算金额', type: 'number' },
      { key: 'contract_amt', label: '合同金额', type: 'number' }
    ]
  }
]

const demoCases = [
  { label: '普通维修：电梯主机', payload: { project_name: '3号楼电梯主机维修', property: 1, is_signed_pc: true, is_signed_esc: true, is_signed_esr: true, need_con: true, has_hou_notion_sum: true, count_hou: 100, agree_hou: 80, sum_area: 1000, agree_area: 800, request_enddate: '20240301', orgn_amt: 120000, contract_amt: 118000 } },
  { label: '紧急维修：外墙脱落', payload: { project_name: '外墙砖脱落应急维修工程', property: 2, is_signed_pc: true, is_signed_esc: true, is_signed_esr: false, need_con: true, orgn_amt: 568770.27, contract_amt: 435000 } },
  {
    label: '专有部分：室内门锁',
    payload: { project_name: '室内门锁维修', property: 1 }
  },
  { label: '资料缺失：消防维修', payload: { project_name: '消防水泵维修工程', property: 1 } }
]

const subAuditMeta = [
  { key: 'entity_audit', title: '专项维修资金使用范围合规性' },
  { key: 'trace_audit', title: '资料/手续完整性' },
  { key: 'process_audit', title: '流程合规性' },
  { key: 'amount_info', title: '金额与造价信息展示' }
]

const resultTone = computed(() => {
  if (!result.value) return 'processing'
  const key = result.value.overall_result
  if (key === 'non_compliant') return 'error'
  if (key === 'manual_review') return 'warning'
  if (key === 'compliant') return 'success'
  if (key === 'need_supplement') return 'warning'
  return 'processing'
})

const summaryStatus = computed(() => getTopStatusLabel(result.value?.overall_result, result.value?.display_result))
const summaryReasons = computed(() => getTopReasons(result.value))
const summaryBasisView = computed(() =>
  getTopBasisView(result.value?.all_basis_documents || result.value?.basis_documents || [])
)
const summaryBasisVisible = computed(() =>
  summaryBasisExpanded.value ? summaryBasisView.value.documents : summaryBasisView.value.documents.slice(0, 3)
)
const summaryBasisHasMore = computed(() => summaryBasisView.value.documents.length > 3)
const subAuditViews = computed(() =>
  subAuditMeta.map((meta) => buildSubAuditView(meta.key, meta.title, result.value?.sub_audits?.[meta.key]))
)
const parsedFiles = computed(() => parseResult.value?.files || [])
const judgedFiles = computed(() => fileJudgeResult.value?.files || [])
const singleAuditResult = computed(() => singleAnalysisResult.value?.audit_result || null)
const singleReportSummary = computed(() => singleAnalysisResult.value?.report_summary || null)
const singleProblemCards = computed(() => buildProblemCards(singleAuditResult.value))
const singleSubAuditViews = computed(() =>
  subAuditMeta.map((meta) => buildSubAuditView(meta.key, meta.title, singleAuditResult.value?.sub_audits?.[meta.key]))
)
const rawFieldRows = computed(() => objectRows(singleAnalysisResult.value?.raw_fields || {}))
const llmFieldRows = computed(() => objectRows(singleAnalysisResult.value?.llm_result?.fields || {}))
const sanitizedFieldRows = computed(() => objectRows(singleAnalysisResult.value?.sanitized_fields || {}))
const finalFieldRows = computed(() => runtimeFieldRows(singleAnalysisResult.value?.final_fields || {}))
const llmModelsResponseText = computed(() => {
  const value = singleAnalysisResult.value?.llm_result?.models_response
  return value ? JSON.stringify(value, null, 2) : ''
})

function objectRows(value) {
  return Object.entries(value || {}).map(([key, fieldValue]) => ({ key, value: fieldValue }))
}

function runtimeFieldRows(value) {
  return Object.entries(value || {}).map(([key, runtime]) => ({
    key,
    value: runtime && typeof runtime === 'object' && 'value' in runtime ? runtime.value : runtime,
    status: runtime && typeof runtime === 'object' ? runtime.status : ''
  }))
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '未识别'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function getRiskLevel(auditResult) {
  if (!auditResult) return '未审计'
  if (auditResult.overall_result === 'non_compliant') return '高'
  if (auditResult.overall_result === 'manual_review') return '中'
  if (auditResult.overall_result === 'need_supplement') return '中'
  return '低'
}

function buildProblemCards(auditResult) {
  if (!auditResult) return []
  const cards = []
  Object.entries(auditResult.sub_audits || {}).forEach(([subKey, item]) => {
    if (!item || item.result === 'compliant' || item.result === 'info_only') return
    const codes = item.reason_codes?.length ? item.reason_codes : ['NO_REASON_CODE']
    codes.forEach((code, index) => {
      cards.push({
        key: `${subKey}-${code}-${index}`,
        title: code,
        reasonCode: code,
        description: item.reasons?.[index] || item.reasons?.[0] || '规则引擎提示该项需要处理。',
        suggestion: item.missing_items?.length
          ? `请补充或核验：${item.missing_items.join('、')}`
          : '请结合原始材料进行人工复核。',
        basis: item.basis_documents || []
      })
    })
  })
  return cards
}

function buildPayload() {
  const projectName = String(form.project_name || '').trim()
  return {
    project_name: projectName,
    flat_fields: {
      project_name: projectName,
      property: form.property,
      expirer_remark: form.expirer_remark ?? '',
      is_signed_pc: form.is_signed_pc,
      is_signed_esc: form.is_signed_esc,
      is_signed_esr: form.is_signed_esr,
      need_con: form.need_con,
      has_hou_notion_sum: form.has_hou_notion_sum,
      count_hou: form.count_hou,
      agree_hou: form.agree_hou,
      sum_area: form.sum_area,
      agree_area: form.agree_area,
      request_enddate: form.request_enddate || undefined,
      request_startdate: form.request_startdate || undefined,
      reg_date: form.reg_date || undefined,
      startup_date: form.startup_date || undefined,
      orgn_amt: form.orgn_amt,
      contract_amt: form.contract_amt
    }
  }
}

function fillDemoCase(demo) {
  Object.keys(form).forEach((key) => {
    form[key] = key === 'project_name' ? '' : undefined
  })
  Object.entries(demo.payload).forEach(([key, value]) => {
    form[key] = value
  })
}

function resetForm() {
  Object.keys(form).forEach((key) => {
    form[key] = key === 'project_name' ? '' : undefined
  })
  result.value = null
  summaryBasisExpanded.value = false
  expandedSubBasisKeys.value = []
}

async function runAudit() {
  const projectName = String(form.project_name || '').trim()
  if (!projectName) {
    message.warning('请输入项目名称')
    return
  }
  loading.value = true
  try {
    const data = await judgeAuditEngine(buildPayload())
    result.value = data
    summaryBasisExpanded.value = false
    expandedSubBasisKeys.value = []
  } finally {
    loading.value = false
  }
}

function isSubBasisExpanded(key) {
  return expandedSubBasisKeys.value.includes(key)
}

function getVisibleBasisPairs(item) {
  const pairs = item.basisPairs || []
  return isSubBasisExpanded(item.key) ? pairs : pairs.slice(0, 2)
}

function toggleSubBasis(key) {
  if (isSubBasisExpanded(key)) {
    expandedSubBasisKeys.value = expandedSubBasisKeys.value.filter((item) => item !== key)
    return
  }
  expandedSubBasisKeys.value = [...expandedSubBasisKeys.value, key]
}

function beforeFileUpload() {
  return false
}

function handleFileListChange(info) {
  uploadFileList.value = info.fileList || []
  parseResult.value = null
  fileJudgeResult.value = null
  singleAnalysisResult.value = null
}

function getSelectedFiles() {
  return uploadFileList.value
    .map((item) => item.originFileObj || item)
    .filter(Boolean)
}

async function parseFiles() {
  const files = getSelectedFiles()
  if (!files.length) {
    message.warning('请先选择 Excel 文件')
    return
  }
  fileLoading.value = true
  try {
    parseResult.value = await parseAuditFiles(files)
    fileJudgeResult.value = null
  } finally {
    fileLoading.value = false
  }
}

async function analyzeSingleFile() {
  const files = getSelectedFiles()
  if (!files.length) {
    message.warning('请先选择 Excel 文件')
    return
  }
  fileLoading.value = true
  try {
    message.info('正在调用本地 LLM 进行字段归类，可能需要 1-2 分钟，请勿刷新页面。')
    singleAnalysisResult.value = await analyzeSingleAuditFile(files)
    parseResult.value = null
    fileJudgeResult.value = null
  } finally {
    fileLoading.value = false
  }
}

async function judgeFiles(params = {}) {
  const files = getSelectedFiles()
  if (!files.length) {
    message.warning('请先选择 Excel 文件')
    return
  }
  fileLoading.value = true
  try {
    fileJudgeResult.value = await judgeAuditFiles(files, params)
  } finally {
    fileLoading.value = false
  }
}

function getBatchItemStatus(item) {
  if (item.error) return '审计失败'
  return getTopStatusLabel(item.audit_result?.overall_result, item.audit_result?.display_result)
}

function getBatchItemReasons(item) {
  if (item.error) return [item.error]
  return getTopReasons(item.audit_result)
}

function getBatchSubAuditViews(auditResult) {
  return subAuditMeta.map((meta) => buildSubAuditView(meta.key, meta.title, auditResult?.sub_audits?.[meta.key]))
}

function getParseModeLabel(mode) {
  if (mode === 'business_package') return '业务导出包模式'
  if (mode === 'flat_table') return '扁平表模式'
  return '文件解析'
}

function getParsedRowTitle(file, item) {
  const prefix = file.parse_mode === 'business_package'
    ? `项目 ${item.row_index}`
    : `第 ${item.row_index} 行`
  return `${prefix}：${item.project_name || '未识别项目名称'}`
}

function getParsedRowDescription(file, item) {
  if (file.parse_mode === 'business_package') {
    const parts = []
    if (item.project_key) parts.push(`项目主键：${item.project_key}`)
    if ((item.source_sheets || []).length) parts.push(`已聚合表：${item.source_sheets.join('、')}`)
    if ((item.business_summary || []).length) parts.push(item.business_summary.join('；'))
    return parts.join(' ｜ ') || '已按业务主键聚合为项目级审计输入'
  }
  return `未识别列：${(item.unmapped_columns || []).join('、') || '无'}`
}

function getJudgedRowHeader(file, item) {
  const prefix = file.parse_mode === 'business_package'
    ? `项目 ${item.row_index}`
    : `第 ${item.row_index} 行`
  const keyText = item.project_key ? `（${item.project_key}）` : ''
  return `${prefix}${keyText}：${item.project_name || '未识别项目名称'} ｜ ${getBatchItemStatus(item)}`
}
</script>

<template>
  <div class="audit-engine-page">
    <a-card title="合规判定（规则引擎）" :bordered="false">
      <a-space direction="vertical" size="large" style="width: 100%">
        <a-space direction="vertical" size="middle" style="width: 100%">
          <a-input
            v-model:value="form.project_name"
            placeholder="请输入工程描述，例如：3号楼电梯主机维修"
            allow-clear
          />
          <a-space wrap>
            <a-button
              v-for="item in demoCases"
              :key="item.label"
              size="small"
              @click="fillDemoCase(item)"
            >
              {{ item.label }}
            </a-button>
          </a-space>
          <a-collapse ghost>
            <a-collapse-panel key="facts" header="补充判断信息（可选）">
              <a-space direction="vertical" size="middle" style="width: 100%">
                <div v-for="group in optionalFieldGroups" :key="group.title" class="fact-group">
                  <div class="group-title">{{ group.title }}</div>
                  <div class="fact-grid">
                    <div v-for="field in group.fields" :key="field.key" class="fact-item">
                      <div class="fact-label">{{ field.label }}</div>
                      <div class="fact-key">{{ field.key }}</div>
                      <a-input
                        v-if="field.type === 'text'"
                        v-model:value="form[field.key]"
                        style="width: 100%"
                      />
                      <a-select
                        v-else-if="field.type === 'property'"
                        v-model:value="form[field.key]"
                        :options="propertySelectOptions"
                        style="width: 100%"
                      />
                      <a-input-number
                        v-else-if="field.type === 'number'"
                        v-model:value="form[field.key]"
                        style="width: 100%"
                      />
                      <a-select
                        v-else
                        v-model:value="form[field.key]"
                        :options="boolSelectOptions"
                        style="width: 100%"
                      />
                    </div>
                  </div>
                </div>
              </a-space>
            </a-collapse-panel>
          </a-collapse>
          <a-space>
            <a-button type="primary" :loading="loading" @click="runAudit">开始审计</a-button>
            <a-button :disabled="loading" @click="resetForm">重新开始</a-button>
          </a-space>
        </a-space>

        <a-card title="Excel/文件上传审计" size="small" :bordered="true">
          <a-space direction="vertical" size="middle" style="width: 100%">
            <a-alert
              type="info"
              show-icon
              message="当前版本正式支持 .xlsx；PDF/OCR 等文件会保留入口并返回暂不支持提示。"
            />
            <a-upload
              v-model:file-list="uploadFileList"
              multiple
              accept=".xlsx,.xls,.pdf,.doc,.docx,.png,.jpg,.jpeg"
              :before-upload="beforeFileUpload"
              @change="handleFileListChange"
            >
              <a-button>选择文件</a-button>
            </a-upload>
            <a-space wrap>
              <a-button
                type="primary"
                :loading="fileLoading"
                :disabled="!uploadFileList.length"
                @click="analyzeSingleFile"
              >
                单项目分析
              </a-button>
              <a-button :loading="fileLoading" :disabled="!uploadFileList.length" @click="parseFiles">
                解析预览
              </a-button>
              <a-button
                :loading="fileLoading"
                :disabled="!uploadFileList.length"
                @click="judgeFiles()"
              >
                旧版批量审计
              </a-button>
            </a-space>

            <template v-if="singleAnalysisResult">
              <a-alert
                v-if="singleAnalysisResult.status !== 'analyzed'"
                type="warning"
                show-icon
                :message="singleAnalysisResult.message || '当前文件未进入单项目审计闭环'"
              />
              <template v-else>
                <div class="single-flow">
                  <a-card size="small" title="1. AI提取信息：原始抽取与辅助归类">
                    <a-space direction="vertical" size="middle" style="width: 100%">
                      <a-alert
                        type="info"
                        show-icon
                        message="AI归类仅作为标准字段候选，不代表最终审计事实；最终结论由规则引擎输出。"
                      />
                      <a-descriptions size="small" bordered :column="1">
                        <a-descriptions-item label="上传文件">{{ singleAnalysisResult.filename }}</a-descriptions-item>
                        <a-descriptions-item label="项目名称">{{ singleAnalysisResult.project_name }}</a-descriptions-item>
                        <a-descriptions-item label="项目主键">{{ singleAnalysisResult.project_key || '无' }}</a-descriptions-item>
                        <a-descriptions-item label="LLM 状态">
                          {{ singleAnalysisResult.llm_result?.available ? '已调用本地 LLM' : '本地 LLM 不可用，已降级' }}
                        </a-descriptions-item>
                        <a-descriptions-item label="LLM 模型">
                          {{ singleAnalysisResult.llm_result?.model || '未返回' }}
                        </a-descriptions-item>
                        <a-descriptions-item
                          v-if="!singleAnalysisResult.llm_result?.available"
                          label="LLM 错误类型"
                        >
                          {{ singleAnalysisResult.llm_result?.error_type || 'unknown' }}
                        </a-descriptions-item>
                        <a-descriptions-item
                          v-if="singleAnalysisResult.llm_result?.error_message"
                          label="LLM 错误详情"
                        >
                          {{ singleAnalysisResult.llm_result.error_message }}
                        </a-descriptions-item>
                      </a-descriptions>
                      <a-collapse v-if="llmModelsResponseText" ghost>
                        <a-collapse-panel key="models" header="LM Studio /v1/models 诊断返回">
                          <pre class="debug-json">{{ llmModelsResponseText }}</pre>
                        </a-collapse-panel>
                      </a-collapse>
                      <div class="field-columns">
                        <a-card size="small" title="原始抽取 raw_fields">
                          <a-table
                            size="small"
                            :pagination="false"
                            :data-source="rawFieldRows"
                            :columns="[
                              { title: '字段', dataIndex: 'key' },
                              { title: '值', dataIndex: 'value' }
                            ]"
                          >
                            <template #bodyCell="{ column, record }">
                              <template v-if="column.dataIndex === 'value'">{{ formatValue(record.value) }}</template>
                            </template>
                          </a-table>
                        </a-card>
                        <a-card size="small" title="AI归类 llm_fields">
                          <a-table
                            size="small"
                            :pagination="false"
                            :data-source="llmFieldRows"
                            :columns="[
                              { title: '字段', dataIndex: 'key' },
                              { title: '值', dataIndex: 'value' }
                            ]"
                          >
                            <template #bodyCell="{ column, record }">
                              <template v-if="column.dataIndex === 'value'">{{ formatValue(record.value) }}</template>
                            </template>
                          </a-table>
                        </a-card>
                      </div>
                      <a-card size="small" title="sanitized_fields（清洗后的 LLM 字段）">
                        <a-table
                          size="small"
                          :pagination="false"
                          :data-source="sanitizedFieldRows"
                          :columns="[
                            { title: '字段', dataIndex: 'key' },
                            { title: '值', dataIndex: 'value' }
                          ]"
                        >
                          <template #bodyCell="{ column, record }">
                            <template v-if="column.dataIndex === 'value'">{{ formatValue(record.value) }}</template>
                          </template>
                        </a-table>
                      </a-card>
                      <a-card size="small" title="final_fields（合并后进入规则引擎的字段）">
                        <a-table
                          size="small"
                          :pagination="false"
                          :data-source="finalFieldRows"
                          :columns="[
                            { title: '字段', dataIndex: 'key' },
                            { title: '最终值', dataIndex: 'value' },
                            { title: '状态', dataIndex: 'status' }
                          ]"
                        >
                          <template #bodyCell="{ column, record }">
                            <template v-if="column.dataIndex === 'value'">{{ formatValue(record.value) }}</template>
                          </template>
                        </a-table>
                      </a-card>
                      <a-alert
                        v-if="(singleAnalysisResult.llm_result?.uncertainties || []).length"
                        type="warning"
                        show-icon
                        :message="singleAnalysisResult.llm_result.uncertainties.join('；')"
                      />
                      <a-alert
                        v-if="(singleAnalysisResult.field_conflicts || []).length"
                        type="warning"
                        show-icon
                        message="存在字段冲突，已保留 parser / 规则字段为 final_value，建议人工复核。"
                      />
                    </a-space>
                  </a-card>

                  <a-card size="small" title="2. 审计过程：规则引擎分项结果">
                    <a-space direction="vertical" size="middle" style="width: 100%">
                      <a-card
                        v-for="item in singleSubAuditViews"
                        :key="`single-${item.key}`"
                        size="small"
                        :title="item.title"
                        class="sub-audit-card"
                        :class="`sub-audit-card--${item.tone}`"
                      >
                        <a-descriptions size="small" :column="1">
                          <a-descriptions-item label="分项结论">{{ item.status }}</a-descriptions-item>
                          <a-descriptions-item label="规则说明">{{ item.brief }}</a-descriptions-item>
                          <a-descriptions-item label="命中依据">{{ item.basis.join('；') || '无' }}</a-descriptions-item>
                        </a-descriptions>
                      </a-card>
                    </a-space>
                  </a-card>

                  <a-card size="small" title="3. 审计结果：审计人员视图">
                    <a-space direction="vertical" size="middle" style="width: 100%">
                      <div class="overview-grid">
                        <a-statistic title="总体结论" :value="getTopStatusLabel(singleAuditResult?.overall_result, singleAuditResult?.display_result)" />
                        <a-statistic title="风险等级" :value="getRiskLevel(singleAuditResult)" />
                        <a-statistic title="问题数量" :value="singleProblemCards.length" />
                        <a-statistic title="人工复核" :value="singleAuditResult?.manual_review_required || (singleAnalysisResult.field_conflicts || []).length ? '建议' : '暂不需要'" />
                      </div>
                      <a-card size="small" class="report-summary-card" :title="singleReportSummary?.title || '审计报告摘要'">
                        {{ singleReportSummary?.summary || singleAuditResult?.display_summary }}
                      </a-card>
                      <a-empty v-if="!singleProblemCards.length" description="未识别到需补正的问题卡片" />
                      <a-card
                        v-for="card in singleProblemCards"
                        v-else
                        :key="card.key"
                        size="small"
                        class="problem-card"
                        :title="card.title"
                      >
                        <a-descriptions size="small" :column="1">
                          <a-descriptions-item label="问题说明">{{ card.description }}</a-descriptions-item>
                          <a-descriptions-item label="reason_code">{{ card.reasonCode }}</a-descriptions-item>
                          <a-descriptions-item label="补正建议">{{ card.suggestion }}</a-descriptions-item>
                          <a-descriptions-item label="相关法规依据">
                            <a-collapse ghost>
                              <a-collapse-panel key="basis" header="展开依据">
                                <a-space direction="vertical" size="small">
                                  <span v-for="basis in card.basis" :key="basis.display_text || basis.display_name">
                                    {{ basis.display_text || basis.display_name || basis.title }}
                                  </span>
                                </a-space>
                              </a-collapse-panel>
                            </a-collapse>
                          </a-descriptions-item>
                        </a-descriptions>
                      </a-card>
                    </a-space>
                  </a-card>
                </div>
              </template>
            </template>

            <template v-if="parsedFiles.length">
              <div class="group-title">解析预览</div>
              <a-collapse>
                <a-collapse-panel
                  v-for="(file, fileIndex) in parsedFiles"
                  :key="`${file.filename}-${fileIndex}`"
                  :header="`${file.filename || '未命名文件'}：${file.status} ｜ ${getParseModeLabel(file.parse_mode)}`"
                >
                  <a-space direction="vertical" size="small" style="width: 100%">
                    <a-alert
                      v-if="(file.business_summary || []).length"
                      type="success"
                      show-icon
                      :message="(file.business_summary || []).join('；')"
                    />
                    <a-alert
                      v-if="file.status !== 'parsed'"
                      type="warning"
                      show-icon
                      :message="file.message || (file.warnings || []).join('；') || '文件暂不支持解析'"
                    />
                    <a-alert
                      v-if="(file.warnings || []).length && file.status === 'parsed'"
                      type="warning"
                      show-icon
                      :message="(file.warnings || []).join('；')"
                    />
                    <a-list
                      v-if="(file.rows || []).length"
                      size="small"
                      bordered
                      :data-source="file.rows"
                    >
                      <template #renderItem="{ item }">
                        <a-list-item>
                          <a-list-item-meta
                            :title="getParsedRowTitle(file, item)"
                            :description="getParsedRowDescription(file, item)"
                          />
                          <a-button
                            size="small"
                            :loading="fileLoading"
                            @click="judgeFiles({ file_index: fileIndex, row_index: item.row_index })"
                          >
                            审计本行
                          </a-button>
                        </a-list-item>
                      </template>
                    </a-list>
                    <a-empty v-else description="未解析到有效数据行" />
                  </a-space>
                </a-collapse-panel>
              </a-collapse>
            </template>

            <template v-if="judgedFiles.length">
              <div class="group-title">审计结果</div>
              <a-collapse>
                <a-collapse-panel
                  v-for="(file, fileIndex) in judgedFiles"
                  :key="`judged-${file.filename}-${fileIndex}`"
                  :header="`${file.filename || '未命名文件'}：${file.status} ｜ ${getParseModeLabel(file.parse_mode)}`"
                >
                  <a-space direction="vertical" size="small" style="width: 100%">
                    <a-alert
                      v-if="file.status !== 'judged'"
                      type="warning"
                      show-icon
                      :message="file.message || (file.warnings || []).join('；') || '文件未完成审计'"
                    />
                    <a-collapse v-if="(file.items || []).length">
                      <a-collapse-panel
                        v-for="item in file.items"
                        :key="`row-${fileIndex}-${item.row_index}`"
                        :header="getJudgedRowHeader(file, item)"
                      >
                        <a-space direction="vertical" size="middle" style="width: 100%">
                          <a-alert
                            v-if="item.error"
                            type="error"
                            show-icon
                            :message="item.error"
                          />
                          <template v-else>
                            <a-descriptions size="small" bordered :column="1">
                              <a-descriptions-item label="项目名称">
                                {{ item.audit_result.project_name }}
                              </a-descriptions-item>
                              <a-descriptions-item v-if="item.project_key" label="项目主键">
                                {{ item.project_key }}
                              </a-descriptions-item>
                              <a-descriptions-item v-if="(item.source_sheets || []).length" label="已聚合表">
                                {{ item.source_sheets.join('、') }}
                              </a-descriptions-item>
                              <a-descriptions-item label="主结论">
                                {{ getBatchItemStatus(item) }}
                              </a-descriptions-item>
                              <a-descriptions-item label="原因说明">
                                <a-space direction="vertical" size="small">
                                  <span v-for="reason in getBatchItemReasons(item)" :key="reason">{{ reason }}</span>
                                </a-space>
                              </a-descriptions-item>
                              <a-descriptions-item label="未识别列">
                                {{ (item.unmapped_columns || []).join('、') || '无，仅作为调试信息' }}
                              </a-descriptions-item>
                            </a-descriptions>
                            <a-card
                              v-for="subItem in getBatchSubAuditViews(item.audit_result)"
                              :key="`${item.row_index}-${subItem.key}`"
                              size="small"
                              :title="subItem.title"
                              class="sub-audit-card"
                              :class="`sub-audit-card--${subItem.tone}`"
                            >
                              <a-descriptions size="small" :column="1">
                                <a-descriptions-item label="结论">{{ subItem.status }}</a-descriptions-item>
                                <a-descriptions-item label="简短说明">{{ subItem.brief }}</a-descriptions-item>
                              </a-descriptions>
                            </a-card>
                          </template>
                        </a-space>
                      </a-collapse-panel>
                    </a-collapse>
                    <a-empty v-else description="没有可展示的审计结果" />
                  </a-space>
                </a-collapse-panel>
              </a-collapse>
            </template>
          </a-space>
        </a-card>

        <template v-if="result">
          <a-alert
            :type="resultTone"
            :message="result.display_summary || result.display_result || '审计完成'"
            show-icon
          />
          <a-descriptions size="small" bordered :column="1">
            <a-descriptions-item label="项目名称">{{ result.project_name }}</a-descriptions-item>
            <a-descriptions-item label="主结论">{{ summaryStatus }}</a-descriptions-item>
            <a-descriptions-item label="原因说明">
              <a-space direction="vertical" size="small">
                <span v-for="item in summaryReasons" :key="item">{{ item }}</span>
              </a-space>
            </a-descriptions-item>
            <a-descriptions-item label="参考依据">
              <a-space direction="vertical" size="small">
                <div class="basis-section">
                  <div class="basis-section-title">法规条文</div>
                  <span v-for="doc in summaryBasisVisible" :key="doc">{{ doc }}</span>
                  <a-button
                    v-if="summaryBasisHasMore"
                    type="link"
                    size="small"
                    class="basis-toggle"
                    @click="summaryBasisExpanded = !summaryBasisExpanded"
                  >
                    {{ summaryBasisExpanded ? '收起' : `展开更多（${summaryBasisView.documents.length - 3}）` }}
                  </a-button>
                </div>
              </a-space>
            </a-descriptions-item>
          </a-descriptions>

          <a-collapse :default-active-key="['subaudits']">
            <a-collapse-panel key="subaudits" header="分项审计结果">
              <a-space direction="vertical" size="middle" style="width: 100%">
                <a-card
                  v-for="item in subAuditViews"
                  :key="item.key"
                  size="small"
                  :title="item.title"
                  class="sub-audit-card"
                  :class="`sub-audit-card--${item.tone}`"
                >
                  <a-descriptions size="small" :column="1">
                    <a-descriptions-item label="结论">
                      {{ item.status }}
                    </a-descriptions-item>
                    <a-descriptions-item label="简短说明">
                      {{ item.brief }}
                    </a-descriptions-item>
                    <a-descriptions-item label="参考依据">
                      <a-space direction="vertical" size="small">
                        <div
                          v-for="(pair, index) in getVisibleBasisPairs(item)"
                          :key="`${item.key}-${pair.lawText}-${index}`"
                          class="basis-pair"
                        >
                          <div class="basis-section">
                            <div class="basis-section-title">法律条文{{ index + 1 }}</div>
                            <span>{{ pair.lawText }}</span>
                          </div>
                          <div class="basis-section">
                            <div class="basis-section-title">依据说明</div>
                            <span>{{ pair.basisExplanation }}</span>
                          </div>
                        </div>
                        <a-button
                          v-if="(item.basisPairs || []).length > 2"
                          type="link"
                          size="small"
                          class="basis-toggle"
                          @click="toggleSubBasis(item.key)"
                        >
                          {{ isSubBasisExpanded(item.key) ? '收起' : `展开更多（${item.basisPairs.length - 2}）` }}
                        </a-button>
                        <span v-if="item.key === 'amount_info' && item.basis.length">{{ item.basis[0] }}</span>
                      </a-space>
                    </a-descriptions-item>
                  </a-descriptions>
                </a-card>
              </a-space>
            </a-collapse-panel>
          </a-collapse>
        </template>
      </a-space>
    </a-card>
  </div>
</template>

<style scoped>
.audit-engine-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fact-group {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
}

.group-title {
  margin-bottom: 12px;
  font-weight: 600;
}

.fact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.single-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.report-summary-card {
  border-left: 4px solid #1677ff;
  background: #f8fbff;
}

.problem-card {
  border-left: 4px solid #ff4d4f;
}

.debug-json {
  max-height: 260px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 8px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  white-space: pre-wrap;
}

.fact-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fact-label {
  font-size: 13px;
  color: #1f2a44;
}

.fact-key {
  font-size: 12px;
  color: #8c8c8c;
}

.sub-audit-card :deep(.ant-card-body) {
  padding: 8px 0 0;
}

.sub-audit-direct-reject-note {
  margin-bottom: 4px;
}

.sub-audit-card {
  border-left: 4px solid #d9d9d9;
}

.sub-audit-card--success {
  border-left-color: #52c41a;
}

.sub-audit-card--warning {
  border-left-color: #faad14;
}

.sub-audit-card--review {
  border-left-color: #fa8c16;
}

.sub-audit-card--error {
  border-left-color: #ff4d4f;
}

.sub-audit-card--info {
  border-left-color: #1677ff;
}

.sub-audit-card--na {
  border-left-color: #8c8c8c;
}

.basis-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.basis-pair {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 8px;
}

.basis-pair + .basis-pair {
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}

.basis-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #667085;
}

.basis-toggle {
  height: auto;
  padding: 0;
  text-align: left;
}

@media (max-width: 960px) {
  .field-columns,
  .overview-grid,
  .fact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
