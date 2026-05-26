from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.ticket import Ticket
from app.models.report import Report
from app.models.action import Action
from typing import Dict, Any

router = APIRouter()

@router.get("/unified")
def get_unified_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for get unified dashboard.
    """
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == "open").count()
    total_actions = db.query(Action).count()
    
    # Get latest 10 reports
    latest_reports = db.query(Report).order_by(Report.id.desc()).limit(10).all()
    reports_data = [
        {
            "id": r.id,
            "department_id": r.department_id,
            "content": r.content,
            "status": r.status,
            "ticket_id": r.ticket_id
        } for r in latest_reports
    ]
    
    # Aggregations for charts
    status_counts = db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
    reports_by_status = [{"name": status, "value": count} for status, count in status_counts]

    dept_counts = db.query(Report.department_id, func.count(Report.id)).group_by(Report.department_id).all()
    reports_by_department = [{"name": dept, "value": count} for dept, count in dept_counts]
    
    return {
        "kpis": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "total_actions": total_actions
        },
        "recent_reports": reports_data,
        "charts": {
            "reports_by_status": reports_by_status,
            "reports_by_department": reports_by_department
        }
    }

@router.get("/department/{department_id}")
def get_department_dashboard(department_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for get department dashboard.
    """
    pending_reports = db.query(Report).filter(
        Report.department_id == department_id,
        Report.status == "pending"
    ).count()
    
    executed_actions = db.query(Action).filter(
        Action.department_id == department_id
    ).count()
    
    return {
        "kpis": {
            "pending_reports": pending_reports,
            "executed_actions": executed_actions
        }
    }

@router.get("/analytics/performance")
def get_agent_performance_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for agent performance analytics.
    Returns simulated or aggregated metrics for agent throughput, accuracy, and confidence.
    """
    dept_counts = db.query(Report.department_id, func.count(Report.id)).group_by(Report.department_id).all()
    
    performance_data = []
    for dept, count in dept_counts:
        # Generate some synthetic performance metrics based on real volume
        # In a fully fleshed out system, this would calculate average processing time and confidence scores
        base_confidence = 0.85
        if dept == "DIR_RISQUE":
            base_confidence = 0.92
        elif dept == "DIR_ALM":
            base_confidence = 0.88
            
        performance_data.append({
            "department_id": dept,
            "reports_processed": count,
            "avg_confidence_score": round(base_confidence + (count * 0.001), 3),  # Mock confidence boost based on volume
            "avg_processing_time_ms": 1200 - (count * 5),  # Mock processing time
            "status": "active" if count > 0 else "idle"
        })
        
    return {
        "performance": performance_data,
        "overall_system_health": "optimal",
        "active_agents": len([p for p in performance_data if p["status"] == "active"])
    }
