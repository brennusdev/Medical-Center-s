"""MED V5 — Business rules for patient status updates.

REGRAS DE SEGURANÇA (obrigatórias):
- state/symptoms/severity/description são RELATOS INFORMADOS PELO PACIENTE.
- O sistema NÃO diagnostica, NÃO interpreta a severidade clinicamente, NÃO
  altera prioridade da fila e NÃO altera status da CareRequest a partir
  destes relatos. Nenhum campo de saída é derivado deles.

Regras de negócio aplicadas:
- Somente o próprio paciente registra sua atualização;
- A atualização deve estar vinculada a uma CareRequest existente (404);
- O paciente deve ser o proprietário da CareRequest (403);
- O paciente informado deve existir e ter papel PATIENT (404/422);
- Histórico é append-only: cada POST cria um novo registro.
"""

from sqlalchemy.orm import Session

from App.modules.patient_status.models import PatientState, PatientStatusUpdate
from App.modules.patient_status.repository import PatientStatusRepository
from App.modules.patient_status.schemas import PatientStatusUpdateCreate


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class AuthorizationError(Exception):
    """Actor not allowed to perform the operation."""


class PatientStatusService:
    def __init__(self, db: Session) -> None:
        self.repo = PatientStatusRepository(db)
        self.db = db

    def create(self, data: PatientStatusUpdateCreate) -> PatientStatusUpdate:
        user = self.repo.get_user(data.patient_id)
        if user is None:
            raise NotFoundError(f"Paciente {data.patient_id} não encontrado")
        if getattr(user, "role", "PATIENT") != "PATIENT":
            raise ValidationError(f"Usuário {data.patient_id} não é um paciente")

        care_request = self.repo.get_care_request(data.care_request_id)
        if care_request is None:
            raise NotFoundError(f"Solicitação {data.care_request_id} não encontrada")

        # Regra 3: apenas o dono da solicitação pode registrar seu estado.
        if care_request.patient_id != data.patient_id:
            raise AuthorizationError(
                "Somente o paciente responsável pela solicitação pode registrar atualizações"
            )

        update = PatientStatusUpdate(
            patient_id=data.patient_id,
            care_request_id=data.care_request_id,
            state=PatientState(data.state),
            symptoms=data.symptoms.strip(),  # relato literal, sem interpretação
            severity=data.severity,
            description=data.description.strip(),
            notes=data.notes.strip(),
        )
        created = self.repo.create(update)
        from App.modules.notifications.events import on_patient_status_updated
        on_patient_status_updated(self.db, created)
        return created

    def get(self, status_id: int) -> PatientStatusUpdate:
        update = self.repo.get(status_id)
        if update is None:
            raise NotFoundError(f"Atualização de estado {status_id} não encontrada")
        return update

    def list_by_patient(self, patient_id: int) -> list[PatientStatusUpdate]:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        user = self.repo.get_user(patient_id)
        if user is None:
            raise NotFoundError(f"Paciente {patient_id} não encontrado")
        return self.repo.list_by_patient(patient_id)

    def list_by_care_request(self, care_request_id: int) -> list[PatientStatusUpdate]:
        if care_request_id <= 0:
            raise ValidationError("care_request_id deve ser um inteiro positivo")
        if self.repo.get_care_request(care_request_id) is None:
            raise NotFoundError(f"Solicitação {care_request_id} não encontrada")
        return self.repo.list_by_care_request(care_request_id)
