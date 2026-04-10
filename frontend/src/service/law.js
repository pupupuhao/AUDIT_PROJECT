import request from '@/utils/request'

export function getLawDocs(params) {
  return request({
    url: '/audit/laws',
    params
  })
}
