# PROJECT_SPEC — MED

## Visão geral
Sistema de gestão para centros médicos, evoluindo em versões incrementais.

## V1 (fundação) — implementada
- Estrutura em módulos: `App/core` (config, database, main, models) e `App/modules/<dominio>`.
- Domínio `users` (modelo User).
- Infraestrutura: FastAPI, SQLAlchemy 2.0, Alembic, SQLite (configurável).
- Registro central de models em `App/core/models.py` para o Alembic.

## V2 (atual) — Consultas e Agendamentos

### Domínio: `App/modules/appointments`

#### Entidade AppointmentRequest (solicitação de consulta)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| patient_id | int | > 0, indexado |
| specialty | str | 2–100 caracteres |
| preferred_date | date | data preferencial do paciente |
| preferred_time | time | horário preferencial |
| reason | str | motivo, até 500 caracteres |
| status | enum | REQUESTED / IN_REVIEW / SCHEDULED / CANCELLED / EXPIRED |
| created_at | datetime | server_default now |

#### Entidade Appointment (consulta)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| request_id | int (FK) | solicitação relacionada (obrigatória) |
| patient_id | int | herdado da solicitação |
| specialty | str | herdado da solicitação |
| doctor_name | str | 2–150 caracteres |
| hospital_name | str | 2–150 caracteres |
| scheduled_at | datetime | deve ser futuro |
| status | enum | SCHEDULED / CONFIRMED / CANCELLED / COMPLETED / EXPIRED |
| notes | str | observações, até 500 caracteres |
| created_at | datetime | server_default now |

### Endpoints
- `POST /api/v1/appointments/requests` — cria solicitação (status inicial REQUESTED).
- `GET /api/v1/appointments/requests/patient/{patient_id}` — lista solicitações do paciente.
- `POST /api/v1/appointments` — agenda consulta a partir de `request_id`; muda a solicitação para SCHEDULED.
- `GET /api/v1/appointments/patient/{patient_id}` — lista consultas do paciente.
- `GET /api/v1/appointments/{appointment_id}` — detalha consulta (404 se não existir).

### Regras de negócio (V2)
1. `patient_id` deve ser inteiro positivo (422 caso contrário).
2. Consulta só pode ser criada a partir de uma solicitação existente (404) e ativa (422 se CANCELLED/EXPIRED/SCHEDULED).
3. `scheduled_at` deve ser estritamente futuro (422).
4. Ao agendar, a solicitação passa a SCHEDULED.
5. Relacionamento bidirecional request ↔ appointments (SQLAlchemy relationship).

### Frontend web (V2)
- Dashboard do paciente (próxima consulta + resumo).
- Minhas solicitações.
- Nova solicitação (formulário).

### Mobile (V2)
- Próxima consulta.
- Pedir consulta.
- Minhas solicitações.

## Fora do escopo da V2 (não implementar)
JWT, filas, prioridade clínica, IA.
