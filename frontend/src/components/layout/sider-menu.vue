<script setup>
import { useRouter } from 'vue-router'
import { userStore } from '@/stores/user'

const store = userStore()
const router = useRouter()

// 菜单点击事件
const menuClick = (menu) => {
  router.push(menu.path)
}

const externalMenu = {
  id: 'external-local-app',
  name: '前往审核',
  icon: 'LinkOutlined',
  path: '/main/audit-engine/judge'
}
</script>

<template>
  <div class="sider-menu">
    <div class="brand">
      <div class="brand-title">审计规则管理系统</div>
    </div>
    <a-menu theme="dark" mode="inline" v-model:selectedKeys="store.selectKey">
      <template v-for="menu in store.userMenus" :key="menu.id">
        <!-- 0 目录 顶层菜单 -->
        <template v-if="menu.type === 0">
          <a-sub-menu :key="menu.id">
            <template #icon>
              <component :is="$loadIconCpn(menu.icon)"></component>
            </template>
            <template #title>{{ menu.name }}</template>
            <!-- 1 组件 子菜单项 -->
            <template v-for="sub in menu.children" :key="sub.id">
              <a-menu-item v-if="!sub.hidden" :key="sub.id" @click="menuClick(sub)">
                <template #icon>
                  <component :is="$loadIconCpn(sub.icon)"></component>
                </template>
                <span>{{ sub.name }}</span>
              </a-menu-item>
            </template>
          </a-sub-menu>
        </template>
      </template>
      <a-menu-item :key="externalMenu.id" @click="menuClick(externalMenu)">
        <template #icon>
          <component :is="$loadIconCpn(externalMenu.icon)"></component>
        </template>
        <span>{{ externalMenu.name }}</span>
      </a-menu-item>
    </a-menu>
  </div>
</template>

<style scoped>
.sider-menu {
  height: 100%;
  padding: 14px 12px 16px;
  background: linear-gradient(180deg, #071a2d 0%, #0a2238 100%);
}

.brand {
  margin: 6px 8px 18px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
}

.brand-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.96);
  line-height: 1.4;
}

.brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.58);
  letter-spacing: 0.04em;
}

:deep(.ant-menu) {
  border-inline-end: none !important;
  background: transparent !important;
}

:deep(.ant-menu-item),
:deep(.ant-menu-submenu-title) {
  outline: none !important;
  height: 42px !important;
  line-height: 42px !important;
  margin: 6px 0 !important;
  border-radius: 10px !important;
  width: 100% !important;
  background: transparent !important;
  padding-inline: 16px !important;
}

:deep(.ant-menu-item:focus-visible),
:deep(.ant-menu-submenu-title:focus-visible) {
  outline: none !important;
  box-shadow: none !important;
}

:deep(.ant-menu-dark .ant-menu-item),
:deep(.ant-menu-dark .ant-menu-submenu-title) {
  color: rgba(255, 255, 255, 0.9) !important;
}

:deep(.ant-menu-dark .ant-menu-item:hover),
:deep(.ant-menu-dark .ant-menu-submenu-title:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}

:deep(.ant-menu-item-selected) {
  box-shadow: none !important;
  background: rgba(255, 255, 255, 0.1) !important;
}

:deep(.ant-menu-dark .ant-menu-item-selected::after) {
  display: none !important;
}

:deep(.ant-menu-sub.ant-menu-inline) {
  background: transparent !important;
}

:deep(.ant-menu-submenu-arrow) {
  color: rgba(255, 255, 255, 0.7) !important;
}

:deep(.ant-menu-title-content) {
  min-width: 0;
}
</style>
