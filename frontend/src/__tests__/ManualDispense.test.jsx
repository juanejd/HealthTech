import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ManualDispense from '../components/ManualDispense'
import * as api from '../services/api'

vi.mock('../services/api')

describe('ManualDispense', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows dispense button initially', () => {
    render(<ManualDispense />)
    expect(screen.getByRole('button', { name: /dispensar/i })).toBeInTheDocument()
  })

  it('clicking button shows confirmation dialog (does NOT immediately POST)', async () => {
    const user = userEvent.setup()
    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    expect(screen.getByText(/confirmar/i)).toBeInTheDocument()
    expect(api.dispense).not.toHaveBeenCalled()
  })

  it('canceling dialog hides it without calling dispense API', async () => {
    const user = userEvent.setup()
    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    // Dialog should be visible
    expect(screen.getByText(/confirmar/i)).toBeInTheDocument()

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancelar/i })
    await user.click(cancelButton)

    // Dialog should be gone
    expect(screen.queryByText(/confirmar/i)).not.toBeInTheDocument()
    expect(api.dispense).not.toHaveBeenCalled()
  })

  it('confirming dialog calls dispense API', async () => {
    const user = userEvent.setup()
    api.dispense.mockResolvedValue({ status: 'OK', extraction_detected: true, timestamp: '2024-01-01T00:00:00Z' })

    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(api.dispense).toHaveBeenCalledTimes(1)
    })
  })

  it('shows loading state while request is pending', async () => {
    const user = userEvent.setup()
    let resolveDispense
    api.dispense.mockReturnValue(new Promise((resolve) => { resolveDispense = resolve }))

    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    // Loading state should be visible
    await waitFor(() => {
      expect(screen.getByText(/cargando|espere|enviando/i)).toBeInTheDocument()
    })

    // Resolve the promise
    resolveDispense({ status: 'OK', extraction_detected: true, timestamp: '2024-01-01' })
  })

  it('shows "OK" result after successful dispense', async () => {
    const user = userEvent.setup()
    api.dispense.mockResolvedValue({ status: 'OK', extraction_detected: true, timestamp: '2024-01-01T00:00:00Z' })

    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(screen.getByText(/OK/)).toBeInTheDocument()
    })
  })

  it('shows "FAIL" result when dispense returns FAIL status', async () => {
    const user = userEvent.setup()
    api.dispense.mockResolvedValue({ status: 'FAIL', extraction_detected: false, timestamp: '2024-01-01T00:00:00Z' })

    render(<ManualDispense />)

    const button = screen.getByRole('button', { name: /dispensar/i })
    await user.click(button)

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(screen.getByText(/FAIL/)).toBeInTheDocument()
    })
  })
})
