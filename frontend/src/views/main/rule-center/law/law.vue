<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  BookOutlined,
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  LinkOutlined,
  PlusOutlined,
  UnorderedListOutlined
} from '@ant-design/icons-vue'
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
    width: 80
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
    { label: '法规文件总数', value: totalDocs, tone: 'blue', icon: BookOutlined },
    { label: '本页条款数量', value: totalSections, tone: 'gold', icon: UnorderedListOutlined },
    { label: '本页关联规则数', value: totalRules, tone: 'slate', icon: LinkOutlined }
  ]
})

const detailMetaItems = computed(() => {
  if (!selectedLaw.value) return []

  return [
    { label: '条款数量', value: selectedLaw.value.section_count || 0, half: true },
    { label: '关联规则数', value: selectedLaw.value.rule_count || 0, half: true }
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

function onTableRow(record) {
  return {
    onClick: () => {
      selectLaw(record)
    }
  }
}

function tableRowClassName(record) {
  return selectedLaw.value?.title === record.title ? 'law-row-selected' : ''
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
      <div class="hero-copy">
        <h2>法律文件库管理</h2>
        <p>管理法规条款原文，作为后续规则提炼和审核依据维护的输入数据。</p>
      </div>
      <div class="hero-actions">
        <a-button class="page-action-button" v-per="'law:create'" @click="openCreateDocumentModal">
          新增法律文件
        </a-button>
        <a-input-search
          v-model:value="keyword"
          class="search"
          placeholder="搜索法规名称"
          allow-clear
          @search="searchLaw"
        />
      </div>
    </div>

    <div class="stats">
      <a-card v-for="item in lawStats" :key="item.label" size="small">
        <div class="stat-card">
          <div class="stat-icon" :class="`stat-icon--${item.tone}`">
            <component :is="item.icon" />
          </div>
          <div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value" :class="`stat-value--${item.tone}`">{{ item.value }}</div>
          </div>
        </div>
      </a-card>
    </div>

    <div class="content">
      <a-card class="list-card">
        <template #title>
          <span class="card-title">法规文件列表</span>
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
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <div class="row-actions">
                <button
                  v-per="'law:delete'"
                  type="button"
                  class="icon-action-button icon-action-button--delete"
                  @click.stop="confirmDeleteLawDocument(record)"
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
          <span class="card-title">法规详情</span>
        </template>
        <template v-if="selectedLaw">
          <div class="detail-header">
            <div>
              <div class="detail-kicker">详情</div>
              <h3>{{ selectedLaw.title }}</h3>
            </div>
            <a-space>
              <a-button
                class="page-action-button"
                v-per="'law:create'"
                @click="openCreateClauseModal"
              >
                <template #icon><PlusOutlined /></template>
                新增条款
              </a-button>
            </a-space>
          </div>
          <div class="detail-meta-grid">
            <article
              v-for="item in detailMetaItems"
              :key="item.label"
              class="logic-item"
              :class="{ 'logic-item--half': item.half }"
            >
              <div class="logic-item__label">{{ item.label }}</div>
              <div class="logic-item__value">{{ item.value }}</div>
            </article>
          </div>
          <section class="detail-section">
            <div class="section-heading">
              <span class="section-heading__bar"></span>
              <span>法规条款</span>
            </div>
            <a-spin :spinning="detailLoading">
              <div class="section-list">
                <section
                  v-for="section in clauses"
                  :key="section.id"
                  class="section-block"
                >
                  <div class="section-head">
                    <div>
                      <div class="section-label">{{ section.clause_label || '-' }}</div>
                      <h4 class="section-title">{{ section.full_title || section.clause_label }}</h4>
                    </div>
                    <div class="row-actions">
                      <button
                        v-per="'law:update'"
                        type="button"
                        class="icon-action-button icon-action-button--edit"
                        @click.stop="openEditModal(section)"
                      >
                        <EditOutlined />
                      </button>
                      <button
                        v-per="'law:delete'"
                        type="button"
                        class="icon-action-button icon-action-button--delete"
                        @click.stop="confirmDeleteClause(section)"
                      >
                        <DeleteOutlined />
                      </button>
                    </div>
                  </div>
                  <div class="detail-surface">
                    <div class="section-text">{{ section.content }}</div>
                  </div>
                </section>
              </div>
            </a-spin>
          </section>
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
  gap: 20px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  padding: 26px 28px;
  border: 1px solid #dfeaf8;
  border-radius: 20px;
  background: linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
  box-shadow: 0 18px 44px rgba(22, 119, 255, 0.08);
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
  color: #5b6475;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
  flex-wrap: nowrap;
}

.search {
  width: 320px;
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

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 999px;
  font-size: 20px;
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

.content {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(360px, 1fr);
  gap: 20px;
  min-width: 0;
  align-items: start;
}

.list-card,
.detail-card {
  min-height: 520px;
  border-radius: 20px;
}

.list-card,
.detail-card,
.content > * {
  min-width: 0;
}

.list-card {
  border: 1px solid #e8edf5;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.detail-card {
  position: sticky;
  top: 24px;
  border: 1px solid #dbeafe;
  box-shadow: 0 22px 52px rgba(37, 99, 235, 0.08);
}

.list-card :deep(.ant-card-head),
.detail-card :deep(.ant-card-head) {
  min-height: 64px;
  border-bottom: 1px solid #eef2f6;
}

.list-card :deep(.ant-card-head-title),
.detail-card :deep(.ant-card-head-title) {
  padding: 18px 0;
}

.list-card :deep(.ant-card-body),
.detail-card :deep(.ant-card-body) {
  padding: 0;
}

.card-title {
  font-weight: 700;
  color: #1f2a44;
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

.list-card :deep(.ant-table-tbody > tr.law-row-selected > td) {
  background: #f4f8ff;
}

.list-card :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fbff;
}

.list-card :deep(.ant-pagination) {
  padding: 16px 20px 18px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 24px 24px 12px;
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

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 0 24px 18px;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.section-block {
  padding: 16px;
  border: 1px solid #edf2f7;
  border-radius: 16px;
  background: #ffffff;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.section-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 700;
}

.section-title {
  margin: 6px 0 0;
  color: #1e293b;
}

.detail-surface {
  margin-top: 12px;
  padding: 16px;
  border: 1px solid #edf2f7;
  border-radius: 16px;
  background: #f8fafc;
}

.section-text {
  white-space: pre-wrap;
  line-height: 1.75;
  color: #2f3a4d;
}

.logic-item {
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
  .content {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .detail-card {
    position: static;
  }

  .detail-meta-grid {
    grid-template-columns: 1fr;
  }

  .search {
    width: 100%;
  }
}
</style>
