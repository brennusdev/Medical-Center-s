#
# ÁREA: CONFIGURAÇÃO CENTRAL (core/config.py)
# Responsabilidade: única fonte de verdade das configurações da aplicação.
# Usa pydantic-settings: cada atributo abaixo pode ser sobrescrito por
# variável de ambiente ou pelo arquivo .env (env_file abaixo) — os valores
# no código são apenas defaults de desenvolvimento.
# `settings` (instância única no final) é importado por todo o projeto.
#
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (MED V1 architecture preserved).

    V9 (segurança):
    - SECRET_KEY assina os JWT. DEVE vir de ambiente (.env) em produção — o
      default existe apenas para desenvolvimento/testes nunca quebrarem.
    - ACCESS_TOKEN_MINUTES/REFRESH_TOKEN_DAYS ficam no módulo auth (security.py).
    - ALLOW_LEGACY_AUTH: durante a transição V8→V9, permite que endpoints
      antigos continuem aceitando ids explícitos sem token (testes V1–V8 e
      frontends existentes). Em produção deve ser False: aí toda rota
      protegida exige Bearer token.
    """

    # ÁREA: IDENTIDADE DA API — nome exibido no /docs e prefixo das rotas.
    # Todas as rotas de negócio ficam em /api/v1/... (versionamento).
    PROJECT_NAME: str = "Medical Center API"
    API_V1_PREFIX: str = "/api/v1"
    # ÁREA: BANCO DE DADOS — SQLAlchemy usa essa URL. Default: SQLite local
    # (arquivo medical_center.db). Em produção, apontar para Postgres via .env.
    DATABASE_URL: str = "sqlite:///./medical_center.db"

    # ÁREA: SEGURANÇA (V9) — os 3 flags abaixo controlam auth/debug.
    # V9 — segredo dos JWT. NÃO colocar valor real no código/fonte.
    SECRET_KEY: str = "dev-only-change-me"
    # V9 — compatibilidade com V1–V8 (documentada em ARCHITECTURE.md).
    ALLOW_LEGACY_AUTH: bool = True
    # V9 — não vazar detalhes internos (stack traces) em produção.
    DEBUG: bool = False

    # ÁREA: CONFIG DO PYDANTIC — lê o arquivo .env; `extra="ignore"` ignora
    # variáveis de ambiente não mapeadas (comum em containers/CI).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# ÁREA: SINGLETON — única instância, importada como `from ...config import settings`.
settings = Settings()
