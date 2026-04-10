<script setup>
import { computed, onMounted, ref } from 'vue'

const targetUrl = (import.meta.env.VITE_AUDIT_JUDGE_URL || '').trim()
const hasTarget = computed(() => Boolean(targetUrl))
const redirected = ref(false)

const jumpToTarget = () => {
  if (!targetUrl) return
  redirected.value = true
  window.open(targetUrl, '_blank', 'noopener,noreferrer')
}

onMounted(() => {
  if (!targetUrl) return
  window.setTimeout(jumpToTarget, 150)
})
</script>

<template>
  <div class="redirect-page">
    <a-card class="redirect-card" title="合规判定">
      <a-result
        v-if="hasTarget"
        status="info"
        title="正在跳转到本地审计系统"
        :sub-title="targetUrl"
      >
        <template #extra>
          <a-space>
            <a-button type="primary" @click="jumpToTarget">新标签页打开</a-button>
            <a-typography-text type="secondary">
              {{ redirected ? '如果没有自动打开，请点击按钮。' : '页面会自动在新标签页打开。' }}
            </a-typography-text>
          </a-space>
        </template>
      </a-result>

      <a-result
        v-else
        status="warning"
        title="未配置跳转地址"
        sub-title="请在前端环境变量中设置 VITE_AUDIT_JUDGE_URL"
      />
    </a-card>
  </div>
</template>

<style scoped>
.redirect-page {
  display: grid;
  place-items: center;
  min-height: 60vh;
}

.redirect-card {
  width: min(760px, 100%);
}
</style>
