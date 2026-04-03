/// <reference types="vite/client" />

// 告诉 TypeScript：所有的 .vue 文件都是 Vue 组件，不要再报错了
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 解决 element-plus 的类型识别问题
declare module 'element-plus'
declare module 'vue'
declare module '@element-plus/icons-vue'
