import { useState } from "react";
import { updateSchedules } from "../services/api";

const TIME_REGEX = /^\d{2}:\d{2}$/;

// API uses string day names — must match exactly
const DAY_NAMES = [
  "lunes",
  "martes",
  "miércoles",
  "jueves",
  "viernes",
  "sábado",
  "domingo",
];

function ScheduleRow({ schedule, index, onChange }) {
  return (
    <div className="care-card space-y-4">
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="font-display text-lg font-medium text-care"
        >
          {schedule.time || "—:—"}
        </span>
        <label className="ml-auto flex items-center gap-2 text-sm font-medium text-ink-soft">
          <input
            type="checkbox"
            className="size-5 accent-[var(--color-care)]"
            checked={schedule.enabled}
            onChange={(e) => onChange(index, "enabled", e.target.checked)}
          />
          Activo
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-[10rem_1fr]">
        <input
          type="text"
          className="care-input max-w-40"
          value={schedule.time}
          onChange={(e) => onChange(index, "time", e.target.value)}
          placeholder="HH:MM"
          aria-label={`Hora del horario ${index + 1}`}
        />
        <input
          type="text"
          className="care-input"
          value={schedule.message}
          onChange={(e) => onChange(index, "message", e.target.value)}
          placeholder="Mensaje"
          aria-label={`Mensaje del horario ${index + 1}`}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {DAY_NAMES.map((day) => {
          const active =
            Array.isArray(schedule.days) && schedule.days.includes(day);
          return (
            <label
              key={day}
              className={`flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium capitalize transition-colors ${
                active
                  ? "border-care bg-[color-mix(in_srgb,var(--color-care)_10%,var(--color-surface))] text-care"
                  : "border-line bg-surface text-ink-soft hover:border-ink-soft"
              }`}
            >
              <input
                type="checkbox"
                className="size-5 accent-[var(--color-care)]"
                checked={active}
                onChange={(e) => {
                  const newDays = e.target.checked
                    ? [...schedule.days, day]
                    : schedule.days.filter((d) => d !== day);
                  onChange(index, "days", newDays);
                }}
              />
              {day}
            </label>
          );
        })}
      </div>
    </div>
  );
}

export default function ScheduleView({
  schedules: initialSchedules,
  onUpdate,
}) {
  const [schedules, setSchedules] = useState(initialSchedules || []);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  function handleChange(index, field, value) {
    setSchedules((prev) =>
      prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)),
    );
  }

  async function handleSave() {
    setError(null);

    // Validate all times
    for (const schedule of schedules) {
      if (!TIME_REGEX.test(schedule.time)) {
        setError(
          `Formato de hora inválido: "${schedule.time}". Use el formato HH:MM (ej. 08:00).`,
        );
        return;
      }
    }

    setSaving(true);
    try {
      const result = await updateSchedules(schedules);
      if (onUpdate) onUpdate(result);
    } catch (err) {
      if (err?.status === 422) {
        setError(
          `Error 422: ${err.message || "Formato de hora inválido en el servidor."}`,
        );
      } else {
        setError(`Error al guardar: ${err?.message || "Error desconocido"}`);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <h2 className="font-display text-xl font-medium text-ink">Horarios</h2>

      {error && (
        <div
          className="rounded-xl border border-[var(--color-fail)] bg-[var(--color-fail-soft)] px-4 py-3 text-[var(--color-fail)]"
          role="alert"
        >
          {error}
        </div>
      )}

      <div className="space-y-4">
        {schedules.map((schedule, index) => (
          <ScheduleRow
            key={index}
            schedule={schedule}
            index={index}
            onChange={handleChange}
          />
        ))}
      </div>

      <button onClick={handleSave} disabled={saving} className="care-btn">
        {saving ? "Guardando..." : "Guardar"}
      </button>
    </div>
  );
}
