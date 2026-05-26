from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecRisqueAgent(BaseExecutionAgent):
    """
    DIR_RISQUE Execution Agent.

    Responsibilities after validation:
    - Update the customer's risk_stage based on the agent's risk_level recommendation
    - Log the reclassification decision with justification
    """

    department_id = "DIR_RISQUE"
    department_name = "Direction Surveillance Risque Crédit"

    # Risk level → stage mapping aligned with BCT classification standards
    RISK_LEVEL_TO_STAGE = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        if not customer:
            return {"status": "skipped", "reason": "Customer not found in DB"}

        old_stage = customer.risk_stage
        risk_level = report_content.get("risk_level", "medium").lower()
        new_stage = self.RISK_LEVEL_TO_STAGE.get(risk_level, old_stage)

        # Only escalate, never auto-deescalate (requires a separate review)
        if new_stage > old_stage:
            customer.risk_stage = new_stage
            db.commit()
            logger.info(f"[ExecRisque] Customer {customer.id}: risk_stage {old_stage} → {new_stage}")
            return {
                "status": "updated",
                "customer_id": customer.id,
                "old_risk_stage": old_stage,
                "new_risk_stage": new_stage,
                "reason": f"Risk level '{risk_level}' from agent analysis. Action: {action_taken}",
            }
        else:
            return {
                "status": "unchanged",
                "customer_id": customer.id,
                "current_risk_stage": old_stage,
                "reason": f"Risk level '{risk_level}' does not warrant escalation from stage {old_stage}.",
            }
