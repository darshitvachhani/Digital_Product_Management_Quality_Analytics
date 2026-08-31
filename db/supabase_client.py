import os
import streamlit as st
from typing import Optional
from supabase import create_client, Client

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Returns a cached Supabase Client if credentials exist."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        print(f"Warning: Could not connect to Supabase: {e}")
        return None
