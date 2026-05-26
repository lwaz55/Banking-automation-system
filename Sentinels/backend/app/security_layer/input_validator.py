from typing import Dict, Any, Tuple
from app.security_layer.prompt_injection import detect_prompt_injection

def validate_input_event(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates incoming payload for required fields and prompt injection.
    Returns (is_valid, error_message)
    """
    required_fields = ["customer_id", "event_type", "details"]
    
    for field in required_fields:
        if field not in payload:
            return False, f"Missing required field: {field}"
            
    # Check for prompt injection in any string fields
    for key, value in payload.items():
        if isinstance(value, str):
            if detect_prompt_injection(value):
                return False, f"Potential prompt injection detected in field '{key}'"
                
    return True, ""
