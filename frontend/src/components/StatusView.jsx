// Weekday order mirrors the physical carousel: lunes -> domingo (7 compartments).
const WEEKDAYS = [
  { key: "lunes", short: "L" },
  { key: "martes", short: "M" },
  { key: "miércoles", short: "X" },
  { key: "jueves", short: "J" },
  { key: "viernes", short: "V" },
  { key: "sábado", short: "S" },
  { key: "domingo", short: "D" },
];

// current_day may arrive as a weekday name or a numeric index — normalize both.
function resolveTodayIndex(current_day) {
  if (typeof current_day === "number") {
    return ((current_day % 7) + 7) % 7;
  }
  if (typeof current_day === "string") {
    const i = WEEKDAYS.findIndex(
      (d) => d.key.toLowerCase() === current_day.toLowerCase(),
    );
    return i >= 0 ? i : null;
  }
  return null;
}

// Geometry for a 7-segment ring (the medication dial).
function polar(cx, cy, r, angle) {
  return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
}

function segmentPath(cx, cy, rInner, rOuter, startAngle, endAngle) {
  const [x1, y1] = polar(cx, cy, rOuter, startAngle);
  const [x2, y2] = polar(cx, cy, rOuter, endAngle);
  const [x3, y3] = polar(cx, cy, rInner, endAngle);
  const [x4, y4] = polar(cx, cy, rInner, startAngle);
  const large = endAngle - startAngle > Math.PI ? 1 : 0;
  return [
    `M ${x1} ${y1}`,
    `A ${rOuter} ${rOuter} 0 ${large} 1 ${x2} ${y2}`,
    `L ${x3} ${y3}`,
    `A ${rInner} ${rInner} 0 ${large} 0 ${x4} ${y4}`,
    "Z",
  ].join(" ");
}

function WeeklyDial({ todayIndex, nextEvent }) {
  const size = 240;
  const cx = size / 2;
  const cy = size / 2;
  const rOuter = 104;
  const rInner = 66;
  const gap = 0.045; // radians of spacing between segments
  const step = (Math.PI * 2) / 7;
  const start = -Math.PI / 2; // 12 o'clock = lunes

  // Next-dose position mirrors a future weekday if we can resolve one,
  // otherwise it falls on today's compartment (the dose about to drop).
  const nextIndex =
    todayIndex == null ? null : (todayIndex + (nextEvent ? 1 : 0)) % 7;

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="h-auto w-full max-w-[260px]"
      role="img"
      aria-label="Disco semanal de medicación"
    >
      {WEEKDAYS.map((day, i) => {
        const a0 = start + i * step + gap;
        const a1 = start + (i + 1) * step - gap;
        const isToday = i === todayIndex;
        const isNext = i === nextIndex && !isToday;
        const fill = isToday
          ? "var(--color-care)"
          : isNext
            ? "var(--color-honey)"
            : "var(--color-surface)";
        const labelAngle = (a0 + a1) / 2;
        const [lx, ly] = polar(cx, cy, (rInner + rOuter) / 2, labelAngle);
        return (
          <g key={day.key}>
            <path
              d={segmentPath(cx, cy, rInner, rOuter, a0, a1)}
              fill={fill}
              stroke="var(--color-line)"
              strokeWidth="1.5"
            />
            <text
              x={lx}
              y={ly}
              textAnchor="middle"
              dominantBaseline="central"
              fontFamily="var(--font-sans)"
              fontSize="15"
              fontWeight="600"
              fill={
                isToday
                  ? "var(--color-surface)"
                  : isNext
                    ? "var(--color-ink)"
                    : "var(--color-ink-soft)"
              }
            >
              {day.short}
            </text>
          </g>
        );
      })}

      {/* Center readout: the next dose, or a calm empty state */}
      <circle cx={cx} cy={cy} r={rInner - 8} fill="var(--color-paper)" />
      {nextEvent ? (
        <>
          <text
            x={cx}
            y={cy - 18}
            textAnchor="middle"
            fontFamily="var(--font-sans)"
            fontSize="11"
            fontWeight="600"
            letterSpacing="1.5"
            fill="var(--color-ink-soft)"
          >
            PRÓXIMA DOSIS
          </text>
          <text
            x={cx}
            y={cy + 12}
            textAnchor="middle"
            fontFamily="var(--font-display)"
            fontSize="38"
            fontWeight="500"
            fill="var(--color-ink)"
          >
            {nextEvent.time}
          </text>
          <text
            x={cx}
            y={cy + 36}
            textAnchor="middle"
            fontFamily="var(--font-sans)"
            fontSize="12"
            fill="var(--color-ink-soft)"
          >
            {nextEvent.message}
          </text>
        </>
      ) : (
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          fontFamily="var(--font-sans)"
          fontSize="13"
          fontWeight="500"
          fill="var(--color-ink-soft)"
        >
          <tspan x={cx} dy="-0.4em">Sin eventos</tspan>
          <tspan x={cx} dy="1.3em">programados</tspan>
        </text>
      )}
    </svg>
  );
}

function Indicator({ connected, testId }) {
  const colorClass = connected ? "indicator-green" : "indicator-red";
  return <span className={colorClass} data-testid={testId} />;
}

export default function StatusView({ status }) {
  if (!status) {
    return (
      <div className="care-card text-ink-soft italic">Cargando...</div>
    );
  }

  const {
    current_day,
    compartment_index,
    next_event,
    last_event,
    wifi_connected,
  } = status;

  const todayIndex = resolveTodayIndex(current_day);

  return (
    <div className="space-y-5">
      <h2 className="font-display text-xl font-medium text-ink">
        Estado del sistema
      </h2>

      {/* Signature hero — the weekly medication dial */}
      <section className="care-card flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:gap-8">
        <div className="flex shrink-0 items-center justify-center">
          <WeeklyDial todayIndex={todayIndex} nextEvent={next_event} />
        </div>
        <div className="w-full space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
              Hoy
            </p>
            <p className="font-display text-2xl font-medium text-ink">
              {current_day}
            </p>
          </div>
          <div className="h-px bg-line" />
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
                Compartimento
              </dt>
              <dd className="mt-1 font-display text-2xl font-medium text-ink">
                {compartment_index}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
                Wi-Fi
              </dt>
              <dd className="mt-1 flex items-center gap-2 text-base text-ink">
                <Indicator
                  connected={wifi_connected}
                  testId="wifi-indicator"
                />
                {wifi_connected ? "Conectado" : "Desconectado"}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="care-card">
          <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
            Próximo evento
          </h3>
          {next_event ? (
            <p className="mt-3 text-base text-ink">
              <span className="font-display text-2xl font-medium text-care">
                {next_event.time}
              </span>
              <span className="mt-1 block text-ink-soft">
                {next_event.message}
              </span>
            </p>
          ) : (
            <p className="mt-3 text-base text-ink-soft">
              Sin eventos programados
            </p>
          )}
        </section>

        <section className="care-card">
          <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
            Último evento
          </h3>
          {last_event ? (
            <div className="mt-3 space-y-2 text-base text-ink">
              <p>
                <span className="text-ink-soft">Hora:</span>{" "}
                {last_event.timestamp}
              </p>
              <p className="flex items-center gap-2">
                <span className="text-ink-soft">Estado:</span>
                <span
                  data-testid="last-event-status"
                  className={
                    last_event.status === "OK"
                      ? "inline-flex items-center gap-1.5 rounded-full bg-[var(--color-ok-soft)] px-2.5 py-0.5 text-sm font-semibold text-[var(--color-ok)] indicator-green-status"
                      : "inline-flex items-center gap-1.5 rounded-full bg-[var(--color-fail-soft)] px-2.5 py-0.5 text-sm font-semibold text-[var(--color-fail)] indicator-red-status"
                  }
                >
                  {last_event.status}
                </span>
              </p>
              <p>
                <span className="text-ink-soft">Extracción detectada:</span>{" "}
                {last_event.extraction_detected ? "Sí" : "No"}
              </p>
            </div>
          ) : (
            <p className="mt-3 text-base text-ink-soft">
              Sin eventos recientes
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
