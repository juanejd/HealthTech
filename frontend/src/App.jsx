import { useState, useEffect, useRef } from "react";
import {
  fetchStatus,
  fetchSchedules,
  fetchLogs,
  createWebSocket,
} from "./services/api";
import StatusView from "./components/StatusView";
import ScheduleView from "./components/ScheduleView";
import LogsView from "./components/LogsView";
import ManualDispense from "./components/ManualDispense";
import DiagnosticView from "./components/DiagnosticView";

const TABS = [
  { id: "status", label: "Estado" },
  { id: "schedules", label: "Horarios" },
  { id: "logs", label: "Registros" },
  { id: "dispense", label: "Dispensar" },
  { id: "diagnostic", label: "Diagnóstico" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("status");
  const [status, setStatus] = useState(null);
  const [schedules, setSchedules] = useState([]);
  const [logs, setLogs] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  async function loadStatus() {
    try {
      const data = await fetchStatus();
      setStatus(data);
    } catch (err) {
      console.error("Error fetching status:", err);
    }
  }

  async function loadSchedules() {
    try {
      const data = await fetchSchedules();
      setSchedules(data.schedules || []);
    } catch (err) {
      console.error("Error fetching schedules:", err);
    }
  }

  async function loadLogs() {
    try {
      const data = await fetchLogs();
      setLogs(data.events || []);
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  }

  useEffect(() => {
    loadStatus();
    loadSchedules();
    loadLogs();

    const ws = createWebSocket(
      (_msg) => {
        loadStatus();
      },
      () => setWsConnected(true),
      () => setWsConnected(false),
    );
    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  function handleScheduleUpdate(updated) {
    setSchedules(updated.schedules || []);
  }

  return (
    <div className="min-h-screen bg-paper">
      <div className="mx-auto w-full max-w-3xl px-4 pb-16 pt-8 sm:px-6">
        <header className="mb-8">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              {/* Carousel mark — 8 spokes echoing the physical dispenser */}
              <span
                aria-hidden="true"
                className="grid size-11 shrink-0 place-items-center rounded-full border border-line bg-surface"
              >
                <svg viewBox="0 0 24 24" className="size-6">
                  <g
                    stroke="var(--color-care)"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  >
                    {Array.from({ length: 8 }).map((_, i) => {
                      const a = (i * Math.PI) / 4;
                      return (
                        <line
                          key={i}
                          x1={12 + Math.cos(a) * 3.5}
                          y1={12 + Math.sin(a) * 3.5}
                          x2={12 + Math.cos(a) * 9}
                          y2={12 + Math.sin(a) * 9}
                        />
                      );
                    })}
                  </g>
                  <circle cx="12" cy="12" r="2.4" fill="var(--color-honey)" />
                </svg>
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-care">
                  HealthTech
                </p>
                <h1 className="font-display text-2xl font-medium leading-tight text-ink sm:text-[1.7rem]">
                  Dispensador de Medicamentos
                </h1>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2 pt-1 text-sm text-ink-soft">
              <span
                aria-hidden="true"
                className={`inline-block size-2.5 rounded-full ${
                  wsConnected ? "bg-care" : "bg-line"
                }`}
              />
              WebSocket: {wsConnected ? "● Conectado" : "○ Desconectado"}
            </div>
          </div>
        </header>

        <nav
          className="mb-8 flex flex-wrap gap-1.5 rounded-2xl border border-line bg-surface p-1.5"
          aria-label="Secciones"
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                aria-current={isActive ? "page" : undefined}
                className={`min-h-11 rounded-xl px-4 text-[0.95rem] font-semibold transition-colors ${
                  isActive
                    ? "bg-care text-surface"
                    : "text-ink-soft hover:bg-paper hover:text-ink"
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        <main>
          {activeTab === "status" && <StatusView status={status} />}
          {activeTab === "schedules" && (
            <ScheduleView schedules={schedules} onUpdate={handleScheduleUpdate} />
          )}
          {activeTab === "logs" && <LogsView events={logs} />}
          {activeTab === "dispense" && <ManualDispense />}
          {activeTab === "diagnostic" && <DiagnosticView status={status} />}
        </main>
      </div>
    </div>
  );
}
