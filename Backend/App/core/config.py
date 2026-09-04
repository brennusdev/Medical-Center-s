from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (MED V1 architecture preserved)."""

    PROJECT_NAME: str = "Medical Center API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./medical_center.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
