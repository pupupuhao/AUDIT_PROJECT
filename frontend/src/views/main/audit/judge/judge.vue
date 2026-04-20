<script setup>
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import { judgeAuditEngine, judgeAuditFiles, parseAuditFiles } from '@/service/audit-engine'
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

function buildPayload() {
  const projectName = String(form.project_name || '').trim()
  const payload = {
    project_name: projectName,
    sources: {
      t_workspace: {
        wsname: projectName,
        property: form.property
      },
      blueprint_draft: {
        wsname: projectName,
        property: form.property,
        expirer_remark: form.expirer_remark ?? ''
      },
      ws_project: {
        is_signed_pc: form.is_signed_pc,
        is_signed_esc: form.is_signed_esc,
        is_signed_esr: form.is_signed_esr,
        need_con: form.need_con,
        orgn_amt: form.orgn_amt
      },
      project_contract: {
        name: projectName,
        startup_date: form.startup_date || undefined,
        orgn_amt: form.orgn_amt,
        contract_amt: form.contract_amt
      }
    }
  }
  if (form.has_hou_notion_sum) {
    payload.sources.hou_notion_sum = {
      __row_exists__: true,
      count_hou: form.count_hou,
      agree_hou: form.agree_hou,
      sum_area: form.sum_area,
      agree_area: form.agree_area,
      request_enddate: form.request_enddate || undefined,
      request_startdate: form.request_startdate || undefined,
      reg_date: form.reg_date || undefined
    }
  }
  return payload
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
              <a-button :loading="fileLoading" :disabled="!uploadFileList.length" @click="parseFiles">
                解析预览
              </a-button>
              <a-button
                type="primary"
                :loading="fileLoading"
                :disabled="!uploadFileList.length"
                @click="judgeFiles()"
              >
                批量审计
              </a-button>
            </a-space>

            <template v-if="parsedFiles.length">
              <div class="group-title">解析预览</div>
              <a-collapse>
                <a-collapse-panel
                  v-for="(file, fileIndex) in parsedFiles"
                  :key="`${file.filename}-${fileIndex}`"
                  :header="`${file.filename || '未命名文件'}：${file.status}`"
                >
                  <a-space direction="vertical" size="small" style="width: 100%">
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
                            :title="`第 ${item.row_index} 行：${item.project_name || '未识别项目名称'}`"
                            :description="`未识别列：${(item.unmapped_columns || []).join('、') || '无'}`"
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
                  :header="`${file.filename || '未命名文件'}：${file.status}`"
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
                        :header="`第 ${item.row_index} 行：${item.project_name || '未识别项目名称'} ｜ ${getBatchItemStatus(item)}`"
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
                              <a-descriptions-item label="主结论">
                                {{ getBatchItemStatus(item) }}
                              </a-descriptions-item>
                              <a-descriptions-item label="原因说明">
                                <a-space direction="vertical" size="small">
                                  <span v-for="reason in getBatchItemReasons(item)" :key="reason">{{ reason }}</span>
                                </a-space>
                              </a-descriptions-item>
                              <a-descriptions-item label="未识别列">
                                {{ (item.unmapped_columns || []).join('、') || '无' }}
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
</style>
