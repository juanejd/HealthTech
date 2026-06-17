export default function LogsView({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="logs-view">
        <h2>Registro de eventos</h2>
        <p className="logs-empty">No hay eventos registrados.</p>
      </div>
    )
  }

  return (
    <div className="logs-view">
      <h2>Registro de eventos</h2>
      <div className="logs-table-wrapper">
        <table className="logs-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Extracción detectada</th>
              <th>Día</th>
              <th>Compartimento</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, index) => (
              <tr key={index}>
                <td>{event.timestamp}</td>
                <td>{event.type}</td>
                <td>
                  <span className={event.status === 'OK' ? 'status-ok' : 'status-fail'}>
                    {event.status}
                  </span>
                </td>
                <td>{event.extraction_detected ? 'Sí' : 'No'}</td>
                <td>{event.day}</td>
                <td>{event.compartment_index}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
