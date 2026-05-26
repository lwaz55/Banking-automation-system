from app.logger import logger
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from app.agents.llm_client import generate_completion
from app.core.rag_service import retrieve_policy
import json


class AgentOutput(BaseModel):
    """
    Pydantic model that enforces a consistent schema for all agent outputs.
    Groq JSON mode guarantees we receive valid JSON; Pydantic ensures the
    correct fields exist with the right types.
    """
    analysis: str = Field(..., description="Clear analysis from the department's perspective")
    proposed_action: str = Field(..., description="Specific action the department recommends")
    confidence: str = Field(default="50%", description="Confidence percentage, e.g. '85%'")
    risk_level: str = Field(default="medium", description="One of: low, medium, high, critical")
    citations: list[str] = Field(default_factory=list, description="List of specific BCT policy quotes relied upon")


class BaseAgent:
    def __init__(self, department_id: str, department_name: str, role_description: str):
        self.department_id = department_id
        self.department_name = department_name
        self.role_description = role_description

    def analyze(self, ticket_data: Dict[str, Any], customer_data: Dict[str, Any], event_details: str) -> Dict[str, Any]:
        """
        Runs the analysis for this department.
        Uses JSON mode + Pydantic validation for robust, schema-guaranteed output.
        Returns a validated dictionary with: analysis, proposed_action, confidence, risk_level.
        """
        segment = customer_data.get('segment', 'Unknown')
        loan_size = customer_data.get('loan_size', 0)
        risk_stage = customer_data.get('risk_stage', 1)
        history = customer_data.get('history', '')

        # Build the customer context block — instruct the LLM to rely on event text when DB data is missing
        if segment == "Unknown" or loan_size == 0:
            customer_context = (
                "NOTE: This customer is not yet in the database. "
                "You MUST extract all relevant financial facts (loan amount, segment, risk indicators) "
                "DIRECTLY from the Event Details text below. Do NOT say 'unknown' — use what is written."
            )
        else:
            customer_context = (
                f"Customer Segment: {segment}\n"
                f"Current Loan Size: {loan_size:,.0f} TND\n"
                f"Risk Stage (IFRS 9): Stage {risk_stage}"
            )

        history_section = f"\nCustomer History:\n{history}\n" if history else ""

        # Retrieve relevant policies using RAG
        rag_query = f"{self.department_name} analyzing risk: {event_details}"
        relevant_policies = retrieve_policy(rag_query)

        system_prompt = f"""You are a senior expert analyst in the {self.department_name} department at STB Bank (Société Tunisienne de Banque).
Your specialized mandate: {self.role_description}

CRITICAL INSTRUCTIONS:
1. Read the Event Details CAREFULLY. Extract ALL financial figures, names, and facts from it.
2. Write your analysis like a professional banking memo — specific, factual, and citing the exact numbers from the event.
3. You MUST apply the BCT (Banque Centrale de Tunisie) policies provided below. 
4. Your proposed_action must be SPECIFIC: name exact steps, thresholds, regulatory frameworks (IFRS 9 stages, Basel III, BCT circular numbers) derived from the policies.
5. In the 'citations' field, include exact quotes from the BCT policies that justify your action.

=== RELEVANT BCT POLICIES (RAG Knowledge Base) ===
{relevant_policies}
==================================================

Respond ONLY with a valid JSON object with exactly these fields:
- "analysis": 3-5 sentences. Cite specific numbers from the event. State the key risk.
- "proposed_action": 2-4 specific steps your department will take. Be concrete.
- "confidence": A percentage string (e.g., "78%").
- "risk_level": Exactly one of: "low", "medium", "high", "critical".
- "citations": A JSON array of string quotes from the BCT policies.
"""

        prompt = f"""=== TICKET #{ticket_data.get('id', 'N/A')} — {self.department_name} ANALYSIS ===

{customer_context}
{history_section}
=== EVENT DETAILS (Primary Source of Truth) ===
{event_details}
===

Based on the above, provide your department's analysis and recommended action.
"""

        # JSON mode is ON — guarantees valid JSON back
        raw_text = generate_completion(prompt=prompt, system_prompt=system_prompt, json_mode=True)

        try:
            raw_dict = json.loads(raw_text)
            output = AgentOutput(**raw_dict)
            return output.model_dump()

        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            logger.info(f"[{self.department_id}] Output validation failed: {e}. Raw: {raw_text[:200]}")
            return AgentOutput(
                analysis=f"Agent produced an unstructured response. Raw output: {raw_text[:300]}",
                proposed_action="Manual review required",
                confidence="0%",
                risk_level="unknown",
                citations=[]
            ).model_dump()

