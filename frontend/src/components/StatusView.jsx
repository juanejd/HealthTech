function Indicator({ connected, testId }) {
  const colorClass = connected ? 'indicator-green' : 'indicator-red'
  return <span className={colorClass} data-testid={testId} />
}

export default function StatusView({ status }) {
  if (!status) {
    return <div className="status-loading">Cargando...</div>
  }

  const {
    current_day,
    compartment_index,
    next_event,
    last_event,
    telegram_connected,
    wifi_connected,
  } = status

  return (
    <div className="status-view">
      <h2>Estado del sistema</h2>

      <div className="status-connectivity">
        <div className="status-row">
          <span>Telegram:</span>
          <Indicator connected={telegram_connected} testId="telegram-indicator" />
          <span>{telegram_connected ? 'Conectado' : 'Desconectado'}</span>
        </div>
        <div className="status-row">
          <span>Wi-Fi:</span>
          <Indicator connected={wifi_connected} testId="wifi-indicator" />
          <span>{wifi_connected ? 'Conectado' : 'Desconectado'}</span>
        </div>
      </div>

      <div className="status-info">
        <p><strong>Día actual:</strong> {current_day}</p>
        <p><strong>Compartimento:</strong> {compartment_index}</p>
      </div>

      {next_event ? (
        <div className="status-next-event">
          <h3>Próximo evento</h3>
          <p>{next_event.time} — {next_event.message}</p>
        </div>
      ) : (
        <div className="status-next-event">
          <h3>Próximo evento</h3>
          <p>Sin eventos programados</p>
        </div>
      )}

      {last_event ? (
        <div className="status-last-event">
          <h3>Último evento</h3>
          <p><strong>Hora:</strong> {last_event.timestamp}</p>
          <p>
            <strong>Estado:</strong>{' '}
            <span
              data-testid="last-event-status"
              className={last_event.status === 'OK' ? 'indicator-green' : 'indicator-red'}
            >
              {last_event.status}
            </span>
          </p>
          <p><strong>Extracción detectada:</strong> {last_event.extraction_detected ? 'Sí' : 'No'}</p>
        </div>
      ) : (
        <div className="status-last-event">
          <h3>Último evento</h3>
          <p>Sin eventos recientes</p>
        </div>
      )}
    </div>
  )
}
