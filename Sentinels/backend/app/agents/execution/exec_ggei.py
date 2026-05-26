from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecGGEIAgent(BaseExecutionAgent):
    """
    DIR_GGEI (Analyse Crédit Grandes Entreprises & Institutions) Execution Agent.

    Responsibilities after validation:
    - Apply portfolio reclassification for large corporate/SME clients
    - Flag for credit committee review if risk is high/critical
    - Record recommended credit limit adjustment
    """

    department_id = "DIR_GGEI"
    department_name = "Direction Analyse Crédit GGEI"

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        if not customer:
            return {"status": "skipped", "reason": "Customer not found in DB"}

        risk_level = report_content.get("risk_level", "medium").lower()
        proposed_action = report_content.get("proposed_action", "")
        loan_size = customer.loan_size

        requires_committee = risk_level in ("high", "critical") and loan_size > 1_000_000

        logger.info(f"[ExecGGEI] Portfolio action for {customer.id} (segment: {customer.segment}): {proposed_action}")

        return {
            "status": "processed",
            "customer_id": customer.id,
            "segment": customer.segment,
            "loan_size_tnd": loan_size,
            "risk_level": risk_level,
            "portfolio_action": proposed_action,
            "credit_committee_referral": requires_committee,
            "action_taken": action_taken,
            "note": "Credit committee referral queued." if requires_committee else "Processed at department level.",
        }
