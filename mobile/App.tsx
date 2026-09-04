/**
 * MED V2 - App do Paciente
 * Telas: Proxima Consulta, Pedir Consulta, Minhas Solicitacoes.
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

type Screen = "next" | "ask" | "requests" | "care" | "care-new";

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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!patientId) return;
    setLoading(true);
    setError("");
    try {
      const [aRes, rRes, cRes] = await Promise.all([
        fetch(`${API_BASE}/appointments/patient/${patientId}`),
        fetch(`${API_BASE}/appointments/requests/patient/${patientId}`),
        fetch(`${API_BASE}/care-requests/patient/${patientId}`),
      ]);
      if (!aRes.ok || !rRes.ok || !cRes.ok) throw new Error("Falha ao carregar dados");
      const appts: Appointment[] = await aRes.json();
      const now = new Date();
      setNext(appts.find((a) => new Date(a.scheduled_at) >= now) ?? null);
      setRequests(await rRes.json());
      setCareRequests(await cRes.json());
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
      <Text style={styles.title}>MED V2</Text>

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
                  </KeyboardAvoidingView>
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
