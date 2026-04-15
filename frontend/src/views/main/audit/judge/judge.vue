<script setup>
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import { judgeAuditEngine } from '@/service/audit-engine'
import {
  buildSubAuditView,
  getBasisList,
  getTopGapText,
  getTopReasons,
  getTopStatusLabel,
  isHighFreqDirectReject
} from '@/utils/audit-display-adapter'

const loading = ref(false)
const result = ref(null)

const form = reactive({
  project_name: '',
  is_common_part: undefined,
  is_common_facility: undefined,
  is_private_part: undefined,
  is_property_service_scope: undefined,
  has_vote: undefined,
  has_announcement: undefined,
  has_budget_review: undefined,
  has_contract: undefined,
  has_site_photos: undefined,
  has_rectification_notice: undefined,
  has_completion_report: undefined,
  has_acceptance_record: undefined,
  has_invoice: undefined,
  has_settlement_report: undefined,
  has_payment_proof: undefined,
  gray_case_evidence_complete: undefined,
  has_damage_assessment: undefined,
  is_emergency: undefined,
  has_emergency_proof: undefined
})

const boolSelectOptions = [
  { label: '未填写', value: undefined },
  { label: '是', value: true },
  { label: '否', value: false }
]

const optionalFieldGroups = [
  {
    title: '范围相关',
    fields: [
      { key: 'is_common_part', label: '共用部位' },
      { key: 'is_common_facility', label: '共用设施' },
      { key: 'is_private_part', label: '专有部分' },
      { key: 'is_property_service_scope', label: '物业服务范围' }
    ]
  },
  {
    title: '流程相关',
    fields: [
      { key: 'has_vote', label: '有无表决' },
      { key: 'has_announcement', label: '有无公示' },
      { key: 'has_budget_review', label: '有无审价' },
      { key: 'has_contract', label: '有无合同' }
    ]
  },
  {
    title: '资料相关',
    fields: [
      { key: 'has_site_photos', label: '现场照片' },
      { key: 'has_rectification_notice', label: '整改通知' },
      { key: 'has_completion_report', label: '完工报告' },
      { key: 'has_acceptance_record', label: '验收记录' },
      { key: 'has_invoice', label: '发票材料' },
      { key: 'has_settlement_report', label: '结算材料' },
      { key: 'has_payment_proof', label: '付款凭证' }
    ]
  },
  {
    title: '灰区/应急相关',
    fields: [
      { key: 'gray_case_evidence_complete', label: '灰区证据完整' },
      { key: 'has_damage_assessment', label: '损坏评估' },
      { key: 'is_emergency', label: '紧急维修' },
      { key: 'has_emergency_proof', label: '应急证明' }
    ]
  }
]

const demoCases = [
  { label: '排除类：小区树木修剪', payload: { project_name: '小区树木修剪' } },
  { label: '排除类：电梯125%制动试验', payload: { project_name: '电梯125%制动试验' } },
  { label: '可纳入：电梯主机维修', payload: { project_name: '3号楼电梯主机维修' } },
  { label: '可纳入：外墙渗漏维修', payload: { project_name: '12号楼外墙渗漏维修' } },
  {
    label: '冲突复核：电梯主机+专有',
    payload: { project_name: '3号楼电梯主机维修', is_private_part: true }
  },
  { label: '户内专有：室内门锁维修', payload: { project_name: '室内门锁维修', is_private_part: true } }
]

const subAuditMeta = [
  { key: 'scope_audit', title: '使用范围审计' },
  { key: 'process_audit', title: '流程合规审计' },
  { key: 'document_completeness_audit', title: '资料完整性审计' },
  { key: 'timeline_audit', title: '时序合规审计' },
  { key: 'amount_audit', title: '金额合理性审计' },
  { key: 'emergency_audit', title: '应急维修审计' }
]

const resultTone = computed(() => {
  if (!result.value) return 'processing'
  const key = result.value.overall_result
  if (key === 'non_compliant') return 'error'
  if (key === 'manual_review') return 'warning'
  if (key === 'compliant') return 'success'
  return 'processing'
})

const summaryStatus = computed(() => getTopStatusLabel(result.value?.overall_result, result.value?.display_result))
const summaryGapText = computed(() => getTopGapText(result.value?.summary_conclusion || {}))
const summaryReasons = computed(() => getTopReasons(result.value))
const summaryBasis = computed(() => getBasisList(result.value?.basis_documents || []))
const isDirectReject = computed(() => isHighFreqDirectReject(result.value?.audit_path || []))
const subAuditViews = computed(() =>
  subAuditMeta.map((meta) => buildSubAuditView(meta.key, meta.title, result.value?.sub_audits?.[meta.key]))
)

function buildPayload() {
  const payload = { project_name: String(form.project_name || '').trim() }
  Object.entries(form).forEach(([key, value]) => {
    if (key === 'project_name') return
    if (value === undefined || value === null || value === '') return
    payload[key] = value
  })
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
  } finally {
    loading.value = false
  }
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
                      <a-select
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

        <template v-if="result">
          <a-alert
            :type="resultTone"
            :message="result.display_summary || result.display_result || '审计完成'"
            show-icon
          />
          <a-descriptions size="small" bordered :column="1">
            <a-descriptions-item label="项目名称">{{ result.project_name }}</a-descriptions-item>
            <a-descriptions-item label="主结论">{{ summaryStatus }}</a-descriptions-item>
            <a-descriptions-item label="缺口说明">{{ summaryGapText }}</a-descriptions-item>
            <a-descriptions-item label="原因说明">
              <a-space direction="vertical" size="small">
                <span v-for="item in summaryReasons" :key="item">{{ item }}</span>
              </a-space>
            </a-descriptions-item>
            <a-descriptions-item label="参考依据">
              <a-space direction="vertical" size="small">
                <span v-for="doc in summaryBasis" :key="doc">{{ doc }}</span>
              </a-space>
            </a-descriptions-item>
          </a-descriptions>

          <a-collapse :default-active-key="['subaudits']">
            <a-collapse-panel key="subaudits" header="分项审计结果">
              <a-alert
                v-if="isDirectReject"
                type="info"
                show-icon
                class="sub-audit-direct-reject-note"
                message="该事项已判定为不纳入维修资金，后续审计环节不适用"
              />
              <a-space v-else direction="vertical" size="middle" style="width: 100%">
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
                        <span v-for="basis in item.basis.slice(0, 2)" :key="`${item.key}-${basis}`">{{ basis }}</span>
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

.sub-audit-card--risk {
  border-left-color: #ff4d4f;
}

.sub-audit-card--na {
  border-left-color: #8c8c8c;
}
</style>
