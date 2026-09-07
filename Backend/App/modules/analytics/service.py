"""MED V8 — Serviço de Analytics.

Responsabilidade: aplicar/validar filtros, delegar SQL ao repository e
traduzir resultados para os schemas. Nenhuma query vive aqui e nenhuma regra
de negócio vive no router — segue a arquitetura em camadas do MED.

Fluxo de aprendizagem:
    query params (HTTP) → AnalyticsFilters (validação) → Service → Repository (SQL) → Schema (resposta)
"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from App.modules.analytics.repository import AnalyticsRepository, _day_start
from App.modules.analytics.schemas import AnalyticsFilters


class ValidationError(Exception):
    """Violação de regra de negócio (422 no transporte)."""


def _window(f: AnalyticsFilters) -> tuple[datetime | None, datetime | None]:
    """Converte a janela de datas para limites datetime em UTC.

    `end_date` é inclusivo para o usuário (2026-01-31 significa "o dia 31
    inteiro"); internamente viramos isso em um limite EXCLUSIVO no dia seguinte
    (ver _day_end_exclusive no repository).
    """
    if f.start_date and f.end_date and f.start_date > f.end_date:
        raise ValidationError("start_date não pode ser maior que end_date")
    start = _day_start(f.start_date) if f.start_date else None
    from App.modules.analytics.repository import _day_end_exclusive

    end = _day_end_exclusive(f.end_date) if f.end_date else None
    return start, end


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repo = AnalyticsRepository(db)
        self.db = db

    def _filters(self, f: AnalyticsFilters) -> AnalyticsFilters:
        # Validação centralizada: qualquer endpoint chama isto primeiro.
        f.validate_window()
        return f

    def overview(self, f: AnalyticsFilters) -> dict[str, int]:
        self._filters(f)
        start, end = _window(f)
        return self.repo.overview_counts(start, end, f.specialty, f.hospital_id)

    def specialties(self, f: AnalyticsFilters) -> list[dict]:
        self._filters(f)
        start, end = _window(f)
        return self.repo.by_specialty(start, end, f.specialty)

    def hospitals(self, f: AnalyticsFilters) -> list[dict]:
        self._filters(f)
        start, end = _window(f)
        return self.repo.by_hospital(start, end, f.hospital_id)

    def wait_times(self, f: AnalyticsFilters) -> dict:
        self._filters(f)
        start, end = _window(f)
        return self.repo.wait_times(start, end, f.specialty, f.hospital_id)

    def appointments_by_period(self, f: AnalyticsFilters) -> list[dict]:
        self._filters(f)
        start, end = _window(f)
        return self.repo.appointments_by_period(start, end, f.specialty)

    def priorities(self, f: AnalyticsFilters) -> list[dict]:
        self._filters(f)
        start, end = _window(f)
        return self.repo.priority_distribution(start, end, f.specialty, f.hospital_id)
