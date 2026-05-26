import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.auth import get_current_user
from app.models.user import User
from unittest.mock import patch

# Mock authentication
def override_get_current_user():
    return User(username="test_op", role="OPERATOR", department_id="DIR_RISQUE")

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    with patch("app.api.v1.inputs.SessionLocal") as mock_session:
        yield mock_session

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@patch("app.api.v1.inputs.validate_input_event", return_value=(True, ""))
@patch("app.api.v1.inputs.threading.Thread")
def test_submit_input_event(mock_thread, mock_validate):
    payload = {
        "source": "api",
        "payload": {
            "customer_id": "CUST-123",
            "event_type": "early_warning",
            "details": "High risk detected"
        }
    }
    response = client.post("/api/v1/inputs/", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "ticket_id" in data
    
    # Assert background thread was started
    mock_thread.assert_called_once()
    mock_thread.return_value.start.assert_called_once()
