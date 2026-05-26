from app.logger import logger
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.report import Report
from app.models.action import Action
from app.core.audit import log_event
from app.api.v1.stream import broadcast_event_sync
from datetime import datetime


class BaseExecutionAgent:
    """
    Base class for all Execution Agents.

    Execution agents are triggered AFTER a department worker validates a report
    (Human-in-the-Loop step). They apply concrete, real changes to the system:
    - Update customer risk classification in DB
    - Adjust loan / collateral records
    - Log decisive actions with full audit trail
    - Broadcast real-time SSE events to the dashboard

    Each subclass implements:
        - `department_id` (class attribute)
        - `department_name` (class attribute)
        - `execute(db, customer, report_content, action_taken)` (core logic)
    """

    department_id: str = "BASE"
    department_name: str = "Base Department"

    def run(
        self,
        db: Session,
        report: Report,
        action_taken: str,
    ) -> Dict[str, Any]:
        """
        Entry point called by the execution pipeline.
        Fetches the customer, delegates to execute(), logs, and broadcasts.
        """
        customer = db.query(Customer).filter(Customer.id == report.ticket.customer_id).first()

        logger.info(f"[ExecAgent:{self.department_id}] Executing for report {report.id} | customer {report.ticket.customer_id}")

        # Delegate concrete logic to subclass
        execution_summary = self.execute(
            db=db,
            customer=customer,
            report_content=report.content or {},
            action_taken=action_taken,
        )

        # Persist an execution record on the Action row
        action = db.query(Action).filter(Action.report_id == report.id).first()
        if action:
            action.status = "executed"
            db.commit()

        # Audit log
        log_event(db, "execution_complete", "report", report.id, details={
            "dept_id": self.department_id,
            "ticket_id": report.ticket_id,
            "report_id": report.id,
            "summary": execution_summary,
        })

        # Real-time broadcast
        broadcast_event_sync("execution_complete", {
            "dept_id": self.department_id,
            "ticket_id": report.ticket_id,
            "report_id": report.id,
            "summary": execution_summary,
        })

        return execution_summary

    def execute(
        self,
        db: Session,
        customer: Optional[Customer],
        report_content: Dict[str, Any],
        action_taken: str,
    ) -> Dict[str, Any]:
        """
        Override in each subclass to apply department-specific changes.
        Returns a summary dict describing what was done.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")
