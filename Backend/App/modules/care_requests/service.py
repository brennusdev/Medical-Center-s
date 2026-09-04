"""MED V3 — Business rules for care requests ("Preciso de atendimento").

REGRAS DE SEGURANÇA (obrigatórias):
- Sintomas, desconforto e descrição são RELATOS INFORMADOS PELO PACIENTE.
- O sistema NÃO diagnostica, NÃO afirma doença, NÃO determina emergência
  clínica, NÃO atribui prioridade clínica automaticamente e NÃO substitui
  avaliação profissional. Nenhum campo de saída é derivado desses relatos.

Regras de negócio aplicadas:
- patient_id deve ser um inteiro positivo;
- o usuário informado deve existir (404 caso contrário);
- o usuário informado deve ser um paciente (422 caso contrário).
"""

from sqlalchemy.orm import Session

from App.modules.care_requests.models import CareRequest, CareRequestStatus
from App.modules.care_requests.repository import CareRequestRepository
from App.modules.care_requests.schemas import CareRequestCreate


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class CareRequestService:
    def __init__(self, db: Session) -> None:
        self.repo = CareRequestRepository(db)

    def create(self, data: CareRequestCreate) -> CareRequest:
        if data.patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")

        user = self.repo.get_user(data.patient_id)
        if user is None:
            raise NotFoundError(f"Paciente {data.patient_id} não encontrado")

        if getattr(user, "role", "PATIENT") != "PATIENT":
            raise ValidationError(f"Usuário {data.patient_id} não é um paciente")

        care_request = CareRequest(
            patient_id=data.patient_id,
            reason=data.reason.strip(),
            specialty=data.specialty.strip(),
            symptoms=data.symptoms.strip(),
            description=data.description.strip(),
            cep=data.cep.strip(),
            referral=data.referral.strip(),
            discomfort_level=data.discomfort_level,
            symptom_onset=data.symptom_onset,
            notes=data.notes.strip(),
            status=CareRequestStatus.CREATED,
        )
        return self.repo.create(care_request)

    def get(self, request_id: int) -> CareRequest:
        care_request = self.repo.get(request_id)
        if care_request is None:
            raise NotFoundError(f"Solicitação {request_id} não encontrada")
        return care_request

    def list_by_patient(self, patient_id: int) -> list[CareRequest]:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        return self.repo.list_by_patient(patient_id)
