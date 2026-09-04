# ARCHITECTURE — MED

## Visão em camadas (preservada da V1)

```
Router (fino)  →  Service (regras de negócio)  →  Repository (acesso ao banco)  →  Models (SQLAlchemy)
     ↑                    ↑                              ↑
  Schemas (contrato)   Exceções de domínio          Session via get_db
```

- **Router** (`modules/appointments/router.py`, `modules/care_requests/router.py`): apenas HTTP — status codes, parsing/serialização, delegação ao service. Sem regras de negócio.
- **Service** (`modules/appointments/service.py`): validações de negócio (patient_id > 0, consulta futura, solicitação ativa), transição de status da solicitação. Erros: `NotFoundError` → 404, `ValidationError` → 422.
- **Repository** (`modules/appointments/repository.py`): único ponto de acesso ao banco (SQLAlchemy ORM). Sem lógica de negócio.
- **Schemas** (`modules/appointments/schemas.py`): contratos Pydantic de entrada/saída (`*Create`, `*Read`).
- **Models** (`modules/appointments/models.py`): `AppointmentRequest` e `Appointment` + enums `RequestStatus` e `AppointmentStatus`.

## Registro central de models
`App/core/models.py` importa todos os models e expõe `Base`. O `alembic/env.py` usa esse registro como `target_metadata` — toda nova versão deve adicionar seus models aqui.

## Migrations
- `0001` — users (V1).
- `a1b2c3d4e5f6` — appointment_requests + appointments (V2).
- `b7c8d9e0f1a2` — care_requests + users.role (V3).

## Configuração
`App/core/config.py` (pydantic-settings): `DATABASE_URL` (default SQLite), `API_V1_PREFIX=/api/v1`. Entrypoint: `App/core/main.py`, com CORS liberado e `/health`.

## Frontends
- `frontend-web/` — React + Vite; consome `/api/v1/appointments*` e `/api/v1/care-requests*`; telas: Dashboard, Minhas Solicitações, Nova Solicitação, Preciso de Atendimento (formulário + lista).
- `mobile/` — React Native/Expo; telas: Próxima Consulta, Pedir Consulta, Minhas Solicitações, Preciso de Atendimento.

## Decisões da V2
- Médico e hospital são strings (`doctor_name`, `hospital_name`): módulos de médicos/hospitais não fazem parte do escopo da V2.
- Sem autenticação (JWT fica para versão futura); `patient_id` vem do payload/query.
- Sem filas, sem prioridade clínica, sem IA.

## Decisões da V3
- Domínio novo `Backend/App/modules/care_requests`, seguindo o mesmo fluxo router → service → repository → database; nada da V1/V2 foi alterado em comportamento.
- `users.role` é uma coluna aditiva com default `PATIENT`: preserva dados existentes da V1 e permite a regra "usuário que não é paciente" (422).
- `patient_id` em care_requests é FK para `users.id` (404 se o usuário não existir).
- **Segurança:** sintomas/desconforto/descrição são armazenados como relatos literais do paciente. O service não deriva diagnóstico, gravidade, emergência nem prioridade — não existe campo calculado ou classificação automática.
- Status operacionais apenas (CREATED, IN_REVIEW, REFERRED, SCHEDULED, CANCELLED, COMPLETED) — sem triagem clínica automática.
