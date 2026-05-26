from app.logger import logger
import os
import requests

def _call_openai_compatible_api(url: str, key: str, model: str, prompt: str, system_prompt: str, json_mode: bool, max_tokens: int = 1024) -> str:
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }

    if json_mode:
        request_body["response_format"] = {"type": "json_object"}

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=request_body,
        timeout=30,
    )
    
    if resp.status_code != 200:
        try:
            error_data = resp.json()
            # xAI/Groq/OpenAI usually have 'error' or 'message'
            msg = error_data.get("error", {}).get("message", error_data.get("error", str(resp.text)))
            if "credits" in msg.lower() or "limit" in msg.lower():
                raise Exception(f"API Quota/Credit Exhausted: {msg}")
            raise Exception(msg)
        except:
            resp.raise_for_status()
            
    return resp.json()["choices"][0]["message"]["content"]

def generate_completion(
    prompt: str,
    system_prompt: str = "You are a helpful banking assistant.",
    model: str = "llama-3.3-70b-versatile",
    json_mode: bool = True,
    max_tokens: int = 1024,
) -> str:
    """
    Generate completion dynamically based on the provided API key.
    Supports Groq, xAI, Gemini, and OpenAI.
    """
    primary_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if not any([primary_key, gemini_key, openai_key]):
        return '{"error": "No LLM API keys available. Please configure GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY."}'

    # 1. Try Primary Key (Groq or xAI)
    if primary_key:
        is_xai = primary_key.startswith("xai-")
        url = "https://api.x.ai/v1/chat/completions" if is_xai else "https://api.groq.com/openai/v1/chat/completions"
        actual_model = "grok-beta" if is_xai else model
        provider_name = "xAI" if is_xai else "Groq"
        
        try:
            logger.info(f"[LLM] Attempting {provider_name} generation...")
            return _call_openai_compatible_api(
                url=url,
                key=primary_key,
                model=actual_model,
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.info(f"[LLM] {provider_name} failed: {e}. Falling back...")

    # 2. Try Gemini Fallback
    if gemini_key:
        try:
            logger.info("[LLM] Attempting Gemini fallback generation...")
            return _call_openai_compatible_api(
                url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                key=gemini_key,
                model="gemini-1.5-flash",
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.info(f"[LLM] Gemini fallback failed: {e}. Falling back...")

    # 3. Try OpenAI Fallback
    if openai_key:
        try:
            logger.info("[LLM] Attempting OpenAI fallback generation...")
            return _call_openai_compatible_api(
                url="https://api.openai.com/v1/chat/completions",
                key=openai_key,
                model="gpt-4o-mini",
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.info(f"[LLM] OpenAI fallback failed: {e}")
            return f'{{"error": "All available LLMs failed. Last error: {e}"}}'

    return '{"error": "Unable to generate analysis: All configured LLMs failed or no credits available."}'
