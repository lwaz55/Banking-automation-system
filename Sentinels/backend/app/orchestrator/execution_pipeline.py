from app.logger import logger
"""
Execution Pipeline — triggered after HITL validation.

When a department worker validates a report, this pipeline:
1. Looks up the correct Execution Agent for the department
2. Loads the report + ticket + customer from DB
3. Calls the agent's run() method which applies real changes
4. Logs everything and broadcasts SSE events

Called from: app/api/v1/reports.py (validate_report endpoint)
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.report import Report
from app.models.ticket import Ticket

# Import all execution agents
from app.agents.execution.exec_risque import ExecRisqueAgent
from app.agents.execution.exec_sfax import ExecSfaxAgent
from app.agents.execution.exec_ggei import ExecGGEIAgent
from app.agents.execution.exec_data import ExecDataAgent
from app.agents.execution.exec_alm import ExecALMAgent
from app.agents.execution.exec_garanties import ExecGarantiesAgent
from app.agents.execution.base_execution import BaseExecutionAgent

# Registry: department_id → execution agent class
EXECUTION_AGENT_REGISTRY = {
    "DIR_RISQUE":    ExecRisqueAgent,
    "DIR_SFAX":      ExecSfaxAgent,
    "DIR_GGEI":      ExecGGEIAgent,
    "DIR_DATA":      ExecDataAgent,
    "DIR_ALM":       ExecALMAgent,
    "DIR_GARANTIES": ExecGarantiesAgent,
}


def run_execution_pipeline(report_id: int, action_taken: str) -> None:
    """
    Main execution pipeline entry point.
    Creates its own DB session (runs in a background thread).

    Args:
        report_id: ID of the validated report to execute
        action_taken: The human operator's validation note
    """
    db: Session = SessionLocal()
    try:
        # Load the report with its relationships
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.info(f"[ExecutionPipeline] Report {report_id} not found.")
            return

        # Ensure ticket is loaded for customer_id access in the agent
        ticket = db.query(Ticket).filter(Ticket.id == report.ticket_id).first()
        if not ticket:
            logger.info(f"[ExecutionPipeline] Ticket for report {report_id} not found.")
            return

        # Manually attach ticket to report so base_execution can access customer_id
        report.ticket = ticket

        dept_id = report.department_id
        agent_class = EXECUTION_AGENT_REGISTRY.get(dept_id)

        if not agent_class:
            logger.info(f"[ExecutionPipeline] No execution agent registered for dept '{dept_id}'. Skipping.")
            return

        agent: BaseExecutionAgent = agent_class()
        result = agent.run(db=db, report=report, action_taken=action_taken)

        logger.info(f"[ExecutionPipeline] ✅ {dept_id} executed report {report_id}: {result.get('status', 'done')}")

    except Exception as e:
        import traceback
        logger.info(f"[ExecutionPipeline] ❌ Error executing report {report_id}: {e}")
        logger.error("Exception occurred", exc_info=True)
    finally:
        db.close()
