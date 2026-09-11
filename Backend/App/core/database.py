#
# ÁREA: CONEXÃO COM O BANCO DE DADOS (core/database.py)
# Responsabilidade: criar engine SQLAlchemy, a SessionLocal (fábrica de
# sessões) e a Base (classe-mãe de todos os models/ORM).
# Padrão: TODA rota recebe a sessão via Depends(get_db) — nunca criar
# sessão manualmente nos módulos.
#
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from App.core.config import settings


# ÁREA: BASE ORM — todos os models de App/modules/* herdam desta classe.
# É ela que registra as tabelas para o Alembic (migrations) e create_all.
class Base(DeclarativeBase):
    pass


# ÁREA: ENGINE — pool de conexões. `check_same_thread=False` é necessário
# APENAS para SQLite (FastAPI usa threads); ignorado para outros bancos.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

# ÁREA: FÁBRICA DE SESSÕES — autocommit/autoflush desligados: o código
# decide quando commitar (transações explícitas = previsibilidade).
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    # ÁREA: DEPENDENCY DE SESSÃO — abre uma sessão por requisição.
    # O `yield` entrega a sessão para a rota; o `finally` garante o
    # fechamento mesmo se a rota lançar exceção (sem vazamento de conexões).
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
