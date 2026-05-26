from app.agents.base import BaseAgent

class ControleGestionALMAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_ALM",
            department_name="Direction Contrôle de Gestion & ALM",
            role_description=(
                "Assess the capital impact of the proposed risk classification change. "
                "Calculate provisioning impact, cost-of-risk increase (in bps), and the "
                "overall CET1 ratio impact."
            )
        )
