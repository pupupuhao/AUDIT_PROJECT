<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { getLawDocs } from '@/service/law'

const loading = ref(false)
const selectedLaw = ref(null)
const keyword = ref('')
const dataSource = ref([])

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
    title: '类型',
    dataIndex: 'doc_type',
    key: 'doc_type',
    width: 120
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
    width: 100
  }
]

const lawStats = computed(() => {
  const totalDocs = pagination.total
  const totalSections = dataSource.value.reduce((sum, item) => sum + item.section_count, 0)
  const totalRules = dataSource.value.reduce((sum, item) => sum + item.rule_count, 0)
  return [
    { label: '当前法规文件', value: totalDocs },
    { label: '本页条款小节', value: totalSections },
    { label: '本页关联规则', value: totalRules }
  ]
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getLawDocs({
      offset: pagination.current,
      limit: pagination.pageSize,
      keyword: keyword.value
    })
    dataSource.value = res.items || []
    pagination.total = res.total || 0
    if (!selectedLaw.value && dataSource.value.length > 0) {
      selectedLaw.value = dataSource.value[0]
    }
  } finally {
    loading.value = false
  }
}

const searchLaw = () => {
  pagination.current = 1
  selectedLaw.value = null
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="law-page">
    <div class="hero">
      <div>
        <h2>法律文件库管理</h2>
        <p>管理法规原文、条款结构和作为审核依据的来源文件。</p>
      </div>
      <a-input-search
        v-model:value="keyword"
        class="search"
        placeholder="搜索法规名称"
        allow-clear
        @search="searchLaw"
      />
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
              <a @click="selectedLaw = record">查看详情</a>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card class="detail-card" title="文件详情">
        <template v-if="selectedLaw">
          <div class="detail-header">
            <h3>{{ selectedLaw.title }}</h3>
            <a-tag color="blue">{{ selectedLaw.doc_type }}</a-tag>
          </div>
          <div class="detail-meta">
            <span>条款小节：{{ selectedLaw.section_count }}</span>
            <span>关联规则：{{ selectedLaw.rule_count }}</span>
          </div>
          <a-collapse ghost>
            <a-collapse-panel
              v-for="section in selectedLaw.sections"
              :key="section.title"
              :header="section.title"
            >
              <div class="section-text">{{ section.content }}</div>
            </a-collapse-panel>
          </a-collapse>
        </template>
        <a-empty v-else description="请选择左侧法规文件查看详情" />
      </a-card>
    </div>
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

.search {
  width: min(320px, 100%);
  align-self: center;
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

.list-card :deep(.ant-card-body),
.detail-card :deep(.ant-card-body) {
  overflow: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.detail-meta {
  display: flex;
  gap: 16px;
  margin: 12px 0 16px;
  color: #5b6475;
}

.section-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #2f3542;
}

@media (max-width: 960px) {
  .hero,
  .content {
    grid-template-columns: 1fr;
    display: grid;
  }

  .search,
  .stats {
    width: 100%;
  }

  .stats {
    grid-template-columns: 1fr;
  }

  .detail-meta {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
