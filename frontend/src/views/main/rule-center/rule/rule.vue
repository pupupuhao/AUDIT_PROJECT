<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { getAuditRules } from '@/service/audit-rule'

const loading = ref(false)
const keyword = ref('')
const category = ref('')
const categories = ref([])
const selectedRule = ref(null)
const dataSource = ref([])

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
    width: 150
  },
  {
    title: '所属法规',
    dataIndex: 'law_name',
    key: 'law_name',
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
    width: 100
  }
]

const stats = computed(() => [
  { label: '规则总数', value: pagination.total },
  { label: '分类数量', value: categories.value.length },
  { label: '当前筛选', value: category.value || '全部' }
])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAuditRules({
      offset: pagination.current,
      limit: pagination.pageSize,
      keyword: keyword.value,
      category: category.value
    })
    dataSource.value = res.items || []
    categories.value = res.categories || []
    pagination.total = res.total || 0
    if (!selectedRule.value && dataSource.value.length > 0) {
      selectedRule.value = dataSource.value[0]
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

onMounted(fetchData)
</script>

<template>
  <div class="rule-page">
    <div class="hero">
      <div>
        <h2>审核规则管理</h2>
        <p>查看规则分类、来源法规和提炼后的判定逻辑，为后续审核流程接入做准备。</p>
      </div>
      <div class="filters">
        <a-select
          v-model:value="category"
          allow-clear
          placeholder="按分类筛选"
          style="width: 220px"
          @change="searchRules"
        >
          <a-select-option v-for="item in categories" :key="item" :value="item">
            {{ item }}
          </a-select-option>
        </a-select>
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
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'category'">
              <a-tag color="processing">{{ record.category }}</a-tag>
            </template>
            <template v-else-if="column.key === 'action'">
              <a @click="selectedRule = record">查看详情</a>
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
            <div class="category-badge">{{ selectedRule.category }}</div>
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
}
</style>
