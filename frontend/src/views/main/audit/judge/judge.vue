<script setup>
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import { judgeAuditEngine } from '@/service/audit-engine'
import {
  buildSubAuditView,
  getBasisList,
  getTopGapText,
  getTopReasons,
  getTopStatusLabel
} from '@/utils/audit-display-adapter'

const loading = ref(false)
const result = ref(null)

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
  startup_date: '',
  orgn_amt: undefined,
  contract_amt: undefined
})

const boolSelectOptions = [
  { label: '未填写', value: undefined },
  { label: '是', value: true },
  { label: '否', value: false }
]

const optionalFieldGroups = [
  {
    title: '工程主表 / 预案',
    fields: [
      { key: 'property', label: '工程性质 property', type: 'number' },
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
      { key: 'agree_area', label: '同意面积', type: 'number' }
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
  { label: '普通维修：电梯主机', payload: { project_name: '3号楼电梯主机维修', property: 1, is_signed_pc: true, is_signed_esc: true, is_signed_esr: true, need_con: true, has_hou_notion_sum: true, count_hou: 100, agree_hou: 80, sum_area: 1000, agree_area: 800, orgn_amt: 120000, contract_amt: 118000 } },
  { label: '紧急维修：外墙脱落', payload: { project_name: '外墙砖脱落应急维修工程', property: 2, is_signed_pc: true, is_signed_esc: true, is_signed_esr: false, need_con: true, orgn_amt: 568770.27, contract_amt: 435000 } },
  {
    label: '专有部分：室内门锁',
    payload: { project_name: '室内门锁维修', property: 1 }
  },
  { label: '资料缺失：消防维修', payload: { project_name: '消防水泵维修工程', property: 1 } }
]

const subAuditMeta = [
  { key: 'entity_audit', title: '项目本体合规' },
  { key: 'trace_audit', title: '资料/手续痕迹完备性' },
  { key: 'process_audit', title: '流程合规' },
  { key: 'amount_info', title: '金额与造价信息展示' }
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
const subAuditViews = computed(() =>
  subAuditMeta.map((meta) => buildSubAuditView(meta.key, meta.title, result.value?.sub_audits?.[meta.key]))
)

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
        expirer_remark: form.expirer_remark || undefined
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
      count_hou: form.count_hou,
      agree_hou: form.agree_hou,
      sum_area: form.sum_area,
      agree_area: form.agree_area
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
                      <a-input
                        v-if="field.type === 'text'"
                        v-model:value="form[field.key]"
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

.sub-audit-card--info {
  border-left-color: #1677ff;
}

.sub-audit-card--risk {
  border-left-color: #ff4d4f;
}

.sub-audit-card--na {
  border-left-color: #8c8c8c;
}
</style>
