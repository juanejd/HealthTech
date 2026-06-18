import { useState, useEffect } from 'react'
import { fetchDiagnosticStep, fetchDiagnosticHome, fetchDiagnosticWeight } from '../services/api'

export default function DiagnosticView({ status }) {
  const [weight, setWeight] = useState(null)
  const isBusy = status?.is_busy || false

  useEffect(() => {
    let intervalId

    if (!isBusy) {
      const pollWeight = async () => {
        try {
          const res = await fetchDiagnosticWeight()
          if (res && typeof res.weight === 'number') {
            setWeight(res.weight.toFixed(2))
          }
        } catch (err) {
          console.error('Error fetching weight:', err)
        }
      }

      pollWeight()
      intervalId = setInterval(pollWeight, 2000)
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [isBusy])

  const handleStep = async () => {
    try {
      await fetchDiagnosticStep()
    } catch (err) {
      console.error('Error stepping compartment:', err)
      alert('Error stepping compartment')
    }
  }

  const handleHome = async () => {
    try {
      await fetchDiagnosticHome()
    } catch (err) {
      console.error('Error homing servo:', err)
      alert('Error homing servo')
    }
  }

  return (
    <div className="diagnostic-view">
      <h2>Panel de Diagnóstico</h2>
      <p>Control manual del hardware.</p>
      
      <div className="diagnostic-controls" style={{ display: 'flex', gap: '1rem', marginTop: '1rem', marginBottom: '2rem' }}>
        <button className="primary-btn" onClick={handleStep} disabled={isBusy}>
          Avanzar Compartimiento
        </button>
        <button className="primary-btn" onClick={handleHome} disabled={isBusy}>
          Ir a Home
        </button>
      </div>

      <div className="weight-display" style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '4px', display: 'inline-block' }}>
        <strong>Peso Actual:</strong> {weight !== null ? `${weight} g` : 'Cargando...'}
        {isBusy && <span style={{ marginLeft: '1rem', color: '#888' }}>(Hardware ocupado...)</span>}
      </div>
    </div>
  )
}
