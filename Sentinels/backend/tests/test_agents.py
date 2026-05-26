import pytest
from unittest.mock import patch
from app.agents.surveillance_risque_credit import SurveillanceRisqueCreditAgent
from app.agents.base import AgentOutput
import json

@pytest.fixture
def ticket_data():
    return {"id": 1}

@pytest.fixture
def customer_data():
    return {"segment": "Corporate", "loan_size": 1500000, "risk_stage": 2, "history": ""}

@pytest.fixture
def event_details():
    return "Customer missed payment by 15 days."

def test_agent_successful_analysis(ticket_data, customer_data, event_details):
    agent = SurveillanceRisqueCreditAgent()
    
    mock_response = {
        "analysis": "Missed payment suggests cash flow issues.",
        "proposed_action": "Contact customer to restructure loan.",
        "confidence": "85%",
        "risk_level": "high"
    }
    
    with patch("app.agents.base.generate_completion", return_value=json.dumps(mock_response)):
        result = agent.analyze(ticket_data, customer_data, event_details)
        
        assert result["analysis"] == mock_response["analysis"]
        assert result["proposed_action"] == mock_response["proposed_action"]
        assert result["risk_level"] == "high"

def test_agent_fallback_on_invalid_json(ticket_data, customer_data, event_details):
    agent = SurveillanceRisqueCreditAgent()
    
    with patch("app.agents.base.generate_completion", return_value="Invalid JSON response"):
        result = agent.analyze(ticket_data, customer_data, event_details)
        
        assert "Manual review required" in result["proposed_action"]
        assert result["confidence"] == "0%"
        assert result["risk_level"] == "unknown"
