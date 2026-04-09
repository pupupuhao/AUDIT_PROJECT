// 动态加载组件
import * as icons from '@ant-design/icons-vue'
import router from '@/router'

/**
 * 动态加载antd icon
 * @param {*} iconName
 * @returns 组件对象
 * jsx：使用 h(loadIconCpn('UserField'))
 * template: 使用 <component :is="loadIconCpn("UserField")">
 */
function loadIconCpn(iconName) {
  return icons[iconName]
}

// 拿到views下所有.vue文件
const modules = import.meta.glob('../views/**/**.vue')

function normalizePath(value) {
  if (!value) return ''
  return value.startsWith('/') ? value : `/${value}`
}

function withVueExt(value) {
  return value.endsWith('.vue') ? value : `${value}.vue`
}

function resolveComponent(menu) {
  const candidates = []
  const component = normalizePath(menu.component || '')
  const routePath = normalizePath(menu.path || '')

  if (component) {
    const componentWithExt = withVueExt(component)
    candidates.push(`../views/main${componentWithExt}`)

    // 兼容数据库里写成 "user/user" 这类旧格式
    if (
      !component.startsWith('/system/') &&
      !component.startsWith('/audit/') &&
      !component.startsWith('/dashboard/') &&
      !component.startsWith('/test/')
    ) {
      candidates.push(`../views/main/system${componentWithExt}`)
    }
  }

  // 兼容只配了 path，没有正确 component 的情况
  if (routePath.startsWith('/main/')) {
    const routeWithExt = withVueExt(routePath)
    candidates.push(`../views${routeWithExt}`)

    const segments = routePath.split('/').filter(Boolean)
    const last = segments[segments.length - 1]
    if (last) {
      candidates.push(`../views${routePath}/${last}.vue`)
    }
  }

  for (const path of candidates) {
    if (modules[path]) {
      return modules[path]
    }
  }

  return modules['../views/error/404.vue']
}

function loadRouter(menus) {
  for (const menu of menus) {
    //   type 为1 菜单组件
    if (menu.type === 1 && menu.path !== '') {
      router.addRoute('main', {
        path: menu.path,
        name: menu.name,
        component: resolveComponent(menu),
        meta: menu.meta
      })
    } else if (menu.children) {
      loadRouter(menu.children)
    }
  }
}

// 获取按钮权限列表，和第一个选中菜单
function getPermissions(menuArr) {
  let arr = []
  let firstMenu = null

  function _forMenu(menus) {
    for (const menu of menus) {
      if (menu.type === 1 && firstMenu === null) {
        firstMenu = menu
      }
      if (menu.type !== 2 && menu.children) {
        _forMenu(menu.children)
      } else {
        arr.push(menu.identifier)
      }
    }
  }

  _forMenu(menuArr)
  return [arr.filter((e) => e !== null), firstMenu]
}

export { loadIconCpn, loadRouter, getPermissions }
