const BASE = import.meta.env.VITE_API_URL || ''

function token() {
  return localStorage.getItem('safewatch_token')
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && token()) headers.Authorization = `Bearer ${token()}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    data = null
  }

  if (!res.ok) {
    const message =
      data?.error || (data?.errors && data.errors.join(', ')) || `Request failed (${res.status})`
    const err = new Error(message)
    err.status = res.status
    err.details = data
    throw err
  }
  return data
}

export const api = {
  health: () => request('/api/health', { auth: false }),

  register: (payload) => request('/api/auth/register', { method: 'POST', body: payload, auth: false }),
  login: (payload) => request('/api/auth/login', { method: 'POST', body: payload, auth: false }),
  me: () => request('/api/auth/me'),
  updateProfile: (payload) => request('/api/auth/profile', { method: 'PUT', body: payload }),
  myIncidents: () => request('/api/users/me/incidents'),

  listIncidents: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null)
    ).toString()
    return request(`/api/incidents${qs ? `?${qs}` : ''}`, { auth: false })
  },
  getIncident: (id) => request(`/api/incidents/${id}`, { auth: false }),
  createIncident: (payload) => request('/api/incidents', { method: 'POST', body: payload }),
  updateIncident: (id, payload) => request(`/api/incidents/${id}`, { method: 'PUT', body: payload }),
  moderateIncident: (id, status) =>
    request(`/api/incidents/${id}/status`, { method: 'PUT', body: { status } }),
  deleteIncident: (id) => request(`/api/incidents/${id}`, { method: 'DELETE' }),
  taxonomy: () => request('/api/meta/taxonomy', { auth: false }),

  listAlerts: (area) => request(`/api/alerts${area ? `?area=${encodeURIComponent(area)}` : ''}`, { auth: false }),
  checkAlerts: () => request('/api/alerts/check', { method: 'POST' }),
  createAlert: (payload) => request('/api/alerts', { method: 'POST', body: payload }),

  analytics: () => request('/api/analytics', { auth: false }),
  adminStats: () => request('/api/admin/stats'),
  adminReports: () => request('/api/admin/reports'),
}

export default api
