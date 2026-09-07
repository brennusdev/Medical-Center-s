# Medical Center's

# MED — Medical Center

Sistema de gestão médica. **V8: Dashboards e Analytics.** V1–V7 preservadas (fundação, consultas, care requests, filas, estado do paciente, avaliações, notificações).

## Estrutura
- `Backend/` — FastAPI + SQLAlchemy + Alembic (Python 3.12+)
- `frontend-web/` — SPA React (dashboard do paciente)
- `mobile/` — React Native (próxima consulta, pedir consulta, minhas solicitações, preciso de atendimento)

## Backend — como rodar
```powershell
cd Backend
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn App.core.main:app --reload
```
Docs interativas: http://localhost:8000/docs

## Endpoints (V2)
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/appointments/requests` | Criar solicitação de consulta |
| GET | `/api/v1/appointments/requests/patient/{patient_id}` | Solicitações do paciente |
| POST | `/api/v1/appointments` | Agendar consulta (a partir de uma solicitação) |
| GET | `/api/v1/appointments/patient/{patient_id}` | Consultas do paciente |
| GET | `/api/v1/appointments/{appointment_id}` | Detalhar consulta |
| GET | `/health` | Health check |

## Endpoints (V3 — Preciso de atendimento)
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/care-requests` | Criar solicitação de atendimento |
| GET | `/api/v1/care-requests/patient/{patient_id}` | Solicitações de atendimento do paciente |
| GET | `/api/v1/care-requests/{request_id}` | Detalhar solicitação de atendimento |

> **Nota de segurança (V3):** os campos de sintomas/desconforto/descrição são **relatos informados pelo paciente**. O sistema não diagnostica, não afirma doença, não determina emergência clínica, não atribui prioridade clínica automaticamente e não substitui avaliação profissional.

## Endpoints (V4 — Filas e priorização)
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/queues` | Criar entrada na fila (status WAITING, prioridade NORMAL, posição calculada) |
| GET | `/api/v1/queues/{queue_id}` | Detalhar entrada na fila |
| GET | `/api/v1/queues/patient/{patient_id}` | Filas do paciente |
| GET | `/api/v1/queues/{queue_id}/events` | Histórico (timeline) imutável da entrada |
| PATCH | `/api/v1/queues/{queue_id}/priority` | Alterar prioridade (somente não-PATIENT; reorganiza a fila) |

> **Nota de segurança (V4):** a prioridade operacional (NORMAL/MEDIUM/HIGH/URGENT) **não representa diagnóstico médico**. O sistema não diagnostica e não decide prioridade clínica sozinho: toda prioridade é atribuída por usuário autorizado do domínio e cada mudança gera `QueueEvent` com o `actor_id` responsável. O histórico nunca é apagado pela aplicação.

## Endpoints (V8 — Dashboards e Analytics)
Dashboards por perfil ("Como está meu atendimento?" no paciente; operacional no hospital; gestão no admin):
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/dashboard/patient/{patient_id}` | Visão pessoal: próxima consulta, solicitações, fila, posição, prioridade, notificações, próximo passo |
| GET | `/api/v1/dashboard/doctor/{doctor_id}` | Casos recebidos, aguardando avaliação, consultas do dia, filas ativas |
| GET | `/api/v1/dashboard/hospital/{hospital_id}` | Filas ativas, distribuição por especialidade, contagens operacionais |
| GET | `/api/v1/dashboard/admin` | Números de gestão (volumes, tempo médio de espera, distribuições) |
| GET | `/api/v1/analytics/overview` | Volumes gerais (COUNT SQL agregado) |
| GET | `/api/v1/analytics/specialties` | Solicitações por especialidade (GROUP BY) |
| GET | `/api/v1/analytics/hospitals` | Filas por hospital (GROUP BY) |
| GET | `/api/v1/analytics/wait-times` | Tempo médio de espera (AVG SQL, esperas encerradas) |
| GET | `/api/v1/analytics/priorities` | Distribuição de prioridades ativas |
| GET | `/api/v1/analytics/appointments` | Consultas por dia |

Filtros comuns: `?start_date=&end_date=&specialty=&hospital_id=` (janela inválida → 422). Performance: todas as métricas usam agregação no banco (COUNT/AVG/GROUP BY), nunca listas completas em Python.

## Testes
```powershell
cd Backend
python -m pytest tests -q
```

## Frontend web
```powershell
cd frontend-web
npm install
npm run dev
```

## Mobile
```powershell
cd mobile
npm install
npx expo start
```

## Roadmap de versões
- **V1** — fundação, usuários, infraestrutura.
- **V2** — consultas e agendamentos.
- **V3** — preciso de atendimento (care requests).
- **V4** — filas e priorização operacional.
- **V5** — estado do paciente: atualizações de estado (Melhor/Igual/Pior), sintomas relatados, intensidade subjetiva 0–10 e histórico (`/api/v1/patient-status*`).
- **V6** — comunicação paciente ↔ profissional: `MedicalEvaluation` (`/api/v1/medical-evaluations*`). O relato do paciente permanece intacto; a avaliação é registrada por profissional autorizado, sem diagnóstico automático.
- **V7** (atual) — notificações: eventos do atendimento geram notificações (`/api/v1/notifications*`) via `NotificationService` central, com histórico preservado e sino no web/mobile.
- **V8** (atual) — dashboards por perfil + analytics (`/api/v1/dashboard/*`, `/api/v1/analytics/*`), camada de leitura sem regras novas de negócio.
- Próximas versões: segurança (V9), auditoria (V10).
