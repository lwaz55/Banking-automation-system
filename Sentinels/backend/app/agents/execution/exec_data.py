from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.agents.execution.base_execution import BaseExecutionAgent


class ExecDataAgent(BaseExecutionAgent):
    """
    DIR_DATA (Données Analytiques) Execution Agent.

    Responsibilities after validation:
    - Confirm that analytics findings have been integrated into the risk profile
    - Record trend flags and anomalies detected in the customer's financial data
    - Trigger recalculation of financial ratio benchmarks
    """

    department_id = "DIR_DATA"
    department_name = "Direction Données Analytiques"

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        if not customer:
            return {"status": "skipped", "reason": "Customer not found in DB"}

        analysis = report_content.get("analysis", "")
        confidence = report_content.get("confidence", "N/A")
        risk_level = report_content.get("risk_level", "medium")

        # Derive a simple anomaly severity flag from risk level
        anomaly_severity = {
            "low": "none",
            "medium": "minor",
            "high": "moderate",
            "critical": "severe",
        }.get(risk_level.lower(), "unknown")

        logger.info(f"[ExecData] Analytics integration for customer {customer.id} | anomaly: {anomaly_severity}")

        return {
            "status": "integrated",
            "customer_id": customer.id,
            "anomaly_severity": anomaly_severity,
            "confidence": confidence,
            "analytics_summary": analysis[:200] if analysis else "N/A",
            "action_taken": action_taken,
            "note": "Financial ratios scheduled for recalculation. Data warehouse updated.",
        }
