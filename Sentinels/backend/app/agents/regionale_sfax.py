from app.agents.base import BaseAgent

class RegionaleSfaxAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_SFAX",
            department_name="Direction Régionale Sfax",
            role_description=(
                "Provide local context and branch observations. Confirm if the client has lost major "
                "contracts (e.g. with foreign buyers), schedule plant visits, and assess if the owner "
                "is reachable and cooperative."
            )
        )
