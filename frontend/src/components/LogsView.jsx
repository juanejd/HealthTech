export default function LogsView({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="space-y-5">
        <h2 className="font-display text-xl font-medium text-ink">
          Registro de eventos
        </h2>
        <div className="care-card text-ink-soft italic">
          No hay eventos registrados.
        </div>
      </div>
    );
  }

  const headers = [
    "Timestamp",
    "Tipo",
    "Estado",
    "Extracción detectada",
    "Día",
    "Compartimento",
  ];

  return (
    <div className="space-y-5">
      <h2 className="font-display text-xl font-medium text-ink">
        Registro de eventos
      </h2>
      <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
        <table className="w-full border-collapse text-left text-[0.95rem]">
          <thead>
            <tr>
              {headers.map((h) => (
                <th
                  key={h}
                  className="border-b border-line bg-paper px-4 py-3 text-xs font-semibold uppercase tracking-[0.1em] text-ink-soft"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {events.map((event, index) => (
              <tr
                key={index}
                className="odd:bg-surface even:bg-[color-mix(in_srgb,var(--color-paper)_55%,var(--color-surface))]"
              >
                <td className="border-b border-line px-4 py-3 font-mono text-sm text-ink-soft">
                  {event.timestamp}
                </td>
                <td className="border-b border-line px-4 py-3 text-ink">
                  {event.type}
                </td>
                <td className="border-b border-line px-4 py-3">
                  <span
                    className={
                      event.status === "OK"
                        ? "inline-flex items-center rounded-full bg-[var(--color-ok-soft)] px-2.5 py-0.5 text-sm font-semibold text-[var(--color-ok)] status-ok"
                        : "inline-flex items-center rounded-full bg-[var(--color-fail-soft)] px-2.5 py-0.5 text-sm font-semibold text-[var(--color-fail)] status-fail"
                    }
                  >
                    {event.status}
                  </span>
                </td>
                <td className="border-b border-line px-4 py-3 text-ink">
                  {event.extraction_detected ? "Sí" : "No"}
                </td>
                <td className="border-b border-line px-4 py-3 text-ink">
                  {event.day}
                </td>
                <td className="border-b border-line px-4 py-3 text-ink">
                  {event.compartment_index}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
