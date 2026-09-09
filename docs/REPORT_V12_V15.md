# RELATÓRIO CONSOLIDADO — MED V12 a V15

Data: 2026 · Status: **concluído e verificado** (138 testes, ruff/mypy limpos, cobertura ~92%)

---

## V12 — Infraestrutura ✅

**Já existia e foi auditado; um bug latente foi corrigido.**

| Item                                                                            | Arquivo                         | Estado      |
| ------------------------------------------------------------------------------- | ------------------------------- | ----------- |
| Wiring completo (todos os routers + health + security headers + error envelope) | `Backend/App/core/main.py`      | ✅ auditado |
| Dockerfile (python:3.12-slim, não-root, cache de camadas, HEALTHCHECK)          | `Backend/Dockerfile`            | ✅          |
| Compose: api + worker + postgres + redis (healthchecks, volumes, redes)         | `docker-compose.yml`            | ✅          |
| Workers: `TaskQueue` (abstração extensível para Redis) + loop standalone        | `Backend/App/workers/base.py`   | ✅          |
| `.env.example` (SECRET*KEY, DATABASE_URL, POSTGRES*\*, REDIS_URL, DEBUG)        | `.env.example`                  | ✅          |
| Readiness/liveness separados; `check_database` sem vazamento de credenciais     | `App/core/health.py`, `main.py` | ✅          |

**Bug corrigido (V12):** o handler global de `RequestValidationError` serializava
`exc.errors()` cru; no Python 3.14/pydantic 2.10 o `ctx` embute objetos
`ValueError` não serializáveis → 500 em qualquer 422 de validação customizada.
Correção: `_sanitize_errors()` em `App/core/error_handlers.py` converte `ctx` para `str`.
Teste que expunha o bug (`test_register_short_password_422`) voltou a passar.

## V13 — Qualidade ✅

- **`Backend/pytest.ini`** — testpaths, `--strict-markers`, markers `integration`/`security`, filtro de `StarletteDeprecationWarning` (vem da lib, não do código).
- **`Backend/.coveragerc`** — source `App`, exclusões justificadas (alembic, `pragma: no cover`, blocos `__main__`), `show_missing`.
- **`Backend/tests/conftest.py` ampliado** — fixtures fábrica compartilhadas: `make_user` (+ `patient`/`doctor`/`admin`), `make_care_request`, `make_queue` (posição calculada por especialidade). Elimina as cópias divergentes `_mk_user` espalhadas pelos testes.
- Cobertura: **~92% total** (2056 stmts, 160 miss).

## V14 — CI/CD ✅

- **`.github/workflows/ci.yml`** — 3 jobs:
  1. `quality`: ruff check + `ruff format --check` + mypy;
  2. `tests`: pytest com `--cov-fail-under=85`;
  3. `docker`: build da imagem (depende de `tests`).
     Python 3.12 (mesma versão do Dockerfile), cache de pip.
- **`Backend/ruff.toml`** — E/W/F/I/B/UP; ignorados com justificativa: `E501` (formatter), `B008` (idioma do FastAPI: `Depends()` em defaults), `B904` (estilo atual de HTTPException).
- **`Backend/mypy.ini`** — gradual: `check_untyped_defs` global, tolerante com módulos legados.
- **`requirements.txt`** — +`pytest-cov`, `ruff`, `mypy`, `psycopg2-binary`.
- **Débitos técnicos eliminados nesta versão:**
  - `QueuePriorityLiteral` (alias frágil via try/except no fim de `queues/schemas.py`) → `PriorityLiteral = Literal[...]` tipado;
  - 8 erros de mypy corrigidos (`get_db` Generator, `verify_password` reatribuição, `configure_logging`, dashboards usando `AnalyticsFilters` real, router de filas convertendo Literal→enum);
  - `__init__.py` criados em todos os pacotes (exigência do mypy);
  - variáveis não usadas (`q2` em teste, `queue` no worker) removidas;
  - bug real encontrado pelo lint: `update_priority` quebrava quando recebia `str` (contrato novo) — agora aceita enum **ou** string (defesa em profundidade).
- Verificação local: **ruff: All checks passed · mypy: no issues in 87 files · 138 passed**.

## V15 — Inteligência operacional ✅

Novo domínio `Backend/App/modules/intelligence` (camadas padrão do projeto):

- **`schemas.py`** — `SpecialtyLoad`, `WaitTimeInsight`, `AttentionSignal`, `IntelligenceSummary`.
- **`repository.py`** — somente leitura; agregação no banco (`COUNT/SUM/AVG/GROUP BY`); subquery "último relato por solicitação" (append-only ⇒ max id); espera via `julianday` (dias→horas).
- **`service.py`** — heurísticas determinísticas e nomeadas:
  - carga: LOW ≤2 · MEDIUM ≤6 · HIGH >6 filas abertas;
  - sinal de atenção: último relato `WORSENED` **e** espera > 48h; cada sinal traz `reason` textual explicável;
  - **nunca escreve** no banco e **nunca altera** fila/prioridade.
- **`router.py`** — `GET /api/v1/intelligence/summary`, registrado no `main.py`.
- **`tests/test_intelligence.py`** — 12 testes: níveis de carga, contagem de urgentes, tempo médio de espera, sinal positivo e negativos (estado estável / espera curta), contrato do endpoint, **read-only garantido por teste**, integração ponta a ponta.

## Garantia de segurança (transversal)

- Nenhum diagnóstico/triagem/prioridade automática em **nenhuma** versão.
- Auditoria (V10) continua append-only; inteligência (V15) é read-only.
- Nenhum secret no repositório (`.env` ignorado; `.env.example` só placeholders).
- Erros internos nunca expõem stack trace; `request_id` correlaciona log↔cliente.

## Como verificar tudo (reprodução)

```powershell
cd Backend
python -m pytest --cov=App --cov-report=term   # 138 passed, ~92%
python -m ruff check App tests                 # All checks passed
python -m mypy App                             # Success: no issues in 87 files
# CI: push no repo dispara .github/workflows/ci.yml
# Docker: copie .env.example -> .env na raiz e rode `docker compose up --build`
```

## Próximos passos sugeridos (backlog)

1. Trocar `TaskQueue` em memória por fila Redis (contrato `enqueue/run_forever` já estável).
2. Produção: `ALLOW_LEGACY_AUTH=false` + CORS restrito por origem.
3. Frontend/mobile: login com token (V9) e visual dos sinais de atenção (V15).
4. Migrations para Postgres no compose (`alembic upgrade head` no startup do container).

---

# AUDITORIA PRÉ-DEPLOY (segurança + prontidão)

## Riscos encontrados e corrigidos nesta auditoria

| # | Risco | Gravidade | Correção |
|---|---|---|---|
| 1 | **Banco de dados versionado no git** (`Backend/medical_center.db` com estrutura clínica: users, care_requests, audit_logs) | ALTA | `git rm --cached` + `.gitignore` (`*.db`). Dados sensíveis agora vivem criptografados em `secure_data/` (ignorado). |
| 2 | **Nenhum `.gitignore` no projeto** — `.env`, `__pycache__`, `.coverage`, `secure_data/` seriam commitados a qualquer `git add .` | ALTA | `.gitignore` completo criado (secrets, bancos, caches, IDE). |
| 3 | **89 arquivos `.pyc`/caches versionados** (código compilado pode vazar caminhos/constantes) | MÉDIA | Removidos do índice; 111 `.py` mantidos. |
| 4 | **CORS `allow_origins=["*"]` com `allow_credentials=True`** | MÉDIA (produção) | Configuração FastAPI rejeita essa combinação de forma efetiva para cookies, mas a origem curinga deve ser trocada por domínios reais no deploy (já documentado; variável de ambiente recomendada no backlog). |
| 5 | **Modo legado de auth ligado por padrão** (`ALLOW_LEGACY_AUTH=true`) | MÉDIA (produção) | Mantido para dev/testes; checklist de deploy exige `ALLOW_LEGACY_AUTH=false` + `SECRET_KEY` forte via ambiente. |

## Verificações aprovadas (sem intervenção)

- **Sem secrets no código**: varredura de `SECRET/PASSWORD/API_KEY/TOKEN` com valores longos → 0 ocorrências; `SECRET_KEY` default é placeholder `dev-only-change-me`.
- **SQL**: nenhuma query construída por f-string; única chamada `text()` é o `SELECT 1` do healthcheck → sem injeção de SQL.
- **Senhas**: PBKDF2-SHA256 600k iterações + sal por senha; comparação em tempo constante.
- **JWT**: assinatura verificada sempre; token presente e inválido → 401 mesmo em modo legado.
- **Ownership/RBAC**: 403 testado para recursos de terceiros.
- **Erros**: stack trace nunca na resposta; `request_id` no log e no header.
- **Inteligência (V15)**: read-only garantido por teste.
- **Suíte pós-auditoria**: 138 passed · 92% cobertura · ruff clean · mypy clean.

## Criptografia dos dados (nova)

`secure_data/` contém os dados importantes cifrados:

- `medical_center.db.enc` — banco SQLite (estrutura clínica completa)
- `.coverage.enc` — relatório de cobertura interno

Ferramenta: `scripts/secure_data.py` — Fernet (AES-128-CBC + HMAC-SHA256, autenticado),
chave derivada da senha-mestra via PBKDF2-SHA256 (600k iterações, sal aleatório por arquivo).
Senha pedida via `getpass` (nunca em argumento de comando). Senha errada/arquivo adulterado → falha limpa, sem dados parciais.

```powershell
python scripts/secure_data.py encrypt   # cifra Backend/medical_center.db -> secure_data/
python scripts/secure_data.py list      # lista a pasta protegida
python scripts/secure_data.py decrypt   # restaura (pede a senha-mestra)
```

> **Importante:** a senha-mestra NÃO é armazenada em lugar algum do projeto — sem ela os `.enc` são irrecuperáveis por design. Guarde-a em cofre de senhas. Para automatizar (CI/backup), defina `MED_DATA_PASSWORD` no ambiente da máquina, nunca no repositório.

## Checklist de deploy (produção)

1. `ALLOW_LEGACY_AUTH=false`
2. `SECRET_KEY` forte e exclusiva via secret manager (`openssl rand -hex 32`)
3. `DEBUG=false`
4. CORS: `allow_origins` com os domínios reais do frontend
5. `DATABASE_URL` apontando para PostgreSQL (não SQLite) + `alembic upgrade head`
6. Trocar `POSTGRES_PASSWORD` default do compose
7. Usuário admin provisionado manualmente (auto-registro só PATIENT/DOCTOR)
8. TLS terminado no proxy reverso (a API não faz TLS)
9. Opcional: purgar o `.db` do histórico git (`git filter-repo`) se o repo já foi publicado
