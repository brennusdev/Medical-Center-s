"""MED V8 — Domínio de Dashboards.

Visões pessoais/operacionais por perfil:
- Patient: "Como está meu atendimento?"
- Doctor: casos recebidos e aguardando avaliação.
- Hospital: fila operacional por especialidade.
- Admin: apenas números de gestão (usa o módulo de analytics).

Os dashboards são CAMADA DE APRESENTAÇÃO: leem os mesmos domínios
(care_requests, queues, patient_status, notifications, appointments) sem
duplicar regras de negócio — nenhum dado é calculado aqui que já não exista
nos serviços de origem.
"""
