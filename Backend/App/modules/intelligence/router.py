"""MED V15 — Router do módulo intelligence.

Somente leitura. Em produção, restringir a perfis operacionais
(DOCTOR/ADMIN) via require_role — em modo legado (ALLOW_LEGACY_AUTH=true)
o comportamento segue o padrão das demais rotas do projeto.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import get_current_user
from App.modules.intelligence.schemas import IntelligenceSummary
from App.modules.intelligence.service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def get_service(db: Session = Depends(get_db)) -> IntelligenceService:
    return IntelligenceService(db)


@router.get(
    "/summary",
    response_model=IntelligenceSummary,
    summary="Resumo de inteligência operacional (carga, esperas, sinais de atenção)",
)
def summary(
    service: IntelligenceService = Depends(get_service),
    _user=Depends(get_current_user),
) -> IntelligenceSummary:
    """Agregado descritivo/sugestivo. NUNCA contém diagnóstico nem decisão clínica."""
    return service.summary()
