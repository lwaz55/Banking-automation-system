from app.logger import logger
from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentOutput
from app.agents.llm_client import generate_completion
from pydantic import ValidationError
from app.core.rag_service import retrieve_policy
import json

class ChiefRiskOfficerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            department_id="CHIEF_RISK_OFFICER",
            department_name="Chief Risk Officer",
            role_description="Evaluate departmental reports, point out discrepancies, and provide a final synthesized risk ruling."
        )

    def analyze_debate(self, ticket_data: Dict[str, Any], customer_data: Dict[str, Any], event_details: str, department_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs the debate analysis. Takes the outputs of all other agents.
        """
        segment = customer_data.get('segment', 'Unknown')
        loan_size = customer_data.get('loan_size', 0)
        risk_stage = customer_data.get('risk_stage', 1)

        customer_context = (
            f"Customer Segment: {segment}\n"
            f"Current Loan Size: {loan_size:,.0f} TND\n"
            f"Risk Stage (IFRS 9): Stage {risk_stage}"
        )

        # Format reports
        reports_text = ""
        for rep in department_reports:
            dept = rep.get("dept_id")
            content = rep.get("content", {})
            reports_text += f"\n--- {dept} REPORT ---\n"
            reports_text += f"Analysis: {content.get('analysis')}\n"
            reports_text += f"Action: {content.get('proposed_action')}\n"
            reports_text += f"Risk Level: {content.get('risk_level')}\n"

        # Retrieve relevant policies using RAG
        rag_query = f"CRO synthesizing final risk for event: {event_details}"
        relevant_policies = retrieve_policy(rag_query)

        system_prompt = f"""You are the Chief Risk Officer (CRO) at STB Bank.
Your role: {self.role_description}

CRITICAL INSTRUCTIONS:
1. You will be provided with the Event Details and the Risk Analysis reports from several departments.
2. Review the reports. If they disagree, point out the discrepancy.
3. Make a final executive ruling on the proposed action and global risk level.
4. You MUST apply the BCT (Banque Centrale de Tunisie) policies provided below to ensure the final ruling is compliant.
5. In the 'citations' field, quote the exact BCT rules that govern your final decision.
6. Be professional, authoritative, and direct.

=== RELEVANT BCT POLICIES (RAG Knowledge Base) ===
{relevant_policies}
==================================================

Respond ONLY with a valid JSON object:
- "analysis": 3-5 sentences summarizing the consensus or debate, and your final view.
- "proposed_action": 2-3 specific steps the bank must take.
- "confidence": Percentage string (e.g., "95%").
- "risk_level": "low", "medium", "high", or "critical".
- "citations": A JSON array of string quotes from the BCT policies.
"""

        prompt = f"""=== TICKET #{ticket_data.get('id', 'N/A')} — CRO REVIEW ===

{customer_context}

=== EVENT DETAILS ===
{event_details}

=== DEPARTMENTAL REPORTS ===
{reports_text}
===

Based on the above, provide your final executive synthesis.
"""

        raw_text = generate_completion(prompt=prompt, system_prompt=system_prompt, json_mode=True, max_tokens=2048)

        try:
            raw_dict = json.loads(raw_text)
            output = AgentOutput(**raw_dict)
            return output.model_dump()
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            logger.info(f"[{self.department_id}] Output validation failed: {e}. Raw: {raw_text[:200]}")
            return AgentOutput(
                analysis=f"CRO Agent produced an unstructured response.",
                proposed_action="Manual review required",
                confidence="0%",
                risk_level="unknown",
                citations=[]
            ).model_dump()
