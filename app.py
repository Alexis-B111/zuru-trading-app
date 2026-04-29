import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
import time
import ta
from datetime import datetime

# --- CONFIGURATION Y'ISURA (UI) ---
st.set_page_config(page_title="ZuriTrade Pro Max", layout="wide", page_icon="💎")

# Guhindura ibara ry'inyuma n'imyandiko (Custom CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

# --- SIDEBAR: AUTHENTICATION ---
with st.sidebar:
    st.title("🛡️ Intelligence Hub")
    user_id = st.text_input("MT5 Login ID", value="168145640")
    password = st.text_input("MT5 Password", type="password")
    server = st.text_input("Broker Server", value="XMGlobal-MT5 2")
    
    st.markdown("---")
    asset_selected = st.selectbox("Select Asset", ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"])
    
    col_start, col_stop = st.columns(2)
    if col_start.button("🚀 ACTIVATE BOT", use_container_width=True):
        st.session_state.bot_running = True
    if col_stop.button("🛑 DEACTIVATE", use_container_width=True):
        st.session_state.bot_running = False
        mt5.shutdown()

# --- FUNCTIONS ---
def get_market_data(symbol):
    # Kopiye imishumi (rates) 100 yanyuma
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
    
    if rates is None or len(rates) == 0:
        return None
        
    df = pd.DataFrame(rates)
    
    # KUKOSORA KEYERROR 'TIME':
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], unit='s')
    
    df['close'] = df['close'].astype(float)
    df['ma'] = df['close'].rolling(50).mean()
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    return df

def execute_trade(symbol, order_type):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None: return
    
    acc = mt5.account_info()
    lot = max(round((acc.balance * 0.01) / 100, 2), 0.01) # Risk 1%
    filling = mt5.symbol_info(symbol).filling_mode
    
    price = tick.ask if order_type == "buy" else tick.bid
    sl = price - 0.0030 if order_type == "buy" else price + 0.0030
    tp = price + 0.0060 if order_type == "buy" else price - 0.0060

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "ZuriTrade Auto",
        "type_filling": filling,
    }
    result = mt5.order_send(request)
    return result

# --- MAIN DASHBOARD ---
st.header(f"💎 ZuriTrade Pro Max - Intelligence Hub")

placeholder = st.empty()

if st.session_state.bot_running:
    if not mt5.initialize(login=int(user_id) if user_id else 0, password=password, server=server):
        st.error("❌ MT5 Initialization Failed. Check Credentials.")
        st.session_state.bot_running = False
    else:
        while st.session_state.bot_running:
            with placeholder.container():
                acc = mt5.account_info()
                df = get_market_data(asset_selected)

                if acc and df is not None:
                    # 1. METRICS ROW
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Account Balance", f"${acc.balance:,.2f}")
                    m2.metric("Equity", f"${acc.equity:,.2f}")
                    m3.metric("Current Profit", f"${acc.profit:,.2f}", delta=f"{acc.profit:.2f}")
                    
                    # 15% Performance Fee Calculation
                    perf_fee = (acc.profit * 0.15) if acc.profit > 0 else 0.0
                    m4.metric("Performance Fee (15%)", f"${perf_fee:,.2f}")

                    # 2. ANALYSIS INFO
                    last_row = df.iloc[-1]
                    st.divider()
                    st.subheader(f"📈 {asset_selected} Market Analysis")
                    st.write(f"**Price:** {last_row['close']} | **RSI:** {last_row['rsi']:.2f} | **MA 50:** {last_row['ma']:.5f}")

                    # 3. TRADING LOGIC
                    if mt5.positions_total() < 1: # Trade 1 at a time for safety
                        if last_row['close'] > last_row['ma'] and 40 < last_row['rsi'] < 60:
                            execute_trade(asset_selected, "buy")
                            st.toast(f"🚀 BUY Order Placed for {asset_selected}!")
                        elif last_row['close'] < last_row['ma'] and 40 < last_row['rsi'] < 60:
                            execute_trade(asset_selected, "sell")
                            st.toast(f"📉 SELL Order Placed for {asset_selected}!")

                    # 4. LIVE POSITIONS
                    st.subheader("📋 Active Trades")
                    positions = mt5.positions_get(symbol=asset_selected)
                    if positions:
                        pos_df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
                        st.dataframe(pos_df[['symbol', 'type', 'volume', 'price_open', 'profit']], use_container_width=True)
                    else:
                        st.info("No active trades. Scanning for signals...")

                else:
                    st.warning(f"Waiting for data from {asset_selected}... Check if Symbol is correct in MT5.")

                time.sleep(5) # Refresh amasegonda 5
                st.rerun()
else:
    st.info("⏸️ Bot is Deactivated. Enter credentials and click 'ACTIVATE BOT' to start.")