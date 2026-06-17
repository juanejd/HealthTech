import { useState, useEffect, useRef } from 'react'
import './App.css'
import { fetchStatus, fetchSchedules, fetchLogs, createWebSocket } from './services/api'
import StatusView from './components/StatusView'
import ScheduleView from './components/ScheduleView'
import LogsView from './components/LogsView'
import ManualDispense from './components/ManualDispense'

const TABS = [
  { id: 'status', label: 'Estado' },
  { id: 'schedules', label: 'Horarios' },
  { id: 'logs', label: 'Registros' },
  { id: 'dispense', label: 'Dispensar' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('status')
  const [status, setStatus] = useState(null)
  const [schedules, setSchedules] = useState([])
  const [logs, setLogs] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)

  async function loadStatus() {
    try {
      const data = await fetchStatus()
      setStatus(data)
    } catch (err) {
      console.error('Error fetching status:', err)
    }
  }

  async function loadSchedules() {
    try {
      const data = await fetchSchedules()
      setSchedules(data.schedules || [])
    } catch (err) {
      console.error('Error fetching schedules:', err)
    }
  }

  async function loadLogs() {
    try {
      const data = await fetchLogs()
      setLogs(data.events || [])
    } catch (err) {
      console.error('Error fetching logs:', err)
    }
  }

  useEffect(() => {
    loadStatus()
    loadSchedules()
    loadLogs()

    const ws = createWebSocket(
      (_msg) => {
        // On WS message, re-fetch full status
        loadStatus()
      },
      () => setWsConnected(true),
      () => setWsConnected(false)
    )
    wsRef.current = ws

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  function handleScheduleUpdate(updated) {
    setSchedules(updated.schedules || [])
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>HealthTech — Dispensador de Medicamentos</h1>
        <div className="ws-status">
          WebSocket: {wsConnected ? '● Conectado' : '○ Desconectado'}
        </div>
      </header>

      <nav className="tab-nav">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="tab-content">
        {activeTab === 'status' && <StatusView status={status} />}
        {activeTab === 'schedules' && (
          <ScheduleView schedules={schedules} onUpdate={handleScheduleUpdate} />
        )}
        {activeTab === 'logs' && <LogsView events={logs} />}
        {activeTab === 'dispense' && <ManualDispense />}
      </div>
    </div>
  )
}
