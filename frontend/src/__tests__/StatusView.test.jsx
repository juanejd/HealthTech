import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusView from '../components/StatusView'

vi.mock('../services/api')

describe('StatusView', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state when data is null', () => {
    render(<StatusView status={null} />)
    expect(screen.getByText(/cargando/i)).toBeInTheDocument()
  })

  it('renders status correctly when next_event is null (no crash)', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: true,
      wifi_connected: true,
    }
    render(<StatusView status={status} />)
    // Should not crash and should render something meaningful
    expect(screen.getByText(/telegram/i)).toBeInTheDocument()
  })

  it('renders status correctly when last_event is null (no crash)', () => {
    const status = {
      current_day: 2,
      compartment_index: 1,
      next_event: { time: '08:00', message: 'Tomar pastilla' },
      last_event: null,
      telegram_connected: false,
      wifi_connected: true,
    }
    render(<StatusView status={status} />)
    expect(screen.getByText(/telegram/i)).toBeInTheDocument()
  })

  it('shows green indicator when telegram_connected is true', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: true,
      wifi_connected: false,
    }
    render(<StatusView status={status} />)
    const indicators = document.querySelectorAll('[data-testid="telegram-indicator"]')
    expect(indicators.length).toBeGreaterThan(0)
    expect(indicators[0].className).toMatch(/green/i)
  })

  it('shows red indicator when telegram_connected is false', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: false,
      wifi_connected: true,
    }
    render(<StatusView status={status} />)
    const indicators = document.querySelectorAll('[data-testid="telegram-indicator"]')
    expect(indicators.length).toBeGreaterThan(0)
    expect(indicators[0].className).toMatch(/red/i)
  })

  it('shows green indicator when wifi_connected is true', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: false,
      wifi_connected: true,
    }
    render(<StatusView status={status} />)
    const indicators = document.querySelectorAll('[data-testid="wifi-indicator"]')
    expect(indicators.length).toBeGreaterThan(0)
    expect(indicators[0].className).toMatch(/green/i)
  })

  it('shows red indicator when wifi_connected is false', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: null,
      telegram_connected: true,
      wifi_connected: false,
    }
    render(<StatusView status={status} />)
    const indicators = document.querySelectorAll('[data-testid="wifi-indicator"]')
    expect(indicators.length).toBeGreaterThan(0)
    expect(indicators[0].className).toMatch(/red/i)
  })

  it('shows last_event.status with color when last_event is present', () => {
    const status = {
      current_day: 1,
      compartment_index: 0,
      next_event: null,
      last_event: {
        timestamp: '2024-01-01T08:00:00Z',
        status: 'OK',
        extraction_detected: true,
      },
      telegram_connected: true,
      wifi_connected: true,
    }
    render(<StatusView status={status} />)
    const lastEventStatus = document.querySelector('[data-testid="last-event-status"]')
    expect(lastEventStatus).toBeInTheDocument()
    expect(lastEventStatus.textContent).toMatch(/OK/i)
    expect(lastEventStatus.className).toMatch(/green/i)
  })
})
