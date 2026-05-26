from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecGarantiesAgent(BaseExecutionAgent):
    """
    DIR_GARANTIES (Direction Garanties & Sûretés) Execution Agent.

    Responsibilities after validation:
    - Record the collateral/guarantee valuation decision
    - Flag collateral for revaluation if risk level is high/critical
    - Trigger legal proceedings notification if exposure is uncollateralized
    """

    department_id = "DIR_GARANTIES"
    department_name = "Direction Garanties & Sûretés"

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
        confidence = report_content.get("confidence", "N/A")

        # Determine collateral action based on risk severity
        requires_revaluation = risk_level in ("high", "critical")
        legal_escalation = risk_level == "critical"

        # Estimated coverage gap — placeholder logic
        # In production: compare loan_size vs. registered collateral value from a guarantees table
        loan_size = customer.loan_size
        estimated_coverage_gap = loan_size * 0.30 if requires_revaluation else 0.0

        logger.info(f"[ExecGaranties] Collateral action for {customer.id}: revaluation={requires_revaluation}, legal={legal_escalation}")

        return {
            "status": "processed",
            "customer_id": customer.id,
            "risk_level": risk_level,
            "collateral_revaluation_required": requires_revaluation,
            "legal_escalation_triggered": legal_escalation,
            "estimated_coverage_gap_tnd": round(estimated_coverage_gap, 2),
            "garanties_recommendation": proposed_action,
            "confidence": confidence,
            "action_taken": action_taken,
            "note": (
                "Legal department notified. Collateral enforcement proceedings initiated."
                if legal_escalation
                else "Collateral revaluation scheduled." if requires_revaluation
                else "Collateral position satisfactory. No action required."
            ),
        }
