import { useState } from 'react'
import { updateSchedules } from '../services/api'

const TIME_REGEX = /^\d{2}:\d{2}$/

// API uses string day names — must match exactly
const DAY_NAMES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']

function ScheduleRow({ schedule, index, onChange }) {
  return (
    <div className="schedule-row">
      <input
        type="text"
        value={schedule.time}
        onChange={(e) => onChange(index, 'time', e.target.value)}
        placeholder="HH:MM"
        aria-label={`Hora del horario ${index + 1}`}
      />
      <input
        type="text"
        value={schedule.message}
        onChange={(e) => onChange(index, 'message', e.target.value)}
        placeholder="Mensaje"
        aria-label={`Mensaje del horario ${index + 1}`}
      />
      <label>
        <input
          type="checkbox"
          checked={schedule.enabled}
          onChange={(e) => onChange(index, 'enabled', e.target.checked)}
        />
        Activo
      </label>
      <div className="schedule-days">
        {DAY_NAMES.map((day) => (
          <label key={day}>
            <input
              type="checkbox"
              checked={Array.isArray(schedule.days) && schedule.days.includes(day)}
              onChange={(e) => {
                const newDays = e.target.checked
                  ? [...schedule.days, day]
                  : schedule.days.filter((d) => d !== day)
                onChange(index, 'days', newDays)
              }}
            />
            {day}
          </label>
        ))}
      </div>
    </div>
  )
}

export default function ScheduleView({ schedules: initialSchedules, onUpdate }) {
  const [schedules, setSchedules] = useState(initialSchedules || [])
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  function handleChange(index, field, value) {
    setSchedules((prev) =>
      prev.map((s, i) => (i === index ? { ...s, [field]: value } : s))
    )
  }

  async function handleSave() {
    setError(null)

    // Validate all times
    for (const schedule of schedules) {
      if (!TIME_REGEX.test(schedule.time)) {
        setError(`Formato de hora inválido: "${schedule.time}". Use el formato HH:MM (ej. 08:00).`)
        return
      }
    }

    setSaving(true)
    try {
      const result = await updateSchedules(schedules)
      if (onUpdate) onUpdate(result)
    } catch (err) {
      if (err?.status === 422) {
        setError(`Error 422: ${err.message || 'Formato de hora inválido en el servidor.'}`)
      } else {
        setError(`Error al guardar: ${err?.message || 'Error desconocido'}`)
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="schedule-view">
      <h2>Horarios</h2>

      {error && (
        <div className="schedule-error" role="alert">
          {error}
        </div>
      )}

      <div className="schedule-list">
        {schedules.map((schedule, index) => (
          <ScheduleRow
            key={index}
            schedule={schedule}
            index={index}
            onChange={handleChange}
          />
        ))}
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="btn-primary"
      >
        {saving ? 'Guardando...' : 'Guardar'}
      </button>
    </div>
  )
}
