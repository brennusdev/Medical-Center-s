# Medical Center's

# MED — Medical Center

Sistema de gestão médica. **V3: Preciso de atendimento.** V1 (fundação) e V2 (consultas e agendamentos) preservadas.

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
- **V3** — preciso de atendimento (care requests) (atual).
- Próximas versões: autenticação JWT, módulos de médicos/hospitais, notificações, filas, IA (fora do escopo da V3).
