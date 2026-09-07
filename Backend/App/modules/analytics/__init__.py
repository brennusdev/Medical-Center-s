"""MED V8 — Domínio de Analytics (métricas de negócio).

Responsabilidade do módulo:
- expor métricas agregadas (COUNT/AVG/GROUP BY) para tomada de decisão;
- NÃO transformar o MED em plataforma de observabilidade: analytics é uma
  camada de apoio, o paciente continua sendo o centro do produto.

Camadas: router (HTTP) → service (regras/filtros) → repository (SQL agregado).
"""
