# ROADMAP — MED

## V1 — Fundação ✅
- [x] Estrutura em camadas (router / service / repository / schemas / models)
- [x] Núcleo: config, database, registro central de models, entrypoint
- [x] Domínio users
- [x] Infraestrutura Alembic

## V2 — Consultas e Agendamentos ✅ (atual)
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

## V3 — Candidatas (fora do escopo da V2)
- [ ] Autenticação JWT e perfis (paciente/recepcionista/médico)
- [ ] Módulos de médicos e hospitais (substituir `doctor_name`/`hospital_name` por FKs)
- [ ] Transições de status da consulta (CONFIRMED, CANCELLED, COMPLETED, EXPIRED) via endpoints
- [ ] Notificações/lembretes

## V4+ — Backlog
- [ ] Filas de solicitações e prioridade clínica
- [ ] Recursos de IA (triagem/sugestão de agenda)
