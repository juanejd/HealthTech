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
    <div className="diagnostic-view">
      <h2>Panel de Diagnóstico</h2>
      <p>Control manual del hardware.</p>

      <div
        className="diagnostic-controls"
        style={{
          display: "flex",
          gap: "1rem",
          marginTop: "1rem",
          marginBottom: "1rem",
        }}
      >
        <button
          className="primary-btn"
          onClick={handleStep}
          disabled={stepLoading}
        >
          {stepLoading ? "Avanzando..." : "Avanzar Compartimiento"}
        </button>
        <button
          className="primary-btn"
          onClick={handleHome}
          disabled={homeLoading}
        >
          {homeLoading ? "Reseteando..." : "Resetear Posición (Home)"}
        </button>
      </div>

      {servoError && (
        <p style={{ color: "#c0392b", marginBottom: "1rem" }}>{servoError}</p>
      )}

      {position !== null && !servoError && (
        <p style={{ marginBottom: "1rem" }}>
          <strong>Posición actual:</strong> {position}
        </p>
      )}

      <div
        className="weight-section"
        style={{
          marginTop: "1rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "4px",
          display: "inline-block",
        }}
      >
        <div style={{ marginBottom: "0.5rem" }}>
          <button
            className="primary-btn"
            onClick={handleReadWeight}
            disabled={weightLoading}
          >
            {weightLoading ? "Leyendo..." : "Leer Peso"}
          </button>
        </div>

        {weightError && <p style={{ color: "#c0392b" }}>{weightError}</p>}

        {weightG !== null && !weightError && (
          <>
            <p>
              <strong>Peso actual:</strong> {weightG.toFixed(2)} g
            </p>
            {!calibrated && (
              <p style={{ color: "#e67e22", fontWeight: "bold" }}>
                Sensor no calibrado — la lectura está en cuentas ADC crudas.
              </p>
            )}
            {isBusy && (
              <p style={{ color: "#888" }}>
                Nota: hay una dispensa en curso — la lectura puede estar
                afectada.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
