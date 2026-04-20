import request from '@/utils/request'

export function judgeAuditEngine(payload) {
  return request({
    url: '/audit/engine/judge',
    method: 'post',
    data: payload
  })
}

function buildFilesFormData(files) {
  const formData = new FormData()
  ;(files || []).forEach((file) => {
    formData.append('files', file)
  })
  return formData
}

export function parseAuditFiles(files) {
  return request({
    url: '/audit/engine/files/parse',
    method: 'post',
    data: buildFilesFormData(files)
  })
}

export function judgeAuditFiles(files, params = {}) {
  return request({
    url: '/audit/engine/files/judge',
    method: 'post',
    params,
    data: buildFilesFormData(files)
  })
}
