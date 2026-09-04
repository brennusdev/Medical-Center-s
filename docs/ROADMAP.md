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

## V5+ — Backlog (fora do escopo da V4)
- [ ] Autenticação JWT e perfis (recepcionista/médico)
- [ ] Módulos de médicos e hospitais (substituir strings/hospital_id por FKs)
- [ ] Transições de status da fila via endpoints (STATUS_CHANGED/REFERRED/REMOVED)
- [ ] Notificações/lembretes
- [ ] Recursos de IA (triagem/sugestão de agenda)
