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
- [ ] Frontend web: dashboard do paciente V8 + telas de operação
- [ ] Mobile: dashboard compacto
- [x] Documentação atualizada (README, PROJECT_SPEC, ARCHITECTURE, ROADMAP, API)

## V9+ — Backlog (fora do escopo da V8)
- [ ] Autenticação JWT e perfis (recepcionista/médico)
- [ ] Módulos de médicos e hospitais (substituir strings/hospital_id por FKs)
- [ ] Transições de status da fila via endpoints (STATUS_CHANGED/REFERRED/REMOVED)
- [ ] Recursos de IA (triagem/sugestão de agenda)
- [ ] MED V8 — Dashboards
- [ ] MED V9 — Segurança
- [ ] MED V10 — Auditoria
- [ ] MED V11 — Banco avançado
- [ ] MED V12 — Infraestrutura
- [ ] MED V13 — Qualidade
- [ ] MED V14 — CI/CD
- [ ] MED V15 — Inteligência operacional
