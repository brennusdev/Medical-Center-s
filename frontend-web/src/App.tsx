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

type CareRequest = {
  id: number;
  patient_id: number;
  reason: string;
  specialty: string;
  symptoms: string;
  description: string;
  cep: string;
  referral: string;
  discomfort_level: number;
  symptom_onset: string;
  notes: string;
  status: string;
  created_at: string;
};

type Tab = "dashboard" | "requests" | "new" | "care" | "care-new";

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [patientId, setPatientId] = useState("1");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [requests, setRequests] = useState<Request[]>([]);
  const [careRequests, setCareRequests] = useState<CareRequest[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setError("");
    try {
      const [aRes, rRes, cRes] = await Promise.all([
        fetch(`${API_BASE}/appointments/patient/${patientId}`),
        fetch(`${API_BASE}/appointments/requests/patient/${patientId}`),
        fetch(`${API_BASE}/care-requests/patient/${patientId}`),
      ]);
      if (!aRes.ok || !rRes.ok || !cRes.ok) throw new Error("Falha ao carregar dados do paciente");
      setAppointments(await aRes.json());
      setRequests(await rRes.json());
      setCareRequests(await cRes.json());
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
        <button className={`tab care-button ${tab === "care" || tab === "care-new" ? "active" : ""}`} onClick={() => setTab("care")}>
          Preciso de atendimento
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
      {tab === "care" && (
        <CareRequestsSection
          careRequests={careRequests}
          onNew={() => setTab("care-new")}
        />
      )}
      {tab === "care-new" && (
        <CareRequestForm
          patientId={Number(patientId)}
          onCreated={() => {
            setTab("care");
            load();
          }}
        />
      )}
    </div>
  );
}

function CareRequestsSection({ careRequests, onNew }: { careRequests: CareRequest[]; onNew: () => void }) {
  return (
    <section>
      <button className="tab care-button" onClick={onNew}>
        + Nova solicitacao de atendimento
      </button>
      {careRequests.length === 0 ? (
        <p className="empty">Nenhuma solicitacao de atendimento encontrada.</p>
      ) : (
        careRequests.map((c) => (
          <div className="card" key={c.id}>
            <h3>
              #{c.id} - {c.specialty} <span className={`badge ${c.status}`}>{c.status}</span>
            </h3>
            <p><strong>Motivo:</strong> {c.reason}</p>
            {c.symptoms && <p><strong>Sintomas relatados:</strong> {c.symptoms}</p>}
            <p className="muted">Desconforto informado: {c.discomfort_level}/10 - Inicio dos sintomas: {c.symptom_onset}</p>
            <p className="muted">CEP: {c.cep} - Criada em: {fmtDateTime(c.created_at)}</p>
          </div>
        ))
      )}
    </section>
  );
}

function CareRequestForm({ patientId, onCreated }: { patientId: number; onCreated: () => void }) {
  const [form, setForm] = useState({
    reason: "", specialty: "", symptoms: "", description: "",
    cep: "", referral: "", discomfort_level: "5", symptom_onset: "", notes: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  function set(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/care-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: patientId,
          reason: form.reason,
          specialty: form.specialty,
          symptoms: form.symptoms,
          description: form.description,
          cep: form.cep,
          referral: form.referral,
          discomfort_level: Number(form.discomfort_level),
          symptom_onset: form.symptom_onset,
          notes: form.notes,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      setSuccess(true);
      setForm({ reason: "", specialty: "", symptoms: "", description: "", cep: "", referral: "", discomfort_level: "5", symptom_onset: "", notes: "" });
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar solicitacao");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h3>Preciso de atendimento</h3>
      <p className="muted">
        Este formulario registra apenas o seu relato. Ele nao faz diagnostico,
        nao avalia gravidade clinica e nao substitui a avaliacao de um profissional de saude.
      </p>
      <label>
        Motivo da solicitacao
        <input required minLength={2} maxLength={500} value={form.reason} onChange={(e) => set("reason", e.target.value)} />
      </label>
      <label>
        Especialidade desejada
        <input required minLength={2} maxLength={100} value={form.specialty} onChange={(e) => set("specialty", e.target.value)} placeholder="Ex.: Clinica geral" />
      </label>
      <label>
        Sintomas relatados
        <textarea maxLength={2000} value={form.symptoms} onChange={(e) => set("symptoms", e.target.value)} />
      </label>
      <label>
        Descricao da situacao
        <textarea maxLength={2000} value={form.description} onChange={(e) => set("description", e.target.value)} />
      </label>
      <label>
        CEP
        <input required minLength={8} maxLength={9} value={form.cep} onChange={(e) => set("cep", e.target.value)} placeholder="Ex.: 01310100" />
      </label>
      <label>
        Encaminhamento medico (opcional)
        <input maxLength={500} value={form.referral} onChange={(e) => set("referral", e.target.value)} />
      </label>
      <label>
        Nivel de desconforto informado (1-10)
        <input required type="number" min={1} max={10} value={form.discomfort_level} onChange={(e) => set("discomfort_level", e.target.value)} />
      </label>
      <label>
        Data de inicio dos sintomas
        <input required type="date" value={form.symptom_onset} onChange={(e) => set("symptom_onset", e.target.value)} />
      </label>
      <label>
        Observacoes
        <textarea maxLength={500} value={form.notes} onChange={(e) => set("notes", e.target.value)} />
      </label>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">Solicitacao de atendimento criada!</p>}
      <button type="submit" disabled={saving}>{saving ? "Enviando..." : "Enviar solicitacao"}</button>
    </form>
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
