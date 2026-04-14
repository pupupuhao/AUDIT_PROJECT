import request from '@/utils/request'

export function judgeAuditEngine(payload) {
  return request({
    url: '/audit/engine/judge',
    method: 'post',
    data: payload
  })
}
