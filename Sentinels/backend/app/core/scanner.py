from app.logger import logger
import asyncio
import threading
from app.database import SessionLocal
from app.models.customer import Customer
from app.models.ticket import Ticket, InputEvent
from app.orchestrator.orchestrator import process_new_event
from app.core.audit import log_event
from app.api.v1.stream import broadcast_event_sync

def _trigger_orchestrator(ticket_id: int, payload: dict):
    """Run orchestrator in thread to avoid blocking the asyncio loop."""
    db = SessionLocal()
    try:
        process_new_event(db, payload, ticket_id=ticket_id)
    except Exception as e:
        logger.info(f"[Scanner Error] Orchestrator failed for ticket {ticket_id}: {e}")
    finally:
        db.close()

async def risk_scanner_loop():
    """
    Simulates a nightly batch job that scans the Core Banking System (CBS).
    For demo purposes, it runs frequently (e.g., every 30 seconds).
    """
    logger.info("[Scanner] Proactive Risk Scanner started.")
    while True:
        await asyncio.sleep(15)  # Wait 15s between scans for demo
        db = SessionLocal()
        try:
            # Find customers with high DPD
            customers = db.query(Customer).filter(Customer.dpd > 0).all()
            for customer in customers:
                event_type = None
                details = ""
                
                # Rule 1: NPL Alert (DPD > 90)
                if customer.dpd > 90:
                    event_type = "npl_alert"
                    details = f"SYSTEM DETECTED NPL: Customer {customer.name} has crossed 90 days past due (DPD {customer.dpd}). Outstanding balance: {customer.outstanding_balance} TND. Stage 3 IFRS9. Immediate recovery and provisioning review required."
                # Rule 2: Early Warning (30 < DPD <= 90)
                elif customer.dpd > 30:
                    event_type = "early_warning"
                    details = f"SYSTEM DETECTED EARLY WARNING: Customer {customer.name} is {customer.dpd} days past due. Outstanding balance: {customer.outstanding_balance} TND. Potential migration to Stage 2."

                if event_type:
                    # Check if a ticket for this customer already exists
                    open_ticket = db.query(Ticket).filter(
                        Ticket.customer_id == customer.id
                    ).first()
                    
                    if not open_ticket:
                        # Auto-create ticket
                        logger.info(f"[Scanner] Detected {event_type} for {customer.id}. Creating ticket...")
                        ticket = Ticket(customer_id=customer.id, status="open")
                        db.add(ticket)
                        db.commit()
                        db.refresh(ticket)
                        
                        payload = {
                            "customer_id": customer.id,
                            "event_type": event_type,
                            "details": details
                        }
                        
                        input_ev = InputEvent(ticket_id=ticket.id, source="system_scanner", payload=payload)
                        db.add(input_ev)
                        db.commit()
                        
                        log_event(db, "ticket_created", "ticket", ticket.id, details={
                            "customer_id": customer.id,
                            "event_type": event_type,
                            "ticket_id": ticket.id,
                            "source": "system_scanner"
                        })
                        
                        broadcast_event_sync("ticket_created", {
                            "ticket_id": ticket.id,
                            "customer_id": customer.id,
                            "event_type": event_type,
                        })
                        
                        # Trigger agents
                        t = threading.Thread(
                            target=_trigger_orchestrator,
                            args=(ticket.id, payload),
                            daemon=True,
                        )
                        t.start()
                        
        except Exception as e:
            logger.info(f"[Scanner Error] {e}")
        finally:
            db.close()
