# Medical Center's

# MED — Medical Center

Sistema de gestão médica. **V4: Filas e priorização.** V1 (fundação), V2 (consultas e agendamentos) e V3 (preciso de atendimento) preservadas.

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
- **V4** — filas e priorização operacional (atual).
- Próximas versões (fora do escopo da V4): autenticação JWT, módulos de médicos/hospitais, notificações, IA.
