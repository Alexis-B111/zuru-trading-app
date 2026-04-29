import streamlit as st
import pandas as pd
import time
import ta
import sqlite3
import os

# --- 1. HANDLING METATRADER 5 & OS CHECK ---
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

st.set_page_config(page_title="ZuriTrade AI - Pro", layout="wide")

# --- 2. DATABASE SETUP (Guhuza Local na Cloud) ---
DB_NAME = "trading_platform.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bot_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, balance REAL, equity REAL, profit REAL, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. RISK MANAGEMENT & TRADING LOGIC ---
def execute_trading_logic(user_id, password, server):
    if not MT5_AVAILABLE: return
    
    if not mt5.initialize(login=int(user_id), password=password, server=server):
        return

    # Assets zo guscaninga
    assets = ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]
    
    while st.session_state.bot_active:
        acc = mt5.account_info()
        if acc is None: break
        
        # --- AUTOMATED RISK MANAGEMENT ---
        initial_balance = 1000.0 # Shaka balance yawe ya mbere hano
        current_profit_pct = (acc.profit / acc.balance) * 100

        # Stop if 1% Loss or 50% Profit reached
        if current_profit_pct <= -1.0 or current_profit_pct >= 50.0:
            st.session_state.bot_active = False
            mt5.positions_get() # Close all logic can be added here
            break

        # --- SMART SCANNING ---
        for symbol in assets:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
            if rates is None: continue
            
            df = pd.DataFrame(rates)
            rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
            ma = df['close'].rolling(50).mean().iloc[-1]
            current_price = df['close'].iloc[-1]

            # Logic: RSI + MA Strategy
            if rsi < 30 and current_price > ma:
                # Place BUY order logic
                pass 

        # Bika amakuru muri Database kugira ngo Internet iyabone
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO bot_logs (balance, equity, profit, status) VALUES (?, ?, ?, ?)",
                  (acc.balance, acc.equity, acc.profit, f"Scanning {len(assets)} assets..."))
        conn.commit()
        conn.close()
        
        time.sleep(10)

# --- 4. UI DASHBOARD ---
st.sidebar.title("🛡️ Zuri Intelligence")
user_id = st.sidebar.text_input("MT5 ID", value="168145640")
password = st.sidebar.text_input("Password", type="password")
server = st.sidebar.text_input("Server", value="XMGlobal-MT5 2")

if st.sidebar.button("🚀 ACTIVATE BOT"):
    st.session_state.bot_active = True
    if MT5_AVAILABLE:
        execute_trading_logic(user_id, password, server)

# --- 5. DATA DISPLAY (Reading from DB) ---
st.header("📊 ZuriTrade AI - Live Intelligence")

conn = sqlite3.connect(DB_NAME)
try:
    df_logs = pd.read_sql_query("SELECT * FROM bot_logs ORDER BY id DESC LIMIT 1", conn)
    if not df_logs.empty:
        last = df_logs.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Balance", f"${last['balance']:,.2f}")
        c2.metric("Equity", f"${last['equity']:,.2f}")
        c3.metric("Live Profit", f"${last['profit']:,.2f}")
        c4.metric("Performance Fee (15%)", f"${last['profit']*0.15 if last['profit'] > 0 else 0:,.2f}")
        st.success(f"Bot Status: {last['status']}")
    else:
        st.info("Waiting for data from local bot...")
except:
    st.warning("Database is syncing...")
conn.close()

# Auto-refresh
time.sleep(5)
st.rerun()
