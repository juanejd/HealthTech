import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  fetchStatus,
  fetchSchedules,
  updateSchedules,
  fetchLogs,
  dispense,
  createWebSocket,
} from '../services/api'

const BASE_URL = 'http://localhost:8000'

describe('fetchStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls GET /api/status and returns parsed JSON', async () => {
    const mockData = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: true,
      wifi_connected: true,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const result = await fetchStatus()

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/api/status`)
    expect(result).toEqual(mockData)
  })
})

describe('fetchSchedules', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls GET /api/schedules and returns parsed JSON', async () => {
    const mockData = {
      schedules: [{ time: '08:00', days: [1, 2], message: 'Test', enabled: true }],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const result = await fetchSchedules()

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/api/schedules`)
    expect(result).toEqual(mockData)
  })
})

describe('updateSchedules', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls PUT /api/schedules with correct body and returns parsed JSON', async () => {
    const schedules = [{ time: '08:00', days: [1], message: 'Test', enabled: true }]
    const mockResponse = { schedules }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    }))

    const result = await updateSchedules(schedules)

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/api/schedules`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedules }),
    })
    expect(result).toEqual(mockResponse)
  })

  it('throws with status 422 when server returns 422', async () => {
    const schedules = [{ time: '8:00', days: ['lunes'], message: 'Test', enabled: true }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: () => Promise.resolve({ detail: 'Formato de hora inválido' }),
    }))

    await expect(updateSchedules(schedules)).rejects.toMatchObject({ status: 422 })
  })
})

describe('fetchLogs', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls GET /api/logs and returns parsed JSON', async () => {
    const mockData = {
      events: [{ timestamp: '2024-01-01T00:00:00Z', type: 'dispense', status: 'OK', extraction_detected: true, day: 1, compartment_index: 0 }],
      total: 1,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const result = await fetchLogs()

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/api/logs`)
    expect(result).toEqual(mockData)
  })
})

describe('dispense', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls POST /api/dispense and returns parsed JSON', async () => {
    const mockData = { status: 'OK', extraction_detected: true, timestamp: '2024-01-01T00:00:00Z' }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const result = await dispense()

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/api/dispense`, {
      method: 'POST',
    })
    expect(result).toEqual(mockData)
  })
})

describe('createWebSocket', () => {
  let MockWebSocket
  let instances

  beforeEach(() => {
    instances = []
    MockWebSocket = class {
      constructor(url) {
        this.url = url
        this.onopen = null
        this.onmessage = null
        this.onclose = null
        this.onerror = null
        this.readyState = 0
        instances.push(this)
      }
      close() {
        this.readyState = 3
      }
    }
    vi.stubGlobal('WebSocket', MockWebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('returns object with ws and close properties', () => {
    const onMessage = vi.fn()
    const result = createWebSocket(onMessage)

    expect(result).toHaveProperty('ws')
    expect(result).toHaveProperty('close')
    expect(typeof result.close).toBe('function')
  })

  it('creates WebSocket with correct URL derived from BASE_URL', () => {
    const onMessage = vi.fn()
    createWebSocket(onMessage)

    expect(instances.length).toBeGreaterThan(0)
    expect(instances[0].url).toBe('ws://localhost:8000/ws/status')
  })

  it('auto-reconnects after 3 seconds on close', () => {
    vi.useFakeTimers()
    const onMessage = vi.fn()
    createWebSocket(onMessage)

    expect(instances.length).toBe(1)

    // Simulate close event
    instances[0].onclose && instances[0].onclose()

    // Before timeout, no reconnect
    vi.advanceTimersByTime(2999)
    expect(instances.length).toBe(1)

    // After 3 seconds, reconnect
    vi.advanceTimersByTime(1)
    expect(instances.length).toBe(2)
  })

  it('calls onMessage callback when message received', () => {
    const onMessage = vi.fn()
    createWebSocket(onMessage)

    const messageData = { status: 'OK', extraction_detected: true, timestamp: '2024-01-01' }
    instances[0].onmessage && instances[0].onmessage({ data: JSON.stringify(messageData) })

    expect(onMessage).toHaveBeenCalledWith(messageData)
  })
})
