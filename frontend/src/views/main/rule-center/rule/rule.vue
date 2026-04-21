<script setup>
import { computed, createVNode, onMounted, reactive, ref } from 'vue'
import {
  ClockCircleOutlined,
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  FilterOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'

import {
  addComplianceRule,
  delComplianceRule,
  getComplianceRules,
  putComplianceRule
} from '@/service/compliance-rule'
import { getLawDocs, queryLawClauses } from '@/service/law'

const loading = ref(false)
const keyword = ref('')
const category = ref('')
const lawName = ref('')
const categories = ref([])
const selectedRule = ref(null)
const dataSource = ref([])
const latestUpdatedAt = ref('')
const lawCount = ref(0)
const modalVisible = ref(false)
const modalMode = ref('create')
const saving = ref(false)
const formRef = ref()
const lawOptions = ref([])
const clauseOptions = ref([])
const clauseLoading = ref(false)

const form = reactive({
  id: '',
  sourceLawName: undefined,
  sourceClauseId: undefined,
  law_name: '',
  clause_label: '',
  full_title: '',
  content: '',
  category: '',
  ruleNature: '',
  auditStage: '',
  auditDimension: '',
  judgementMode: '',
  projectTypesText: '',
  repairModesText: '',
  applicableObjectsText: '',
  requiredFieldsText: '',
  requiredDocumentsText: '',
  fieldExpectationsText: '[]',
  riskPointsText: '',
  conclusionType: '',
  riskLevel: '',
  messageTemplate: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: false,
  showTotal: (total) => `共 ${total} 条规则`,
  onChange: (page) => {
    pagination.current = page
    fetchData()
  }
})

const columns = [
  {
    title: '规则编号',
    dataIndex: 'id',
    key: 'id',
    width: 110
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    width: 190
  },
  {
    title: '所属法规',
    dataIndex: 'law_name',
    key: 'law_name',
    width: 220,
    ellipsis: true
  },
  {
    title: '条款',
    dataIndex: 'clause_label',
    key: 'clause_label',
    width: 100
  },
  {
    title: '操作',
    key: 'action',
    width: 120
  }
]

const presetCategories = [
  '使用范围合规审计',
  '流程合规审计',
  '资料完整性审计',
  '时序合规审计',
  '金额合理性审计',
  '应急维修审计'
]

const stats = computed(() => [
  { label: '规则总数', value: pagination.total, tone: 'blue', icon: FileTextOutlined },
  { label: '命中法规数', value: lawCount.value, tone: 'gold', icon: SafetyCertificateOutlined },
  { label: '最近更新时间', value: latestUpdatedAt.value || '暂无', tone: 'slate', icon: ClockCircleOutlined, compact: true }
])

const detailLogicItems = computed(() => {
  if (!selectedRule.value) return []

  return [
    { label: '规则性质', value: selectedRule.value.logic_rules?.rule_nature || '-' , half: true},
    { label: '审计阶段', value: selectedRule.value.logic_rules?.audit_stage || '-', half: true },
    { label: '审计维度', value: selectedRule.value.logic_rules?.audit_dimension || '-', half: true },
    { label: '判定方式', value: selectedRule.value.logic_rules?.judgement_mode || '-', half: true },
    { label: '项目类型', value: formatLineList(selectedRule.value.logic_rules?.apply_scope?.project_types), half: true },
    { label: '维修模式', value: formatLineList(selectedRule.value.logic_rules?.apply_scope?.repair_modes), half: true },
    { label: '适用对象', value: formatLineList(selectedRule.value.logic_rules?.apply_scope?.applicable_objects) },
    { label: '所需字段', value: formatLineList(selectedRule.value.logic_rules?.required_fields) },
    { label: '所需材料', value: formatLineList(selectedRule.value.logic_rules?.required_documents) },
    { label: '风险点', value: formatLineList(selectedRule.value.logic_rules?.risk_points) },
    { label: '输出结论', value: selectedRule.value.logic_rules?.output_hint?.conclusion_type || '-', half: true },
    { label: '风险等级', value: selectedRule.value.logic_rules?.output_hint?.risk_level || '-', half: true },
    { label: '输出模板', value: selectedRule.value.logic_rules?.output_hint?.message_template || '-' },
    { label: '字段判定', value: formatFieldExpectations(selectedRule.value.logic_rules?.field_expectations) }
  ]
})

const categoryToneMap = {
  使用范围合规审计: 'slate',
  流程合规审计: 'blue',
  资料完整性审计: 'green',
  时序合规审计: 'gold',
  金额合理性审计: 'rose',
  应急维修审计: 'purple'
}

function getCategoryTone(categoryName) {
  return categoryToneMap[categoryName] || 'slate'
}

const formRules = {
  id: [{ required: true, message: '请输入规则编号', trigger: 'blur' }],
  law_name: [{ required: true, message: '请输入所属法规', trigger: 'blur' }],
  full_title: [{ required: true, message: '请输入规则标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入规则原文', trigger: 'blur' }],
  category: [{ required: true, message: '请选择规则分类', trigger: 'change' }]
}

const mergedCategories = computed(() => [
  ...presetCategories,
  ...categories.value.filter((item) => !presetCategories.includes(item))
])

const categoryOptions = computed(() =>
  mergedCategories.value.map((item) => ({
    label: item,
    value: item
  }))
)

const sourceLawOptions = computed(() =>
  lawOptions.value.map((item) => ({
    label: item.title,
    value: item.title
  }))
)

const mergedLawNames = computed(() => {
  const names = new Set()

  for (const item of lawOptions.value) {
    if (item?.title) {
      names.add(item.title)
    }
  }

  for (const item of dataSource.value) {
    if (item?.law_name) {
      names.add(item.law_name)
    }
  }

  return Array.from(names)
})

const sourceClauseSelectOptions = computed(() =>
  clauseOptions.value.map((item) => ({
    label: item.full_title || item.clause_label,
    value: item.id
  }))
)

function splitLines(value) {
  return String(value || '')
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatLineList(value) {
  if (!Array.isArray(value) || !value.length) return '-'
  return value.join('，')
}

function formatFieldExpectations(value) {
  if (!Array.isArray(value) || !value.length) return '-'
  return value
    .map((item) => {
      const field = item?.field || ''
      const operator = item?.operator || ''
      const rawValue = item?.value
      const renderedValue = Array.isArray(rawValue)
        ? rawValue.join(' / ')
        : rawValue === null || rawValue === undefined
          ? 'null'
          : String(rawValue)
      const message = item?.message ? `（${item.message}）` : ''
      return `${field} ${operator} ${renderedValue}${message}`
    })
    .join('；')
}

function parseJsonArray(value) {
  const text = String(value || '').trim()
  if (!text) return []
  try {
    const parsed = JSON.parse(text)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function fillForm(rule) {
  form.id = rule?.id || ''
  form.sourceLawName = rule?.law_name || undefined
  form.sourceClauseId = undefined
  form.law_name = rule?.law_name || ''
  form.clause_label = rule?.clause_label || ''
  form.full_title = rule?.full_title || ''
  form.content = rule?.content || ''
  form.category = rule?.category || categories.value[0] || ''
  form.ruleNature = rule?.logic_rules?.rule_nature || ''
  form.auditStage = rule?.logic_rules?.audit_stage || ''
  form.auditDimension = rule?.logic_rules?.audit_dimension || ''
  form.judgementMode = rule?.logic_rules?.judgement_mode || ''
  form.projectTypesText = (rule?.logic_rules?.apply_scope?.project_types || []).join('\n')
  form.repairModesText = (rule?.logic_rules?.apply_scope?.repair_modes || []).join('\n')
  form.applicableObjectsText = (rule?.logic_rules?.apply_scope?.applicable_objects || []).join('\n')
  form.requiredFieldsText = (rule?.logic_rules?.required_fields || []).join('\n')
  form.requiredDocumentsText = (rule?.logic_rules?.required_documents || []).join('\n')
  form.fieldExpectationsText = JSON.stringify(rule?.logic_rules?.field_expectations || [], null, 2)
  form.riskPointsText = (rule?.logic_rules?.risk_points || []).join('\n')
  form.conclusionType = rule?.logic_rules?.output_hint?.conclusion_type || ''
  form.riskLevel = rule?.logic_rules?.output_hint?.risk_level || ''
  form.messageTemplate = rule?.logic_rules?.output_hint?.message_template || ''
}

function autoFillFromClause(clause) {
  if (!clause) return
  form.sourceLawName = clause.law_name
  form.sourceClauseId = clause.id
  form.law_name = clause.law_name || ''
  form.clause_label = clause.clause_label || ''
  form.full_title = clause.full_title || ''
  form.content = clause.content || ''
}

async function loadLawOptions() {
  const res = await getLawDocs({ offset: 1, limit: 1000, keyword: '' })
  lawOptions.value = res.data?.items || []
}

async function loadClauseOptions(lawName) {
  if (!lawName) {
    clauseOptions.value = []
    form.sourceClauseId = undefined
    return
  }

  clauseLoading.value = true
  try {
    const res = await queryLawClauses({
      law_name: lawName,
      offset: 1,
      limit: 1000
    })
    clauseOptions.value = res.data?.items || []
  } finally {
    clauseLoading.value = false
  }
}

async function onSourceLawChange(lawName) {
  form.sourceClauseId = undefined
  form.law_name = lawName || ''
  form.clause_label = ''
  form.full_title = ''
  form.content = ''
  await loadClauseOptions(lawName)
}

function onSourceClauseChange(clauseId) {
  const clause = clauseOptions.value.find((item) => item.id === clauseId)
  autoFillFromClause(clause)
}

function buildPayload() {
  return {
    id: form.id.trim(),
    law_name: form.law_name.trim(),
    clause_label: form.clause_label.trim(),
    full_title: form.full_title.trim(),
    content: form.content.trim(),
    category: form.category,
    logic_rules: {
      rule_nature: form.ruleNature.trim(),
      audit_stage: form.auditStage.trim(),
      audit_dimension: form.auditDimension.trim(),
      apply_scope: {
        project_types: splitLines(form.projectTypesText),
        repair_modes: splitLines(form.repairModesText),
        applicable_objects: splitLines(form.applicableObjectsText)
      },
      judgement_mode: form.judgementMode.trim(),
      required_fields: splitLines(form.requiredFieldsText),
      required_documents: splitLines(form.requiredDocumentsText),
      field_expectations: parseJsonArray(form.fieldExpectationsText),
      risk_points: splitLines(form.riskPointsText),
      output_hint: {
        conclusion_type: form.conclusionType.trim(),
        risk_level: form.riskLevel.trim(),
        message_template: form.messageTemplate.trim()
      }
    }
  }
}

async function openCreateModal() {
  modalMode.value = 'create'
  fillForm({
    category: category.value || categories.value[0] || ''
  })
  await loadClauseOptions(form.sourceLawName)
  modalVisible.value = true
}

async function openEditModal(rule) {
  modalMode.value = 'update'
  fillForm(rule)
  await loadClauseOptions(form.sourceLawName)
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  formRef.value?.resetFields()
}

function applyRuleToCurrentView(rule) {
  if (!rule?.id) return

  const existingIndex = dataSource.value.findIndex((item) => item.id === rule.id)
  if (existingIndex >= 0) {
    dataSource.value.splice(existingIndex, 1, rule)
  }

  if (selectedRule.value?.id === rule.id) {
    selectedRule.value = rule
  }
}

function onTableRow(record) {
  return {
    onClick: () => {
      selectedRule.value = record
    }
  }
}

function tableRowClassName(record) {
  return selectedRule.value?.id === record.id ? 'rule-row-selected' : ''
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getComplianceRules({
      offset: pagination.current,
      limit: pagination.pageSize,
      keyword: keyword.value,
      category: category.value,
      law_name: lawName.value
    })
    dataSource.value = res.items || []
    categories.value = res.categories || []
    pagination.total = res.total || 0
    lawCount.value = res.law_count || 0
    latestUpdatedAt.value = res.latest_updated_at
      ? new Date(res.latest_updated_at).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        })
      : ''
    if (!selectedRule.value && dataSource.value.length > 0) {
      selectedRule.value = dataSource.value[0]
    } else if (selectedRule.value) {
      selectedRule.value = dataSource.value.find((item) => item.id === selectedRule.value.id) || dataSource.value[0] || null
    }
  } finally {
    loading.value = false
  }
}

const searchRules = () => {
  pagination.current = 1
  selectedRule.value = null
  fetchData()
}

function onCategoryMenuClick({ key }) {
  category.value = key
  searchRules()
}

function onLawMenuClick({ key }) {
  lawName.value = key
  searchRules()
}

function clearFilters() {
  category.value = ''
  lawName.value = ''
  searchRules()
}

async function saveRule() {
  await formRef.value?.validateFields()
  saving.value = true
  try {
    const payload = buildPayload()
    let savedRule = null
    if (modalMode.value === 'create') {
      savedRule = await addComplianceRule(payload)
      message.success('规则已新增')
    } else {
      savedRule = await putComplianceRule(payload.id, payload)
      message.success('规则已更新')
    }
    applyRuleToCurrentView(savedRule)
    modalVisible.value = false
    await fetchData()
    selectedRule.value = dataSource.value.find((item) => item.id === payload.id) || dataSource.value[0] || null
  } finally {
    saving.value = false
  }
}

function confirmDelete(rule) {
  Modal.confirm({
    title: '确认删除这条规则吗？',
    icon: createVNode(ExclamationCircleOutlined),
    content: `${rule.id} 删除后将无法恢复`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    async onOk() {
      await delComplianceRule(rule.id)
      message.success('规则已删除')
      if (selectedRule.value?.id === rule.id) {
        selectedRule.value = null
      }
      await fetchData()
    }
  })
}

onMounted(async () => {
  await Promise.all([fetchData(), loadLawOptions()])
})
</script>

<template>
  <div class="rule-page">
    <div class="hero">
      <div class="hero-copy">
        <h2>审核规则管理</h2>
        <p>查看规则分类、来源法规和提炼后的判定逻辑，为后续审核流程接入做准备。</p>
      </div>
      <div class="filters">
        <a-button class="page-action-button" v-per="'compliance:rule:create'" @click="openCreateModal">
          新增规则
        </a-button>
        <a-input-search
          v-model:value="keyword"
          placeholder="搜索规则编号、法规或条文"
          allow-clear
          style="width: 320px"
          @search="searchRules"
        />
      </div>
    </div>

    <div class="stats">
      <a-card v-for="item in stats" :key="item.label" size="small">
        <div class="stat-card" :class="{ 'stat-card--compact': item.compact }">
          <div class="stat-icon" :class="[`stat-icon--${item.tone}`, { 'stat-icon--compact': item.compact }]">
            <component :is="item.icon" />
          </div>
          <div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value" :class="[`stat-value--${item.tone}`, { 'stat-value--compact': item.compact }]">
              {{ item.value }}
            </div>
          </div>
        </div>
      </a-card>
    </div>

    <div class="content">
      <a-card class="list-card">
        <template #title>
          <div class="card-title-row">
            <span>规则列表</span>
            <a-popover trigger="click" placement="bottomRight" overlay-class-name="rule-filter-popover">
              <template #content>
                <div class="filter-panel">
                  <div class="filter-panel__group">
                    <div class="filter-panel__label">分类</div>
                    <a-select
                      v-model:value="category"
                      allow-clear
                      show-search
                      placeholder="全部分类"
                      :options="categoryOptions"
                      style="width: 220px"
                      @change="searchRules"
                    />
                  </div>
                  <div class="filter-panel__group">
                    <div class="filter-panel__label">所属法规</div>
                    <a-select
                      v-model:value="lawName"
                      allow-clear
                      show-search
                      placeholder="全部法规"
                      :options="mergedLawNames.map((item) => ({ label: item, value: item }))"
                      style="width: 220px"
                      @change="searchRules"
                    />
                  </div>
                  <div class="filter-panel__footer">
                    <a-button size="small" @click="clearFilters">清空</a-button>
                  </div>
                </div>
              </template>
              <button class="ghost-filter-button" type="button">
                <FilterOutlined />
                <span>筛选</span>
              </button>
            </a-popover>
          </div>
        </template>
        <a-table
          :columns="columns"
          :data-source="dataSource"
          :pagination="pagination"
          :loading="loading"
          :row-key="(record) => record.id"
          :custom-row="onTableRow"
          :row-class-name="tableRowClassName"
        >
          <template #headerCell="{ column }">
            <template v-if="column.key === 'category'">
              <a-dropdown :trigger="['click']">
                <span class="header-filter">
                  <span>{{ category || '分类' }}</span>
                  <DownOutlined class="header-filter__icon" />
                </span>
                <template #overlay>
                  <a-menu @click="onCategoryMenuClick">
                    <a-menu-item key="">全部</a-menu-item>
                    <a-menu-item v-for="item in mergedCategories" :key="item">
                      {{ item }}
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </template>
            <template v-else-if="column.key === 'law_name'">
              <a-dropdown :trigger="['click']">
                <span class="header-filter">
                  <span>{{ lawName || '所属法规' }}</span>
                  <DownOutlined class="header-filter__icon" />
                </span>
                <template #overlay>
                  <a-menu @click="onLawMenuClick">
                    <a-menu-item key="">全部</a-menu-item>
                    <a-menu-item v-for="item in mergedLawNames" :key="item">
                      {{ item }}
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </template>
            <template v-else>
              {{ column.title }}
            </template>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'category'">
              <span class="category-pill" :class="`category-pill--${getCategoryTone(record.category)}`">
                {{ record.category }}
              </span>
            </template>
            <template v-else-if="column.key === 'action'">
              <div class="row-actions">
                <button
                  v-per="'compliance:rule:update'"
                  type="button"
                  class="icon-action-button icon-action-button--edit"
                  @click.stop="openEditModal(record)"
                >
                  <EditOutlined />
                </button>
                <button
                  v-per="'compliance:rule:delete'"
                  type="button"
                  class="icon-action-button icon-action-button--delete"
                  @click.stop="confirmDelete(record)"
                >
                  <DeleteOutlined />
                </button>
              </div>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card class="detail-card">
        <template #title>
          <span>规则详情</span>
        </template>
        <template v-if="selectedRule">
          <div class="detail-header">
            <div>
              <div class="detail-kicker">详情</div>
              <h3>{{ selectedRule.id }}</h3>
              <div class="detail-title">{{ selectedRule.full_title || selectedRule.clause_label }}</div>
            </div>
            <a-space>
              <a-button
                v-per="'compliance:rule:update'"
                class="page-action-button"
                @click="openEditModal(selectedRule)"
              >
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
            </a-space>
          </div>
          <div class="detail-meta">
            <div><strong>所属法规：</strong>{{ selectedRule.law_name }}</div>
            <div><strong>条款位置：</strong>{{ selectedRule.clause_label || '-' }}</div>
            <div><strong>层级路径：</strong>{{ (selectedRule.path || []).join(' / ') || '-' }}</div>
            <div><strong>节点类型：</strong>{{ selectedRule.node_type || '-' }}</div>
          </div>

          <section class="detail-section">
            <div class="section-heading">
              <span class="section-heading__bar"></span>
              <span>规则原文</span>
            </div>
            <div class="detail-surface">
              <div class="section-text">{{ selectedRule.content }}</div>
            </div>
          </section>

          <section class="detail-section">
            <div class="section-heading">
              <span class="section-heading__bar"></span>
              <span>提炼逻辑</span>
            </div>
            <div class="logic-grid">
              <article
                v-for="item in detailLogicItems"
                :key="item.label"
                class="logic-item"
                :class="{ 'logic-item--half': item.half }"
              >
                <div class="logic-item__label">{{ item.label }}</div>
                <div class="logic-item__value">{{ item.value }}</div>
              </article>
            </div>
          </section>
        </template>
        <a-empty v-else description="请选择左侧规则查看详情" />
      </a-card>
    </div>

    <a-modal
      v-model:visible="modalVisible"
      :title="modalMode === 'create' ? '新增规则' : '编辑规则'"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="saving"
      width="760px"
      @ok="saveRule"
      @cancel="closeModal"
    >
      <a-form ref="formRef" :model="form" :rules="formRules" layout="vertical">
        <div class="form-grid">
          <a-form-item label="来源法规">
            <a-select
              v-model:value="form.sourceLawName"
              allow-clear
              show-search
              :options="sourceLawOptions"
              placeholder="选择法规后可自动回填"
              @change="onSourceLawChange"
            />
          </a-form-item>
          <a-form-item label="来源条款">
            <a-select
              v-model:value="form.sourceClauseId"
              allow-clear
              show-search
              :options="sourceClauseSelectOptions"
              :loading="clauseLoading"
              placeholder="选择条款后自动回填信息"
              @change="onSourceClauseChange"
            />
          </a-form-item>
          <a-form-item name="id" label="规则编号">
            <a-input v-model:value="form.id" :disabled="modalMode === 'update'" />
          </a-form-item>
          <a-form-item name="category" label="规则分类">
            <a-select v-model:value="form.category" :options="categoryOptions" />
          </a-form-item>
          <a-form-item name="law_name" label="所属法规" class="span-2">
            <a-input v-model:value="form.law_name" />
          </a-form-item>
          <a-form-item name="clause_label" label="条款位置">
            <a-input v-model:value="form.clause_label" />
          </a-form-item>
          <a-form-item name="full_title" label="规则标题">
            <a-input v-model:value="form.full_title" />
          </a-form-item>
          <a-form-item name="content" label="规则原文" class="span-2">
            <a-textarea v-model:value="form.content" :rows="5" />
          </a-form-item>
          <a-form-item label="规则性质">
            <a-input v-model:value="form.ruleNature" placeholder="如 process / document / amount" />
          </a-form-item>
          <a-form-item label="审计阶段">
            <a-input v-model:value="form.auditStage" placeholder="如 initiation / settlement" />
          </a-form-item>
          <a-form-item label="审计维度">
            <a-input v-model:value="form.auditDimension" placeholder="如 entity / trace / process / amount" />
          </a-form-item>
          <a-form-item label="判定方式">
            <a-input v-model:value="form.judgementMode" placeholder="如 boolean / threshold / document_presence" />
          </a-form-item>
          <a-form-item label="项目类型">
            <a-textarea v-model:value="form.projectTypesText" :rows="3" placeholder="每行一个 project_type" />
          </a-form-item>
          <a-form-item label="维修模式">
            <a-textarea v-model:value="form.repairModesText" :rows="3" placeholder="每行一个 repair_mode" />
          </a-form-item>
          <a-form-item label="适用对象">
            <a-textarea v-model:value="form.applicableObjectsText" :rows="3" placeholder="每行一个 applicable_object" />
          </a-form-item>
          <a-form-item label="所需字段">
            <a-textarea v-model:value="form.requiredFieldsText" :rows="4" placeholder="每行一个 required_field" />
          </a-form-item>
          <a-form-item label="所需材料">
            <a-textarea v-model:value="form.requiredDocumentsText" :rows="4" placeholder="每行一个 required_document" />
          </a-form-item>
          <a-form-item label="风险点">
            <a-textarea v-model:value="form.riskPointsText" :rows="4" placeholder="每行一个 risk_point" />
          </a-form-item>
          <a-form-item label="字段判定(JSON)" class="span-2">
            <a-textarea v-model:value="form.fieldExpectationsText" :rows="8" placeholder='[{"field":"has_vote_trace","operator":"==","value":true,"message":"应存在业主表决痕迹"}]' />
          </a-form-item>
          <a-form-item label="输出结论">
            <a-input v-model:value="form.conclusionType" placeholder="如 compliant / manual_review" />
          </a-form-item>
          <a-form-item label="风险等级">
            <a-input v-model:value="form.riskLevel" placeholder="如 low / medium / high" />
          </a-form-item>
          <a-form-item label="输出模板" class="span-2">
            <a-textarea v-model:value="form.messageTemplate" :rows="3" />
          </a-form-item>
        </div>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.rule-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  padding: 26px 28px;
  border: 1px solid #f1e3c4;
  border-radius: 20px;
  background: linear-gradient(135deg, #fffaf0 0%, #fff3da 100%);
  box-shadow: 0 18px 44px rgba(180, 134, 38, 0.08);
}

.hero-copy {
  flex: 1 1 360px;
  min-width: 0;
}

.hero h2,
.detail-header h3 {
  margin: 0;
}

.hero p {
  margin: 8px 0 0;
  color: #6e6251;
}

.filters {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: nowrap;
  gap: 12px;
  align-items: center;
}

.danger-link {
  color: #ff4d4f;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.icon-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-action-button--edit:hover {
  background: #eef4ff;
  color: #1677ff;
}

.icon-action-button--delete:hover {
  background: #fff1f2;
  color: #ef4444;
}

.page-action-button {
  height: 38px;
  padding: 0 16px;
  border: 1px solid #1677ff;
  border-radius: 12px;
  font-weight: 600;
  background: #ffffff;
  color: #1677ff;
  box-shadow: 0 10px 22px rgba(22, 119, 255, 0.1);
}

.page-action-button:hover,
.page-action-button:focus {
  border-color: #4096ff;
  background: #f4f9ff;
  color: #4096ff;
}

.header-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(0, 0, 0, 0.88);
  font-weight: 600;
  white-space: nowrap;
}

.header-filter:hover {
  color: #1677ff;
}

.header-filter__icon {
  font-size: 11px;
}

.category-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  width: 132px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  text-align: center;
  border: 1px solid transparent;
}

.category-pill--slate {
  color: #445066;
  background: #f3f5f8;
  border-color: #e2e8f0;
}

.category-pill--blue {
  color: #215ea6;
  background: #edf4ff;
  border-color: #cdddff;
}

.category-pill--green {
  color: #21674b;
  background: #eefaf3;
  border-color: #caecd9;
}

.category-pill--gold {
  color: #8a5a12;
  background: #fff6e8;
  border-color: #f3ddba;
}

.category-pill--rose {
  color: #9a435e;
  background: #fff1f5;
  border-color: #f3cfda;
}

.category-pill--purple {
  color: #6f4aa3;
  background: #f5f1ff;
  border-color: #ddd1ff;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.stats :deep(.ant-card) {
  border: 1px solid #e7edf5;
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.stats :deep(.ant-card-body) {
  padding: 18px 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-card--compact {
  align-items: flex-start;
}

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 999px;
  font-size: 20px;
}

.stat-icon--compact {
  margin-top: 2px;
}

.stat-icon--blue {
  color: #1677ff;
  background: #edf4ff;
}

.stat-icon--gold {
  color: #c28103;
  background: #fff6df;
}

.stat-icon--slate {
  color: #516072;
  background: #f2f5f8;
}

.stat-label {
  color: #7c8596;
  font-size: 12px;
  font-weight: 600;
}

.stat-value {
  margin-top: 6px;
  font-size: 27px;
  font-weight: 700;
  color: #1f2a44;
}

.stat-value--blue {
  color: #1677ff;
}

.stat-value--gold {
  color: #c28103;
}

.stat-value--slate {
  color: #1f2a44;
}

.stat-value--compact {
  font-size: 24px;
  line-height: 1.25;
  font-weight: 700;
}

.content {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(360px, 1fr);
  gap: 20px;
  min-width: 0;
  align-items: start;
}

.list-card,
.detail-card,
.content > * {
  min-width: 0;
}

.list-card :deep(.ant-card),
.detail-card :deep(.ant-card) {
  border-radius: 20px;
}

.list-card :deep(.ant-card-head),
.detail-card :deep(.ant-card-head) {
  min-height: 64px;
  border-bottom: 1px solid #eef2f6;
}

.list-card :deep(.ant-card-body),
.detail-card :deep(.ant-card-body) {
  overflow: auto;
  padding: 0;
}

.list-card {
  border: 1px solid #e8edf5;
  border-radius: 20px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.detail-card {
  position: sticky;
  top: 24px;
  border: 1px solid #dbeafe;
  border-radius: 20px;
  box-shadow: 0 22px 52px rgba(37, 99, 235, 0.08);
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  font-weight: 700;
  color: #1f2a44;
}

.ghost-filter-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #66758a;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.ghost-filter-button:hover {
  color: #1677ff;
}

.filter-panel {
  display: grid;
  gap: 14px;
}

.filter-panel__group {
  display: grid;
  gap: 6px;
}

.filter-panel__label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.filter-panel__footer {
  display: flex;
  justify-content: flex-end;
}

.list-card :deep(.ant-table) {
  background: transparent;
}

.list-card :deep(.ant-table-thead > tr > th) {
  padding-top: 16px;
  padding-bottom: 16px;
  background: #f8fafc;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  border-bottom: 1px solid #edf2f7;
}

.list-card :deep(.ant-table-tbody > tr > td) {
  padding-top: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid #f0f4f8;
  transition: background-color 0.2s ease;
}

.list-card :deep(.ant-table-tbody > tr.rule-row-selected > td) {
  background: #f4f8ff;
}

.list-card :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fbff;
}

.list-card :deep(.ant-pagination) {
  padding: 16px 20px 18px;
}

.list-card :deep(.ant-card-head-title),
.detail-card :deep(.ant-card-head-title) {
  padding: 18px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 24px 24px 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 12px;
}

.span-2 {
  grid-column: 1 / -1;
}

.detail-title {
  margin-top: 6px;
  color: #6a7282;
}

.detail-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  margin-bottom: 10px;
  padding: 0 10px;
  border-radius: 999px;
  background: #eaf3ff;
  color: #1677ff;
  font-size: 12px;
  font-weight: 700;
}

.detail-meta {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0 24px 18px;
  color: #334155;
}

.detail-section {
  padding: 0 24px 24px;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  color: #1e293b;
  font-weight: 700;
}

.section-heading__bar {
  width: 4px;
  height: 18px;
  border-radius: 999px;
  background: #1677ff;
}

.detail-surface {
  padding: 16px;
  border: 1px solid #edf2f7;
  border-radius: 16px;
  background: #f8fafc;
}

.section-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #2f3542;
}

.logic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.logic-item {
  grid-column: 1 / -1;
  padding: 16px;
  border: 1px solid #edf2f7;
  border-radius: 16px;
  background: #f8fafc;
}

.logic-item--half {
  grid-column: span 1;
}

.logic-item__label {
  margin-bottom: 6px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.logic-item__value {
  color: #334155;
  line-height: 1.75;
}

@media (max-width: 960px) {
  .hero,
  .content {
    display: grid;
    grid-template-columns: 1fr;
  }

  .filters,
  .stats {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .filters {
    display: grid;
    grid-template-columns: 1fr;
  }

  .stats {
    display: grid;
  }

  .filters :deep(.ant-select),
  .filters :deep(.ant-input-search) {
    width: 100% !important;
  }

  .detail-header {
    flex-direction: column;
  }

  .detail-card {
    position: static;
  }

  .logic-grid {
    grid-template-columns: 1fr;
  }

  .logic-item--half {
    grid-column: auto;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }
}
</style>
