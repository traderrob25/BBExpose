
import sys
import os
from datetime import datetime

# Añadir path del motor
sys.path.append('/Users/robertonoguez/Desktop/Roberto/PARA/AREAS/Financial Freedom/Biz Ready/Hexada/Hexada AiAgent/Trading/Scanner/hexada-scanner-web/api')

from yos_bot_engine import YOSTradingBot, Config, OperationalMoment

def run_full_scan():
    bot = YOSTradingBot(api_key=None)
    
    # Parcheamos el proveedor de datos para traer suficiente historial para EMA 200
    def patched_get_intraday(self, symbol, interval="15min"):
        yf_interval = "15m" if interval == "15min" else "60m"
        ticker = import_yf().Ticker(symbol)
        df = ticker.history(period="60d", interval=yf_interval) # 60 días para tener >200 barras de 60m
        if df.empty: return df
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        if df.index.tz is not None: df.index = df.index.tz_convert(None)
        return df

    def patched_get_daily(self, symbol):
        ticker = import_yf().Ticker(symbol)
        df = ticker.history(period="2y", interval="1d") # 2 años para EMA 200 Daily
        if df.empty: return df
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        if df.index.tz is not None: df.index = df.index.tz_convert(None)
        return df

    def import_yf():
        import yfinance as yf
        return yf

    import types
    bot.data_provider.get_intraday_data = types.MethodType(patched_get_intraday, bot.data_provider)
    bot.data_provider.get_daily_data = types.MethodType(patched_get_daily, bot.data_provider)
    
    # Reiniciamos el analizador a su estado original (que pide 200 barras)
    # porque ahora sí las tenemos.
    
    print("--- INICIANDO ESCANEO MULTI-ACTIVO PROFUNDO ---")
    signals = bot.run_scan("mid_session")

    
    report = bot.generate_report()
    print(report)

if __name__ == "__main__":
    run_full_scan()
