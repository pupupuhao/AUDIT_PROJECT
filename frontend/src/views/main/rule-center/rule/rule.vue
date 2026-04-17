<script setup>
import { computed, createVNode, onMounted, reactive, ref } from 'vue'
import { DownOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'

import { addComplianceRule, delComplianceRule, getComplianceRules, putComplianceRule } from '@/service/compliance-rule'
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
  keywordsText: '',
  action: '',
  targetText: '',
  conditionText: '',
  forbiddenText: '',
  requiredDocsText: '',
  responsibility: ''
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
    width: 180
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
  { label: '规则总数', value: pagination.total },
  { label: '命中法规数', value: lawCount.value },
  { label: '最近更新时间', value: latestUpdatedAt.value || '暂无' }
])

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

function fillForm(rule) {
  form.id = rule?.id || ''
  form.sourceLawName = rule?.law_name || undefined
  form.sourceClauseId = undefined
  form.law_name = rule?.law_name || ''
  form.clause_label = rule?.clause_label || ''
  form.full_title = rule?.full_title || ''
  form.content = rule?.content || ''
  form.category = rule?.category || categories.value[0] || ''
  form.keywordsText = (rule?.keywords || []).join('\n')
  form.action = rule?.logic_rules?.action || ''
  form.targetText = (rule?.logic_rules?.target || []).join('\n')
  form.conditionText = (rule?.logic_rules?.condition || []).join('\n')
  form.forbiddenText = (rule?.logic_rules?.forbidden || []).join('\n')
  form.requiredDocsText = (rule?.logic_rules?.required_docs || rule?.required_docs || []).join('\n')
  form.responsibility = rule?.logic_rules?.responsibility || ''
}

function autoFillFromClause(clause) {
  if (!clause) return
  form.sourceLawName = clause.law_name
  form.sourceClauseId = clause.id
  form.law_name = clause.law_name || ''
  form.clause_label = clause.clause_label || ''
  form.full_title = clause.full_title || ''
  form.content = clause.content || ''
  if (!form.keywordsText.trim()) {
    form.keywordsText = String(clause.content || '')
      .split(/[\s，。；、]/)
      .map((item) => item.trim())
      .filter((item) => item.length >= 2)
      .slice(0, 6)
      .join('\n')
  }
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
  form.keywordsText = ''
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
    keywords: splitLines(form.keywordsText),
    logic_rules: {
      action: form.action.trim(),
      target: splitLines(form.targetText),
      condition: splitLines(form.conditionText),
      forbidden: splitLines(form.forbiddenText),
      required_docs: splitLines(form.requiredDocsText),
      responsibility: form.responsibility.trim()
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

async function saveRule() {
  await formRef.value?.validateFields()
  saving.value = true
  try {
    const payload = buildPayload()
    if (modalMode.value === 'create') {
      await addComplianceRule(payload)
      message.success('规则已新增')
    } else {
      await putComplianceRule(payload.id, payload)
      message.success('规则已更新')
    }
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
      <div>
        <h2>审核规则管理</h2>
        <p>查看规则分类、来源法规和提炼后的判定逻辑，为后续审核流程接入做准备。</p>
      </div>
      <div class="filters">
        <a-button type="primary" v-per="'compliance:rule:create'" @click="openCreateModal">
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
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value">{{ item.value }}</div>
      </a-card>
    </div>

    <div class="content">
      <a-card class="list-card" title="规则列表">
        <a-table
          :columns="columns"
          :data-source="dataSource"
          :pagination="pagination"
          :loading="loading"
          :row-key="(record) => record.id"
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
              <a-space>
                <a @click="selectedRule = record">查看详情</a>
                <a v-per="'compliance:rule:update'" @click="openEditModal(record)">编辑</a>
                <a v-per="'compliance:rule:delete'" class="danger-link" @click="confirmDelete(record)">删除</a>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card class="detail-card" title="规则详情">
        <template v-if="selectedRule">
          <div class="detail-header">
            <div>
              <h3>{{ selectedRule.id }}</h3>
              <div class="detail-title">{{ selectedRule.full_title || selectedRule.clause_label }}</div>
            </div>
            <a-space>
              <div class="category-badge">{{ selectedRule.category }}</div>
              <a-button v-per="'compliance:rule:update'" size="small" @click="openEditModal(selectedRule)">
                编辑
              </a-button>
            </a-space>
          </div>
          <div class="detail-meta">
            <div><strong>所属法规：</strong>{{ selectedRule.law_name }}</div>
            <div><strong>条款位置：</strong>{{ selectedRule.clause_label || '-' }}</div>
          </div>

          <a-divider orientation="left">规则原文</a-divider>
          <div class="section-text">{{ selectedRule.content }}</div>

          <a-divider orientation="left">提炼逻辑</a-divider>
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="动作">
              {{ selectedRule.logic_rules?.action || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="适用对象">
              {{ selectedRule.logic_rules?.target?.join('，') || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="触发条件">
              {{ selectedRule.logic_rules?.condition?.join('，') || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="禁止事项">
              {{ selectedRule.logic_rules?.forbidden?.join('，') || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="所需材料">
              {{ selectedRule.logic_rules?.required_docs?.join('，') || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="责任主体">
              {{ selectedRule.logic_rules?.responsibility || '-' }}
            </a-descriptions-item>
          </a-descriptions>
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
          <a-form-item label="关键词" class="span-2">
            <a-textarea v-model:value="form.keywordsText" :rows="3" placeholder="每行一个关键词" />
          </a-form-item>
          <a-form-item label="动作">
            <a-input v-model:value="form.action" />
          </a-form-item>
          <a-form-item label="责任主体">
            <a-input v-model:value="form.responsibility" />
          </a-form-item>
          <a-form-item label="适用对象">
            <a-textarea v-model:value="form.targetText" :rows="3" placeholder="每行一个对象" />
          </a-form-item>
          <a-form-item label="触发条件">
            <a-textarea v-model:value="form.conditionText" :rows="3" placeholder="每行一个条件" />
          </a-form-item>
          <a-form-item label="禁止事项">
            <a-textarea v-model:value="form.forbiddenText" :rows="3" placeholder="每行一个禁止事项" />
          </a-form-item>
          <a-form-item label="所需材料">
            <a-textarea v-model:value="form.requiredDocsText" :rows="3" placeholder="每行一个材料" />
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
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff9ef 0%, #fff3dc 100%);
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
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.danger-link {
  color: #ff4d4f;
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
  gap: 16px;
}

.stat-label {
  color: #7c8596;
  font-size: 13px;
}

.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 600;
  color: #1f2a44;
}

.content {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 16px;
  min-width: 0;
}

.list-card,
.detail-card,
.content > * {
  min-width: 0;
}

.list-card :deep(.ant-card-body),
.detail-card :deep(.ant-card-body) {
  overflow: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
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

.category-badge {
  flex: 0 0 auto;
  max-width: 180px;
  padding: 6px 10px;
  border: 1px solid #8fc6ff;
  border-radius: 8px;
  background: #eef7ff;
  color: #1677ff;
  font-size: 13px;
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}

.detail-meta {
  display: grid;
  gap: 8px;
  margin: 16px 0;
}

.section-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #2f3542;
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

  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }
}
</style>
