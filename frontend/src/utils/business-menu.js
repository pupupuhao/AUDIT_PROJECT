function cloneMenu(menu) {
  const next = { ...menu }
  if (Array.isArray(menu.children)) {
    next.children = menu.children.map(cloneMenu)
  }
  return next
}

function normalizeBusinessTree(menu) {
  const next = cloneMenu(menu)

  if (next.id === 10 || next.path === '/main/audit') {
    next.name = '业务管理'
    next.path = '/main/business'
  }

  if (next.id === 11 || next.path === '/main/audit/rules') {
    next.name = '法律文件库管理'
    next.path = '/main/business/law'
    next.component = 'rule-center/law/law'
    next.api = '/api/audit/rules'
    next.method = 'GET'
  }

  if (next.id === 12 || next.path === '/main/audit/search') {
    next.hidden = true
  }

  if (next.id === 13 || next.path === '/main/audit/judge') {
    next.name = '审核规则管理'
    next.path = '/main/business/rule'
    next.component = 'rule-center/rule/rule'
    next.api = '/api/audit/rules'
    next.method = 'GET'
  }

  if (Array.isArray(next.children)) {
    next.children = next.children.map(normalizeBusinessTree)
  }

  return next
}

export function normalizeBusinessMenus(menus) {
  return menus.map(normalizeBusinessTree)
}
