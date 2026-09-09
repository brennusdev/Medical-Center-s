"""MED V15 — Service do módulo intelligence.

Heurísticas DETERMINÍSTICAS e EXPLICÁVEIS (sem ML externo, sem diagnóstico):
- Carga por especialidade: LOW ≤2 abertas, MEDIUM ≤6, HIGH >6. Constantes
  nomeadas no topo — ajustáveis por operação, nunca por modelo opaco.
- Sinal de atenção: WORSENED + espera > ATTENTION_THRESHOLD_HOURS (default 48h).
  A saída inclui `reason` textual — cada sinal se explica sozinho (auditável).

O service nunca escreve no banco: quem age sobre um sinal é um profissional
autorizado, usando os endpoints existentes (prioridade da fila V4, avaliação V6).
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from App.modules.intelligence.repository import IntelligenceRepository
from App.modules.intelligence.schemas import (
    AttentionSignal,
    IntelligenceSummary,
    SpecialtyLoad,
    WaitTimeInsight,
)

# Limiares operacionais (não clínicos!) — nomeados para serem auditáveis.
LOAD_MEDIUM_THRESHOLD = 2   # abertas > 2 → pelo menos MEDIUM
LOAD_HIGH_THRESHOLD = 6     # abertas > 6 → HIGH
ATTENTION_THRESHOLD_HOURS = 48.0


class IntelligenceService:
    def __init__(self, db: Session) -> None:
        self.repo = IntelligenceRepository(db)

    @staticmethod
    def _load_level(open_queues: int) -> str:
        if open_queues > LOAD_HIGH_THRESHOLD:
            return "HIGH"
        if open_queues > LOAD_MEDIUM_THRESHOLD:
            return "MEDIUM"
        return "LOW"

    def specialty_loads(self) -> list[SpecialtyLoad]:
        return [
            SpecialtyLoad(
                specialty=specialty,
                open_queues=open_count,
                urgent_count=urgent,
                level=self._load_level(open_count),
            )
            for specialty, open_count, urgent in self.repo.open_queues_by_specialty()
        ]

    def wait_time_insights(self) -> list[WaitTimeInsight]:
        return [
            WaitTimeInsight(specialty=specialty, average_wait_hours=hours, samples=samples)
            for specialty, hours, samples in self.repo.completed_wait_by_specialty()
        ]

    def attention_signals(self) -> list[AttentionSignal]:
        signals: list[AttentionSignal] = []
        for queue in self.repo.long_waiting_with_worsening(ATTENTION_THRESHOLD_HOURS):
            hours = self.repo.hours_waiting(queue)
            patient_id = self.repo.patient_of(queue.care_request_id)
            signals.append(
                AttentionSignal(
                    queue_id=queue.id,
                    patient_id=patient_id,
                    care_request_id=queue.care_request_id,
                    specialty=queue.specialty,
                    priority=queue.priority.value,
                    position=queue.position,
                    hours_waiting=hours,
                    last_state="WORSENED",
                    reason=(
                        f"Paciente relatou piora do estado e aguarda há {hours}h "
                        f"na fila de {queue.specialty} (posição {queue.position}). "
                        "Revisão humana recomendada — o sistema NÃO altera prioridade."
                    ),
                )
            )
        return signals

    def summary(self) -> IntelligenceSummary:
        return IntelligenceSummary(
            generated_at=datetime.now(UTC),
            loads=self.specialty_loads(),
            wait_times=self.wait_time_insights(),
            attention_signals=self.attention_signals(),
        )
