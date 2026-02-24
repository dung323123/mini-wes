const API_KEY = 'mini_wes_api_base'
const DEFAULT_API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export function getApiBase() {
  return (localStorage.getItem(API_KEY) || DEFAULT_API_BASE).replace(/\/+$/, '')
}

export function setApiBase(url) {
  localStorage.setItem(API_KEY, url.replace(/\/+$/, ''))
}

export async function api(path, options = {}) {
  const res = await fetch(`${getApiBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch (_e) {}
    throw new Error(detail)
  }

  if (res.status === 204) return null
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text()
}
