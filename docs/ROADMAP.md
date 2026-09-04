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

## V4+ — Backlog (fora do escopo da V3)
- [ ] Autenticação JWT e perfis (recepcionista/médico)
- [ ] Módulos de médicos e hospitais (substituir strings por FKs)
- [ ] Transições de status da consulta via endpoints
- [ ] Notificações/lembretes
- [ ] Filas de solicitações e prioridade clínica
- [ ] Recursos de IA (triagem/sugestão de agenda)
