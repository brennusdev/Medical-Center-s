/**
 * MED V4 - Portal do Paciente
 * Telas: Dashboard (proxima consulta + resumo), Minhas Solicitacoes,
 * Nova Solicitacao, Preciso de Atendimento e Minhas Filas (V4).
 * Consome a API (/api/v1/appointments, /api/v1/care-requests, /api/v1/queues).
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

type QueueEntry = {
  id: number;
  care_request_id: number;
  specialty: string;
  hospital_id: number | null;
  status: string;
  priority: string;
  position: number;
  entered_at: string;
  updated_at: string;
};

type QueueEventItem = {
  id: number;
  queue_id: number;
  event_type: string;
  previous_position: number | null;
  new_position: number | null;
  previous_priority: string | null;
  new_priority: string | null;
  description: string;
  actor_id: number | null;
  created_at: string;
};

type PatientStatusUpdate = {
  id: number;
  patient_id: number;
  care_request_id: number;
  state: string;
  symptoms: string;
  severity: number;
  description: string;
  notes: string;
  created_at: string;
};

type MedicalEvaluation = {
  id: number;
  professional_id: number;
  patient_status_update_id: number;
  care_request_id: number;
  evaluation: string;
  recommendation: string;
  queue_id: number | null;
  created_at: string;
};

type Tab = "dashboard" | "requests" | "new" | "care" | "care-new" | "queues" | "status" | "professional" | "notifications";

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [patientId, setPatientId] = useState("1");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [requests, setRequests] = useState<Request[]>([]);
  const [careRequests, setCareRequests] = useState<CareRequest[]>([]);
  const [queues, setQueues] = useState<QueueEntry[]>([]);
  const [notifCount, setNotifCount] = useState(0);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setError("");
    try {
      const [aRes, rRes, cRes, qRes] = await Promise.all([
        fetch(`${API_BASE}/appointments/patient/${patientId}`),
        fetch(`${API_BASE}/appointments/requests/patient/${patientId}`),
        fetch(`${API_BASE}/care-requests/patient/${patientId}`),
        fetch(`${API_BASE}/queues/patient/${patientId}`),
      ]);
      if (!aRes.ok || !rRes.ok || !cRes.ok || !qRes.ok) throw new Error("Falha ao carregar dados do paciente");
      setAppointments(await aRes.json());
      setRequests(await rRes.json());
      setCareRequests(await cRes.json());
      setQueues(await qRes.json());
      const nRes = await fetch(`${API_BASE}/notifications/user/${patientId}`);
      if (nRes.ok) setNotifCount((await nRes.json()).filter((n: { read: boolean }) => !n.read).length);
      const nRes = await fetch(`${API_BASE}/notifications/user/${patientId}`);
      if (nRes.ok) setNotifCount((await nRes.json()).filter((n: { read: boolean }) => !n.read).length);
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
        <h1>MED - Portal do Paciente (V4)</h1>
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
        <button className={`tab ${tab === "queues" ? "active" : ""}`} onClick={() => setTab("queues")}>
          Minhas filas
        </button>
        <button className={`tab ${tab === "status" ? "active" : ""}`} onClick={() => setTab("status")}>
          Meu Estado
        </button>
        <button className={`tab ${tab === "professional" ? "active" : ""}`} onClick={() => setTab("professional")}>
          Atendimento (Profissional)
        </button>
        <button className={`tab ${tab === "notifications" ? "active" : ""}`} onClick={() => setTab("notifications")}>
          🔔 {notifCount > 0 ? notifCount : ""}
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
      {tab === "queues" && <QueuesSection queues={queues} onChanged={load} />}
      {tab === "status" && <MyStatusSection patientId={Number(patientId)} />}
      {tab === "professional" && <ProfessionalSection />}
      {tab === "notifications" && (
        <NotificationsSection patientId={Number(patientId)} onMarked={load} />
      )}
    </div>
  );
}

function ProfessionalSection() {
  const [careRequestId, setCareRequestId] = useState("");
  const [updates, setUpdates] = useState<PatientStatusUpdate[]>([]);
  const [evaluations, setEvaluations] = useState<MedicalEvaluation[]>([]);
  const [selected, setSelected] = useState<PatientStatusUpdate | null>(null);
  const [evaluationText, setEvaluationText] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadContext() {
    setError("");
    setSuccess("");
    setSelected(null);
    try {
      const [uRes, eRes] = await Promise.all([
        fetch(`${API_BASE}/patient-status/request/${careRequestId}`),
        fetch(`${API_BASE}/medical-evaluations/request/${careRequestId}`),
      ]);
      if (!uRes.ok || !eRes.ok) throw new Error("Solicitação não encontrada");
      setUpdates(await uRes.json());
      setEvaluations(await eRes.json());
    } catch (e) {
      setUpdates([]);
      setEvaluations([]);
      setError(e instanceof Error ? e.message : "Erro ao carregar contexto");
    }
  }

  async function submitEvaluation(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API_BASE}/medical-evaluations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          professional_id: Number(localStorage.getItem("med_actor_id") ?? "2"),
          patient_status_update_id: selected.id,
          care_request_id: selected.care_request_id,
          evaluation: evaluationText,
          recommendation,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      setSuccess("Avaliação registrada!");
      setEvaluationText("");
      setRecommendation("");
      loadContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao registrar avaliação");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <form
        className="card form"
        onSubmit={(e) => {
          e.preventDefault();
          loadContext();
        }}
      >
        <h3>Paciente — contexto do atendimento</h3>
        <p className="muted">
          Atualizações do paciente são RELATOS. Avaliações são registradas por um profissional autorizado e nunca são geradas automaticamente.
        </p>
        <label>
          Solicitação de atendimento (ID)
          <input required type="number" min={1} value={careRequestId} onChange={(e) => setCareRequestId(e.target.value)} />
        </label>
        <button type="submit">Carregar</button>
      </form>

      <h3>Atualizações do paciente</h3>
      {updates.length === 0 ? (
        <p className="empty">Nenhuma atualização registrada para esta solicitação.</p>
      ) : (
        updates.map((u) => (
          <div className="card" key={u.id}>
            <strong>{fmtDateTime(u.created_at)}</strong> — {STATE_LABELS[u.state] ?? u.state} — {u.severity}/10
            {u.symptoms && <p className="muted">Sintomas relatados: {u.symptoms}</p>}
            {u.notes && <p className="muted">Observações: {u.notes}</p>}
            <button
              className="tab"
              onClick={() => {
                setSelected(u);
                setSuccess("");
              }}
            >
              Visualizar / Avaliar
            </button>
          </div>
        ))
      )}

      {selected && (
        <form className="card form" onSubmit={submitEvaluation}>
          <h3>Avaliação profissional — relato #{selected.id}</h3>
          <label>
            Avaliação
            <textarea required minLength={2} maxLength={2000} value={evaluationText} onChange={(e) => setEvaluationText(e.target.value)} />
          </label>
          <label>
            Recomendação
            <textarea maxLength={500} value={recommendation} onChange={(e) => setRecommendation(e.target.value)} />
          </label>
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}
          <button type="submit" disabled={busy}>
            {busy ? "Enviando..." : "Registrar avaliação"}
          </button>
        </form>
      )}

      <h3>Avaliações registradas</h3>
      {evaluations.length === 0 ? (
        <p className="empty">Nenhuma avaliação registrada.</p>
      ) : (
        evaluations.map((ev) => (
          <div className="card" key={ev.id}>
            <strong>{fmtDateTime(ev.created_at)}</strong> — Profissional #{ev.professional_id}
            <p>{ev.evaluation}</p>
            {ev.recommendation && <p className="muted">Recomendação: {ev.recommendation}</p>}
          </div>
        ))
      )}
      {error && !selected && <p className="error">{error}</p>}
    </section>
  );
}

function priorityLabel(p: string) {
  return { NORMAL: "Normal", MEDIUM: "Media", HIGH: "Alta", URGENT: "Urgente" }[p] ?? p;
}

function QueuesSection({ queues, onChanged }: { queues: QueueEntry[]; onChanged: () => void }) {
  return (
    <section>
      <p className="muted">
        A prioridade operacional nao representa diagnostico medico. Ela e atribuida por um profissional autorizado.
      </p>
      {queues.length === 0 ? (
        <p className="empty">Nenhuma entrada em fila encontrada.</p>
      ) : (
        queues.map((q) => <QueueCard key={q.id} queue={q} onChanged={onChanged} />)
      )}
    </section>
  );
}

function QueueCard({ queue, onChanged }: { queue: QueueEntry; onChanged: () => void }) {
  const [events, setEvents] = useState<QueueEventItem[]>([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadEvents() {
    try {
      const res = await fetch(`${API_BASE}/queues/${queue.id}/events`);
      if (!res.ok) throw new Error("Falha ao carregar historico");
      setEvents(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar historico");
    }
  }

  useEffect(() => {
    if (open) loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, queue.position, queue.priority]);

  async function changePriority(priority: string) {
    const actorId = Number(localStorage.getItem("med_actor_id") ?? "2");
    if (!actorId) {
      setError("Informe um actor_id valido (perfil da equipe, nao do paciente).");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/queues/${queue.id}/priority`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority, actor_id: actorId }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      onChanged();
      if (open) loadEvents();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao alterar prioridade");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3>
        #{queue.id} - {queue.specialty} <span className={`badge ${queue.status}`}>{queue.status}</span>
      </h3>
      <p>
        <strong>Prioridade:</strong> {priorityLabel(queue.priority)} — <strong>Posicao:</strong> {queue.position}
      </p>
      <p className="muted">
        Entrada: {fmtDateTime(queue.entered_at)} - Ultima atualizacao: {fmtDateTime(queue.updated_at)}
      </p>
      <div className="queue-actions">
        {queue.status === "WAITING" &&
          ["NORMAL", "MEDIUM", "HIGH", "URGENT"].map((p) => (
            <button key={p} className="tab" disabled={busy || p === queue.priority} onClick={() => changePriority(p)}>
              {priorityLabel(p)}
            </button>
          ))}
      </div>
      {error && <p className="error">{error}</p>}
      <button className="tab" onClick={() => setOpen((v) => !v)}>
        {open ? "Ocultar timeline" : "Ver timeline"}
      </button>
      {open && (
        <ol className="timeline">
          {events.length === 0 && <li className="muted">Nenhum evento registrado.</li>}
          {events.map((ev) => (
            <li key={ev.id}>
              <strong>{ev.event_type}</strong> — {ev.description}
              <span className="muted"> ({fmtDateTime(ev.created_at)}{ev.actor_id ? ` - ator ${ev.actor_id}` : ""})</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

const STATE_LABELS: Record<string, string> = {
  IMPROVED: "Melhor",
  STABLE: "Igual",
  WORSENED: "Pior",
};

function MyStatusSection({ patientId }: { patientId: number }) {
  const [careRequestId, setCareRequestId] = useState("");
  const [state, setState] = useState("STABLE");
  const [symptoms, setSymptoms] = useState("");
  const [severity, setSeverity] = useState(5);
  const [notes, setNotes] = useState("");
  const [history, setHistory] = useState<PatientStatusUpdate[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const loadHistory = useCallback(async () => {
    if (!patientId) return;
    try {
      const res = await fetch(`${API_BASE}/patient-status/patient/${patientId}`);
      if (res.ok) setHistory(await res.json());
    } catch {
      // historico e best-effort; o formulario continua utilizavel
    }
  }, [patientId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/patient-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: patientId,
          care_request_id: Number(careRequestId),
          state,
          symptoms,
          severity,
          description: "",
          notes,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      setSuccess(true);
      setSymptoms("");
      setNotes("");
      loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar atualizacao");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <form className="card form" onSubmit={submit}>
        <h3>Meu Estado</h3>
        <p className="muted">
          Registro apenas do seu relato. Nao e diagnostico e nao altera sua prioridade na fila.
        </p>
        <label>
          Solicitação de atendimento (ID)
          <input
            required
            type="number"
            min={1}
            value={careRequestId}
            onChange={(e) => setCareRequestId(e.target.value)}
            placeholder="Ex.: 1042"
          />
        </label>
        <label>Como você está hoje?</label>
        <div className="queue-actions">
          {["IMPROVED", "STABLE", "WORSENED"].map((s) => (
            <button
              key={s}
              type="button"
              className={`tab ${state === s ? "active" : ""}`}
              onClick={() => setState(s)}
            >
              {STATE_LABELS[s]}
            </button>
          ))}
        </div>
        <label>
          Sintomas relatados
          <textarea maxLength={2000} value={symptoms} onChange={(e) => setSymptoms(e.target.value)} />
        </label>
        <label>
          Intensidade: {severity}/10
          <input
            type="range"
            min={0}
            max={10}
            value={severity}
            onChange={(e) => setSeverity(Number(e.target.value))}
          />
        </label>
        <label>
          Observações
          <textarea maxLength={500} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        {error && <p className="error">{error}</p>}
        {success && <p className="success">Estado atualizado!</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Enviando..." : "Atualizar meu estado"}
        </button>
      </form>
      <h3>Histórico</h3>
      {history.length === 0 ? (
        <p className="empty">Nenhuma atualizacao registrada.</p>
      ) : (
        history.map((h) => (
          <div className="card" key={h.id}>
            <strong>{fmtDateTime(h.created_at)}</strong> — {STATE_LABELS[h.state] ?? h.state} —{" "}
            {h.severity}/10
            {h.symptoms && <p className="muted">Sintomas relatados: {h.symptoms}</p>}
            {h.notes && <p className="muted">Observações: {h.notes}</p>}
            <p className="muted">Solicitação #{h.care_request_id}</p>
          </div>
        ))
      )}
    </section>
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
