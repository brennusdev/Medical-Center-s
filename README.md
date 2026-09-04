# Medical Center's

# MED — Medical Center

Sistema de gestão médica. **V2: Consultas e Agendamentos.**

## Estrutura
- `Backend/` — FastAPI + SQLAlchemy + Alembic (Python 3.12+)
- `frontend-web/` — SPA React (dashboard do paciente)
- `mobile/` — React Native (próxima consulta, pedir consulta, minhas solicitações)

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
- **V2** — consultas e agendamentos (atual).
- Próximas versões: autenticação JWT, prioridade clínica, filas, IA (fora do escopo da V2).
