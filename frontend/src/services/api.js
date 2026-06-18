const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function fetchStatus() {
  const response = await fetch(`${BASE_URL}/api/status`)
  return response.json()
}

export async function fetchSchedules() {
  const response = await fetch(`${BASE_URL}/api/schedules`)
  return response.json()
}

export async function updateSchedules(schedules) {
  const response = await fetch(`${BASE_URL}/api/schedules`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ schedules }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const err = new Error(body?.detail || `HTTP ${response.status}`)
    err.status = response.status
    err.body = body
    throw err
  }
  return response.json()
}

export async function fetchLogs() {
  const response = await fetch(`${BASE_URL}/api/logs`)
  return response.json()
}

export async function dispense() {
  const response = await fetch(`${BASE_URL}/api/dispense`, {
    method: 'POST',
  })
  return response.json()
}

export async function fetchDiagnosticStep() {
  const response = await fetch(`${BASE_URL}/api/diagnostic/step`, {
    method: 'POST',
  })
  return response.json()
}

export async function fetchDiagnosticHome() {
  const response = await fetch(`${BASE_URL}/api/diagnostic/home`, {
    method: 'POST',
  })
  return response.json()
}

export async function fetchDiagnosticWeight() {
  const response = await fetch(`${BASE_URL}/api/diagnostic/weight`)
  return response.json()
}

export function createWebSocket(onMessage, onOpen, onClose) {
  const wsUrl = BASE_URL.replace(/^http/, 'ws') + '/ws/status'
  let ws
  let closed = false

  function connect() {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      if (onOpen) onOpen()
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (onMessage) onMessage(data)
    }

    ws.onclose = () => {
      if (onClose) onClose()
      if (!closed) {
        setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      // error handling — close will fire after this
    }
  }

  connect()

  return {
    get ws() {
      return ws
    },
    close() {
      closed = true
      if (ws) ws.close()
    },
  }
}
