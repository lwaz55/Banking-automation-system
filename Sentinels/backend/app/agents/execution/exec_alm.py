from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecALMAgent(BaseExecutionAgent):
    """
    DIR_ALM (Contrôle de Gestion & Asset-Liability Management) Execution Agent.

    Responsibilities after validation:
    - Record the liquidity impact assessment of the NPL exposure
    - Flag large exposures (>5M TND) for ALM committee review
    - Update coverage ratio tracking for the affected loan
    """

    department_id = "DIR_ALM"
    department_name = "Direction Contrôle de Gestion & ALM"

    # BCT regulatory threshold for large exposure reporting
    LARGE_EXPOSURE_THRESHOLD = 5_000_000  # 5M TND

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        if not customer:
            return {"status": "skipped", "reason": "Customer not found in DB"}

        loan_size = customer.loan_size
        risk_level = report_content.get("risk_level", "medium").lower()
        proposed_action = report_content.get("proposed_action", "")

        is_large_exposure = loan_size >= self.LARGE_EXPOSURE_THRESHOLD
        alm_committee_required = is_large_exposure and risk_level in ("high", "critical")

        # Estimated provisioning rate based on risk stage
        provision_rates = {1: 0.0, 2: 0.20, 3: 0.50, 4: 1.0}
        estimated_provision = loan_size * provision_rates.get(customer.risk_stage, 0.20)

        logger.info(f"[ExecALM] Liquidity impact for {customer.id}: loan={loan_size} TND, estimated provision={estimated_provision:.0f} TND")

        return {
            "status": "assessed",
            "customer_id": customer.id,
            "loan_size_tnd": loan_size,
            "is_large_exposure": is_large_exposure,
            "alm_committee_required": alm_committee_required,
            "estimated_provision_tnd": round(estimated_provision, 2),
            "risk_level": risk_level,
            "alm_recommendation": proposed_action,
            "action_taken": action_taken,
            "note": "ALM committee convened." if alm_committee_required else "Handled at department level.",
        }
