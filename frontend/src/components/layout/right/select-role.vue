<script setup>
import { computed, ref, watch } from 'vue'
import { userStore } from '@/stores/user'
import { message } from 'ant-design-vue'

const store = userStore()

const visible = ref(false)
const currentRoleId = ref()

// 角色列表选项
const options = computed(() => {
  return (store.userInfo.roles || []).map((role) => ({
    label: role.name,
    value: role.id
  }))
})

watch(
  visible,
  (newValue) => {
    if (newValue) {
      currentRoleId.value = store.userInfo.roles?.[0]?.id
    }
  },
  { immediate: true }
)

const handleOk = async () => {
  if (!currentRoleId.value || currentRoleId.value === store.userInfo.roles?.[0]?.id) {
    visible.value = false
    return
  }

  await store.userSelectRole(currentRoleId.value)
  message.success('角色切换成功')
  visible.value = false
}

const handleCancel = () => {
  visible.value = false
}

defineExpose({
  visible
})
</script>

<template>
  <div class="select-role">
    <a-modal v-model:visible="visible" title="切换角色">
      <template #footer>
        <a-button key="back" @click="handleCancel">取消</a-button>
        <a-button
          key="submit"
          type="primary"
          @click="handleOk"
          :disabled="currentRoleId === store.userInfo.roles?.[0]?.id"
          >确定</a-button
        >
      </template>
      <span>选择角色：</span>

      <a-space direction="vertical">
        <a-select
          v-model:value="currentRoleId"
          size="default"
          style="width: 400px"
          :options="options"
        ></a-select>
      </a-space>
    </a-modal>
  </div>
</template>

<style scoped></style>
