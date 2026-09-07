"""MED V6 — Business rules for professional medical evaluations.

REGRAS DE SEGURANÇA (obrigatórias):
- A avaliação é texto registrado por um profissional autorizado. O sistema não
  gera, interpreta ou transforma esse texto em diagnóstico automático.
- O relato original (PatientStatusUpdate) permanece intacto; a avaliação é
  append-only e referencia o relato.
- Paciente NÃO pode criar avaliação (403). Profissional inexistente → 404.
- Sem RBAC completo: apenas papel não-PATIENT é autorizado (estrutura
  compatível com a futura V9).
"""

from sqlalchemy.orm import Session

from App.modules.medical_evaluations.models import MedicalEvaluation
from App.modules.medical_evaluations.repository import MedicalEvaluationRepository
from App.modules.medical_evaluations.schemas import MedicalEvaluationCreate


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class AuthorizationError(Exception):
    """Actor not allowed to perform the operation."""


class MedicalEvaluationService:
    def __init__(self, db: Session) -> None:
        self.repo = MedicalEvaluationRepository(db)

    def create(self, data: MedicalEvaluationCreate) -> MedicalEvaluation:
        # Regra 2: profissional responsável deve existir e não pode ser paciente.
        professional = self.repo.get_user(data.professional_id)
        if professional is None:
            raise NotFoundError(f"Profissional {data.professional_id} não encontrado")
        if getattr(professional, "role", "PATIENT") == "PATIENT":
            raise AuthorizationError("Paciente não pode criar avaliação profissional")

        # Regra 7/8: o relato avaliado deve existir e pertencer à CareRequest.
        status_update = self.repo.get_status_update(data.patient_status_update_id)
        if status_update is None:
            raise NotFoundError(
                f"Atualização de estado {data.patient_status_update_id} não encontrada"
            )

        care_request = self.repo.get_care_request(data.care_request_id)
        if care_request is None:
            raise NotFoundError(f"Solicitação {data.care_request_id} não encontrada")

        if status_update.care_request_id != data.care_request_id:
            raise ValidationError("A atualização avaliada não pertence à solicitação informada")

        evaluation = MedicalEvaluation(
            patient_status_update_id=data.patient_status_update_id,
            care_request_id=data.care_request_id,
            professional_id=data.professional_id,
            evaluation=data.evaluation.strip(),  # texto literal, sem interpretação
            recommendation=data.recommendation.strip(),
            queue_id=data.queue_id,
        )
        return self.repo.create(evaluation)

    def get(self, evaluation_id: int) -> MedicalEvaluation:
        evaluation = self.repo.get(evaluation_id)
        if evaluation is None:
            raise NotFoundError(f"Avaliação {evaluation_id} não encontrada")
        return evaluation

    def list_by_care_request(self, care_request_id: int) -> list[MedicalEvaluation]:
        if care_request_id <= 0:
            raise ValidationError("care_request_id deve ser um inteiro positivo")
        if self.repo.get_care_request(care_request_id) is None:
            raise NotFoundError(f"Solicitação {care_request_id} não encontrada")
        return self.repo.list_by_care_request(care_request_id)
