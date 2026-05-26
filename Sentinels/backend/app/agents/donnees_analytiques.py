from app.agents.base import BaseAgent

class DonneesAnalytiquesAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_DATA",
            department_name="Direction Données Analytiques",
            role_description=(
                "Analyze transactional data and behavioral anomalies predicting default. "
                "Look for large cash withdrawals before missed payments or pattern matches "
                "with past NPL cohorts."
            )
        )
