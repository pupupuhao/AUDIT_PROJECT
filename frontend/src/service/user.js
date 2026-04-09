import request from '@/utils/request'

export function login(data) {
  return request({
    url: '/system/login',
    method: 'post',
    data
  })
}

// 获取用户信息
export function getUserInfo(uid) {
  return request({
    url: `/system/user/${uid}`
  })
}

// 获取权限信息
export function getMenus(rid) {
  return request({
    url: `/system/role/${rid}/menu`
  })
}

// 修改用户信息
export function selectRole(rid) {
  return request({
    url: `/system/user/role/${rid}`,
    method: 'put'
  })
}

// 获取用户列表
export function getUsers(params) {
  return request({
    url: '/system/user',
    params
  })
}

// 条件查询用户列表
export function queryUser(data) {
  return request({
    url: '/system/user/query',
    method: 'post',
    data
  })
}

//  删除用户
export function delUser(id) {
  return request({
    url: `/system/user/${id}`,
    method: 'delete'
  })
}

// 新增用户
export function addUser(data) {
  return request({
    url: '/system/user',
    method: 'post',
    data
  })
}

// 更新用户
export function putUser(id, data) {
  return request({
    url: `/system/user/${id}`,
    method: 'put',
    data
  })
}
