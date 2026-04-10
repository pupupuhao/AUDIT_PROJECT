<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import { userStore } from '@/stores/user'

const route = useRoute()
const store = userStore()

function findMenuTrail(menus, path, parents = []) {
  for (const menu of menus) {
    const trail = [...parents, menu]
    if (menu.path === path) {
      return trail
    }
    if (menu.children?.length) {
      const result = findMenuTrail(menu.children, path, trail)
      if (result.length) {
        return result
      }
    }
  }
  return []
}

const crumbs = computed(() => {
  if (route.path === '/main') {
    return ['首页']
  }

  const menus = store.userMenus || []
  const trail = findMenuTrail(menus, route.path)
    .filter((item) => item.type !== 2 && !item.hidden)
    .map((item) => item.name)

  return trail.length ? trail : ['首页']
})
</script>

<template>
  <div class="crumb">
    <a-breadcrumb>
      <template v-for="item in crumbs" :key="item">
        <a-breadcrumb-item>
          {{ item }}
        </a-breadcrumb-item>
      </template>
    </a-breadcrumb>
  </div>
</template>

<style scoped>
.crumb {
  display: flex;
  align-items: center;
  margin-left: 16px;
  font-size: 10px;
}
</style>
