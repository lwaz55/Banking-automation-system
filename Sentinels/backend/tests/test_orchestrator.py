import pytest
from app.orchestrator.routing_matrix import get_target_departments
from app.orchestrator.execution_pipeline import run_execution_pipeline

def test_routing_matrix_rule_based(monkeypatch):
    # Mock LLM generation to force fallback
    monkeypatch.setattr("app.orchestrator.routing_matrix.generate_completion", lambda **kwargs: "invalid json")
    
    routes = get_target_departments(event_type="early_warning", customer_segment="retail", loan_size=10000)
    assert "DIR_RISQUE" in routes
    
    routes_high = get_target_departments(event_type="default", customer_segment="GGEI", loan_size=6000000)
    assert "DIR_RISQUE" in routes_high
    assert "DIR_RECOUVREMENT" in routes_high

def test_execution_pipeline_registration():
    # Since it's a function we can just assert it exists and is callable
    assert callable(run_execution_pipeline)

def test_execution_pipeline_empty():
    # Calling it with invalid report id shouldn't crash
    run_execution_pipeline(report_id=99999, action_taken="test")
