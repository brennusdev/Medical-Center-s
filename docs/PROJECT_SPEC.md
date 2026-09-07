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
JWT, triagem automática, prioridade clínica automática, IA.

## V4 (atual) — Filas e Priorização
### Domínio: `Backend/App/modules/queues`

#### Entidade Queue (entrada na fila)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| care_request_id | int (FK care_requests.id) | solicitação existente (404) |
| specialty | str | 2–100 caracteres; define a fila |
| hospital_id | int | opcional (sem FK — módulo de hospitais não existe) |
| status | enum | WAITING / IN_REVIEW / REFERRED / SCHEDULED / REMOVED / COMPLETED |
| priority | enum | NORMAL / MEDIUM / HIGH / URGENT (sempre NORMAL na criação) |
| position | int | posição na fila (fim da fila ativa na criação) |
| entered_at | datetime | server_default now |
| updated_at | datetime | atualizado em alterações |

#### Entidade QueueEvent (histórico imutável, append-only)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| queue_id | int (FK queues.id) | entrada relacionada |
| event_type | enum | CREATED / POSITION_CHANGED / PRIORITY_CHANGED / STATUS_CHANGED / REFERRED / REMOVED |
| previous_position / new_position | int | obrigatórios em POSITION_CHANGED |
| previous_priority / new_priority | enum | obrigatórios em PRIORITY_CHANGED |
| description | str | até 500 caracteres |
| actor_id | int | opcional; usuário responsável (registro de auditoria) |
| created_at | datetime | server_default now |

#### Endpoints
- `POST /api/v1/queues` — cria entrada (status WAITING, prioridade NORMAL, posição no fim da fila; 201).
- `GET /api/v1/queues/{queue_id}` — detalha entrada (404 se não existir).
- `GET /api/v1/queues/patient/{patient_id}` — filas do paciente.
- `GET /api/v1/queues/{queue_id}/events` — histórico (timeline) da entrada.
- `PATCH /api/v1/queues/{queue_id}/priority` — altera prioridade (403 se ator é PATIENT ou papel não autorizado; 404 ator inexistente).

### Regras de negócio (V4)
1. Uma CareRequest não pode ter mais de uma entrada ATIVA na mesma fila (422).
2. Toda entrada nova recebe posição (fim da fila ativa).
3. Toda alteração relevante gera QueueEvent (append-only, nunca apagado).
4. POSITION_CHANGED registra posição anterior e nova; PRIORITY_CHANGED registra prioridade anterior e nova.
5. Reorganização determinística: URGENT > HIGH > MEDIUM > NORMAL; dentro da mesma prioridade, menor entered_at primeiro.
6. Mudança de prioridade renumera as posições ativas (1..N) e gera POSITION_CHANGED para cada item movido.

### Regras de segurança (V4 — obrigatórias)
- A prioridade operacional NÃO representa diagnóstico médico.
- O sistema NÃO diagnostica e NÃO decide sozinho prioridade clínica definitiva.
- Somente usuários autorizados no domínio (não-PATIENT, papéis RECEPTIONIST/NURSE/DOCTOR/ADMIN) alteram prioridade.
- O paciente NÃO pode alterar a própria prioridade (403).
- Toda mudança de prioridade fica associada ao usuário responsável (actor_id).

### Frontend web (V4)
- Tela de filas: especialidade, status, prioridade, posição, entrada/atualização e timeline (histórico de eventos).

### Mobile (V4)
- Tela de filas: prioridade, posição, status e histórico simplificado.

## Fora do escopo da V4 (não implementar)
JWT (usa actor_id informado), IA, triagem automática, transições de status da fila via endpoints (eventos STATUS_CHANGED/REFERRED/REMOVED já previstos no modelo).

## V5 (atual) — Estado do Paciente

### Domínio: `Backend/App/modules/patient_status`

#### Entidade PatientStatusUpdate (atualização de estado)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| patient_id | int (FK users.id) | paciente existente (404) e papel PATIENT (422) |
| care_request_id | int (FK care_requests.id) | solicitação existente (404) |
| state | enum | IMPROVED / STABLE / WORSENED (relato do paciente) |
| symptoms | text | sintomas RELATADOS pelo paciente |
| severity | int | 0–10, escala SUBJETIVA informada pelo paciente (não interpretada) |
| description | text | descrição da situação (relato) |
| notes | str | observações, até 500 caracteres |
| created_at | datetime | server_default now |

#### Endpoints
- `POST /api/v1/patient-status` — cria atualização (201); somente o próprio dono da solicitação (403 caso contrário).
- `GET /api/v1/patient-status/{status_id}` — detalha (404).
- `GET /api/v1/patient-status/patient/{patient_id}` — histórico do paciente (mais recente primeiro).
- `GET /api/v1/patient-status/request/{care_request_id}` — atualizações da solicitação (ordem cronológica).

### Regras de negócio (V5)
1. Somente o próprio paciente registra sua atualização (dono da CareRequest, 403).
2. Vinculação obrigatória a uma CareRequest existente (404).
3. Relatos literais: sem diagnóstico, sem interpretação de severidade.
4. NÃO altera prioridade da fila e NÃO altera status da CareRequest/fila.
5. Histórico append-only: cada POST cria novo registro, nada sobrescrito.

### Frontend web (V5)
- Tela "Meu Estado": estado (Melhor/Igual/Pior), sintomas, intensidade 0–10, observações e histórico.

### Mobile (V5)
- Tela simplificada: estado, sintomas, intensidade e histórico.

## Fora do escopo da V5 (não implementar)
Diagnóstico/triagem automática, IA, alteração automática de prioridade/fila, JWT.


## V6 (atual) — Comunicação Paciente ↔ Profissional

### Domínio: `Backend/App/modules/medical_evaluations`

Separação explícita: RELATO DO PACIENTE (PatientStatusUpdate, intacto) ≠ AVALIAÇÃO PROFISSIONAL (MedicalEvaluation, registrada por profissional autorizado).

#### Entidade MedicalEvaluation (avaliação profissional)
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| patient_status_update_id | int (FK patient_status_updates.id) | relato avaliado, existente (404) |
| care_request_id | int (FK care_requests.id) | solicitação existente (404); deve ser a do relato (422) |
| professional_id | int (FK users.id) | profissional existente (404); paciente não pode criar (403) |
| evaluation | text | texto literal do profissional; sem diagnóstico automático |
| recommendation | str | até 500 caracteres |
| queue_id | int (opcional) | ligação opcional com fila, sem FK |
| created_at | datetime | server_default now |

#### Endpoints
- `POST /api/v1/medical-evaluations` — cria avaliação (201); paciente → 403.
- `GET /api/v1/medical-evaluations/request/{care_request_id}` — histórico do atendimento.
- `GET /api/v1/medical-evaluations/{evaluation_id}` — detalhe (404).
- `GET /api/v1/patient-status/request/{care_request_id}` — profissional visualiza atualizações do paciente (controle de domínio no service).

### Regras de negócio (V6)
1. Paciente NÃO cria avaliação (403).
2. Profissional responsável registrado em cada avaliação (professional_id + timestamp).
3. Relato original permanece intacto; avaliações são append-only.
4. Sem RBAC completo — estrutura compatível com a futura V9.

### Frontend web (V6)
- Aba "Atendimento (Profissional)": atualizações do paciente + registro de avaliação + histórico de avaliações.

### Mobile (V6)
- Tela "Atendimento (Prof.)": atualizações (ver), avaliação e registro.

### Migration
- `e6f7a8b9c0d1` — tabela `medical_evaluations` (FKs e índice composto).

## V7 (atual) — Notificações

### Domínio: `Backend/App/modules/notifications`

Fluxo: EVENTO → NotificationService → NotificationRepository → PostgreSQL.
Todas as notificações são criadas pela camada de serviço (`events.py` + `NotificationService.emit`) — nunca espalhadas nas rotas. Best-effort: falha de notificação nunca quebra o fluxo de negócio. Preparado para Queue/Worker/Email/Push/SMS no futuro (sem Kafka nesta versão).

#### Entidade Notification
| Campo | Tipo | Regras |
|---|---|---|
| id | int (PK) | gerado |
| user_id | int (FK users.id) | usuário só vê as próprias (403 caso contrário) |
| type | enum | CARE_REQUEST_CREATED/RECEIVED, QUEUE_POSITION/PRIORITY_CHANGED, CARE_REQUEST_REFERRED, APPOINTMENT_AVAILABLE/SCHEDULED/CANCELLED/RESCHEDULED, PATIENT_STATUS_UPDATED, MEDICAL_EVALUATION_CREATED, DOCUMENT_RECEIVED |
| title | str | até 200 caracteres |
| message | str | até 500 caracteres |
| read | bool | marcar como lida NÃO apaga (histórico preservado) |
| related_resource_type / related_resource_id | opcional | direciona ao atendimento correspondente |
| created_at | datetime | server_default now |

#### Endpoints
- `GET /api/v1/notifications/user/{user_id}` — lista (mais recente primeiro).
- `GET /api/v1/notifications/{id}?user_id=` — detalhe (403 de outro usuário, 404).
- `PATCH /api/v1/notifications/{id}/read?user_id=` — marca como lida.

#### Eventos integrados (automaticamente)
- CareRequest criada → paciente recebe "Solicitação recebida".
- Fila criada / posição alterada → paciente recebe "Sua posição na fila foi atualizada.".
- Prioridade alterada → paciente recebe "Sua solicitação foi atualizada.".
- PatientStatusUpdate criada → contexto autorizado (DOCTOR/NURSE/RECEPTIONIST/HOSPITAL/ADMIN) recebe "Nova atualização do paciente disponível.".
- MedicalEvaluation criada → paciente recebe "Seu atendimento recebeu uma nova atualização.".
- Appointment agendada → paciente recebe "Consulta agendada.".

### Frontend web (V7)
- Sino 🔔 com contador de não lidas + aba de notificações (marcar uma/todas como lidas).

### Mobile (V7)
- Tela 🔔 Notificações com ícones por tipo e "marcar todas como lidas".

### Migration
- `f7a8b9c0d1e2` — tabela `notifications` (FK users.id + índice composto).

## Fora do escopo da V7 (não implementar)
Kafka/mensageria, e-mail/push/SMS, RBAC completo, IA.

## V8 (atual) — Dashboards e Analytics
### Domínios: `Backend/App/modules/dashboards` e `Backend/App/modules/analytics`

Camada de LEITURA (apresentação + decisão), sem regras novas de negócio e sem tabelas novas. Arquitetura:

```text
Dashboard  →  Analytics Service  →  Analytics Repository  →  PostgreSQL
```

#### Dashboards (por perfil)
- `GET /api/v1/dashboard/patient/{patient_id}` — próxima consulta, solicitações abertas, filas (prioridade/posição/status), última atualização, notificações, próximo passo. Responde "Como está meu atendimento?".
- `GET /api/v1/dashboard/doctor/{doctor_id}` — casos recebidos, aguardando avaliação (último relato de cada solicitação aberta), consultas do dia, filas ativas. Só dados de contexto profissional.
- `GET /api/v1/dashboard/hospital/{hospital_id}` — filas ativas, distribuição por especialidade, contagens (abertas/aguardando/concluídas).
- `GET /api/v1/dashboard/admin` — volumes de gestão: solicitações, atendimentos, espera média, distribuições por especialidade/hospital (mesma fonte do analytics — nunca dois cálculos para o mesmo número).

#### Analytics
- `GET /api/v1/analytics/overview` — COUNTs em um único SELECT com subqueries escalares.
- `GET /api/v1/analytics/specialties` e `/hospitals` — GROUP BY com SUM(CASE) para abertos.
- `GET /api/v1/analytics/wait-times` — AVG no banco (julianday no SQLite; EXTRACT(EPOCH) no Postgres) sobre esperas ENCERRADAS (COMPLETED/REMOVED).
- `GET /api/v1/analytics/priorities` e `/appointments` — distribuições operacionais.
- Filtros comuns: `start_date`, `end_date` (inclusivo), `specialty`, `hospital_id`. Janela invertida → 422.

### Regras de performance (V8)
1. Nenhuma métrica carrega listas completas para contar em Python — toda contagem/agrupamento/média é agregação SQL.
2. Queries de tela usam LIMIT explícito.
3. Limites de janela são EXCLUSIVOS no dia seguinte (evita perder registros de 00:00 do último dia).

### Casos vazios
Paciente/hospital/métrica sem dados respondem 200 com listas vazias e `average_wait_hours = null` — nunca erro.

## Fora do escopo da V8 (não implementar)
Observabilidade/plataforma de monitoramento, IA, ML, autenticação (V9), auditoria (V10).

## V9 (atual) — Segurança
### Domínio: `Backend/App/modules/auth`

```text
Request → JWT → Current User → Role → Permission → Resource Ownership → Service
```

#### Senhas (`security.py`)
- Hash PBKDF2-HMAC-SHA256 (600.000 iterações) + sal aleatório de 16 bytes POR senha.
- Por hash (irreversível) e não encryption (reversível com chave): vazamento do banco não expõe senhas.
- Formato versionado `pbkdf2_sha256$iter$salt$hash` permite subir iterações sem invalidar hashes.
- Verificação com `hmac.compare_digest` (tempo constante, anti timing-attack).

#### JWT (`security.py`)
- HS256 assinado com `SECRET_KEY` (ambiente, nunca código). Claims mínimas: `sub`, `role`, `type`, `iat`, `exp`, `jti` (id único — rotação sempre visível).
- Payload NÃO é criptografado → nenhum dado sensível no token.
- Access 30 min; refresh 7 dias com `type="refresh"` — um nunca vale como o outro.
- Riscos documentados: token roubado vale até expirar; revogação imediata exige state no servidor (futuro).

#### RBAC e permissões (`dependencies.py`)
- Papéis: PATIENT, DOCTOR, HOSPITAL, ADMIN (+ legados RECEPTIONIST/NURSE da V4, preservados).
- `get_current_user()`, `require_role()`, `require_permission()` reutilizáveis; matriz de permissões nomeadas num único lugar.

#### Resource ownership (`check_ownership`)
- "Role diz o que o usuário pode fazer; ownership verifica em qual recurso."
- Paciente autenticado só acessa recursos próprios (403 caso contrário); ADMIN acessa qualquer recurso.

#### Proteção das rotas existentes
- Routers passam a depender de `get_current_user`; quando há token: `patient_id`, `actor_id` e `professional_id` informados pelo cliente são SOBRESCRITOS pelos valores do token (cliente não é fonte de identidade).
- **Modo legado** (`ALLOW_LEGACY_AUTH=true`): sem header Authorization o comportamento V1–V8 é preservado (compatibilidade com frontends e testes); token PRESENTE e inválido SEMPRE falha 401. Produção: `ALLOW_LEGACY_AUTH=false`.
- `/auth/register` só aceita PATIENT/DOCTOR (ADMIN/HOSPITAL são provisionados — evita escalação de privilégio).
- Login com mensagem genérica (sem user enumeration); 401 para credenciais erradas.

#### Configuração e headers
- `SECRET_KEY` (ambiente), `ALLOW_LEGACY_AUTH`, `DEBUG=false` em config.py.
- Middleware de security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

#### Migration
- `a8b9c0d1e2f3` — coluna aditiva `users.password_hash` (nullable: usuários pré-V9 migram no fluxo de senha; nunca backfill de senha inventada).

## Fora do escopo da V9 (não implementar)
2FA/MFA, OAuth/SSO, revogação de tokens com state, rate limiting, auditoria (V10).
