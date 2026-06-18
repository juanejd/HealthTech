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
    <div className="space-y-5">
      <h2 className="font-display text-xl font-medium text-ink">
        Dispensar manualmente
      </h2>

      <section className="care-card space-y-4">
        <p className="text-base text-ink-soft">
          Hace girar el carrusel y suelta la pastilla del día en este momento.
        </p>
        <button
          onClick={handleDispenseClick}
          disabled={loading}
          className="care-btn w-full text-lg sm:w-auto"
        >
          Dispensar
        </button>

        {loading && (
          <div
            className="flex items-center gap-2 text-base text-ink-soft"
            role="status"
          >
            <span
              aria-hidden="true"
              className="inline-block size-2.5 animate-pulse rounded-full bg-honey"
            />
            Enviando orden...
          </div>
        )}
      </section>

      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[color-mix(in_srgb,var(--color-ink)_45%,transparent)] p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-sm rounded-2xl border border-line bg-surface p-7 text-center shadow-xl">
            <p className="mb-6 text-lg text-ink">
              ¿Está seguro de que desea dispensar ahora?
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
              <button onClick={handleConfirm} className="care-btn w-full sm:w-auto">
                Confirmar
              </button>
              <button
                onClick={handleCancel}
                className="care-btn-ghost w-full sm:w-auto"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div
          className={`rounded-2xl border p-5 ${
            result.status === "OK"
              ? "result-ok border-[var(--color-ok)] bg-[var(--color-ok-soft)]"
              : "result-fail border-[var(--color-fail)] bg-[var(--color-fail-soft)]"
          }`}
          role="alert"
        >
          <p
            className={`font-display text-xl font-medium ${
              result.status === "OK"
                ? "text-[var(--color-ok)]"
                : "text-[var(--color-fail)]"
            }`}
          >
            Resultado: {result.status}
          </p>
          <div className="mt-2 space-y-1 text-base text-ink">
            {result.extraction_detected !== undefined && (
              <p>
                <span className="text-ink-soft">Extracción detectada:</span>{" "}
                {result.extraction_detected ? "Sí" : "No"}
              </p>
            )}
            {result.timestamp && (
              <p>
                <span className="text-ink-soft">Hora:</span> {result.timestamp}
              </p>
            )}
            {result.error && (
              <p>
                <span className="text-ink-soft">Error:</span> {result.error}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
