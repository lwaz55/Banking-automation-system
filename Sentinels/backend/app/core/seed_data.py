from app.logger import logger
from sqlalchemy.orm import Session
from app.models.customer import Customer

def seed_cbs_data(db: Session):
    """Seed the database with realistic customers for the automated scanner to detect."""
    
    customers_to_seed = [
        # Healthy Customer
        {
            "id": "CUST-GGEI-101",
            "name": "Global Tech Industries",
            "segment": "GGEI",
            "loan_size": 25000000.0,
            "risk_stage": 1,
            "dpd": 0,
            "outstanding_balance": 24500000.0,
            "payment_status": "current",
            "ifrs9_stage": 1,
            "history": "Solid financial performance. Quarterly payments made on time."
        },
        # Early Warning Trigger (DPD 45)
        {
            "id": "CUST-SME-205",
            "name": "Atlas Manufacturing Ltd",
            "segment": "SME",
            "loan_size": 3500000.0,
            "risk_stage": 2,
            "dpd": 45,
            "outstanding_balance": 3100000.0,
            "payment_status": "late",
            "ifrs9_stage": 2,
            "history": "Supply chain issues reported last month. Missed recent payment."
        },
        # NPL Trigger (DPD 95)
        {
            "id": "CUST-RETAIL-404",
            "name": "Mourad Trading",
            "segment": "Retail",
            "loan_size": 850000.0,
            "risk_stage": 4,
            "dpd": 95,
            "outstanding_balance": 820000.0,
            "payment_status": "default",
            "ifrs9_stage": 3,
            "history": "Business closure due to fire. Insurance claims pending. Default threshold crossed."
        },
        # Proactive/Optima (Existing test case, kept stable)
        {
            "id": "CUST-OPT-007",
            "name": "Optima Retail Group",
            "segment": "TPME",
            "loan_size": 1200000.0,
            "risk_stage": 2,
            "dpd": 0,
            "outstanding_balance": 1200000.0,
            "payment_status": "current",
            "ifrs9_stage": 1,
            "history": "Proactive restructuring requested. Good past payment history."
        },
        # High Risk Real Estate (Triggers ALM + Garanties due to size & collateral)
        {
            "id": "CUST-CORP-999",
            "name": "Horizon Real Estate Dev",
            "segment": "Corporate",
            "loan_size": 15000000.0,
            "risk_stage": 3,
            "dpd": 60,
            "outstanding_balance": 14500000.0,
            "payment_status": "late",
            "ifrs9_stage": 2,
            "history": "Construction delays caused cash flow issues. Property collateral needs revaluation."
        },
        # Tech Startup (High risk, low collateral)
        {
            "id": "CUST-SME-777",
            "name": "Quantum AI Solutions",
            "segment": "SME",
            "loan_size": 500000.0,
            "risk_stage": 2,
            "dpd": 30,
            "outstanding_balance": 480000.0,
            "payment_status": "late",
            "ifrs9_stage": 2,
            "history": "Missed Series A funding round. Burn rate high, first payment missed."
        }
    ]

    # Only insert if they don't exist
    for c_data in customers_to_seed:
        existing = db.query(Customer).filter(Customer.id == c_data["id"]).first()
        if not existing:
            new_cust = Customer(**c_data)
            db.add(new_cust)
        else:
            # Update existing to ensure CBS fields are populated for the demo
            for key, value in c_data.items():
                setattr(existing, key, value)

    # Add Admin User for frontend API auth
    from app.models.user import User
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(username="admin", role="ADMIN", department_id="DIR_RISQUE")
        db.add(new_admin)

    db.commit()
    logger.info("[Seed] CBS Customer data seeded successfully.")
