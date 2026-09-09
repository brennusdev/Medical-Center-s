"""MED V15 — Inteligência operacional (sem diagnóstico médico).

REGRAS DE SEGURANÇA (obrigatórias, herdadas de V4/V5/V8):
- Este módulo NÃO diagnostica, NÃO tria clinicamente e NÃO atribui prioridade.
- Toda saída é DESCRITIVA (o que já aconteceu) ou SUGESTIVA (operação), e a
  decisão final é sempre de um usuário autorizado do domínio.
- Nenhum dado entra aqui que não venha das tabelas operacionais existentes
  (care_requests, queues, patient_status, appointments) — sem modelo de ML
  externo nesta versão: heurísticas determinísticas e explicáveis.

Conteúdo:
- Congestionamento por especialidade (fila aberta vs. capacidade observada).
- Tempo médio de espera por especialidade (base para sugestão de agenda).
- Sinal de atenção: pacientes com piora de estado (WORSENED) e fila demorada —
  INFORMATIVO para o profissional, nunca uma decisão automática.
"""
