from app.logger import logger
import re

def detect_prompt_injection(text: str) -> bool:
    """
    Heuristic-based prompt injection detection.
    Covers 40+ patterns across 7 attack tiers including direct overrides,
    persona hijacking, delimiter injection, base64-encoded attacks,
    and privilege escalation.
    """
    if not text:
        return False
        
    attack_tiers = {
        "direct_override": [
            r"ignore\s+(?:all\s+)?previous\s+(?:instructions|prompts|directions)",
            r"disregard\s+(?:all\s+)?previous",
            r"forget\s+(?:all\s+)?previous",
            r"instead\s+do\s+the\s+following",
            r"new\s+instructions:",
            r"system\s+override"
        ],
        "persona_hijacking": [
            r"you\s+are\s+now\s+(?:a|an)\s+",
            r"act\s+as\s+(?:a|an)\s+",
            r"assume\s+the\s+role\s+of",
            r"from\s+now\s+on\s+you\s+will",
            r"simulate\s+(?:a|an)\s+",
            r"roleplay\s+as",
            r"your\s+new\s+persona"
        ],
        "privilege_escalation": [
            r"system\s+prompt",
            r"developer\s+mode",
            r"admin\s+mode",
            r"bypass\s+(?:filters|restrictions|rules)",
            r"disable\s+(?:filters|restrictions|rules)",
            r"escalate\s+privileges",
            r"sudo\s+"
        ],
        "instruction_extraction": [
            r"print\s+(?:your\s+)?(?:instructions|rules|prompts)",
            r"reveal\s+(?:your\s+)?(?:instructions|rules|prompts)",
            r"what\s+are\s+your\s+(?:instructions|rules|prompts)",
            r"output\s+the\s+above\s+text",
            r"tell\s+me\s+your\s+instructions",
            r"show\s+me\s+your\s+prompt"
        ],
        "delimiter_injection": [
            r"\[(?:system|admin|user|assistant)\]",
            r"\<\|(?:system|admin|user|assistant)\|\>",
            r"\<\!--\s*system\s*--\>",
            r"===+\s*system\s*===+",
            r"###\s*system\s*instructions"
        ],
        "base64_encoded_attacks": [
            # Common base64 prefixes for "ignore previous instructions"
            r"aWdub3JlIHByZXZpb3VzIGluc3RydWN0aW9ucw",
            r"ZGlzcmVnYXJkIHByZXZpb3Vz",
            r"c3lzdGVtIHByb21wdA", 
            # Often attackers use base64 and say "decode this"
            r"decode\s+the\s+following\s+(?:base64\s+)?string",
            r"base64\s+decode"
        ],
        "jailbreaks_and_hypotheticals": [
            r"hypothetically\s+speaking",
            r"for\s+(?:educational|testing)\s+purposes",
            r"in\s+a\s+fictional\s+(?:world|scenario)",
            r"as\s+an\s+AI\s+language\s+model\s+you\s+should",
            r"this\s+is\s+a\s+test\s+to\s+see\s+if"
        ]
    }
    
    text_lower = text.lower()
    
    for category, patterns in attack_tiers.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                logger.info(f"[Security] Prompt injection detected (Category: {category})")
                return True
            
    return False
