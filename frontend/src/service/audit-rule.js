import request from '@/utils/request'

export function getAuditRules(params) {
  return request({
    url: '/audit/rules',
    params
  })
}
