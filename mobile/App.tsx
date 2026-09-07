/**
 * MED V4 - App do Paciente
 * Telas: Proxima Consulta, Pedir Consulta, Minhas Solicitacoes,
 * Preciso de Atendimento e Minhas Filas (V4).
 */
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Button,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

const API_BASE = "http://localhost:8000/api/v1";

type QueueEntry = {
  id: number;
  specialty: string;
  status: string;
  priority: string;
  position: number;
  entered_at: string;
  updated_at: string;
};

type QueueEventItem = {
  id: number;
  event_type: string;
  description: string;
  created_at: string;
};

type PatientStatusUpdate = {
  id: number;
  state: string;
  symptoms: string;
  severity: number;
  created_at: string;
  care_request_id: number;
};

type MedicalEvaluation = {
  id: number;
  professional_id: number;
  evaluation: string;
  recommendation: string;
  created_at: string;
};

type NotificationItem = {
  id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
};

type Screen = "next" | "ask" | "requests" | "care" | "care-new" | "queues" | "status" | "professional" | "notifications";

type Request = {
  id: number;
  specialty: string;
  preferred_date: string;
  preferred_time: string;
  reason: string;
  status: string;
};

type CareRequest = {
  id: number;
  reason: string;
  specialty: string;
  symptoms: string;
  discomfort_level: number;
  symptom_onset: string;
  status: string;
  created_at: string;
};

type Appointment = {
  id: number;
  specialty: string;
  doctor_name: string;
  hospital_name: string;
  scheduled_at: string;
  status: string;
};

export default function App() {
  const [screen, setScreen] = useState<Screen>("next");
  const [patientId, setPatientId] = useState("1");
  const [next, setNext] = useState<Appointment | null>(null);
  const [requests, setRequests] = useState<Request[]>([]);
  const [careRequests, setCareRequests] = useState<CareRequest[]>([]);
  const [queues, setQueues] = useState<QueueEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [aRes, rRes, cRes, qRes] = await Promise.all([
        fetch(`${API_BASE}/appointments/patient/${patientId}`),
        fetch(`${API_BASE}/appointments/requests/patient/${patientId}`),
        fetch(`${API_BASE}/care-requests/patient/${patientId}`),
        fetch(`${API_BASE}/queues/patient/${patientId}`),
      ]);
      if (!aRes.ok || !rRes.ok || !cRes.ok || !qRes.ok) throw new Error("Falha ao carregar dados");
      const appts: Appointment[] = await aRes.json();
      const now = new Date();
      setNext(appts.find((a) => new Date(a.scheduled_at) >= now) ?? null);
      setRequests(await rRes.json());
      setCareRequests(await cRes.json());
      setQueues(await qRes.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro de conexao com a API");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load, screen]);

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <Text style={styles.title}>MED V4</Text>

      <View style={styles.patientRow}>
        <Text>Paciente ID: </Text>
        <TextInput style={styles.patientInput} keyboardType="number-pad" value={patientId} onChangeText={setPatientId} />
        <Button title="Recarregar" onPress={load} />
      </View>

      <View style={styles.nav}>
        <Button title="Proxima Consulta" onPress={() => setScreen("next")} color={screen === "next" ? "#1d4ed8" : "#888"} />
        <Button title="Pedir Consulta" onPress={() => setScreen("ask")} color={screen === "ask" ? "#1d4ed8" : "#888"} />
        <Button title="Minhas Solicitacoes" onPress={() => setScreen("requests")} color={screen === "requests" ? "#1d4ed8" : "#888"} />
        <Button title="Preciso de atendimento" onPress={() => setScreen("care")} color={screen === "care" || screen === "care-new" ? "#dc2626" : "#888"} />
        <Button title="Minhas filas" onPress={() => setScreen("queues")} color={screen === "queues" ? "#1d4ed8" : "#888"} />
        <Button title="Meu estado" onPress={() => setScreen("status")} color={screen === "status" ? "#1d4ed8" : "#888"} />
        <Button title="Atendimento (Prof.)" onPress={() => setScreen("professional")} color={screen === "professional" ? "#1d4ed8" : "#888"} />
        <Button title="🔔 Notificacoes" onPress={() => setScreen("notifications")} color={screen === "notifications" ? "#1d4ed8" : "#888"} />
      </View>

      {loading && <ActivityIndicator />}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {screen === "next" && <NextAppointment next={next} />}
      {screen === "ask" && <AskConsultation patientId={Number(patientId)} onCreated={() => setScreen("requests")} />}
      {screen === "requests" && (
        <FlatList
          data={requests}
          keyExtractor={(r) => String(r.id)}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>#{item.id} - {item.specialty}</Text>
              <Text style={styles.muted}>Status: {item.status}</Text>
              <Text style={styles.muted}>Preferencia: {item.preferred_date} {item.preferred_time}</Text>
                      {item.reason ? <Text>{item.reason}</Text> : null}
                      </View>
                    )}
                      ListEmptyComponent={<Text style={styles.empty}>Nenhuma solicitacao.</Text>}
                      />
                    )}
                    {screen === "care" && (
                      <FlatList
                        data={careRequests}
                        keyExtractor={(c) => String(c.id)}
                        renderItem={({ item }) => (
                          <View style={styles.card}>
                            <Text style={styles.cardTitle}>#{item.id} - {item.specialty}</Text>
                            <Text style={styles.muted}>Status: {item.status}</Text>
                            <Text><Text style={styles.muted}>Motivo: </Text>{item.reason}</Text>
                            {item.symptoms ? <Text style={styles.muted}>Sintomas relatados: {item.symptoms}</Text> : null}
                            <Text style={styles.muted}>Desconforto informado: {item.discomfort_level}/10</Text>
                          </View>
                        )}
                        ListEmptyComponent={<Text style={styles.empty}>Nenhuma solicitacao de atendimento.</Text>}
                        ListHeaderComponent={
                          <Button title="Nova solicitacao de atendimento" onPress={() => setScreen("care-new")} color="#dc2626" />
                        }
                      />
                    )}
                    {screen === "care-new" && <CareRequestForm patientId={Number(patientId)} onCreated={() => setScreen("care")} />}
                    {screen === "queues" && <Queues queues={queues} />}
                    {screen === "status" && <MyStatus patientId={Number(patientId)} />}
                    {screen === "professional" && <ProfessionalReviews />}
                    {screen === "notifications" && <Notifications patientId={Number(patientId)} />}
                  </KeyboardAvoidingView>
                );
              }

function priorityLabel(p: string) {
  return { NORMAL: "Normal", MEDIUM: "Media", HIGH: "Alta", URGENT: "Urgente" }[p] ?? p;
}

const NOTIF_ICONS: Record<string, string> = {
  CARE_REQUEST_RECEIVED: "🔵",
  QUEUE_POSITION_CHANGED: "🔵",
  QUEUE_PRIORITY_CHANGED: "🔵",
  PATIENT_STATUS_UPDATED: "🔴",
  MEDICAL_EVALUATION_CREATED: "🔴",
  APPOINTMENT_SCHEDULED: "📅",
};

function Notifications({ patientId }: { patientId: number }) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/notifications/user/${patientId}`);
      if (res.ok) setItems(await res.json());
    } catch {
      // historico e best-effort no mobile
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  async function markAllRead() {
    const unread = items.filter((n) => !n.read);
    await Promise.all(
      unread.map((n) =>
        fetch(`${API_BASE}/notifications/${n.id}/read?user_id=${patientId}`, { method: "PATCH" })
      )
    );
    load();
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(n) => String(n.id)}
      renderItem={({ item }) => (
        <View style={[styles.card, { opacity: item.read ? 0.6 : 1 }]}>
          <Text style={styles.cardTitle}>
            {NOTIF_ICONS[item.type] ?? "🔔"} {item.title}
          </Text>
          {item.message ? <Text style={styles.muted}>{item.message}</Text> : null}
          <Text style={styles.muted}>{new Date(item.created_at).toLocaleString("pt-BR")}</Text>
        </View>
      )}
      ListEmptyComponent={<Text style={styles.empty}>Nenhuma notificacao.</Text>}
      ListFooterComponent={
        items.some((n) => !n.read) ? (
          <Button title="Marcar todas como lidas" onPress={markAllRead} color="#64748b" />
        ) : null
      }
    />
  );
}
  const [careRequestId, setCareRequestId] = useState("");
  const [updates, setUpdates] = useState<PatientStatusUpdate[]>([]);
  const [evaluations, setEvaluations] = useState<MedicalEvaluation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [evaluationText, setEvaluationText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadContext() {
    setError("");
    setSuccess("");
    try {
      const [uRes, eRes] = await Promise.all([
        fetch(`${API_BASE}/patient-status/request/${careRequestId}`),
        fetch(`${API_BASE}/medical-evaluations/request/${careRequestId}`),
      ]);
      if (!uRes.ok || !eRes.ok) throw new Error("Solicitacao nao encontrada");
      setUpdates(await uRes.json());
      setEvaluations(await eRes.json());
      setSelectedId(null);
    } catch (e) {
      setUpdates([]); setEvaluations([]);
      setError(e instanceof Error ? e.message : "Erro ao carregar");
    }
  }

  async function submitEvaluation() {
    if (selectedId == null) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/medical-evaluations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          professional_id: 2,
          patient_status_update_id: selectedId,
          care_request_id: Number(careRequestId),
          evaluation: evaluationText,
          recommendation: "",
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(typeof body.detail === "string" ? body.detail : `Erro ${res.status}`);
      }
      setSuccess("Avaliacao registrada!");
      setEvaluationText("");
      loadContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao registrar");
    } finally {
      setSaving(false);
    }
  }

  const selected = updates.find((u) => u.id === selectedId) ?? null;

  return (
    <ScrollView>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Atendimento (Profissional)</Text>
        <Text style={styles.muted}>Relatos do paciente nao sao diagnosticos. Avaliacoes sao registradas manualmente.</Text>
        <TextInput style={styles.input} placeholder="ID da solicitacao" value={careRequestId} onChangeText={setCareRequestId} keyboardType="number-pad" />
        <Button title="Carregar" onPress={loadContext} color="#1d4ed8" />
        {error ? <Text style={styles.error}>{error}</Text> : null}
      </View>

      {updates.map((u) => (
        <View key={u.id} style={styles.card}>
          <Text style={styles.cardTitle}>
            {u.state === "WORSENED" ? "🔴" : "🔵"} {new Date(u.created_at).toLocaleString("pt-BR")}
          </Text>
          <Text>{STATE_LABELS[u.state] ?? u.state} — {u.severity}/10</Text>
          {u.symptoms ? <Text style={styles.muted}>Sintomas relatados: {u.symptoms}</Text> : null}
          <Button
            title={selectedId === u.id ? "Selecionado" : "VER"}
            onPress={() => { setSelectedId(u.id); setSuccess(""); }}
            color={selectedId === u.id ? "#1d4ed8" : "#64748b"}
          />
        </View>
      ))}

      {selected && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Avaliacao — relato #{selected.id}</Text>
          <TextInput style={styles.input} placeholder="Avaliacao profissional" value={evaluationText} onChangeText={setEvaluationText} multiline />
          {success ? <Text style={{ color: "#16a34a", marginBottom: 8 }}>{success}</Text> : null}
          <Button title={saving ? "Enviando..." : "REGISTRAR"} onPress={submitEvaluation} disabled={saving} color="#1d4ed8" />
        </View>
      )}

      <Text style={styles.cardTitle}>Avaliacoes registradas</Text>
      {evaluations.length === 0 && <Text style={styles.muted}>Nenhuma avaliacao.</Text>}
      {evaluations.map((ev) => (
        <View key={ev.id} style={styles.card}>
          <Text style={styles.muted}>{new Date(ev.created_at).toLocaleString("pt-BR")} — Prof. #{ev.professional_id}</Text>
          <Text>{ev.evaluation}</Text>
          {ev.recommendation ? <Text style={styles.muted}>Recomendacao: {ev.recommendation}</Text> : null}
        </View>
      ))}
    </ScrollView>
  );
}

const STATE_LABELS: Record<string, string> = {
  IMPROVED: "Melhor",
  STABLE: "Igual",
  WORSENED: "Pior",
};

function ProfessionalReviews() {

function MyStatus({ patientId }: { patientId: number }) {
  const [careRequestId, setCareRequestId] = useState("");
  const [state, setState] = useState("STABLE");
  const [symptoms, setSymptoms] = useState("");
  const [severity, setSeverity] = useState(5);
  const [history, setHistory] = useState<PatientStatusUpdate[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory() {
    try {
      const res = await fetch(`${API_BASE}/patient-status/patient/${patientId}`);
      if (res.ok) setHistory(await res.json());
    } catch {
      // historico e best-effort; o formulario continua utilizavel
    }
  }

  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  async function submit() {
    setSaving(true);
    setError("");
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
          notes: "",
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(typeof body.detail === "string" ? body.detail : `Erro ${res.status}`);
      }
      setSymptoms("");
      loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Meu estado</Text>
        <Text style={styles.muted}>
          Registro apenas do seu relato. Nao e diagnostico e nao altera sua prioridade.
        </Text>
        <TextInput style={styles.input} placeholder="ID da solicitacao" value={careRequestId} onChangeText={setCareRequestId} keyboardType="number-pad" />
        <Text>Como você está?</Text>
        <View style={styles.nav}>
          {["IMPROVED", "STABLE", "WORSENED"].map((s) => (
            <Button key={s} title={STATE_LABELS[s]} onPress={() => setState(s)} color={state === s ? "#1d4ed8" : "#888"} />
          ))}
        </View>
        <TextInput style={styles.input} placeholder="Sintomas relatados" value={symptoms} onChangeText={setSymptoms} multiline />
        <Text>Intensidade: {severity}/10</Text>
        <View style={styles.nav}>
          <Button title="-" onPress={() => setSeverity((v) => Math.max(0, v - 1))} />
          <Button title="+" onPress={() => setSeverity((v) => Math.min(10, v + 1))} />
        </View>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button title={saving ? "Enviando..." : "Enviar atualizacao"} onPress={submit} disabled={saving} color="#1d4ed8" />
      </View>
      <Text style={styles.cardTitle}>Histórico</Text>
      {history.length === 0 && <Text style={styles.muted}>Nenhuma atualizacao.</Text>}
      {history.map((h) => (
        <View key={h.id} style={styles.card}>
          <Text style={styles.cardTitle}>{new Date(h.created_at).toLocaleString("pt-BR")}</Text>
          <Text>{STATE_LABELS[h.state] ?? h.state} — {h.severity}/10</Text>
          {h.symptoms ? <Text style={styles.muted}>Sintomas relatados: {h.symptoms}</Text> : null}
        </View>
      ))}
    </ScrollView>
  );
}

function Queues({ queues }: { queues: QueueEntry[] }) {
  return (
    <FlatList
      data={queues}
      keyExtractor={(q) => String(q.id)}
      renderItem={({ item }) => <QueueCard queue={item} />}
      ListEmptyComponent={<Text style={styles.empty}>Nenhuma entrada em fila.</Text>}
      ListHeaderComponent={
        <Text style={styles.muted}>
          A prioridade operacional nao representa diagnostico medico.
        </Text>
      }
    />
  );
}

function QueueCard({ queue }: { queue: QueueEntry }) {
  const [events, setEvents] = useState<QueueEventItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  async function loadHistory() {
    try {
      const res = await fetch(`${API_BASE}/queues/${queue.id}/events`);
      if (!res.ok) return;
      setEvents(await res.json());
    } catch {
      // historico e best-effort no mobile; a fila continua visivel
    }
  }

  useEffect(() => {
    if (showHistory) loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showHistory, queue.position, queue.priority]);

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>#{queue.id} - {queue.specialty}</Text>
      <Text style={styles.when}>
        {priorityLabel(queue.priority)} - Posicao {queue.position}
      </Text>
      <Text style={styles.muted}>Status: {queue.status}</Text>
      <Button
        title={showHistory ? "Ocultar historico" : "Ver historico"}
        onPress={() => setShowHistory((v) => !v)}
        color="#64748b"
      />
      {showHistory && (
        <View>
          {events.length === 0 && <Text style={styles.muted}>Nenhum evento.</Text>}
          {events.map((ev) => (
            <Text key={ev.id} style={styles.muted}>
              - {ev.event_type}: {ev.description}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

              function CareRequestForm({ patientId, onCreated }: { patientId: number; onCreated: () => void }) {
                const [reason, setReason] = useState("");
                const [specialty, setSpecialty] = useState("");
                const [symptoms, setSymptoms] = useState("");
                const [cep, setCep] = useState("");
                const [discomfort, setDiscomfort] = useState("5");
                const [onset, setOnset] = useState("");
                const [saving, setSaving] = useState(false);
                const [error, setError] = useState("");

                async function submit() {
                  setSaving(true);
                  setError("");
                  try {
                    const res = await fetch(`${API_BASE}/care-requests`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        patient_id: patientId,
                        reason,
                        specialty,
                        symptoms,
                        description: "",
                        cep,
                        referral: "",
                        discomfort_level: Number(discomfort),
                        symptom_onset: onset,
                        notes: "",
                      }),
                    });
                    if (!res.ok) {
                      const body = await res.json().catch(() => ({}));
                      throw new Error(typeof body.detail === "string" ? body.detail : `Erro ${res.status}`);
                    }
                    setReason(""); setSpecialty(""); setSymptoms(""); setCep(""); setDiscomfort("5"); setOnset("");
                    onCreated();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Erro ao enviar");
                  } finally {
                    setSaving(false);
                  }
                }

                return (
                  <ScrollView>
                    <View style={styles.card}>
                      <Text style={styles.cardTitle}>Preciso de atendimento</Text>
                      <Text style={styles.muted}>
                        Registro apenas do seu relato. Nao diagnostica e nao substitui avaliacao profissional.
                      </Text>
                      <TextInput style={styles.input} placeholder="Motivo da solicitacao" value={reason} onChangeText={setReason} />
                      <TextInput style={styles.input} placeholder="Especialidade desejada" value={specialty} onChangeText={setSpecialty} />
                      <TextInput style={styles.input} placeholder="Sintomas relatados" value={symptoms} onChangeText={setSymptoms} multiline />
                      <TextInput style={styles.input} placeholder="CEP" value={cep} onChangeText={setCep} keyboardType="number-pad" />
                      <TextInput style={styles.input} placeholder="Desconforto (1-10)" value={discomfort} onChangeText={setDiscomfort} keyboardType="number-pad" />
                      <TextInput style={styles.input} placeholder="Inicio dos sintomas (AAAA-MM-DD)" value={onset} onChangeText={setOnset} />
                      {error ? <Text style={styles.error}>{error}</Text> : null}
                      <Button title={saving ? "Enviando..." : "Enviar solicitacao"} onPress={submit} disabled={saving} color="#dc2626" />
                    </View>
                  </ScrollView>
                );
              }

function NextAppointment({ next }: { next: Appointment | null }) {
  if (!next) return <Text style={styles.empty}>Nenhuma consulta futura agendada.</Text>;
  return (
    <ScrollView>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Proxima consulta</Text>
        <Text style={styles.when}>{new Date(next.scheduled_at).toLocaleString("pt-BR")}</Text>
        <Text>{next.specialty} - {next.doctor_name}</Text>
        <Text style={styles.muted}>{next.hospital_name}</Text>
        <Text style={styles.muted}>Status: {next.status}</Text>
      </View>
    </ScrollView>
  );
}

function AskConsultation({ patientId, onCreated }: { patientId: number; onCreated: () => void }) {
  const [specialty, setSpecialty] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setSaving(true);
    setError("");
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
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      setSpecialty("");
      setDate("");
      setTime("");
      setReason("");
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Pedir consulta</Text>
        <TextInput style={styles.input} placeholder="Especialidade" value={specialty} onChangeText={setSpecialty} />
        <TextInput style={styles.input} placeholder="Data (AAAA-MM-DD)" value={date} onChangeText={setDate} />
        <TextInput style={styles.input} placeholder="Horario (HH:MM)" value={time} onChangeText={setTime} />
        <TextInput style={styles.input} placeholder="Motivo" value={reason} onChangeText={setReason} multiline />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button title={saving ? "Enviando..." : "Enviar solicitacao"} onPress={submit} disabled={saving} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, paddingTop: 48, backgroundColor: "#f1f5f9" },
  title: { fontSize: 24, fontWeight: "700", color: "#1d4ed8", marginBottom: 12 },
  patientRow: { flexDirection: "row", alignItems: "center", marginBottom: 8, gap: 8 },
  patientInput: { borderWidth: 1, borderColor: "#cbd5e1", borderRadius: 6, padding: 6, width: 70, textAlign: "center" },
  nav: { flexDirection: "row", gap: 4, marginBottom: 12, flexWrap: "wrap" },
  card: { backgroundColor: "#fff", borderRadius: 10, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: "#e2e8f0" },
  cardTitle: { fontWeight: "700", marginBottom: 4 },
  when: { fontSize: 16, fontWeight: "700", color: "#1d4ed8", marginVertical: 4 },
  muted: { color: "#64748b", fontSize: 13 },
  empty: { textAlign: "center", color: "#64748b", marginTop: 24 },
  input: { borderWidth: 1, borderColor: "#cbd5e1", borderRadius: 8, padding: 10, marginBottom: 10 },
  error: { color: "#dc2626", marginBottom: 8 },
});
