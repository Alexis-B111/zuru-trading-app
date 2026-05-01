import streamlit as st
import pandas as pd
from supabase import create_client
import time

# --- 1. CONFIGURATION (Shyira amakuru yawe hano) ---
SUPABASE_URL = "URL_YA_SUPABASE"
SUPABASE_KEY = "KEY_YA_SUPABASE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ZuriTrade AI - Live", layout="wide")
st.title("📊 ZuriTrade AI - Live Dashboard")

# --- 2. GUKURA AMAKURU KURI CLOUD ---
def get_data():
    try:
        # Isoma umurongo wa nyuma muri Table yitwa 'bot_logs'
        response = supabase.table("bot_logs").select("*").order("id", desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    except:
        return None

data = get_data()

if data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Balance", f"${data['balance']:,.2f}")
    c2.metric("Equity", f"${data['equity']:,.2f}")
    c3.metric("Profit", f"${data['profit']:,.2f}")
    
    st.info(f"Bot Status: {data['status']}")
else:
    st.warning("Waiting for data from local bot... Make sure Supabase is connected.")

# Refresh automatic buri masegonda 5
time.sleep(5)
st.rerun()
