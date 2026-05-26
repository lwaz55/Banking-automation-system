from app.agents.base import BaseAgent

class SurveillanceRisqueCreditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_RISQUE",
            department_name="Direction Centrale Surveillance Risque Crédit",
            role_description=(
                "Lead the risk evaluation. Your task is to identify credit deterioration signals "
                "like DPD, turnover drop, late filing, or sector risk. If these are present, propose "
                "reclassifying the loan (e.g. Stage 1 to Stage 2 per IFRS 9) and calculate the "
                "provisioning impact. Cite BCT Circulaire 91-24."
            )
        )
