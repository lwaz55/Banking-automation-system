from app.agents.base import BaseAgent

class AnalyseCreditGGEIAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="DIR_GGEI",
            department_name="Direction GGEI",
            role_description=(
                "Re-score creditworthiness for Grandes Entreprises. Use updated turnover, DSCR, "
                "and Debt-EBITDA. If the client is struggling, propose a restructuring offer "
                "like a principal moratorium + collateral top-up."
            )
        )
