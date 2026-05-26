import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

from app.database import engine, Base, SessionLocal
from app.models.department import Department
from app.models.user import User
from app.models.customer import Customer
from app.models.ticket import Ticket, InputEvent
from app.models.report import Report
from app.models.action import Action
from app.models.audit_log import AuditLog  # noqa: ensure registered


def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed():
    print("Creating / verifying tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed Departments
        if not db.query(Department).first():
            print("Seeding departments...")
            depts = load_json("departments.json")
            for d in depts:
                db.add(Department(**d))
            db.commit()
            print(f"  [OK] {len(depts)} departments seeded.")

        # Seed Users
        if not db.query(User).first():
            print("Seeding users...")
            users = load_json("users.json")
            for u in users:
                db.add(User(**u))
            db.commit()
            print(f"  [OK] {len(users)} users seeded.")

        # Seed Customers — upsert
        print("Seeding customers (upsert)...")
        customers = load_json("customers.json")
        for c in customers:
            existing = db.query(Customer).filter(Customer.id == c["id"]).first()
            if not existing:
                db.add(Customer(**c))
        db.commit()
        total = db.query(Customer).count()
        print(f"  [OK] {total} customers in DB.")

        print("\n[SUCCESS] Database ready!")
    except Exception as e:
        print(f"[ERROR] Error seeding database: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
