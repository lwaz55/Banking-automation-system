from app.logger import logger
from typing import List, Dict, Any
import json
from app.agents.llm_client import generate_completion

def get_target_departments(event_type: str, customer_segment: str, loan_size: float, details: str = "") -> List[str]:
    """
    Determines which departments should be involved based on the event payload using an LLM.
    Returns a list of department IDs.
    """
    system_prompt = """You are a routing orchestrator for a bank's risk management system.
Your job is to read the event details and decide which departments should analyze this ticket.

Available Departments:
- DIR_RISQUE: Surveillance Risque Crédit (always include for credit risks)
- DIR_DATA: Données & Analytiques (include if historical data, ML models, or large datasets are needed)
- DIR_GGEI: Analyse Crédit Grandes Entreprises & Institutions (include ONLY if customer segment is GGEI)
- DIR_SFAX: Régionale Sfax (include if there is a regional or branch-level component mentioned, e.g., "Sfax", "regional", "branch")
- DIR_ALM: Contrôle de Gestion & ALM (include if loan size > 5,000,000 TND or if liquidity/rate risks are involved)
- DIR_GARANTIES: Garanties (include if collateral, mortgage, or guarantees are mentioned, or loan size > 5,000,000 TND)
- DIR_RECOUVREMENT: Recouvrement (include if the event is a default or requires collection)

Respond in pure JSON format:
{
  "departments": ["DIR_RISQUE", "DIR_DATA"]
}
"""

    prompt = f"""Event Type: {event_type}
Customer Segment: {customer_segment}
Loan Size (TND): {loan_size}
Event Details: {details}

Which departments should analyze this event?
"""

    try:
        response_text = generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            model="llama-3.3-70b-versatile",
            json_mode=True
        )
        data = json.loads(response_text)
        depts = data.get("departments", [])
        
        # Fallback if empty or invalid
        if not depts or not isinstance(depts, list):
            raise ValueError("Invalid department list from LLM")
            
        # Optional: Validate that elements are in the allowed list
        allowed_depts = {"DIR_RISQUE", "DIR_DATA", "DIR_GGEI", "DIR_SFAX", "DIR_ALM", "DIR_GARANTIES", "DIR_RECOUVREMENT"}
        depts = [d for d in depts if d in allowed_depts]
        if not depts:
            depts = ["DIR_RISQUE"]
            
        return depts
        
    except Exception as e:
        logger.info(f"[Routing Matrix] LLM routing failed: {e}. Falling back to rule-based routing.")
        
        departments = set()
        if event_type == "early_warning":
            departments.add("DIR_RISQUE")
            departments.add("DIR_DATA")
            if customer_segment == "GGEI":
                departments.add("DIR_GGEI")
            if loan_size > 5000000:
                departments.add("DIR_ALM")
                departments.add("DIR_GARANTIES")
        elif event_type == "default":
            departments.add("DIR_RISQUE")
            departments.add("DIR_RECOUVREMENT")
            departments.add("DIR_GARANTIES")
            
        if not departments:
            departments.add("DIR_RISQUE")
            
        return list(departments)
