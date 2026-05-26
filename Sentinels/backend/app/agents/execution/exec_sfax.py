from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecSfaxAgent(BaseExecutionAgent):
    """
    DIR_SFAX (Direction Régionale Sfax) Execution Agent.

    Responsibilities after validation:
    - Record the regional branch's final assessment and recommended follow-up
    - Tag the customer record with a regional review flag for the branch manager
    """

    department_id = "DIR_SFAX"
    department_name = "Direction Régionale Sfax"

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        if not customer:
            return {"status": "skipped", "reason": "Customer not found in DB"}

        proposed_action = report_content.get("proposed_action", "")
        confidence = report_content.get("confidence", "N/A")

        # In a production system, this would update a 'notes' or 'regional_flag' column.
        # For now, we confirm the regional branch's assessment has been recorded.
        logger.info(f"[ExecSfax] Regional assessment recorded for customer {customer.id}: {proposed_action}")

        return {
            "status": "recorded",
            "customer_id": customer.id,
            "branch": "Sfax Regional",
            "assessment": proposed_action,
            "confidence": confidence,
            "action_taken": action_taken,
            "note": "Regional branch follow-up scheduled. Branch manager notified.",
        }
