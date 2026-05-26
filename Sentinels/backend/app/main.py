from app.logger import logger
from dotenv import load_dotenv
load_dotenv()

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Store a reference to the running event loop for cross-thread SSE broadcasting."""
    from app.api.v1.stream import set_event_loop
    loop = asyncio.get_running_loop()
    set_event_loop(loop)

    # Ensure all DB tables exist (including new AuditLog)
    from app.database import engine, Base, SessionLocal
    from app.models import audit_log, customer  # noqa: ensure model is registered
    Base.metadata.create_all(bind=engine)
    from app.logger import logger
    logger.info("[Sentinels] Database tables verified/created.")

    # Seed CBS Data
    from app.core.seed_data import seed_cbs_data
    db = SessionLocal()
    try:
        seed_cbs_data(db)
    finally:
        db.close()

    # Start Proactive Risk Scanner
    from app.core.scanner import risk_scanner_loop
    scanner_task = asyncio.create_task(risk_scanner_loop())
    
    yield
    
    scanner_task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}


from app.api.v1 import inputs, tickets, reports, dashboards, auth, stream, audit, customers, chat

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(inputs.router, prefix="/api/v1/inputs", tags=["Inputs"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Dashboards"])
app.include_router(stream.router, prefix="/api/v1/stream", tags=["Stream"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])

