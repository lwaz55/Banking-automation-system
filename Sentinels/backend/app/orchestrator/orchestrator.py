from app.logger import logger
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.ticket import Ticket, InputEvent
from app.models.report import Report
from app.models.customer import Customer
from app.models.department import Department
from app.models.user import User  # noqa: imported for SQLAlchemy mapper
from app.orchestrator.routing_matrix import get_target_departments

# Import specific agents
from app.agents.surveillance_risque_credit import SurveillanceRisqueCreditAgent
from app.agents.analyse_credit_ggei import AnalyseCreditGGEIAgent
from app.agents.donnees_analytiques import DonneesAnalytiquesAgent
from app.agents.regionale_sfax import RegionaleSfaxAgent
from app.agents.controle_gestion_alm import ControleGestionALMAgent
from app.agents.garanties import GarantiesAgent
from app.agents.base import BaseAgent
from app.api.v1.stream import broadcast_event_sync
from app.core.audit import log_event

from concurrent.futures import ThreadPoolExecutor, as_completed

# Map department IDs to specific agent classes
AGENT_MAPPING = {
    "DIR_RISQUE": SurveillanceRisqueCreditAgent,
    "DIR_GGEI": AnalyseCreditGGEIAgent,
    "DIR_DATA": DonneesAnalytiquesAgent,
    "DIR_SFAX": RegionaleSfaxAgent,
    "DIR_ALM": ControleGestionALMAgent,
    "DIR_GARANTIES": GarantiesAgent,
}


def _get_or_create_agent(dept_id: str, db: Session) -> BaseAgent:
    agent_class = AGENT_MAPPING.get(dept_id)
    if not agent_class:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        dept_name = dept.name if dept else dept_id
        return BaseAgent(department_id=dept_id, department_name=dept_name, role_description="Provide risk analysis.")
    return agent_class()


def _run_single_agent(dept_id: str, ticket_data: Dict, customer_data: Dict, details: str) -> Dict[str, Any]:
    """
    Runs a single agent in isolation (no DB session — pure compute).
    Returns a dict with dept_id and the analysis result.
    """
    agent_class = AGENT_MAPPING.get(dept_id)
    if agent_class:
        agent = agent_class()
    else:
        agent = BaseAgent(department_id=dept_id, department_name=dept_id, role_description="Provide risk analysis.")

    result = agent.analyze(ticket_data, customer_data, details)
    return {"dept_id": dept_id, "content": result}


def process_new_event(db: Session, payload: Dict[str, Any], ticket_id: Optional[int] = None) -> Ticket:
    """
    Main orchestration flow. Called from the background thread in inputs.py.
    Agents run in PARALLEL using ThreadPoolExecutor for maximum speed.
    ticket_id is passed in if the ticket was already created by the route handler.
    """
    customer_id = payload.get("customer_id")
    event_type = payload.get("event_type", "early_warning")
    details = payload.get("details", "")

    # Get or reuse ticket
    if ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    else:
        ticket = Ticket(customer_id=customer_id, status="open")
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        input_event = InputEvent(ticket_id=ticket.id, source="api", payload=payload)
        db.add(input_event)
        db.commit()

        log_event(db, "ticket_created", "ticket", ticket.id, details={
            "customer_id": customer_id,
            "event_type": event_type,
            "ticket_id": ticket.id,
        })
        broadcast_event_sync("ticket_created", {"ticket_id": ticket.id, "customer_id": customer_id})

    # Get customer data for routing
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    customer_data = {"segment": "Unknown", "loan_size": 0, "risk_stage": 1, "history": ""}
    if customer:
        customer_data = {
            "segment": customer.segment,
            "loan_size": customer.loan_size,
            "risk_stage": customer.risk_stage,
            "history": ""
        }

    # Agent Memory: Fetch past tickets history for this customer
    past_events = db.query(InputEvent).join(Ticket).filter(
        Ticket.customer_id == customer_id,
        Ticket.id != ticket.id
    ).order_by(InputEvent.created_at.desc()).limit(3).all()
    
    if past_events:
        history_str = "Recent Customer History:\n"
        for ev in reversed(past_events):
            history_str += f"- {ev.created_at.strftime('%Y-%m-%d')}: {ev.payload.get('event_type')} - {ev.payload.get('details')}\n"
        customer_data["history"] = history_str

    # Routing Matrix
    target_depts = get_target_departments(
        event_type=event_type,
        customer_segment=customer_data["segment"],
        loan_size=customer_data["loan_size"],
        details=details,
    )

    log_event(db, "routing_complete", "ticket", ticket.id, details={
        "ticket_id": ticket.id,
        "target_depts": target_depts,
        "event_type": event_type,
    })

    broadcast_event_sync("routing_complete", {
        "ticket_id": ticket.id,
        "target_depts": target_depts,
    })

    # Broadcast all agents as "started" before launching them in parallel
    ticket_data = {"id": ticket.id}
    for dept_id in target_depts:
        log_event(db, "agent_started", "ticket", ticket.id, details={
            "ticket_id": ticket.id,
            "dept_id": dept_id,
        })
        broadcast_event_sync("agent_started", {
            "ticket_id": ticket.id,
            "dept_id": dept_id,
        })

    # ── Run ALL agents in PARALLEL ──────────────────────────────────────────
    futures_map = {}
    department_reports = []
    with ThreadPoolExecutor(max_workers=len(target_depts)) as executor:
        for dept_id in target_depts:
            future = executor.submit(
                _run_single_agent,
                dept_id, ticket_data, customer_data, details
            )
            futures_map[future] = dept_id

        # Persist each report as it finishes (first-come, first-served)
        for future in as_completed(futures_map):
            dept_id = futures_map[future]
            try:
                agent_result = future.result()
                analysis_result = agent_result["content"]
            except Exception as exc:
                logger.info(f"[Orchestrator] Agent {dept_id} raised: {exc}")
                analysis_result = {
                    "analysis": f"Agent failed with error: {exc}",
                    "proposed_action": "Manual review required",
                    "confidence": "0%",
                    "risk_level": "unknown",
                }

            department_reports.append({"dept_id": dept_id, "content": analysis_result})

            # Save report to DB
            report = Report(
                ticket_id=ticket.id,
                department_id=dept_id,
                content=analysis_result,
                status="pending",
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            log_event(db, "agent_done", "report", report.id, details={
                "ticket_id": ticket.id,
                "dept_id": dept_id,
                "report_id": report.id,
                "content": analysis_result,
            })
            broadcast_event_sync("agent_done", {
                "ticket_id": ticket.id,
                "dept_id": dept_id,
                "report_id": report.id,
                "content": analysis_result,
            })
    # ────────────────────────────────────────────────────────────────────────

    # ── Run CHIEF_RISK_OFFICER for Multi-Agent Debate ──
    from app.agents.chief_risk_officer import ChiefRiskOfficerAgent
    cro_agent = ChiefRiskOfficerAgent()

    log_event(db, "agent_started", "ticket", ticket.id, details={
        "ticket_id": ticket.id,
        "dept_id": cro_agent.department_id,
    })
    broadcast_event_sync("agent_started", {
        "ticket_id": ticket.id,
        "dept_id": cro_agent.department_id,
    })

    cro_result = cro_agent.analyze_debate(ticket_data, customer_data, details, department_reports)

    cro_report = Report(
        ticket_id=ticket.id,
        department_id=cro_agent.department_id,
        content=cro_result,
        status="pending",
    )
    db.add(cro_report)
    db.commit()
    db.refresh(cro_report)

    log_event(db, "agent_done", "report", cro_report.id, details={
        "ticket_id": ticket.id,
        "dept_id": cro_agent.department_id,
        "report_id": cro_report.id,
        "content": cro_result,
    })
    broadcast_event_sync("agent_done", {
        "ticket_id": ticket.id,
        "dept_id": cro_agent.department_id,
        "report_id": cro_report.id,
        "content": cro_result,
    })
    # ───────────────────────────────────────────────────

    # Mark ticket as analysis_complete
    ticket.status = "analysis_complete"
    db.commit()

    broadcast_event_sync("analysis_complete", {
        "ticket_id": ticket.id,
        "total_reports": len(target_depts),
    })

    return ticket


def reanalyze_report(report_id: int):
    """
    Re-run the LLM for a specific report (called after invalidation).
    Creates its own DB session.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        ticket = db.query(Ticket).filter(Ticket.id == report.ticket_id).first()
        if not ticket:
            return

        # Get original event details
        input_event = db.query(InputEvent).filter(InputEvent.ticket_id == ticket.id).first()
        if not input_event:
            return

        payload = input_event.payload
        customer = db.query(Customer).filter(Customer.id == ticket.customer_id).first()
        customer_data = {"segment": "Unknown", "loan_size": 0, "risk_stage": 1, "history": ""}
        if customer:
            customer_data = {
                "segment": customer.segment,
                "loan_size": customer.loan_size,
                "risk_stage": customer.risk_stage,
                "history": ""
            }

        # Agent Memory: Fetch past tickets history for this customer
        past_events = db.query(InputEvent).join(Ticket).filter(
            Ticket.customer_id == ticket.customer_id,
            Ticket.id != ticket.id
        ).order_by(InputEvent.created_at.desc()).limit(3).all()
        
        if past_events:
            history_str = "Recent Customer History:\n"
            for ev in reversed(past_events):
                history_str += f"- {ev.created_at.strftime('%Y-%m-%d')}: {ev.payload.get('event_type')} - {ev.payload.get('details')}\n"
            customer_data["history"] = history_str

        broadcast_event_sync("agent_started", {
            "ticket_id": ticket.id,
            "dept_id": report.department_id,
            "reanalysis": True,
        })

        agent = _get_or_create_agent(report.department_id, db)
        ticket_data = {"id": ticket.id}
        new_content = agent.analyze(ticket_data, customer_data, payload.get("details", ""))

        report.content = new_content
        report.status = "pending"
        db.commit()
        db.refresh(report)

        log_event(db, "agent_reanalysis_done", "report", report.id, details={
            "ticket_id": ticket.id,
            "dept_id": report.department_id,
            "report_id": report.id,
            "content": new_content,
        })

        broadcast_event_sync("agent_done", {
            "ticket_id": ticket.id,
            "dept_id": report.department_id,
            "report_id": report.id,
            "content": new_content,
            "reanalysis": True,
        })

    except Exception as e:
        logger.info(f"[Reanalysis Error] Report {report_id}: {e}")
        import traceback; logger.error("Exception occurred", exc_info=True)
    finally:
        db.close()
