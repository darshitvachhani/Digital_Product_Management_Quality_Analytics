import os
from typing import Optional

def get_gemini_api_key() -> Optional[str]:
    """Safely retrieves the Gemini API Key from environment, Streamlit session, or secrets."""
    # 1. Environment Variable
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key

    # 2. Streamlit Session / Secrets (only if Streamlit runtime is running)
    try:
        import streamlit as st
        if hasattr(st, "runtime") and st.runtime.exists():
            if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
                return st.session_state["gemini_api_key"]
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY", "")

def call_gemini(
    prompt: str,
    system_instruction: str = "",
    model: str = "gemini-2.5-flash",
    fallback: Optional[str] = None
) -> Optional[str]:
    """
    Executes a Gemini API generation request using google-genai SDK.
    Returns the response text, or fallback/None if the API call fails.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return fallback

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        if response and response.text:
            return response.text
    except Exception as e:
        # Fallback retry with gemini-2.5-flash / gemini-2.5-pro
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception:
            pass

    return fallback
