import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from flask import Flask, jsonify

warnings.filterwarnings('ignore')

OPTIONABLE_STOCKS = ['NVDA', 'SPY', 'QQQ', 'IWM', 'AMD', 'PLTR', 'AAPL', 'GOOGL', 'NFLX', 'SOXL', 'MU', 'AVGO']

app = Flask(__name__)

def calculate_bollinger_bands(df, period=20, std_dev=2):
    if df is None or len(df) < period:
        return None, None, None, None
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return sma, upper_band, lower_band, std

def get_bb_position(current_price, upper_band, lower_band, sma):
    if pd.isna(upper_band) or pd.isna(lower_band):
        return None, 0
    band_width = upper_band - lower_band
    if band_width > 0:
        position_pct = ((current_price - lower_band) / band_width) * 100
    else:
        position_pct = 50
    if position_pct >= 100:
        return 'UPPER', position_pct
    elif position_pct <= 0:
        return 'LOWER', position_pct
    else:
        return 'MIDDLE', position_pct

def analyze_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        current_price_info = info.get('currentPrice', info.get('regularMarketPrice', 0))

        spread_pct = 0
        spread_ok = True
        if bid and ask and ask > bid and current_price_info > 0:
            spread_pct = ((ask - bid) / current_price_info) * 100
            if spread_pct > 0.5:
                spread_ok = False

        if not spread_ok:
            return None

        hist_15m = ticker.history(period="5d", interval="15m")
        hist_1h = ticker.history(period="1mo", interval="1h")
        hist_1d = ticker.history(period="6mo", interval="1d")
        hist_1wk = ticker.history(period="2y", interval="1wk")
        hist_1mo = ticker.history(period="5y", interval="1mo")

        if len(hist_1d) < 20 or len(hist_1h) < 20 or len(hist_15m) < 52 or len(hist_1wk) < 20 or len(hist_1mo) < 20:
            return None

        sma_15m, upper_15m, lower_15m, _ = calculate_bollinger_bands(hist_15m)
        sma_1h, upper_1h, lower_1h, _ = calculate_bollinger_bands(hist_1h)
        sma_1d, upper_1d, lower_1d, _ = calculate_bollinger_bands(hist_1d)
        sma_1wk, upper_1wk, lower_1wk, _ = calculate_bollinger_bands(hist_1wk)
        sma_1mo, upper_1mo, lower_1mo, _ = calculate_bollinger_bands(hist_1mo)

        if any(x is None for x in [sma_15m, sma_1h, sma_1d, sma_1wk, sma_1mo]):
            return None

        current_price = hist_1d['Close'].iloc[-1]
        
        bb_width_15m = ((upper_15m - lower_15m) / sma_15m) * 100
        is_expanding = bb_width_15m.iloc[-1] > bb_width_15m.iloc[-2]
        min_48h = bb_width_15m.iloc[-52:].min()
        is_squeeze = bb_width_15m.iloc[-1] <= min_48h

        pos_15m, pct_15m = get_bb_position(hist_15m['Close'].iloc[-1], upper_15m.iloc[-1], lower_15m.iloc[-1], sma_15m.iloc[-1])
        pos_1h, pct_1h = get_bb_position(hist_1h['Close'].iloc[-1], upper_1h.iloc[-1], lower_1h.iloc[-1], sma_1h.iloc[-1])
        pos_1d, pct_1d = get_bb_position(current_price, upper_1d.iloc[-1], lower_1d.iloc[-1], sma_1d.iloc[-1])
        pos_1wk, pct_1wk = get_bb_position(current_price, upper_1wk.iloc[-1], lower_1wk.iloc[-1], sma_1wk.iloc[-1])
        pos_1mo, pct_1mo = get_bb_position(current_price, upper_1mo.iloc[-1], lower_1mo.iloc[-1], sma_1mo.iloc[-1])

        if any(x is None for x in [pos_15m, pos_1h, pos_1d, pos_1wk, pos_1mo]):
            return None

        triple_confluence = False
        confluence_type = None
        if pos_1d == 'UPPER' and pos_1h == 'UPPER' and pos_15m == 'UPPER':
            triple_confluence = True
            confluence_type = 'UPPER'
            confluencia_str = "UPPER"
        elif pos_1d == 'LOWER' and pos_1h == 'LOWER' and pos_15m == 'LOWER':
            triple_confluence = True
            confluence_type = 'LOWER'
            confluencia_str = "LOWER"
        else:
            confluencia_str = "NINGUNA"

        long_term_confluence = False
        long_term_type = None
        if pos_1wk == 'UPPER' and pos_1mo == 'UPPER':
            long_term_confluence = True
            long_term_type = 'UPPER'
        elif pos_1wk == 'LOWER' and pos_1mo == 'LOWER':
            long_term_confluence = True
            long_term_type = 'LOWER'

        target_sma20 = round(sma_15m.iloc[-1], 2)
        distancia_target_pct = round(((target_sma20 - current_price) / current_price) * 100, 2)
        alerta_reversion = pos_15m in ['UPPER', 'LOWER']

        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'spread_pct': round(spread_pct, 4) if spread_pct > 0 else 'N/A',
            'triple_confluence': triple_confluence,
            'confluence_type': confluence_type,
            'confluencia_3tf': confluencia_str,
            'is_volatility_active': bool(is_expanding or is_squeeze),
            'is_expanding': bool(is_expanding),
            'is_squeeze': bool(is_squeeze),
            'long_term_confluence': long_term_confluence,
            'long_term_type': long_term_type,
            'target_sma20': target_sma20,
            'distancia_target_pct': distancia_target_pct,
            'alerta_reversion': alerta_reversion,
            'pos_15m': pos_15m, 'pct_15m': round(pct_15m, 1),
            'pos_1h': pos_1h, 'pct_1h': round(pct_1h, 1),
            'pos_1d': pos_1d, 'pct_1d': round(pct_1d, 1),
            'pos_1wk': pos_1wk, 'pct_1wk': round(pct_1wk, 1),
            'pos_1mo': pos_1mo, 'pct_1mo': round(pct_1mo, 1)
        }
    except Exception as e:
        return None

@app.route('/api/scan')
def scan_api():
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {executor.submit(analyze_stock, symbol): symbol for symbol in OPTIONABLE_STOCKS}
        for future in as_completed(future_to_symbol):
            try:
                res = future.result()
                if res is not None:
                    results.append(res)
            except Exception:
                pass

    return jsonify({"status": "success", "data": results})

if __name__ == "__main__":
    app.run(port=5328)
