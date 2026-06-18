import { useState } from "react";
import { dispense } from "../services/api";

export default function ManualDispense() {
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  function handleDispenseClick() {
    setResult(null);
    setShowConfirm(true);
  }

  function handleCancel() {
    setShowConfirm(false);
  }

  async function handleConfirm() {
    setShowConfirm(false);
    setLoading(true);
    setResult(null);
    try {
      const data = await dispense();
      setResult(data);
    } catch (err) {
      setResult({ status: "FAIL", error: err?.message || "Error desconocido" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="manual-dispense">
      <h2>Dispensar manualmente</h2>

      <button
        onClick={handleDispenseClick}
        disabled={loading}
        className="btn-primary btn-dispense"
      >
        Dispensar
      </button>

      {loading && (
        <div className="dispense-loading" role="status">
          Enviando orden...
        </div>
      )}

      {showConfirm && (
        <div className="dispense-dialog" role="dialog" aria-modal="true">
          <div className="dispense-dialog-inner">
            <p>¿Está seguro de que desea dispensar ahora?</p>
            <div className="dispense-dialog-actions">
              <button onClick={handleConfirm} className="btn-primary">
                Confirmar
              </button>
              <button onClick={handleCancel} className="btn-secondary">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div
          className={`dispense-result ${result.status === "OK" ? "result-ok" : "result-fail"}`}
          role="alert"
        >
          <p>
            <strong>Resultado:</strong> {result.status}
          </p>
          {result.extraction_detected !== undefined && (
            <p>
              <strong>Extracción detectada:</strong>{" "}
              {result.extraction_detected ? "Sí" : "No"}
            </p>
          )}
          {result.timestamp && (
            <p>
              <strong>Hora:</strong> {result.timestamp}
            </p>
          )}
          {result.error && (
            <p>
              <strong>Error:</strong> {result.error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
