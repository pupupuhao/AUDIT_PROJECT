import request from '@/utils/request'

export function getComplianceRules(params) {
  return request({
    url: '/compliance/rules',
    params
  })
}

export function addComplianceRule(data) {
  return request({
    url: '/compliance/rules',
    method: 'post',
    data
  })
}

export function putComplianceRule(id, data) {
  return request({
    url: `/compliance/rules/${id}`,
    method: 'put',
    data
  })
}

export function delComplianceRule(id) {
  return request({
    url: `/compliance/rules/${id}`,
    method: 'delete'
  })
}
