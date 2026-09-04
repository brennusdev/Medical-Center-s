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

## V3 (atual) — Preciso de atendimento

### Domínio: `Backend/App/modules/care_requests`

#### Entidade CareRequest (solicitação de atendimento)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| patient_id | int (FK users.id) | paciente existente (404); usuário com role PATIENT (422) |
| reason | str | motivo, 2–500 caracteres |
| specialty | str | especialidade desejada, 2–100 caracteres |
| symptoms | text | sintomas RELATADOS pelo paciente |
| description | text | descrição da situação (relato) |
| cep | str | CEP/localização, 8–9 caracteres |
| referral | str | encaminhamento médico, opcional |
| discomfort_level | int | 1–10, informado pelo paciente |
| symptom_onset | date | data de início dos sintomas |
| notes | str | observações, até 500 caracteres |
| status | enum | CREATED / IN_REVIEW / REFERRED / SCHEDULED / CANCELLED / COMPLETED |
| created_at | datetime | server_default now |

#### Endpoints
- `POST /api/v1/care-requests` — cria solicitação (status inicial CREATED; 201).
- `GET /api/v1/care-requests/patient/{patient_id}` — lista solicitações do paciente.
- `GET /api/v1/care-requests/{request_id}` — detalha solicitação (404 se não existir).

### Regras de segurança (V3 — obrigatórias)
Os campos de sintomas, desconforto e descrição são **RELATOS INFORMADOS PELO PACIENTE**. O sistema NÃO:
- diagnostica;
- afirma que o paciente possui uma doença;
- determina sozinho uma emergência clínica;
- atribui automaticamente prioridade clínica;
- substitui avaliação profissional.

### Mudanças aditivas na V1
- `users.role` (str, default `PATIENT`) — necessária para a regra "usuário que não é paciente".

### Frontend web (V3)
- Botão "Preciso de atendimento", formulário de solicitação, lista das minhas solicitações com status.

### Mobile (V3)
- Botão "Preciso de atendimento", formulário básico e visualização das solicitações.

## Fora do escopo da V3 (não implementar)
JWT, filas, triagem automática, prioridade clínica automática, IA.
