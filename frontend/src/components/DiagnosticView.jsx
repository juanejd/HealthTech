import { useState, useEffect, useRef, useCallback } from "react";
import { stepServo, homeServo, readWeight, tareScale } from "../services/api";

// Live polling cadence. The HX711 is a slow ADC (~1-2 Hz effective with our
// median filter), so polling faster than this just re-reads stale conversions.
const LIVE_POLL_MS = 700;
// Ring buffer cap — keeps the sparkline readable and bounded in memory.
const BUFFER_CAP = 40;

// Sparkline geometry. Read like a measuring tape: a baseline at the tare zero,
// the care-colored deviation line above/below it, a honey dot at "now".
const SPARK_W = 240;
const SPARK_H = 60;
const SPARK_PAD_Y = 8;

/**
 * WeightSparkline — bespoke SVG "scale tape".
 *
 * The tare zero is a real hairline that runs edge to edge; the care line is the
 * deviation from it, so negative readings (below tare) genuinely dip under the
 * baseline. Y auto-scales to the buffer's own min/max so small wobbles stay
 * legible, and the zero line is always placed by the data, never pinned.
 */
function WeightSparkline({ buffer }) {
  if (buffer.length === 0) {
    return (
      <div
        className="flex items-center text-sm text-ink-soft"
        style={{ width: SPARK_W, height: SPARK_H }}
      >
        Sin datos aún
      </div>
    );
  }

  const values = buffer.map((p) => p.value);
  let min = Math.min(...values, 0);
  let max = Math.max(...values, 0);
  // Pad the range a touch so the line never kisses the top/bottom edge.
  const span = max - min || 1;
  min -= span * 0.12;
  max += span * 0.12;
  const range = max - min;

  const innerH = SPARK_H - SPARK_PAD_Y * 2;
  const yFor = (v) => SPARK_PAD_Y + (1 - (v - min) / range) * innerH;
  const xFor = (i) =>
    buffer.length === 1 ? SPARK_W : (i / (buffer.length - 1)) * SPARK_W;

  const zeroY = yFor(0);
  const points = buffer.map((p, i) => `${xFor(i)},${yFor(p.value)}`).join(" ");
  const last = buffer[buffer.length - 1];
  const lastX = xFor(buffer.length - 1);
  const lastY = yFor(last.value);

  return (
    <svg
      width={SPARK_W}
      height={SPARK_H}
      viewBox={`0 0 ${SPARK_W} ${SPARK_H}`}
      role="img"
      aria-label={`Tendencia de peso, últimas ${buffer.length} lecturas`}
      style={{ overflow: "visible" }}
    >
      {/* Tare-zero baseline — the reference the whole reading is relative to */}
      <line
        x1="0"
        y1={zeroY}
        x2={SPARK_W}
        y2={zeroY}
        stroke="var(--color-line)"
        strokeWidth="1.5"
        strokeDasharray="2 3"
      />
      {/* Deviation line */}
      <polyline
        points={points}
        fill="none"
        stroke="var(--color-care)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* "Now" — honey needle dot at the latest sample */}
      <circle cx={lastX} cy={lastY} r="3.5" fill="var(--color-honey)" />
    </svg>
  );
}

export default function DiagnosticView({ status }) {
  const [position, setPosition] = useState(null);
  const [weightG, setWeightG] = useState(null);
  const [calibrated, setCalibrated] = useState(true);
  const [stepLoading, setStepLoading] = useState(false);
  const [homeLoading, setHomeLoading] = useState(false);
  const [weightLoading, setWeightLoading] = useState(false);
  const [tareLoading, setTareLoading] = useState(false);
  const [servoError, setServoError] = useState(null);
  const [weightError, setWeightError] = useState(null);

  // Live-polling state. `buffer` is the sparkline ring buffer.
  const [live, setLive] = useState(false);
  const [buffer, setBuffer] = useState([]);

  const isBusy = status?.is_busy || false;

  const appendSample = useCallback((value) => {
    setBuffer((prev) => {
      const next = [...prev, { value, t: Date.now() }];
      // Drop oldest once we exceed the cap.
      return next.length > BUFFER_CAP ? next.slice(next.length - BUFFER_CAP) : next;
    });
  }, []);

  const handleStep = async () => {
    setServoError(null);
    setStepLoading(true);
    try {
      const res = await stepServo();
      setPosition(res.position);
    } catch (err) {
      if (err.status === 409) {
        setServoError("Dispensa en curso. La acción no fue realizada.");
      } else {
        setServoError("Error al avanzar el compartimiento.");
      }
    } finally {
      setStepLoading(false);
    }
  };

  const handleHome = async () => {
    setServoError(null);
    setHomeLoading(true);
    try {
      const res = await homeServo();
      setPosition(res.position);
    } catch (err) {
      if (err.status === 409) {
        setServoError("Dispensa en curso. La acción no fue realizada.");
      } else {
        setServoError("Error al resetear posición.");
      }
    } finally {
      setHomeLoading(false);
    }
  };

  const handleReadWeight = async () => {
    setWeightError(null);
    setWeightLoading(true);
    try {
      const res = await readWeight();
      setWeightG(res.weight_g);
      setCalibrated(res.calibrated);
    } catch (err) {
      if (err.status === 503) {
        setWeightError("Error de sensor — no se pudo leer el peso.");
        setWeightG(null);
      } else {
        setWeightError("Error al leer el sensor de peso.");
        setWeightG(null);
      }
    } finally {
      setWeightLoading(false);
    }
  };

  const handleTare = async () => {
    setWeightError(null);
    setTareLoading(true);
    try {
      const res = await tareScale();
      setWeightG(res.weight_g);
      setCalibrated(res.calibrated);
      // Fresh zero — the old trend no longer shares a baseline.
      setBuffer([]);
    } catch (err) {
      if (err.status === 409) {
        setWeightError("Dispensa en curso. La acción no fue realizada.");
      } else if (err.status === 503) {
        setWeightError("Error de sensor — no se pudo leer el peso.");
      } else {
        setWeightError("Error al poner la balanza a cero.");
      }
    } finally {
      setTareLoading(false);
    }
  };

  // Live polling. One interval, owned by this effect; cleaned up on unmount and
  // whenever `live` flips off — no leaked timers.
  useEffect(() => {
    if (!live) return undefined;

    let cancelled = false;

    const poll = async () => {
      try {
        const res = await readWeight();
        if (cancelled) return;
        setWeightG(res.weight_g);
        setCalibrated(res.calibrated);
        appendSample(res.weight_g);
        setWeightError(null);
      } catch (err) {
        if (cancelled) return;
        // On a sensor failure, stop live mode and surface the error.
        setLive(false);
        if (err.status === 503) {
          setWeightError("Error de sensor — no se pudo leer el peso.");
        } else {
          setWeightError("Error al leer el sensor de peso.");
        }
      }
    };

    poll(); // immediate first sample, then on the interval
    const id = setInterval(poll, LIVE_POLL_MS);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [live, appendSample]);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-medium text-ink">
          Panel de Diagnóstico
        </h2>
        <p className="mt-1 text-base text-ink-soft">
          Control manual del hardware.
        </p>
      </div>

      <section className="care-card space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
          Carrusel
        </h3>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            className="care-btn-ghost"
            onClick={handleStep}
            disabled={stepLoading}
          >
            {stepLoading ? "Avanzando..." : "Avanzar Compartimiento"}
          </button>
          <button
            className="care-btn-ghost"
            onClick={handleHome}
            disabled={homeLoading}
          >
            {homeLoading ? "Reseteando..." : "Resetear Posición (Home)"}
          </button>
        </div>

        {servoError && (
          <p className="text-[var(--color-fail)]">{servoError}</p>
        )}

        {position !== null && !servoError && (
          <p className="text-base text-ink">
            <span className="text-ink-soft">Posición actual:</span>{" "}
            <span className="font-mono">{position}</span>
          </p>
        )}
      </section>

      <section className="care-card space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
          Sensor de peso
        </h3>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <button
            className="care-btn-ghost"
            onClick={handleReadWeight}
            disabled={weightLoading || live}
          >
            {weightLoading ? "Leyendo..." : "Leer Peso"}
          </button>
          <button
            className="care-btn-ghost"
            onClick={handleTare}
            disabled={tareLoading}
          >
            {tareLoading ? "Poniendo a cero..." : "Poner a cero"}
          </button>
          <button
            className={live ? "care-btn" : "care-btn-ghost"}
            onClick={() => setLive((v) => !v)}
            aria-pressed={live}
          >
            {live ? "En vivo · detener" : "En vivo"}
          </button>
        </div>

        <p className="text-sm text-ink-soft">
          Lectura ~1/seg (sensor lento). Los valores son relativos al último
          cero{!calibrated ? " y en cuentas ADC crudas hasta calibrar" : ""}.
        </p>

        {weightError && (
          <p className="text-[var(--color-fail)]">{weightError}</p>
        )}

        {weightG !== null && !weightError && (
          <div className="space-y-3">
            <div className="rounded-xl border border-line bg-paper px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
                    Peso actual
                  </p>
                  <p className="mt-1 font-mono text-3xl font-medium text-ink">
                    {weightG.toFixed(2)}
                    <span className="ml-1 text-lg text-ink-soft">g</span>
                  </p>
                </div>
                <WeightSparkline buffer={buffer} />
              </div>
            </div>

            {!calibrated && (
              <p className="font-medium text-honey">
                Sensor no calibrado — la lectura está en cuentas ADC crudas.
              </p>
            )}
            {isBusy && (
              <p className="text-ink-soft">
                Nota: hay una dispensa en curso — la lectura puede estar
                afectada.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
