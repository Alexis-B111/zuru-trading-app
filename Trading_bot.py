import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import ta

# ---------- CONFIGURATION ----------
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
MAGIC = 999
MAX_TRADES = 2
PERFORMANCE_FEE_RATE = 0.15  # 15% Fee
DAILY_LOSS_LIMIT = 0.03      # Guhagarara iyo mwahombye 3% ku munsi

# Iyi izajya ibika amafaranga menshi konti yigeze kugeraho (High Water Mark)
peak_balance = 0.0

# ---------- CONNECT ----------
def connect():
    if not mt5.initialize():
        print("MT5 initialization failed")
        return False
    print("Connected to MT5 - Ready to Trade")
    return True

# ---------- GET DATA ----------
def get_data():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 200)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['close'] = df['close'].astype(float)
    return df

# ---------- SMART STRATEGY ----------
def apply_strategy(df):
    # Moving Average (Trend)
    df['ma'] = df['close'].rolling(50).mean()
    # RSI (Momentum)
    indicator_rsi = ta.momentum.RSIIndicator(close=df['close'], window=14)
    df['rsi'] = indicator_rsi.rsi()
    return df

# ---------- RISK & FEE MANAGEMENT ----------
def risk_and_fee_check():
    global peak_balance
    acc = mt5.account_info()
    if acc is None: return False

    current_balance = acc.balance
    equity = acc.equity

    # 1. Update Peak Balance & Calculate Fee
    if current_balance > peak_balance:
        if peak_balance > 0:
            profit = current_balance - peak_balance
            fee = profit * PERFORMANCE_FEE_RATE
            print(f">>> New Profit! Total: ${profit:.2f} | Your 15% Fee: ${fee:.2f}")
        peak_balance = current_balance

    # 2. Daily Drawdown Protection
    if equity < (current_balance * (1 - DAILY_LOSS_LIMIT)):
        print("!!! ALERT: Daily loss limit reached. Trading suspended for safety.")
        return False

    # 3. Spread Filter
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info.spread > 20: # Adjust based on broker
        print("Spread too high, waiting for better market conditions.")
        return False

    return True

# ---------- LOT SIZE CALCULATION ----------
def get_lot():
    acc = mt5.account_info()
    if acc is None: return 0.01
    # Risking 1% of balance per trade
    lot = round((acc.balance * 0.01) / 100, 2) 
    return max(lot, 0.01)

# ---------- PLACE TRADE ----------
def place(order_type):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None: return

    lot = get_lot()
    filling_mode = mt5.symbol_info(SYMBOL).filling_mode

    if order_type == "buy":
        price = tick.ask
        sl = price - 0.0020 # 20 pips
        tp = price + 0.0040 # 40 pips
        order = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl = price + 0.0020
        tp = price - 0.0040
        order = mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": order,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": MAGIC,
        "comment": "Zuri Smart Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }

    result = mt5.order_send(request)
    print(f"Trade Execution: {order_type} | Result: {result.comment if result else 'Failed'}")

# ---------- MAIN LOOP ----------
def run():
    if not connect(): return

    print("Bot is running...")
    
    while True:
        try:
            # Check Risk & Performance fees
            if not risk_and_fee_check():
                time.sleep(60)
                continue

            # Check Max Trades
            if mt5.positions_total() >= MAX_TRADES:
                time.sleep(30)
                continue

            # Get and Process Data
            df = get_data()
            if df is None:
                time.sleep(10)
                continue

            df = apply_strategy(df)
            last = df.iloc[-1]

            # TRADING LOGIC
            # BUY: Price > MA AND RSI is neutral (45-55)
            if last['close'] > last['ma'] and 45 < last['rsi'] < 55:
                place("buy")

            # SELL: Price < MA AND RSI is neutral (45-55)
            elif last['close'] < last['ma'] and 45 < last['rsi'] < 55:
                place("sell")

            time.sleep(60) # Wait 1 minute before next check

        except Exception as e:
            print(f"System Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run()