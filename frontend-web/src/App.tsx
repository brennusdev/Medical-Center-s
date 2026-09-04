/**
 * MED V2 - Portal do Paciente
 * Telas: Dashboard (proxima consulta + resumo), Minhas Solicitacoes,
 * Nova Solicitacao. Consome a API V2 (/api/v1/appointments).
 */
import { useCallback, useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

type Request = {
  id: number;
  patient_id: number;
  specialty: string;
  preferred_date: string;
  preferred_time: string;
  reason: string;
  status: string;
  created_at: string;
};

type Appointment = {
  id: number;
  request_id: number;
  patient_id: number;
  specialty: string;
  doctor_name: string;
  hospital_name: string;
  scheduled_at: string;
  status: string;
  notes: string;
  created_at: string;
};

type Tab = "dashboard" | "requests" | "new";

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [patientId, setPatientId] = useState("1");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [requests, setRequests] = useState<Request[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setError("");
    try {
      const [aRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/appointments/patient/${patientId}`),
        fetch(`${API_BASE}/appointments/requests/patient/${patientId}`),
      ]);
      if (!aRes.ok || !rRes.ok) throw new Error("Falha ao carregar dados do paciente");
      setAppointments(await aRes.json());
      setRequests(await rRes.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro de conexao com a API");
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load, tab]);

  const next = appointments.find((a) => new Date(a.scheduled_at) >= new Date());

  return (
    <div className="container">
      <header className="header">
        <h1>MED - Portal do Paciente (V2)</h1>
      </header>

      <div className="patient-picker">
        <strong>Paciente ID:</strong>
        <input
          type="number"
          min={1}
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
        />
        <button className="tab" onClick={load}>Recarregar</button>
      </div>

      <nav className="tabs">
        <button className={`tab ${tab === "dashboard" ? "active" : ""}`} onClick={() => setTab("dashboard")}>
          Dashboard
        </button>
        <button className={`tab ${tab === "requests" ? "active" : ""}`} onClick={() => setTab("requests")}>
          Minhas Solicitacoes
        </button>
        <button className={`tab ${tab === "new" ? "active" : ""}`} onClick={() => setTab("new")}>
          Nova Solicitacao
        </button>
      </nav>

      {error && <p className="error">{error}</p>}

      {tab === "dashboard" && <Dashboard next={next} total={appointments.length} pending={requests.filter((r) => r.status === "REQUESTED" || r.status === "IN_REVIEW").length} />}
      {tab === "requests" && <RequestsList requests={requests} />}
      {tab === "new" && (
        <NewRequestForm
          patientId={Number(patientId)}
          onCreated={() => {
            setTab("requests");
            load();
          }}
        />
      )}
    </div>
  );
}

function Dashboard({ next, total, pending }: { next?: Appointment; total: number; pending: number }) {
  return (
    <section>
      <div className="card next-appointment">
        <h3>Proxima consulta</h3>
        {next ? (
          <>
            <p className="when">{fmtDateTime(next.scheduled_at)}</p>
            <p>{next.specialty} - {next.doctor_name}</p>
            <p className="muted">{next.hospital_name}</p>
            <span className={`badge ${next.status}`}>{next.status}</span>
          </>
        ) : (
          <p className="muted">Nenhuma consulta futura agendada.</p>
        )}
      </div>
      <div className="card">
        <h3>Resumo</h3>
        <p>Consultas totais: {total}</p>
        <p>Solicitacoes aguardando: {pending}</p>
      </div>
    </section>
  );
}

function RequestsList({ requests }: { requests: Request[] }) {
  if (requests.length === 0) return <p className="empty">Nenhuma solicitacao encontrada.</p>;
  return (
    <section>
      {requests.map((r) => (
        <div className="card" key={r.id}>
          <h3>
            #{r.id} - {r.specialty} <span className={`badge ${r.status}`}>{r.status}</span>
          </h3>
          <p className="muted">
            Preferencia: {new Date(`${r.preferred_date}T${r.preferred_time}`).toLocaleString("pt-BR")}
          </p>
          {r.reason && <p>{r.reason}</p>}
        </div>
      ))}
    </section>
  );
}

function NewRequestForm({ patientId, onCreated }: { patientId: number; onCreated: () => void }) {
  const [specialty, setSpecialty] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/appointments/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: patientId,
          specialty,
          preferred_date: date,
          preferred_time: time,
          reason,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      setSuccess(true);
      setSpecialty("");
      setDate("");
      setTime("");
      setReason("");
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar solicitacao");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h3>Nova solicitacao de consulta</h3>
      <label>
        Especialidade
        <input required minLength={2} value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Ex.: Cardiologia" />
      </label>
      <label>
        Data preferencial
        <input required type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </label>
      <label>
        Horario preferencial
        <input required type="time" value={time} onChange={(e) => setTime(e.target.value)} />
      </label>
      <label>
        Motivo
        <textarea maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Descreva o motivo da consulta" />
      </label>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">Solicitacao criada com sucesso!</p>}
      <button type="submit" disabled={saving}>{saving ? "Enviando..." : "Enviar solicitacao"}</button>
    </form>
  );
}
