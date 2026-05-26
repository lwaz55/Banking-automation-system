from app.agents.base import BaseAgent

class GarantiesAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_GARANTIES",
            department_name="Direction Contrôle & Suivi des Garanties",
            role_description=(
                "Evaluate current collateral coverage. Identify existing valid collateral (e.g., real estate), "
                "calculate the current coverage ratio, and recommend top-ups to reach 100% coverage if needed."
            )
        )
