<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'
import { createVNode } from 'vue'
import { message, Modal } from 'ant-design-vue'

import {
  addLawClause,
  delLawClause,
  getLawDocs,
  putLawClause,
  queryLawClauses
} from '@/service/law'

const loading = ref(false)
const detailLoading = ref(false)
const selectedLaw = ref(null)
const keyword = ref('')
const dataSource = ref([])
const clauses = ref([])

const modalVisible = ref(false)
const modalMode = ref('create')
const createScope = ref('document')
const saving = ref(false)
const editingClauseId = ref(null)

const clauseForm = reactive({
  law_name: '',
  clause_label: '',
  full_title: '',
  content: ''
})

const clauseRules = {
  law_name: [{ required: true, message: '请输入法规名称', trigger: 'blur' }],
  clause_label: [{ required: true, message: '请输入条款编号', trigger: 'blur' }],
  full_title: [{ required: true, message: '请输入完整标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入条款内容', trigger: 'blur' }]
}

const formRef = ref()

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: false,
  showTotal: (total) => `共 ${total} 份文件`,
  onChange: (page) => {
    pagination.current = page
    fetchData()
  }
})

const columns = [
  {
    title: '法规名称',
    dataIndex: 'title',
    key: 'title',
    ellipsis: true
  },
  {
    title: '条款数',
    dataIndex: 'section_count',
    key: 'section_count',
    width: 100
  },
  {
    title: '关联规则数',
    dataIndex: 'rule_count',
    key: 'rule_count',
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    width: 160
  }
]

const modalTitle = computed(() => {
  if (modalMode.value === 'update') return '编辑法律条款'
  return createScope.value === 'document' ? '新增法律文件' : '新增法律条款'
})

const lawStats = computed(() => {
  const totalDocs = pagination.total
  const totalSections = dataSource.value.reduce((sum, item) => sum + (item.section_count || 0), 0)
  const totalRules = dataSource.value.reduce((sum, item) => sum + (item.rule_count || 0), 0)
  return [
    { label: '法规文件总数', value: totalDocs },
    { label: '本页条款数量', value: totalSections },
    { label: '本页关联规则数', value: totalRules }
  ]
})

const resetClauseForm = () => {
  clauseForm.law_name = ''
  clauseForm.clause_label = ''
  clauseForm.full_title = ''
  clauseForm.content = ''
  editingClauseId.value = null
}

const fillClauseForm = (record) => {
  clauseForm.law_name = record.law_name || ''
  clauseForm.clause_label = record.clause_label || ''
  clauseForm.full_title = record.full_title || ''
  clauseForm.content = record.content || ''
}

const fetchClauses = async (lawName) => {
  if (!lawName) {
    clauses.value = []
    return
  }

  detailLoading.value = true
  try {
    const res = await queryLawClauses({
      law_name: lawName,
      offset: 1,
      limit: 1000
    })
    clauses.value = res.data?.items || []
  } finally {
    detailLoading.value = false
  }
}

const syncSelectedLaw = async () => {
  if (!selectedLaw.value?.title) {
    clauses.value = []
    return
  }

  const nextSelected = dataSource.value.find((item) => item.title === selectedLaw.value.title)
  selectedLaw.value = nextSelected || null
  await fetchClauses(selectedLaw.value?.title)
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getLawDocs({
      offset: pagination.current,
      limit: pagination.pageSize,
      keyword: keyword.value
    })

    dataSource.value = res.data?.items || []
    pagination.total = res.data?.total || 0

    if (!selectedLaw.value && dataSource.value.length > 0) {
      selectedLaw.value = dataSource.value[0]
    } else if (selectedLaw.value) {
      const nextSelected = dataSource.value.find((item) => item.title === selectedLaw.value.title)
      selectedLaw.value = nextSelected || dataSource.value[0] || null
    }

    await fetchClauses(selectedLaw.value?.title)
  } finally {
    loading.value = false
  }
}

const selectLaw = async (record) => {
  selectedLaw.value = record
  await fetchClauses(record.title)
}

const searchLaw = () => {
  pagination.current = 1
  selectedLaw.value = null
  fetchData()
}

const openCreateDocumentModal = () => {
  modalMode.value = 'create'
  createScope.value = 'document'
  resetClauseForm()
  modalVisible.value = true
}

const openCreateClauseModal = () => {
  if (!selectedLaw.value?.title) {
    message.warning('请先选择一部法规，再新增条款')
    return
  }

  modalMode.value = 'create'
  createScope.value = 'clause'
  resetClauseForm()
  clauseForm.law_name = selectedLaw.value.title
  modalVisible.value = true
}

const openEditModal = (record) => {
  modalMode.value = 'update'
  createScope.value = 'clause'
  editingClauseId.value = record.id
  fillClauseForm(record)
  modalVisible.value = true
}

const onModalCancel = () => {
  modalVisible.value = false
  resetClauseForm()
  formRef.value?.resetFields()
}

const onModalOk = () => {
  formRef.value?.validateFields().then(async () => {
    saving.value = true
    const currentLawName = clauseForm.law_name
    try {
      if (modalMode.value === 'create') {
        await addLawClause({ ...clauseForm })
        message.success('法律条款新增成功')
      } else {
        await putLawClause(editingClauseId.value, { ...clauseForm })
        message.success('法律条款更新成功')
      }

      modalVisible.value = false
      resetClauseForm()
      formRef.value?.resetFields()

      if (keyword.value && !currentLawName.includes(keyword.value)) {
        keyword.value = ''
        pagination.current = 1
      }

      await fetchData()
    } finally {
      saving.value = false
    }
  })
}

const deleteClause = async (record) => {
  await delLawClause(record.id)
  message.success('条款已删除')
  await fetchData()
}

const deleteLawDocument = async (record) => {
  const res = await queryLawClauses({
    law_name: record.title,
    offset: 1,
    limit: 1000
  })
  const items = res.data?.items || []
  await Promise.all(items.map((item) => delLawClause(item.id)))
  message.success('法规及其条款已删除')

  if (selectedLaw.value?.title === record.title) {
    selectedLaw.value = null
    clauses.value = []
  }

  await fetchData()
}

const confirmDeleteClause = (record) => {
  Modal.confirm({
    title: '确认删除吗？',
    icon: createVNode(ExclamationCircleOutlined),
    content: `删除后将无法恢复：${record.clause_label || record.full_title}`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    onOk: () => deleteClause(record)
  })
}

const confirmDeleteLawDocument = (record) => {
  Modal.confirm({
    title: '确认删除吗？',
    icon: createVNode(ExclamationCircleOutlined),
    content: `删除后将移除《${record.title}》下的全部条款。`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    onOk: () => deleteLawDocument(record)
  })
}

onMounted(fetchData)
</script>

<template>
  <div class="law-page">
    <div class="hero">
      <div>
        <h2>法律文件库管理</h2>
        <p>管理法规条款原文，作为后续规则提炼和审核依据维护的输入数据。</p>
      </div>
      <div class="hero-actions">
        <a-input-search
          v-model:value="keyword"
          class="search"
          placeholder="搜索法规名称"
          allow-clear
          @search="searchLaw"
        />
        <a-button type="primary" @click="openCreateDocumentModal">新增法律文件</a-button>
      </div>
    </div>

    <div class="stats">
      <a-card v-for="item in lawStats" :key="item.label" size="small">
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value">{{ item.value }}</div>
      </a-card>
    </div>

    <div class="content">
      <a-card title="法规文件列表" class="list-card">
        <a-table
          :columns="columns"
          :data-source="dataSource"
          :pagination="pagination"
          :loading="loading"
          :row-key="(record) => record.id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-space>
                <a @click="selectLaw(record)">查看详情</a>
                <a class="danger-link" @click="confirmDeleteLawDocument(record)">删除法规</a>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card class="detail-card" title="法规详情">
        <template v-if="selectedLaw">
          <div class="detail-header">
            <div>
              <h3>{{ selectedLaw.title }}</h3>
              <div class="detail-subtitle">
                共 {{ selectedLaw.section_count || 0 }} 条
              </div>
            </div>
            <a-space>
              <a-tag color="blue">法规文件</a-tag>
              <a-button size="small" type="primary" ghost @click="openCreateClauseModal">
                新增条款
              </a-button>
            </a-space>
          </div>
          <div class="detail-meta">
            <span>条款数量：{{ selectedLaw.section_count || 0 }}</span>
            <span>关联规则数：{{ selectedLaw.rule_count || 0 }}</span>
          </div>
          <a-divider orientation="left">法规原文</a-divider>
          <a-spin :spinning="detailLoading">
            <div class="section-list">
              <section
                v-for="section in clauses"
                :key="section.id"
                class="section-block"
              >
                <div class="section-head">
                  <div>
                    <div class="section-label">{{ section.clause_label }}</div>
                    <h4 class="section-title">{{ section.full_title || section.clause_label }}</h4>
                  </div>
                  <a-space>
                    <a @click="openEditModal(section)">编辑</a>
                    <a class="danger-link" @click="confirmDeleteClause(section)">删除</a>
                  </a-space>
                </div>
                <div class="section-text">{{ section.content }}</div>
              </section>
            </div>
          </a-spin>
        </template>
        <a-empty v-else description="请选择左侧法规文件查看详情" />
      </a-card>
    </div>

    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="saving"
      @ok="onModalOk"
      @cancel="onModalCancel"
    >
      <a-form ref="formRef" :model="clauseForm" :rules="clauseRules" layout="vertical">
        <a-form-item name="law_name" label="法规名称">
          <a-input
            v-model:value="clauseForm.law_name"
            placeholder="例如：住宅专项维修资金管理办法"
            :disabled="modalMode === 'update' || createScope === 'clause'"
          />
        </a-form-item>
        <a-form-item name="clause_label" label="条款编号">
          <a-input v-model:value="clauseForm.clause_label" placeholder="例如：第十三条" />
        </a-form-item>
        <a-form-item name="full_title" label="完整标题">
          <a-input v-model:value="clauseForm.full_title" placeholder="例如：第十三条 专项维修资金的用途" />
        </a-form-item>
        <a-form-item name="content" label="条款内容">
          <a-textarea
            v-model:value="clauseForm.content"
            :rows="6"
            placeholder="请输入条款正文"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.law-page {
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
  background: linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
}

.hero h2,
.detail-header h3 {
  margin: 0;
}

.hero p {
  margin: 8px 0 0;
  color: #5b6475;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search {
  width: min(320px, 100%);
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
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  min-width: 0;
}

.list-card,
.detail-card {
  min-height: 520px;
}

.list-card,
.detail-card,
.content > * {
  min-width: 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.detail-subtitle,
.detail-meta {
  color: #6b7280;
}

.detail-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-block {
  padding: 16px;
  border: 1px solid #edf1f7;
  border-radius: 12px;
  background: #fbfcfe;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.section-label {
  font-size: 12px;
  color: #7c8596;
}

.section-title {
  margin: 6px 0 0;
}

.section-text {
  margin-top: 12px;
  white-space: pre-wrap;
  line-height: 1.75;
  color: #2f3a4d;
}

.danger-link {
  color: #d14343;
}

@media (max-width: 960px) {
  .content {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
