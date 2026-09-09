# MED V12 — Dockerfile da API FastAPI.
#
# DECISÕES:
# - python:3.12-slim: imagem oficial, superfície menor que a full e com
#   suporte de segurança da upstream. Evitamos alpine por problemas com
#   wheels nativas (psycopg) que complicam builds reproduzíveis.
# - requirements instalados ANTES do código: o cache de camadas do Docker
#   só re-instala dependências quando requirements.txt muda, não a cada
#   alteração de código (build mais rápido em CI).
# - usuário não-root: o container nunca precisa de privilégios; rodar como
#   root amplifica o impacto de qualquer RCE na aplicação.
# - healthcheck local: uvicorn responde em /health (liveness).
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (cache de camadas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação por último (camada que muda sempre).
COPY . .

# Usuário sem privilégios (uid 1000, padrão de imagens Debian).
RUN useradd --create-home --uid 1000 meduser && chown -R meduser /app
USER meduser

EXPOSE 8000

# Healthcheck do container: liveness da própria API (sem dependências externas).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

# Uvicorn com 1 worker: escala horizontal é feita por réplicas de container
# (padrão 12-factor) e evita compartilhar pools de conexão no mesmo processo.
CMD ["uvicorn", "App.core.main:app", "--host", "0.0.0.0", "--port", "8000"]
