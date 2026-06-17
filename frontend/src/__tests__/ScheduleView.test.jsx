import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ScheduleView from '../components/ScheduleView'
import * as api from '../services/api'

vi.mock('../services/api')

const sampleSchedules = [
  { time: '08:00', days: ['lunes', 'martes', 'miércoles'], message: 'Pastilla mañana', enabled: true },
  { time: '20:00', days: ['lunes', 'martes', 'miércoles', 'jueves', 'viernes'], message: 'Pastilla noche', enabled: false },
]

describe('ScheduleView', () => {
  beforeEach(() => {
    api.updateSchedules.mockResolvedValue({ schedules: sampleSchedules })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders schedule list from props', () => {
    render(<ScheduleView schedules={sampleSchedules} onUpdate={vi.fn()} />)
    expect(screen.getByDisplayValue('08:00')).toBeInTheDocument()
    expect(screen.getByDisplayValue('20:00')).toBeInTheDocument()
  })

  it('shows validation error when time is not HH:MM zero-padded (e.g. "8:00" is invalid)', async () => {
    const user = userEvent.setup()
    render(<ScheduleView schedules={sampleSchedules} onUpdate={vi.fn()} />)

    // Find first time input and clear+type invalid value
    const timeInputs = screen.getAllByDisplayValue(/^\d{2}:\d{2}$/)
    await user.clear(timeInputs[0])
    await user.type(timeInputs[0], '8:00')

    // Find and click save button
    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/formato/i)).toBeInTheDocument()
    })

    // API should NOT have been called
    expect(api.updateSchedules).not.toHaveBeenCalled()
  })

  it('accepts "08:00" as valid time format', async () => {
    const user = userEvent.setup()
    const onUpdate = vi.fn()
    render(<ScheduleView schedules={sampleSchedules} onUpdate={onUpdate} />)

    // Find save button and click with valid data
    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    // API should have been called
    await waitFor(() => {
      expect(api.updateSchedules).toHaveBeenCalled()
    })
  })

  it('shows 422 error message when API returns 422', async () => {
    const user = userEvent.setup()
    api.updateSchedules.mockRejectedValue({ status: 422, message: 'Formato de hora inválido' })

    render(<ScheduleView schedules={sampleSchedules} onUpdate={vi.fn()} />)

    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/422|inválido|error/i)).toBeInTheDocument()
    })
  })

  it('calls updateSchedules with correct payload on save', async () => {
    const user = userEvent.setup()
    const onUpdate = vi.fn()
    render(<ScheduleView schedules={sampleSchedules} onUpdate={onUpdate} />)

    const saveButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(api.updateSchedules).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ time: '08:00' }),
        ])
      )
    })
  })
})
