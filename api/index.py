import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from flask import Flask, jsonify, request

warnings.filterwarnings('ignore')

# Prioridad definida por el usuario
PRIORITY_STOCKS = ['PLTR', 'GOOGL']
SECONDARY_STOCKS = ['SPY', 'QQQ', 'AMD', 'NVDA']
OPTIONABLE_STOCKS = PRIORITY_STOCKS + SECONDARY_STOCKS + ['AAPL', 'IWM', 'NFLX', 'SOXL', 'MU', 'AVGO']

# Base de datos pre-configurada (Cualitativa) para el Asymmetry Dashboard
DEEP_VALUE_DB = [
    {"ticker": "POWL", "asymmetriesPresent": [1, 3, 4, 6], "notes": "Electrical equipment, strong ROIC, insider buying"},
    {"ticker": "SSD",  "asymmetriesPresent": [1, 2, 6, 7], "notes": "Construction products, decentralized operations"},
    {"ticker": "ROLL", "asymmetriesPresent": [1, 2, 3, 6], "notes": "Industrial bearings, active acquirer"},
    {"ticker": "EXPD", "asymmetriesPresent": [2, 6, 7], "notes": "Logistics, exceptional ROIC, decentralized model"},
    {"ticker": "BZH",  "asymmetriesPresent": [1, 5, 6], "notes": "Deep value builder, P/B bajo 1.0, enorme potencial alcista."},
    {"ticker": "CWH",  "asymmetriesPresent": [2, 4, 5, 7], "notes": "Muy por debajo de valor, fuerte compra de insiders."},
    {"ticker": "RICK", "asymmetriesPresent": [3, 4, 6, 7], "notes": "Fuerte flujo de caja libre, recompras masivas."},
    {"ticker": "LANC", "asymmetriesPresent": [2, 5, 6, 7], "notes": "Pricing power, adquisiciones estratégicas recientes."},
    {"ticker": "PLAB", "asymmetriesPresent": [1, 4, 5, 7], "notes": "Sector semi castigado, compras de insiders."},
    {"ticker": "SXC",  "asymmetriesPresent": [1, 2, 4, 6], "notes": "Materiales básicos con escasez estructural."}
]

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

        # Determinar nivel de alerta para prioridad
        is_priority = symbol in PRIORITY_STOCKS
        high_alert = pos_1wk in ['UPPER', 'LOWER'] or pos_1mo in ['UPPER', 'LOWER']

        return {
            'symbol': symbol,
            'is_priority': is_priority,
            'high_alert': high_alert,
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
        print(f"Error analizando {symbol}: {e}")
        return None

def get_deep_value_metrics(stock_data):
    """Obtiene metadata cuantitativa pesada de YF y la fusiona con la data cualitativa."""
    symbol = stock_data['ticker']
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        target_price = info.get('targetMeanPrice') or info.get('targetPrice') or current_price
        
        # Mezclamos la data cualitativa de la DB con la Cuantitativa Viva
        result = {
            'ticker': symbol,
            'name': info.get('longName') or info.get('shortName') or symbol,
            'sector': info.get('sector', 'N/A'),
            'price': current_price,
            'marketCap': round((info.get('marketCap') or 0) / 1e9, 2), # Billions
            'pbRatio': round(info.get('priceToBook') or 99.9, 2),
            'targetPrice': target_price,
            'analystScore': round(info.get('recommendationMean') or 5.0, 1),
            'change': 0.0, # Placeholder
            
            # Asimetrías y métricas cualitativas
            'asymmetriesPresent': stock_data.get('asymmetriesPresent', []),
            'notes': stock_data.get('notes', ''),
            'insiderOwnership': round((info.get('heldPercentInsiders') or 0) * 100, 1),
            'roic': round((info.get('returnOnEquity') or 0) * 100, 1), # Proxy usando ROE
            'analystCoverage': info.get('numberOfAnalystOpinions', 0),
            'recentInsiderBuys': stock_data.get('recentInsiderBuys', 0),
            'acquisitionsYearly': stock_data.get('acquisitionsYearly', 0)
        }
        return result
    except Exception as e:
        print(f"Error fetching deep value for {symbol}: {e}")
        return stock_data # Retorna data básica si falla YF

def send_discord_alert(reversiones):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return
    
    # Ordenar por prioridad
    reversiones.sort(key=lambda x: (not x.get('is_priority', False), not x.get('high_alert', False)))

    content = "🛡️ **HEXADA BOLLINGER SCANNER** 🛡️\n"
    content += f"Prioridad: **PLTR, GOOGL** | Scanner: Multi-TF\n"
    content += "─" * 20 + "\n"

    for s in reversiones:
        emoji = "⭐" if s.get('is_priority') else "▶️"
        tf_alert = []
        if s['pos_1mo'] != 'MIDDLE': tf_alert.append(f"MES ({s['pos_1mo']})")
        if s['pos_1wk'] != 'MIDDLE': tf_alert.append(f"SEM ({s['pos_1wk']})")
        if s['pos_1d'] != 'MIDDLE': tf_alert.append(f"DIA ({s['pos_1d']})")
        if s['pos_1h'] != 'MIDDLE': tf_alert.append(f"1H ({s['pos_1h']})")
        if s['pos_15m'] != 'MIDDLE': tf_alert.append(f"15M ({s['pos_15m']})")
        
        tfs_str = " | ".join(tf_alert) if tf_alert else "Squeeze/Exposición detectada"
        
        content += f"{emoji} **{s['symbol']}** | ${s['price']}\n"
        content += f"📍 Exposición: `{tfs_str}`\n"
        
        if s['pos_15m'] != 'MIDDLE':
            direccion = "🔴 VENDER/SHORT" if s['pos_15m'] == 'UPPER' else "🟢 COMPRAR/REBOTE"
            content += f"⚡ Señal 15M: **{direccion}** (Target: ${s['target_sma20']})\n"
        
        if s['triple_confluence']:
            content += f"⚠️ **TRIPLE CONFLUENCIA ACTIVA ({s['confluencia_3tf']})**\n"
        
        content += "─" * 15 + "\n"
    
    payload = {"content": content}
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print("Error enviando a Discord:", e)

@app.route('/api/asymmetry')
def asymmetry_api():
    """Endpoint para cargar el Dashboard de Asimetrías con datos reales"""
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {executor.submit(get_deep_value_metrics, stock): stock for stock in DEEP_VALUE_DB}
        for future in as_completed(future_to_symbol):
            try:
                res = future.result()
                if res and 'price' in res:
                    results.append(res)
            except Exception:
                pass
                
    return jsonify({
        "status": "success",
        "data": results
    })

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

    yoel_signals_dict = []
    modo = "unknown"
    try:
        from yos_bot_engine import YOSTradingBot
        from datetime import datetime
        import pytz
        
        tz = pytz.timezone("America/New_York")
        now = datetime.now(tz)
        hora = now.hour
        minuto = now.minute
        if hora == 9 and minuto <= 45:
            modo = "yoel_open"
        elif hora == 15 and minuto >= 45:
            modo = "cardona_close"
        else:
            modo = "mid_session"
            
        yoel_bot = YOSTradingBot(api_key=None)
        yoel_signals = yoel_bot.run_scan(modo)
        
        # Filtrar o mandar todas, las mandamos todas como diccionario
        yoel_signals_dict = yoel_bot.get_signals_json()
        if yoel_signals_dict is None:
             yoel_signals_dict = []
    except Exception as e:
        print("Error con YOS Bot:", e)

    return jsonify({
        "status": "success", 
        "data": results,
        "yos_signals": yoel_signals_dict,
        "yos_mode": modo
    })

@app.route('/api/cron')
def cron_api():
    # Seguridad básica de Vercel Cron 
    auth_header = request.headers.get('Authorization')
    if os.environ.get('CRON_SECRET') and auth_header != f"Bearer {os.environ.get('CRON_SECRET')}":
        return jsonify({"status": "unauthorized"}), 401
        
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

    # Filtrar cualquier activo que tenga exposición en CUALQUIER timeframe
    alertas = []
    for r in results:
        tfs = [r['pos_15m'], r['pos_1h'], r['pos_1d'], r['pos_1wk'], r['pos_1mo']]
        if any(tf != 'MIDDLE' for tf in tfs):
            alertas.append(r)
            
    if alertas:
        send_discord_alert(alertas)

    return jsonify({"status": "success", "alerts_sent": len(alertas)})

if __name__ == "__main__":
    app.run(port=5328)
