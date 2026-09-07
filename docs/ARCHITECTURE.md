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
- `c4d5e6f7a8b9` — queues + queue_events (V4).
- `d5e6f7a8b9c0` — patient_status_updates (V5).
- `e6f7a8b9c0d1` — medical_evaluations (V6).
- `f7a8b9c0d1e2` — notifications (V7).

## Configuração
`App/core/config.py` (pydantic-settings): `DATABASE_URL` (default SQLite), `API_V1_PREFIX=/api/v1`. Entrypoint: `App/core/main.py`, com CORS liberado e `/health`.

## Frontends
- `frontend-web/` — React + Vite; telas: Dashboard, Minhas Solicitações, Nova Solicitação, Preciso de Atendimento, Minhas Filas (V4), Meu Estado (V5), Atendimento/Profissional (V6) e sino/aba de Notificações (V7).
- `mobile/` — React Native/Expo; telas equivalentes, incluindo Meu Estado (V5), Atendimento (Prof.) (V6) e Notificações (V7).

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

## Decisões da V4
- Domínio novo `Backend/App/modules/queues` seguindo router → service → repository; nada de V1/V2/V3 foi alterado em comportamento.
- `hospital_id` é opcional e sem FK: módulos de hospitais ainda não existem (mesma decisão de strings da V2).
- Prioridade inicial é sempre NORMAL: o sistema nunca sugere ou calcula prioridade clínica.
- Ordenação determinística centralizada no service (`PRIORITY_WEIGHT`): prioridade desc, depois entered_at asc e id asc como desempate estável.
- `QueueEvent` é append-only: nenhum endpoint ou regra apaga/atualiza eventos — o histórico é imutável pela lógica normal da aplicação.
- Sem JWT ainda: `actor_id` vem do payload; autorização V4 = papel do ator (PATIENT → 403; papéis RECEPTIONIST/NURSE/DOCTOR/ADMIN autorizados; outros → 403). JWT ficará para versão futura.
- `STATUS_CHANGED`, `REFERRED` e `REMOVED` já existem como tipos de evento no modelo; os endpoints de transição de status ficam para versão futura (não são escopo da V4).


## V5 — Estado do Paciente
- Domínio novo `Backend/App/modules/patient_status` (router → service → repository); migration `d5e6f7a8b9c0`.
- `PatientStatusUpdate` é append-only: cada POST cria novo registro; nada é sobrescrito.
- `state`/`symptoms`/`severity`/`description` são relatos literais. O service não deriva diagnóstico, prioridade ou mudança de status de fila.
- Endpoints: `POST /api/v1/patient-status`, `GET .../{id}`, `GET .../patient/{id}`, `GET .../request/{id}`.
- Frontend web: tela "Meu Estado"; mobile: tela simplificada com histórico.

## Decisões da V6
- Domínio novo `Backend/App/modules/medical_evaluations` (router → service → repository); migration `e6f7a8b9c0d1`.
- Separação explícita entre RELATO DO PACIENTE (`PatientStatusUpdate`, intacto) e AVALIAÇÃO PROFISSIONAL (`MedicalEvaluation`, append-only).
- `MedicalEvaluation` referencia o relato (`patient_status_update_id`) e a solicitação (`care_request_id`); coerência validada no service (422 se o relato não pertence à solicitação).
- Autorização mínima compatível com futura V9: usuário PATIENT não pode criar avaliação (403); profissional inexistente → 404.
- `queue_id` é opcional e sem FK (mesma decisão da V4 — módulo de hospitais não existe).
- Sem diagnóstico automático: `evaluation`/`recommendation` são texto literal do profissional.
- Frontend web: aba "Atendimento (Profissional)"; mobile: tela "Atendimento (Prof.)".

## Decisões da V7
- Domínio novo `Backend/App/modules/notifications` (router → service → repository) + `events.py`; migration `f7a8b9c0d1e2`.
- Criação de notificações centralizada em `NotificationService.emit` + emissores de evento em `events.py` — as rotas não criam notificações diretamente.
- Emissão é best-effort: uma falha de notificação nunca quebra o fluxo de negócio (rollback silencioso).
- `read=True` apenas marca como lida; nenhuma notificação é apagada pela aplicação (histórico preservado).
- Acesso: usuário só vê/marca as próprias notificações (403 caso contrário); sem JWT ainda — `user_id` vem da query.
- `related_resource_type/id` (opcionais, sem FK) permitem direcionar o usuário ao atendimento correspondente.
- Preparado para processamento assíncrono futuro (Queue/Worker/Email/Push/SMS) sem Kafka nesta versão.

## Decisões da V8
- Dois domínios novos de LEITURA: `Backend/App/modules/dashboards` (visões por perfil) e `Backend/App/modules/analytics` (métricas de negócio). Nenhuma tabela nova — dashboards leem os domínios existentes.
- Fluxo: Dashboard → Analytics Service → Analytics Repository → PostgreSQL. Router fino, regras no service, SQL agregado no repository.
- PERFORMANCE: toda métrica usa agregação no banco (COUNT/AVG/GROUP BY + SUM(CASE)); um único SELECT com subqueries escalares no overview; LIMIT explícito nas queries de tela. Queries importantes comentadas no repository (por que daquela forma, que problema resolvem, índices que ajudam).
- Tempo de espera = AVG(updated_at − entered_at) das esperas ENCERRADAS (COMPLETED/REMOVED) — entradas ativas seriam projeção, não medida. Dialetes isoladas no repository (julianday no SQLite, EXTRACT(EPOCH) no Postgres).
- Janelas de data com limite inferior inclusivo e superior EXCLUSIVO (dia seguinte 00:00) — evita perder registros de 00:00 e o clássico bug de BETWEEN.
- Casos vazios são respostas válidas (listas vazias / null), nunca erro.
- Sem JWT ainda (V9): dashboards e analytics abertos nesta versão, com restrição chegando na V9 sem mudar o formato da resposta.

## Decisões da V9
- Domínio novo `Backend/App/modules/auth` (schemas, security, service, dependencies, router); migration aditiva `a8b9c0d1e2f3` (users.password_hash, nullable).
- Primitivas de segurança SEM dependências externas: PBKDF2-HMAC-SHA256 (600k iterações + sal por senha) para hash; JWT HS256 manual (hmac stdlib) com claims mínimas + `jti`. Contrato permite trocar por passlib/PyJWT depois sem tocar nos demais módulos.
- Autorização em DUPLA camada: RBAC (papéis/permissões nomeadas centralizadas em `dependencies.py`) + resource ownership (`check_ownership` — paciente só acessa os próprios recursos; ADMIN passa).
- Identidade sempre derivada do token quando presente: routers sobrescrevem `patient_id`/`actor_id`/`professional_id` do payload pelos valores do token. Modo legado (`ALLOW_LEGACY_AUTH=true`) preserva o comportamento V1–V8 sem token — débito de transição documentado; em produção deve ser `false`.
- `/auth/register` restrito a PATIENT/DOCTOR (self-service); ADMIN/HOSPITAL são provisionados (anti escalação de privilégio).
- Mensagem de login genérica (sem user enumeration); token presente e inválido sempre 401, mesmo em modo legado.
- Security headers via middleware simples; SECRET_KEY/ALLOW_LEGACY_AUTH/DEBUG via ambiente.
