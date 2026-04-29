import streamlit as st
import pandas as pd
import time
import ta
import plotly.graph_objects as go

# --- Genzura niba MetaTrader5 ihari (Kuri Windows gusa) ---
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

st.set_page_config(page_title="ZuriTrade Pro Max", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .main { background-color: #111; color: white; }
    .stMetric { border: 1px solid #333; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Zuri Intelligence")
    user_id = st.text_input("MT5 Login ID", value="168145640")
    password = st.text_input("MT5 Password", type="password")
    server = st.text_input("Broker Server", value="XMGlobal-MT5 2")
    
    st.divider()
    if not MT5_AVAILABLE:
        st.warning("⚠️ Cloud Mode: MT5 is only active when running locally on Windows.")
    
    if st.button("🚀 ACTIVATE BOT", use_container_width=True):
        st.session_state.bot_active = True

# --- LOGIC ---
st.header("📊 ZuriTrade AI - Live Operations")

placeholder = st.empty()

if st.session_state.get('bot_active', False):
    # Kugerageza gufungura MT5 niba ihari
    initialized = False
    if MT5_AVAILABLE:
        if mt5.initialize(login=int(user_id), password=password, server=server):
            initialized = True
    
    while True:
        with placeholder.container():
            if initialized and MT5_AVAILABLE:
                # --- REAL DATA MODE (Kuri Laptop yawe) ---
                acc = mt5.account_info()
                balance = acc.balance
                equity = acc.equity
                profit = acc.profit
                status = "Connected to Live MT5"
            else:
                # --- DEMO DATA MODE (Kuri Internet/Cloud) ---
                balance = 1000.87
                equity = 1000.87
                profit = 0.00
                status = "Demo Mode (Internet Preview)"

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Balance", f"${balance:,.2f}")
            c2.metric("Equity", f"${equity:,.2f}")
            c3.metric("Profit", f"${profit:,.2f}")
            fee = profit * 0.15 if profit > 0 else 0
            c4.metric("Performance Fee (15%)", f"${fee:,.2f}")

            st.info(f"🛰️ Bot Status: {status}")
            
            # Placeholder for Graph
            st.subheader("Market Trend Analysis")
            st.write("Scanning market for RSI and Moving Average signals...")
            
            time.sleep(10)
            st.rerun()
else:
    st.info("Waiting for Activation... Enter credentials and click 'ACTIVATE BOT'.")
