# ROADMAP — MED

## V1 — Fundação ✅
- [x] Estrutura em camadas (router / service / repository / schemas / models)
- [x] Núcleo: config, database, registro central de models, entrypoint
- [x] Domínio users
- [x] Infraestrutura Alembic

## V2 — Consultas e Agendamentos ✅
- [x] Domínio `App/modules/appointments`
- [x] Entidades `AppointmentRequest` e `Appointment` com enums de status
- [x] Endpoints: criação/listagem de solicitações, agendamento, listagem e detalhe de consultas
- [x] Regras de negócio no service (paciente válido, consulta futura, solicitação ativa, transição de status)
- [x] Migration Alembic da V2 + atualização do registro central de models
- [x] Router registrado no main.py
- [x] Testes automatizados (15 testes: criação, validações, paciente, consulta futura, relacionamento)
- [x] Frontend web: dashboard do paciente, minhas solicitações, próxima consulta, nova solicitação
- [x] Mobile: próxima consulta, pedir consulta, minhas solicitações
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, API)

## V3 — Preciso de Atendimento ✅ (atual)
- [x] Domínio `Backend/App/modules/care_requests` (models, schemas, repository, service, router)
- [x] Entidade `CareRequest` com status operacionais (CREATED, IN_REVIEW, REFERRED, SCHEDULED, CANCELLED, COMPLETED)
- [x] Endpoints: criação, detalhe por ID e listagem por paciente
- [x] Regras de segurança: relatos do paciente sem diagnóstico/triagem/prioridade automática; paciente inexistente (404); usuário não-paciente (422)
- [x] Coluna aditiva `users.role` (default PATIENT) + migration `b7c8d9e0f1a2`
- [x] Models registrados em `App/core/models.py`; router registrado no main.py
- [x] Testes (6 novos: criação, validação de campos, paciente inexistente, não-paciente, consulta por ID, listagem)
- [x] Frontend web: botão "Preciso de atendimento", formulário, lista de solicitações com status
- [x] Mobile: botão, formulário básico e visualização das solicitações
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP)

## V4 — Filas e Priorização ✅ (atual)
- [x] Domínio `Backend/App/modules/queues` (models, schemas, repository, service, router)
- [x] Entidades `Queue` e `QueueEvent` (histórico imutável, append-only) com enums de status, prioridade e tipo de evento
- [x] Endpoints: criação, detalhe, listagem por paciente, histórico e alteração de prioridade
- [x] Regras: duplicidade de fila ativa (422), posição inicial no fim, QueueEvent para toda alteração relevante
- [x] Reorganização determinística: URGENT > HIGH > MEDIUM > NORMAL; empate por entered_at; POSITION_CHANGED para cada item movido
- [x] Segurança: prioridade nunca automática/diagnóstica; paciente não altera prioridade (403); mudanças associadas ao actor_id
- [x] Migration `c4d5e6f7a8b9` + models registrados em `App/core/models.py`; router registrado no main.py
- [x] Testes (14 novos: criação, care request inexistente, duplicação, posição/prioridade inicial, alteração de prioridade, autorização, eventos, reorganização, listagem, histórico)
- [x] Frontend web: tela de filas com especialidade, status, prioridade, posição, datas e timeline
- [x] Mobile: prioridade, posição, status e histórico simplificado
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, API)

## V5 — Estado do Paciente ✅ (atual)
- [x] Domínio `Backend/App/modules/patient_status` (models, schemas, repository, service, router)
- [x] Entidade `PatientStatusUpdate` (state IMPROVED/STABLE/WORSENED, severity 0–10 subjetiva, relatos literais)
- [x] Endpoints: criação, detalhe, histórico por paciente e por solicitação
- [x] Regras: somente o dono da CareRequest registra (403); append-only; sem diagnóstico; sem alterar fila/prioridade
- [x] Migration `d5e6f7a8b9c0` + models registrados em `App/core/models.py`; router registrado no main.py
- [x] Testes (16 novos: criação, validações 404/403/422, severity fora da faixa, histórico, integração)
- [x] Frontend web: tela "Meu Estado" com formulário e histórico
- [x] Mobile: tela simplificada de estado + histórico
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP)

## V6 — Comunicação Paciente ↔ Profissional ✅ (atual)
- [x] Domínio `Backend/App/modules/medical_evaluations` (models, schemas, repository, service, router)
- [x] Entidade `MedicalEvaluation` (evaluation/recommendation textuais do profissional, relato original intacto)
- [x] Endpoints: criação, detalhe, listagem por solicitação; profissional visualiza relatos via patient-status/request
- [x] Regras: paciente não cria avaliação (403); profissional registrado (404/422); append-only; sem diagnóstico automático
- [x] Migration `e6f7a8b9c0d1` + models registrados em `App/core/models.py`; router registrado no main.py
- [x] Testes (10 novos: criação, 403 paciente, 404s, 422 de coerência, preservação do relato, integração)
- [x] Frontend web: aba "Atendimento (Profissional)" — atualizações do paciente + avaliação + histórico
- [x] Mobile: tela "Atendimento (Prof.)" — ver atualizações e registrar avaliação
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP)

## V7 — Notificações ✅ (atual)
- [x] Domínio `Backend/App/modules/notifications` (models, schemas, repository, service, router, events)
- [x] Entidade `Notification` com 12 tipos, `read` (não apaga), `related_resource_*` opcionais
- [x] Endpoints: listagem por usuário, detalhe e marcar como lida (403 de outro usuário)
- [x] Camada central de notificações (NotificationService.emit + events.py) integrada a: care_requests, queues, patient_status, medical_evaluations e appointments
- [x] Best-effort e ponto único de extensão para processamento assíncrono futuro (sem Kafka)
- [x] Migration `f7a8b9c0d1e2` + models registrados em `App/core/models.py`; router registrado no main.py
- [x] Testes (13 novos: criação por evento, listagem, usuário correto/incorreto, marcar como lida, histórico, integração)
- [x] Frontend web: sino 🔔 com contador + aba de notificações
- [x] Mobile: tela 🔔 Notificações
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP)

## V8 — Dashboards e Analytics ✅ (atual)
- [x] Domínio `Backend/App/modules/analytics` (schemas, repository, service, router) — métricas via agregação SQL (COUNT/AVG/GROUP BY)
- [x] Domínio `Backend/App/modules/dashboards` (schemas, service, router) — visões por perfil (paciente, médico, hospital, admin)
- [x] Endpoints: `/api/v1/dashboard/patient/{id}`, `/doctor/{id}`, `/hospital/{id}`, `/admin`; `/api/v1/analytics/overview`, `/specialties`, `/hospitals`, `/wait-times`, `/priorities`, `/appointments`
- [x] Filtros de período/especialidade/hospital com validação (janela invertida → 422)
- [x] Performance: agregação no banco, subqueries escalares no overview, LIMIT nas queries de tela, queries comentadas
- [x] Casos vazios cobertos (sem atendimento/consulta/fila/hospital)
- [x] Testes (16 novos: dashboards por perfil, contagem, agrupamento, tempo médio, filtros, casos vazios) — 92 no total, V1–V7 preservadas
- [x] Frontend web: dashboard do paciente V8 + telas de operação
- [ ] Mobile: dashboard compacto
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP, API)

## V9 — Segurança ✅ (atual)
- [x] Domínio `Backend/App/modules/auth` (schemas, security, service, dependencies, router)
- [x] `hash_password`/`verify_password` (PBKDF2-SHA256, 600k iterações, sal por senha) — nunca texto puro
- [x] Endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` (usuário sempre do token)
- [x] JWT HS256 com claims mínimas (sub, role, type, iat, exp, jti); access 30 min, refresh 7 dias com rotação
- [x] RBAC (PATIENT/DOCTOR/HOSPITAL/ADMIN) + permissões nomeadas centralizadas; legados RECEPTIONIST/NURSE preservados
- [x] Resource ownership (`check_ownership`): paciente não acessa recurso de outro paciente (403); ADMIN passa
- [x] Proteção das rotas existentes: care-requests, queues, patient-status, notifications, appointments (id derivado do token quando há token)
- [x] Migration `a8b9c0d1e2f3` (users.password_hash, aditiva/nullable) + SECRET_KEY/ALLOW_LEGACY_AUTH/DEBUG na config
- [x] Security headers + mensagens de erro genéricas no login (sem user enumeration)
- [x] Testes (22 novos: senha, login, token expirado/inválido, refresh, role, permission, ownership, regressão V1–V8) — 114 no total
- [ ] Frontend web: login + uso do token
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP, API)

## V10 — Auditoria ✅
- [x] `AuditLog` append-only com ator, recurso e valores anterior/novo (JSON)
- [x] Router de consulta ADMIN (`audit.read`)
- [x] Integração com eventos V4–V9

## V11 — Banco avançado ✅
- [x] Constraints (CHECK/UNIQUE), índices de leitura, paginação (limit/offset)
- [x] `check_database` (`SELECT 1` + latência, sem vazamento de credenciais)
- [x] Migration `c1d2e3f4a5b6`

## V12 — Infraestrutura ✅ (finalizada)
- [x] Logging estruturado JSON (stdout, padrão containers)
- [x] Envelope de erro global `{error, message, request_id}` + header X-Request-ID
- [x] Readiness/liveness separados (banco fora do liveness)
- [x] Dockerfile (3.12-slim, não-root, cache de camadas, healthcheck)
- [x] docker-compose: api + worker + postgres + redis com healthchecks
- [x] Workers: `TaskQueue` (abstração V12, ponto de extensão para Redis)
- [x] `.env.example` completo (nenhum secret real no repo)
- [x] Bug corrigido: ctx de `RequestValidationError` não era serializável (Python 3.14)

## V13 — Qualidade ✅ (finalizada)
- [x] `pytest.ini` (strict-markers, markers integration/security, filtro de warnings)
- [x] `.coveragerc` (fonte App, exclusões justificadas, show_missing)
- [x] Fixtures compartilhadas: `make_user`/`patient`/`doctor`/`admin`, `make_care_request`, `make_queue`
- [x] Cobertura total ~92% (138 testes)

## V14 — CI/CD ✅ (finalizada)
- [x] `.github/workflows/ci.yml`: ruff (lint+format), mypy, pytest com gate de cobertura 85%, build Docker
- [x] `ruff.toml` + `mypy.ini` graduais (estrito no novo, tolerante com legado)
- [x] Débitos técnicos limpos: `QueuePriorityLiteral` frágil → `Literal` tipado; 8 erros de mypy corrigidos; imports `__init__.py`;
- [x] Pipeline 100% verde local (ruff, mypy, 138 testes)

## V15 — Inteligência operacional ✅ (finalizada)
- [x] Domínio `Backend/App/modules/intelligence` (schemas, repository, service, router)
- [x] `GET /api/v1/intelligence/summary`: carga por especialidade (LOW/MEDIUM/HIGH), tempo médio de espera, sinais de atenção
- [x] Heurísticas determinísticas e explicáveis (`reason` textual); SOMENTE LEITURA; sem diagnóstico/triagem automática
- [x] 12 testes novos (carga, esperas, sinais, contrato, read-only, integração) — 138 no total

## Backlog futuro
- [ ] Fila Redis real substituindo `TaskQueue` em memória (contrato já estável)
- [ ] Autenticação obrigatória em produção (`ALLOW_LEGACY_AUTH=false`)
- [ ] Frontends consumindo token (V9) e sinais de atenção (V15)
- [ ] IA assistiva FUTURA: apenas sugestão explicável sujeita a aprovação humana
