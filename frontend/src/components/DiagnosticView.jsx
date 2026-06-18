import { useState } from "react";
import { stepServo, homeServo, readWeight } from "../services/api";

export default function DiagnosticView({ status }) {
  const [position, setPosition] = useState(null);
  const [weightG, setWeightG] = useState(null);
  const [calibrated, setCalibrated] = useState(true);
  const [stepLoading, setStepLoading] = useState(false);
  const [homeLoading, setHomeLoading] = useState(false);
  const [weightLoading, setWeightLoading] = useState(false);
  const [servoError, setServoError] = useState(null);
  const [weightError, setWeightError] = useState(null);

  const isBusy = status?.is_busy || false;

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
        <button
          className="care-btn-ghost"
          onClick={handleReadWeight}
          disabled={weightLoading}
        >
          {weightLoading ? "Leyendo..." : "Leer Peso"}
        </button>

        {weightError && (
          <p className="text-[var(--color-fail)]">{weightError}</p>
        )}

        {weightG !== null && !weightError && (
          <div className="space-y-3">
            <div className="rounded-xl border border-line bg-paper px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">
                Peso actual
              </p>
              <p className="mt-1 font-mono text-3xl font-medium text-ink">
                {weightG.toFixed(2)}
                <span className="ml-1 text-lg text-ink-soft">g</span>
              </p>
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
