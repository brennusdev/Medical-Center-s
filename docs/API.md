# API — MED V2

Base: `http://localhost:8000/api/v1`

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
- `GET /health` → `{"status": "ok", "version": "2.0.0"}`
- Docs interativas: `/docs` (Swagger) e `/redoc`.

## Erros
```json
{"detail": "A consulta deve ser agendada para uma data/hora futura"}
```
`ValidationError` de negócio → 422; recurso inexistente → 404; payload inválido (Pydantic) → 422.
