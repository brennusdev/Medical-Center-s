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

    PROJECT_NAME: str = "Medical Center API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./medical_center.db"

    # V9 — segredo dos JWT. NÃO colocar valor real no código/fonte.
    SECRET_KEY: str = "dev-only-change-me"
    # V9 — compatibilidade com V1–V8 (documentada em ARCHITECTURE.md).
    ALLOW_LEGACY_AUTH: bool = True
    # V9 — não vazar detalhes internos (stack traces) em produção.
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
