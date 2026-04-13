import request from '@/utils/request'

export function getLawDocs(params) {
  return request({
    url: '/audit/laws',
    params: {
      offset: params?.offset || 1,
      limit: params?.limit || 10,
      keyword: params?.keyword || ''
    }
  })
}

export function queryLawClauses(data) {
  return request({
    url: '/audit/law-clauses/query',
    method: 'post',
    data: {
      offset: data?.offset || 1,
      limit: data?.limit || 1000,
      law_name: data?.law_name || '',
      clause_label: data?.clause_label || '',
      full_title: data?.full_title || ''
    }
  })
}

export function addLawClause(data) {
  return request({
    url: '/audit/law-clauses',
    method: 'post',
    data
  })
}

export function putLawClause(id, data) {
  return request({
    url: `/audit/law-clauses/${id}`,
    method: 'put',
    data
  })
}

export function delLawClause(id) {
  return request({
    url: `/audit/law-clauses/${id}`,
    method: 'delete'
  })
}
