const API_BASE = 'http://127.0.0.1:8000/api'

export async function login(payload) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchTickets(role, email) {
  const params = new URLSearchParams({ role })
  if (email) params.set('email', email)
  return request(`/tickets?${params.toString()}`)
}

export async function fetchDashboard() {
  return request('/dashboard')
}

export async function createTicket(payload) {
  return request('/tickets', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateTicket(ticketId, payload) {
  return request(`/tickets/${ticketId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

async function request(path, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    })
  } catch (error) {
    throw new Error('Backend not reachable. Start the FastAPI server on http://127.0.0.1:8000 and try again.')
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || 'Request failed')
  }

  return response.json()
}
