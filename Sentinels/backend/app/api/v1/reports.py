from app.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.report import Report
from app.models.action import Action
from app.schemas.common import ReportOut, ActionOut
from app.api.v1.auth import RequireRole
from app.core.pdf_export import generate_pdf_report
from pydantic import BaseModel
from typing import Any, Dict
import threading

router = APIRouter()


class ValidateRequest(BaseModel):
    action_taken: str


class ModifyRequest(BaseModel):
    content: Dict[str, Any]


@router.get("/", response_model=List[ReportOut])
def list_reports(
    ticket_id: Optional[int] = None,
    department_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Endpoint for list reports.
    """
    query = db.query(Report)
    if ticket_id:
        query = query.filter(Report.ticket_id == ticket_id)
    if department_id:
        query = query.filter(Report.department_id == department_id)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.id.desc()).all()


@router.get("/ticket/{ticket_id}", response_model=List[ReportOut])
def get_reports_for_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Endpoint for get reports for ticket.
    """
    return db.query(Report).filter(Report.ticket_id == ticket_id).all()

@router.get("/ticket/{ticket_id}/export/pdf", dependencies=[Depends(RequireRole(["ANALYST", "ADMIN"]))])
def export_ticket_reports_pdf(ticket_id: int, db: Session = Depends(get_db)):
    """
    Endpoint for export ticket reports pdf.
    """
    logger.info(f"[PDF Export] Generating report for ticket {ticket_id}")
    reports = db.query(Report).filter(Report.ticket_id == ticket_id).order_by(Report.id.asc()).all()
    if not reports:
        logger.info(f"[PDF Export] Error: No reports found for ticket {ticket_id}")
        raise HTTPException(status_code=404, detail="No reports found for this ticket")
        
    try:
        pdf_bytes = generate_pdf_report(ticket_id, reports)
        logger.info(f"[PDF Export] Successfully generated {len(pdf_bytes)} bytes")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ticket_{ticket_id}_report.pdf",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    except Exception as e:
        logger.info(f"[PDF Export] Critical error: {e}")
        import traceback
        logger.error("Exception occurred", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")


@router.post("/{report_id}/validate", response_model=ActionOut, dependencies=[Depends(RequireRole(["ANALYST", "ADMIN"]))])
def validate_report(report_id: int, request: ValidateRequest, db: Session = Depends(get_db)):
    """
    Endpoint for validate report.
    """
    from app.core.audit import log_event
    from app.api.v1.stream import get_event_loop, broadcast_event_sync
    from app.orchestrator.execution_pipeline import run_execution_pipeline

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "validated"

    action = Action(
        report_id=report.id,
        department_id=report.department_id,
        action_taken=request.action_taken,
        status="pending_execution",  # Will be updated to 'executed' by the execution agent
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    # Audit log
    log_event(db, "report_validated", "report", report_id, details={
        "ticket_id": report.ticket_id,
        "dept_id": report.department_id,
        "action_taken": request.action_taken,
    })

    # SSE broadcast — validation confirmed
    broadcast_event_sync("report_validated", {
        "ticket_id": report.ticket_id,
        "report_id": report_id,
        "dept_id": report.department_id,
        "action_taken": request.action_taken,
        "action_id": action.id,
    })

    # ── Launch Execution Agent in background ────────────────────────────────
    # The execution agent applies real changes (risk_stage updates, ALM
    # assessments, collateral flags, etc.) and broadcasts execution_complete.
    t = threading.Thread(
        target=run_execution_pipeline,
        args=(report_id, request.action_taken),
        daemon=True,
    )
    t.start()
    # ────────────────────────────────────────────────────────────────────────

    return action



@router.post("/{report_id}/invalidate", dependencies=[Depends(RequireRole(["ANALYST", "ADMIN"]))])
def invalidate_report(report_id: int, db: Session = Depends(get_db)):
    """
    Endpoint for invalidate report.
    """
    from app.core.audit import log_event
    from app.api.v1.stream import broadcast_event_sync
    from app.orchestrator.orchestrator import reanalyze_report

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "invalidated"
    db.commit()

    log_event(db, "report_invalidated", "report", report_id, details={
        "ticket_id": report.ticket_id,
        "dept_id": report.department_id,
    })

    broadcast_event_sync("report_invalidated", {
        "ticket_id": report.ticket_id,
        "report_id": report_id,
        "dept_id": report.department_id,
    })

    # Trigger re-analysis in background
    import threading
    t = threading.Thread(target=reanalyze_report, args=(report_id,), daemon=True)
    t.start()

    return {"status": "invalidated", "report_id": report_id, "message": "Agent is rewriting the report."}


@router.patch("/{report_id}/modify", dependencies=[Depends(RequireRole(["ANALYST", "ADMIN"]))])
def modify_report(report_id: int, request: ModifyRequest, db: Session = Depends(get_db)):
    """
    Endpoint for modify report.
    """
    from app.core.audit import log_event
    from app.api.v1.stream import broadcast_event_sync

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.content = request.content
    report.status = "modified"
    db.commit()

    log_event(db, "report_modified", "report", report_id, details={
        "ticket_id": report.ticket_id,
        "dept_id": report.department_id,
        "new_content": request.content,
    })

    broadcast_event_sync("report_modified", {
        "ticket_id": report.ticket_id,
        "report_id": report_id,
        "dept_id": report.department_id,
        "content": request.content,
    })

    return {"status": "modified", "report_id": report_id}
