# API — MED

Base: `http://localhost:8000/api/v1`

## Filas (V4)

### POST /queues
Cria uma entrada na fila a partir de uma solicitação de atendimento (CareRequest).
```json
{
  "care_request_id": 1,
  "specialty": "Cardiologia",
  "hospital_id": 3,
  "actor_id": 2
}
```
`201` → entrada criada com `status: "WAITING"`, `priority: "NORMAL"` e `position` no fim da fila ativa.
`404` → CareRequest inexistente. `422` → já existe entrada ativa na mesma especialidade.

### GET /queues/{queue_id}
Detalha a entrada na fila. `200` ou `404`.

### GET /queues/patient/{patient_id}
Lista as entradas de fila do paciente (todas as especialidades), ordenadas por posição. `200` → lista.

### GET /queues/{queue_id}/events
Histórico (timeline) imutável da entrada: CREATED, POSITION_CHANGED, PRIORITY_CHANGED, STATUS_CHANGED, REFERRED, REMOVED. `200` → lista em ordem cronológica. `404` → entrada inexistente.

### PATCH /queues/{queue_id}/priority
Altera a prioridade operacional (não clínica) e reorganiza a fila de forma determinística:
```json
{
  "priority": "HIGH",
  "actor_id": 2
}
```
Ordenação: `URGENT > HIGH > MEDIUM > NORMAL`; empate resolvido pelo menor `entered_at`. Para cada item movido é gerado `POSITION_CHANGED`; para a entrada alterada, `PRIORITY_CHANGED` com `actor_id` do responsável.
`200` → entrada atualizada. `403` → ator é paciente ou papel não autorizado. `404` → fila ou ator inexistente. `422` → prioridade inválida.

> **Nota de segurança:** a prioridade NÃO representa diagnóstico médico. O sistema não diagnostica nem decide prioridade clínica — apenas usuários autorizados do domínio alteram prioridade, e toda mudança fica registrada no histórico com o responsável.

## Solicitações

### POST /appointments/requests
Cria uma solicitação de consulta.
```json
{
  "patient_id": 1,
  "specialty": "Cardiologia",
  "preferred_date": "2030-05-20",
  "preferred_time": "09:00",
  "reason": "Dor no peito"
}
```
`201` → retorna a solicitação criada com `status: "REQUESTED"` e `created_at`.
`422` → dados inválidos (patient_id <= 0, specialty vazia, data/hora inválidas).

### GET /appointments/requests/patient/{patient_id}
Lista as solicitações do paciente (mais recentes primeiro). `200` → lista.

## Consultas

### POST /appointments
Agenda uma consulta a partir de uma solicitação.
```json
{
  "request_id": 1,
  "doctor_name": "Dra. Ana Souza",
  "hospital_name": "Hospital Central",
  "scheduled_at": "2030-06-01T10:00:00+00:00",
  "notes": "Levar exames anteriores"
}
```
`201` → consulta criada (`status: "SCHEDULED"`); a solicitação passa a `SCHEDULED`.
`404` → solicitação inexistente. `422` → data no passado ou solicitação CANCELLED/EXPIRED/SCHEDULED.

### GET /appointments/patient/{patient_id}
Lista consultas do paciente ordenadas por `scheduled_at`. `200` → lista.

### GET /appointments/{appointment_id}
Detalhe da consulta. `200` ou `404`.

## Outros
- `GET /health` → `{"status": "ok", "version": "4.0.0"}`
- Docs interativas: `/docs` (Swagger) e `/redoc`.

## Erros
```json
{"detail": "A consulta deve ser agendada para uma data/hora futura"}
```
`ValidationError` de negócio → 422; recurso inexistente → 404; payload inválido (Pydantic) → 422.
