
import sys
import os
import json
from datetime import datetime
import pandas as pd

# Añadir el path para importar yos_bot_engine
# Estamos en hexada-scanner-web/api/nvda_debug.py
# El motor está en el mismo directorio.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yos_bot_engine import YOSTradingBot, Config, OperationalMoment

def analyze_nvda():
    # Forzamos NVDA como único instrumento para el análisis rápido
    Config.INSTRUMENTS = ["NVDA"]
    
    # Parcheamos el analizador para que acepte menos de 200 barras si es necesario
    # para poder ver NVDA ahora mismo aunque falten datos históricos en el fetch.
    from yos_bot_engine import TechnicalAnalyzer
    original_analyze = TechnicalAnalyzer.analyze
    def patched_analyze(self, df, symbol, timeframe):
        if df.empty or len(df) < 20: # Bajamos a 20 para debug de 1H y 15M
            return None
        return original_analyze(self, df, symbol, timeframe)
    
    # TechnicalAnalyzer.analyze = patched_analyze # Esto no funcionará bien si es un método de instancia ya ligado
    
    bot = YOSTradingBot(api_key=None)
    # Aplicamos el parche a la instancia
    import types
    bot.analyzer.analyze = types.MethodType(patched_analyze, bot.analyzer)
    
    print("--- ANALIZANDO NVDA (DIAGNÓSTICO VIVO) ---")
    
    # Obtenemos datos manualmente para ver qué está pasando
    df_15m = bot.data_provider.get_intraday_data("NVDA", "15min")
    print(f"Barras 15m obtenidas: {len(df_15m)}")
    
    if not df_15m.empty:
        # Calcular indicadores básicos manuales por si el motor falla
        close = df_15m['close'].iloc[-1]
        sma20 = df_15m['close'].rolling(20).mean().iloc[-1]
        std20 = df_15m['close'].rolling(20).std().iloc[-1]
        upper = sma20 + (2 * std20)
        lower = sma20 - (2 * std20)
        
        print(f"\n[DATOS CRUDOS NVDA 15M]")
        print(f"Precio: ${close:.2f}")
        print(f"SMA 20: ${sma20:.2f}")
        print(f"Upper Band: ${upper:.2f}")
        print(f"Lower Band: ${lower:.2f}")
        
        if close > upper:
            print("⚠️ NVDA SOBREBANDA SUPERIOR (Exceso Alcista)")
        elif close < lower:
            print("⚠️ NVDA BAJOBANDA INFERIOR (Exceso Bajista)")
        else:
            print("✅ NVDA dentro de bandas.")

    signals = bot.run_scan("yoel_open")
    if signals:
        print(bot.generate_report())
    else:
        print("\nEl motor Yoel no generó señales automáticas (posiblemente por falta de confirmaciones o datos).")

if __name__ == "__main__":
    analyze_nvda()
