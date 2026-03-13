"""
═══════════════════════════════════════════════════════════════════════════════
                    YOS TRADING BOT ENGINE v1.1 (CORREGIDO)
                    Sistema Yoel Sardiñas + Cardona
═══════════════════════════════════════════════════════════════════════════════

ESTRUCTURA DEL SISTEMA:
┌─────────────────────────────────────────────────────────────────────────────┐
│  YOEL (PRIORIDAD) - 9:15-9:45 AM ET                                        │
│  ├── Objetivo: Capturar VOLATILIDAD extrema de Bollinger en apertura       │
│  ├── Estrategias: #1-#8 (especialmente #5, #6 para excesos)                │
│  ├── Entrada: INMEDIATA (primeros 5-15 minutos del mercado)                │
│  └── Timeframe: 15M para ejecución, 1H para contexto                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  CARDONA - 3:45 PM ET (15 min antes del cierre)                            │
│  ├── Objetivo: Detectar GAPs potenciales para MAÑANA                       │
│  ├── Análisis: Cierre vs EMAs, proyección de gaps                          │
│  └── Timeframe: Daily                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Autor: Roberto (AI-Enhanced Trading System)
Instrumentos: SPY, QQQ, NVDA, AMD, AAPL, PLTR, GOOGL
═══════════════════════════════════════════════════════════════════════════════
"""

import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    """Configuración central del bot"""
    
    # API Keys (reemplazar con tu key)
    ALPHA_VANTAGE_API_KEY = "TU_API_KEY_AQUI"
    
    # Instrumentos autorizados (Prioridad)
    INSTRUMENTS = ["PLTR", "GOOGL", "SPY", "QQQ", "NVDA", "AMD", "AAPL"]
    
    # Configuración de indicadores YOS
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD = 2
    EMA_PERIODS = [20, 40, 100, 200]
    VOLUME_MA_PERIOD = 50
    
    # Gestión de riesgo
    MAX_POSITION_SIZE = 0.15  # 15% máximo por posición
    CASH_RESERVE = 0.10       # 10% siempre en efectivo
    MIN_CONFIRMATIONS = 3     # Mínimo 3/4 confirmaciones
    
    # ═══════════════════════════════════════════════════════════════════════
    # MOMENTOS OPERATIVOS (hora ET) - CORREGIDO
    # ═══════════════════════════════════════════════════════════════════════
    
    # YOEL - Apertura del mercado (PRIORIDAD)
    YOEL_PRE_ANALYSIS = time(9, 15)      # Análisis pre-apertura
    MARKET_OPEN = time(9, 30)            # Apertura oficial
    YOEL_EXECUTION_WINDOW = time(9, 45)  # Ventana de ejecución Yoel (primeros 15 min)
    
    # Sesión media (estrategias de tendencia)
    MID_SESSION_START = time(10, 0)
    MID_SESSION_END = time(15, 30)
    
    # CARDONA - Pre-cierre (análisis para mañana)
    CARDONA_ANALYSIS = time(15, 45)      # 15 min antes del cierre
    MARKET_CLOSE = time(16, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS Y DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    CALL = "CALL"
    PUT = "PUT"
    NEUTRAL = "NEUTRAL"

class Methodology(Enum):
    """Metodología del sistema"""
    YOEL = "YOEL"           # Prioridad - Apertura
    CARDONA = "CARDONA"     # Pre-cierre - GAPs para mañana
    HYBRID = "HYBRID"       # Combinación (estrategias Daily)

class StrategyType(Enum):
    TREND_CHANGE = "Cambio de Tendencia"
    REBOUND = "Rebote"
    VOLATILITY_EXCESS = "Exceso de Volatilidad"  # Renombrado de GAP_EXCESS
    MAGNET_EFFECT = "Efecto Imán"
    V_PATTERN = "V-Pattern"
    BOLLINGER_SQUEEZE = "Bollinger Squeeze"
    CHANNEL_BREAKOUT = "Canal/Breakout"

class SignalStrength(Enum):
    STRONG = 5      # ⭐⭐⭐⭐⭐
    HIGH = 4        # ⭐⭐⭐⭐
    MEDIUM = 3      # ⭐⭐⭐
    LOW = 2         # ⭐⭐
    WEAK = 1        # ⭐

class OperationalMoment(Enum):
    """Momentos operativos del bot"""
    YOEL_PRE_OPEN = "yoel_pre_open"       # 9:15 AM - Análisis
    YOEL_OPEN = "yoel_open"               # 9:30-9:45 AM - EJECUCIÓN INMEDIATA
    MID_SESSION = "mid_session"           # 10:00 AM - 3:30 PM
    CARDONA_PRE_CLOSE = "cardona_close"   # 3:45 PM - Análisis GAPs mañana

@dataclass
class TechnicalData:
    """Datos técnicos calculados para un instrumento"""
    symbol: str
    timeframe: str
    timestamp: datetime
    
    # Precios OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    # Bollinger Bands (20, 2)
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_width: float  # Ancho relativo (volatilidad)
    
    # EMAs (20, 40, 100, 200)
    ema_20: float
    ema_40: float
    ema_100: float
    ema_200: float
    
    # Derivados
    ema_20_slope: float  # Pendiente de EMA 20
    volume_ratio: float  # Volumen actual / Media 50
    price_vs_bb: str     # "above", "inside", "below"
    trend_direction: str # "bullish", "bearish", "lateral"

@dataclass
class Signal:
    """Señal de trading generada por el bot"""
    timestamp: datetime
    symbol: str
    strategy_id: int
    strategy_name: str
    strategy_type: StrategyType
    methodology: Methodology  # NUEVO: Indica si es YOEL o CARDONA
    direction: Direction
    strength: SignalStrength
    
    # Confirmaciones
    confirmations: List[str] = field(default_factory=list)
    confirmations_met: int = 0
    confirmations_total: int = 4
    
    # Niveles
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    timeframe: str = "15M"
    execution_window: str = "INMEDIATA"  # NUEVO: Ventana de ejecución
    notes: str = ""
    
    def quality_score(self) -> float:
        """Calcula score de calidad del setup (0-100)"""
        return (self.confirmations_met / self.confirmations_total) * 100
    
    def suggested_position_size(self) -> float:
        """Sugiere tamaño de posición basado en calidad"""
        score = self.quality_score()
        if score >= 100:
            return 0.15  # 15%
        elif score >= 75:
            return 0.10  # 10%
        elif score >= 50:
            return 0.05  # 5%
        else:
            return 0.0   # NO OPERAR


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO DE DATOS DE MERCADO
# ═══════════════════════════════════════════════════════════════════════════════

class MarketDataProvider:
    """Proveedor de datos de mercado usando yfinance"""
    
    def __init__(self, api_key: str = None):
        self._cache = {}  # Cache para evitar llamadas repetidas
    
    def get_intraday_data(self, symbol: str, interval: str = "15min") -> pd.DataFrame:
        """
        Obtiene datos intradía de yfinance
        """
        yf_interval = "15m" if interval == "15min" else "60m" if interval == "60min" else interval
        cache_key = f"{symbol}_{interval}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval=yf_interval)
            
            if df.empty:
                return pd.DataFrame()
            
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype(float)
            
            # yfinance returns timezone-aware index, making it naive to match the datetime ops if needed
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
                
            self._cache[cache_key] = df
            return df
            
        except Exception as e:
            print(f"❌ Error en API para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos diarios de yfinance"""
        cache_key = f"{symbol}_daily"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1mo", interval="1d")
            
            if df.empty:
                return pd.DataFrame()
            
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype(float)
            
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
                
            self._cache[cache_key] = df
            return df
            
        except Exception as e:
            print(f"❌ Error en API diaria para {symbol}: {e}")
            return pd.DataFrame()
    
    def clear_cache(self):
        """Limpia el cache de datos"""
        self._cache = {}


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO DE ANÁLISIS TÉCNICO
# ═══════════════════════════════════════════════════════════════════════════════

class TechnicalAnalyzer:
    """Calculador de indicadores técnicos YOS"""
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: int = 2) -> pd.DataFrame:
        """Calcula Bandas de Bollinger (20, 2)"""
        df = df.copy()
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        df['bb_std'] = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (std * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (std * df['bb_std'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'] * 100
        return df
    
    @staticmethod
    def calculate_emas(df: pd.DataFrame, periods: List[int] = [20, 40, 100, 200]) -> pd.DataFrame:
        """Calcula EMAs múltiples (20, 40, 100, 200)"""
        df = df.copy()
        for period in periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_volume_ma(df: pd.DataFrame, period: int = 50) -> pd.DataFrame:
        """Calcula media móvil de volumen (50)"""
        df = df.copy()
        df['volume_ma'] = df['volume'].rolling(window=period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        return df
    
    @staticmethod
    def calculate_slope(series: pd.Series, periods: int = 5) -> float:
        """Calcula la pendiente de una serie (positivo = alcista)"""
        if len(series) < periods:
            return 0.0
        
        recent = series.tail(periods).values
        x = np.arange(periods)
        
        # Regresión lineal simple
        slope = np.polyfit(x, recent, 1)[0]
        return slope
    
    @staticmethod
    def detect_trend(df: pd.DataFrame) -> str:
        """
        Detecta la tendencia basada en orden de EMAs
        
        ALCISTA: close > ema20 > ema40 > ema100 > ema200
        BAJISTA: close < ema20 < ema40 < ema100 < ema200
        LATERAL: Cualquier otro caso
        """
        if df.empty or len(df) < 5:
            return "lateral"
        
        last = df.iloc[-1]
        
        if 'ema_20' in df.columns and 'ema_200' in df.columns:
            ema_20 = last['ema_20']
            ema_40 = last.get('ema_40', ema_20)
            ema_100 = last.get('ema_100', ema_40)
            ema_200 = last['ema_200']
            close = last['close']
            
            if close > ema_20 > ema_40 > ema_100 > ema_200:
                return "bullish"
            elif close < ema_20 < ema_40 < ema_100 < ema_200:
                return "bearish"
        
        return "lateral"
    
    @staticmethod
    def is_lateral_trend(df: pd.DataFrame, periods: int = 10) -> bool:
        """
        Detecta si la tendencia es LATERAL (requisito para estrategias #5, #6)
        Bollinger Bands horizontal y sin volatilidad
        """
        if len(df) < periods:
            return False
        
        recent = df.tail(periods)
        
        # BB Width relativamente constante (baja volatilidad)
        bb_width_std = recent['bb_width'].std()
        bb_width_mean = recent['bb_width'].mean()
        
        # Lateralidad: BB width bajo y estable
        return bb_width_mean < 5.0 and bb_width_std < 1.0
    
    @staticmethod
    def price_position_vs_bollinger(close: float, bb_upper: float, bb_lower: float) -> str:
        """
        Determina posición del precio respecto a Bollinger
        
        ABOVE (Sobrecompra): close > bb_upper → Señal para PUT
        BELOW (Sobreventa): close < bb_lower → Señal para CALL
        INSIDE: Dentro de las bandas
        """
        if close > bb_upper:
            return "above"  # Sobrecompra extrema
        elif close < bb_lower:
            return "below"  # Sobreventa extrema
        else:
            return "inside"
    
    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[TechnicalData]:
        """
        Realiza análisis técnico completo
        
        Returns:
            TechnicalData con todos los indicadores calculados
        """
        if df.empty or len(df) < 200:
            return None
        
        # Calcular todos los indicadores
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_emas(df)
        df = self.calculate_volume_ma(df)
        
        last = df.iloc[-1]
        
        return TechnicalData(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=df.index[-1],
            
            # Precios
            open=last['open'],
            high=last['high'],
            low=last['low'],
            close=last['close'],
            volume=int(last['volume']),
            
            # Bollinger
            bb_upper=last['bb_upper'],
            bb_middle=last['bb_middle'],
            bb_lower=last['bb_lower'],
            bb_width=last['bb_width'],
            
            # EMAs
            ema_20=last['ema_20'],
            ema_40=last['ema_40'],
            ema_100=last['ema_100'],
            ema_200=last['ema_200'],
            
            # Derivados
            ema_20_slope=self.calculate_slope(df['ema_20']),
            volume_ratio=last['volume_ratio'],
            price_vs_bb=self.price_position_vs_bollinger(
                last['close'], last['bb_upper'], last['bb_lower']
            ),
            trend_direction=self.detect_trend(df)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTORES DE ESTRATEGIAS YOEL (PRIORIDAD - APERTURA)
# ═══════════════════════════════════════════════════════════════════════════════

class YoelStrategyDetector:
    """
    Detectores de estrategias YOEL (Prioridad)
    
    MOMENTO: 9:15-9:45 AM ET
    OBJETIVO: Capturar volatilidad extrema de Bollinger en apertura
    EJECUCIÓN: INMEDIATA (primeros 5-15 minutos)
    """
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
    
    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #1: Cambio de Tendencia al Alza (BB 1H)
    # Dirección: CALL | Timeframe: 1H | Prioridad: ⭐⭐⭐
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_1(self, data_1h: TechnicalData, data_15m: TechnicalData) -> Optional[Signal]:
        """
        Cambio de tendencia al alza en 1H
        
        CONFIRMACIONES:
        1. Precio cruza EMA 20 al alza (close > ema20)
        2. EMA 20 en 15M inclinada al alza (slope > 0)
        3. Vela de confirmación alcista (close > open)
        4. Volumen superior al promedio (volume_ratio > 1.0)
        """
        confirmations = []
        
        # CONF 1: Precio sobre EMA 20
        if data_1h.close > data_1h.ema_20:
            confirmations.append("✅ Precio > EMA 20 (1H)")
        else:
            confirmations.append("❌ Precio < EMA 20 (1H)")
        
        # CONF 2: EMA 20 en 15M con pendiente positiva
        if data_15m.ema_20_slope > 0:
            confirmations.append("✅ EMA 20 alcista en 15M")
        else:
            confirmations.append("❌ EMA 20 no alcista en 15M")
        
        # CONF 3: Vela alcista
        if data_1h.close > data_1h.open:
            confirmations.append("✅ Vela de confirmación alcista")
        else:
            confirmations.append("❌ Vela no alcista")
        
        # CONF 4: Volumen alto
        if data_1h.volume_ratio > 1.0:
            confirmations.append("✅ Volumen > promedio")
        else:
            confirmations.append("❌ Volumen bajo")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_1h.symbol,
                strategy_id=1,
                strategy_name="#1 Cambio Tendencia al Alza (BB 1H)",
                strategy_type=StrategyType.TREND_CHANGE,
                methodology=Methodology.YOEL,
                direction=Direction.CALL,
                strength=SignalStrength.HIGH if confirmations_met == 4 else SignalStrength.MEDIUM,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_1h.close,
                stop_loss=data_1h.ema_20 * 0.99,
                take_profit=data_1h.bb_upper,
                timeframe="1H",
                execution_window="Sesión media (después de 10:00 AM)",
                notes="Setup de cambio de tendencia alcista. Horizonte: 2-5 días"
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #2: Cambio de Tendencia a la Baja (BB 1H)
    # Dirección: PUT | Timeframe: 1H | Prioridad: ⭐⭐⭐
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_2(self, data_1h: TechnicalData, data_15m: TechnicalData) -> Optional[Signal]:
        """Cambio de tendencia a la baja en 1H (espejo de #1)"""
        confirmations = []
        
        if data_1h.close < data_1h.ema_20:
            confirmations.append("✅ Precio < EMA 20 (1H)")
        else:
            confirmations.append("❌ Precio > EMA 20 (1H)")
        
        if data_15m.ema_20_slope < 0:
            confirmations.append("✅ EMA 20 bajista en 15M")
        else:
            confirmations.append("❌ EMA 20 no bajista en 15M")
        
        if data_1h.close < data_1h.open:
            confirmations.append("✅ Vela de confirmación bajista")
        else:
            confirmations.append("❌ Vela no bajista")
        
        if data_1h.volume_ratio > 1.0:
            confirmations.append("✅ Volumen > promedio")
        else:
            confirmations.append("❌ Volumen bajo")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_1h.symbol,
                strategy_id=2,
                strategy_name="#2 Cambio Tendencia a la Baja (BB 1H)",
                strategy_type=StrategyType.TREND_CHANGE,
                methodology=Methodology.YOEL,
                direction=Direction.PUT,
                strength=SignalStrength.HIGH if confirmations_met == 4 else SignalStrength.MEDIUM,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_1h.close,
                stop_loss=data_1h.ema_20 * 1.01,
                take_profit=data_1h.bb_lower,
                timeframe="1H",
                execution_window="Sesión media (después de 10:00 AM)",
                notes="Setup de cambio de tendencia bajista. Horizonte: 2-5 días"
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #5: Exceso Alcista en Apertura (YOEL - INMEDIATA)
    # Dirección: PUT | Timeframe: 15M | Prioridad: ⭐⭐⭐⭐
    # ⚡ EJECUCIÓN: INMEDIATA (primeros 5-15 min de mercado)
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_5(self, data_15m: TechnicalData, prev_close: float, 
                          df_15m: pd.DataFrame) -> Optional[Signal]:
        """
        YOEL #5: Exceso alcista en apertura - Capturar reversión de volatilidad
        
        CONTEXTO REQUERIDO:
        - Tendencia LATERAL previa en 15M (BB horizontal, sin volatilidad)
        
        CONFIRMACIONES:
        1. Tendencia lateral previa en BB 15M
        2. Precio fuera de banda SUPERIOR (sobrecompra extrema)
        3. Volumen clímax (>1.5x promedio) - Indica exceso
        4. Señal de debilitamiento (precio comienza a bajar)
        
        ⚡ ENTRADA: INMEDIATA en primeros 5-15 minutos
        """
        confirmations = []
        
        # CONF 1: Tendencia lateral previa (requisito de contexto)
        is_lateral = self.analyzer.is_lateral_trend(df_15m, periods=10)
        if is_lateral:
            confirmations.append("✅ Tendencia lateral previa (BB horizontal)")
        else:
            confirmations.append("❌ No hay lateralidad previa")
        
        # CONF 2: Precio fuera de banda superior (sobrecompra extrema)
        if data_15m.price_vs_bb == "above":
            confirmations.append("✅ Precio FUERA de banda superior (sobrecompra)")
        else:
            confirmations.append("❌ Precio dentro de bandas")
        
        # CONF 3: Volumen clímax
        if data_15m.volume_ratio > 1.5:
            confirmations.append(f"✅ Volumen clímax ({data_15m.volume_ratio:.1f}x)")
        else:
            confirmations.append(f"❌ Volumen normal ({data_15m.volume_ratio:.1f}x)")
        
        # CONF 4: Señal de debilitamiento (precio empieza a bajar o mecha superior)
        candle_range = data_15m.high - data_15m.low + 0.001
        upper_wick = (data_15m.high - max(data_15m.close, data_15m.open)) / candle_range
        is_weakening = upper_wick > 0.3 or data_15m.close < data_15m.open
        
        if is_weakening:
            confirmations.append("✅ Señal de debilitamiento detectada")
        else:
            confirmations.append("❌ Sin debilitamiento claro")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_15m.symbol,
                strategy_id=5,
                strategy_name="#5 Exceso Alcista en Apertura (YOEL)",
                strategy_type=StrategyType.VOLATILITY_EXCESS,
                methodology=Methodology.YOEL,
                direction=Direction.PUT,
                strength=SignalStrength.HIGH,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_15m.close,
                stop_loss=data_15m.high * 1.005,  # Sobre el máximo
                take_profit=prev_close,  # Objetivo: cierre anterior
                timeframe="15M",
                execution_window="⚡ INMEDIATA (primeros 5-15 min)",
                notes="⚡ YOEL: Ejecutar en primeros 5-15 min. Capturar reversión de volatilidad."
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #6: Exceso Bajista en Apertura (YOEL - INMEDIATA)
    # Dirección: CALL | Timeframe: 15M | Prioridad: ⭐⭐⭐⭐
    # ⚡ EJECUCIÓN: INMEDIATA (primeros 5-15 min de mercado)
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_6(self, data_15m: TechnicalData, prev_close: float,
                          df_15m: pd.DataFrame) -> Optional[Signal]:
        """
        YOEL #6: Exceso bajista en apertura - Capturar rebote de volatilidad
        
        CONTEXTO REQUERIDO:
        - Tendencia LATERAL previa en 15M
        
        CONFIRMACIONES:
        1. Tendencia lateral previa en BB 15M
        2. Precio fuera de banda INFERIOR (sobreventa extrema)
        3. Volumen de capitulación (>1.5x promedio)
        4. Señal de rebote (vela verde O cola inferior larga)
        
        ⚡ ENTRADA: INMEDIATA en primeros 5-15 minutos
        """
        confirmations = []
        
        # CONF 1: Tendencia lateral previa
        is_lateral = self.analyzer.is_lateral_trend(df_15m, periods=10)
        if is_lateral:
            confirmations.append("✅ Tendencia lateral previa (BB horizontal)")
        else:
            confirmations.append("❌ No hay lateralidad previa")
        
        # CONF 2: Precio fuera de banda inferior (sobreventa extrema)
        if data_15m.price_vs_bb == "below":
            confirmations.append("✅ Precio FUERA de banda inferior (sobreventa)")
        else:
            confirmations.append("❌ Precio dentro de bandas")
        
        # CONF 3: Volumen de capitulación
        if data_15m.volume_ratio > 1.5:
            confirmations.append(f"✅ Volumen de capitulación ({data_15m.volume_ratio:.1f}x)")
        else:
            confirmations.append(f"❌ Volumen normal ({data_15m.volume_ratio:.1f}x)")
        
        # CONF 4: Señal de rebote (vela verde O cola inferior larga)
        is_green = data_15m.close > data_15m.open
        body = abs(data_15m.close - data_15m.open) + 0.001
        lower_wick = min(data_15m.open, data_15m.close) - data_15m.low
        has_long_wick = lower_wick > body * 1.5
        
        if is_green or has_long_wick:
            confirmations.append("✅ Señal de rebote (comienza a subir)")
        else:
            confirmations.append("❌ Sin señal de rebote")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_15m.symbol,
                strategy_id=6,
                strategy_name="#6 Exceso Bajista en Apertura (YOEL)",
                strategy_type=StrategyType.VOLATILITY_EXCESS,
                methodology=Methodology.YOEL,
                direction=Direction.CALL,
                strength=SignalStrength.HIGH,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_15m.close,
                stop_loss=data_15m.low * 0.995,  # Bajo el mínimo
                take_profit=prev_close,  # Objetivo: cierre anterior
                timeframe="15M",
                execution_window="⚡ INMEDIATA (primeros 5-15 min)",
                notes="⚡ YOEL: Ejecutar en primeros 5-15 min. Capturar rebote de volatilidad."
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #7: Efecto Imán Alcista
    # Dirección: CALL | Timeframe: 1H | Prioridad: ⭐⭐
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_7(self, data_1h: TechnicalData, data_15m: TechnicalData) -> Optional[Signal]:
        """Efecto Imán alcista - EMA 20 atrae al precio"""
        confirmations = []
        
        # CONF 1: Precio muy por debajo de EMA 20 (>2%)
        distance_pct = ((data_1h.ema_20 - data_1h.close) / data_1h.ema_20) * 100
        if distance_pct > 2.0:
            confirmations.append(f"✅ Precio alejado de EMA 20 ({distance_pct:.2f}%)")
        else:
            confirmations.append(f"❌ Precio cerca de EMA 20 ({distance_pct:.2f}%)")
        
        # CONF 2: Sobreventa en 15M
        if data_15m.price_vs_bb == "below" or data_15m.close < data_15m.bb_lower * 1.01:
            confirmations.append("✅ Sobreventa en 15M")
        else:
            confirmations.append("❌ Sin sobreventa en 15M")
        
        # CONF 3: Vela de giro
        if data_1h.close > data_1h.open:
            confirmations.append("✅ Vela de giro alcista")
        else:
            confirmations.append("❌ Sin vela de giro")
        
        # CONF 4: Volumen
        if data_1h.volume_ratio > 1.0:
            confirmations.append("✅ Volumen confirma")
        else:
            confirmations.append("❌ Volumen bajo")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_1h.symbol,
                strategy_id=7,
                strategy_name="#7 Efecto Imán Alcista (YOEL)",
                strategy_type=StrategyType.MAGNET_EFFECT,
                methodology=Methodology.YOEL,
                direction=Direction.CALL,
                strength=SignalStrength.MEDIUM,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_1h.close,
                stop_loss=data_15m.low * 0.99,
                take_profit=data_1h.ema_20,  # EMA 20 = el imán
                timeframe="1H",
                execution_window="Sesión media",
                notes="Objetivo: EMA 20 actúa como imán. Horizonte: 1-3 días"
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #8: Efecto Imán Bajista
    # Dirección: PUT | Timeframe: 1H | Prioridad: ⭐⭐
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_8(self, data_1h: TechnicalData, data_15m: TechnicalData) -> Optional[Signal]:
        """Efecto Imán bajista - EMA 20 atrae al precio"""
        confirmations = []
        
        distance_pct = ((data_1h.close - data_1h.ema_20) / data_1h.ema_20) * 100
        if distance_pct > 2.0:
            confirmations.append(f"✅ Precio alejado de EMA 20 ({distance_pct:.2f}%)")
        else:
            confirmations.append(f"❌ Precio cerca de EMA 20 ({distance_pct:.2f}%)")
        
        if data_15m.price_vs_bb == "above" or data_15m.close > data_15m.bb_upper * 0.99:
            confirmations.append("✅ Sobrecompra en 15M")
        else:
            confirmations.append("❌ Sin sobrecompra en 15M")
        
        if data_1h.close < data_1h.open:
            confirmations.append("✅ Vela de giro bajista")
        else:
            confirmations.append("❌ Sin vela de giro")
        
        if data_1h.volume_ratio > 1.0:
            confirmations.append("✅ Volumen confirma")
        else:
            confirmations.append("❌ Volumen bajo")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_1h.symbol,
                strategy_id=8,
                strategy_name="#8 Efecto Imán Bajista (YOEL)",
                strategy_type=StrategyType.MAGNET_EFFECT,
                methodology=Methodology.YOEL,
                direction=Direction.PUT,
                strength=SignalStrength.MEDIUM,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_1h.close,
                stop_loss=data_15m.high * 1.01,
                take_profit=data_1h.ema_20,
                timeframe="1H",
                execution_window="Sesión media",
                notes="Objetivo: EMA 20 actúa como imán. Horizonte: 1-3 días"
            )
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTORES CARDONA (PRE-CIERRE - GAPS PARA MAÑANA)
# ═══════════════════════════════════════════════════════════════════════════════

class CardonaStrategyDetector:
    """
    Detectores de estrategias CARDONA
    
    MOMENTO: 3:45 PM ET (15 min antes del cierre)
    OBJETIVO: Detectar GAPs potenciales para la apertura de MAÑANA
    ANÁLISIS: Cierre vs EMAs, proyección de gaps
    """
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
    
    def detect_potential_gap(self, data_daily: TechnicalData, df_daily: pd.DataFrame) -> Optional[Signal]:
        """
        CARDONA: Análisis pre-cierre para detectar GAPs potenciales mañana
        
        INDICADORES DE GAP POTENCIAL:
        1. Cierre muy alejado de EMA 20 (extensión)
        2. Cierre en extremo de Bollinger
        3. Volumen inusualmente alto hoy
        4. Patrón de vela sugiere continuación o reversión
        
        NOTA: Esta señal es para PREPARACIÓN, no ejecución inmediata
        """
        confirmations = []
        direction = Direction.NEUTRAL
        
        # ANÁLISIS 1: Cierre vs EMA 20
        distance_ema20 = ((data_daily.close - data_daily.ema_20) / data_daily.ema_20) * 100
        
        if abs(distance_ema20) > 3.0:
            if distance_ema20 > 0:
                confirmations.append(f"✅ Cierre muy sobre EMA 20 (+{distance_ema20:.2f}%) - Potencial GAP bajista mañana")
                direction = Direction.PUT  # Prepararse para PUT mañana
            else:
                confirmations.append(f"✅ Cierre muy bajo EMA 20 ({distance_ema20:.2f}%) - Potencial GAP alcista mañana")
                direction = Direction.CALL  # Prepararse para CALL mañana
        else:
            confirmations.append(f"❌ Cierre cerca de EMA 20 ({distance_ema20:.2f}%)")
        
        # ANÁLISIS 2: Posición en Bollinger
        if data_daily.price_vs_bb == "above":
            confirmations.append("✅ Cierre sobre banda superior - Sobrecompra")
            direction = Direction.PUT
        elif data_daily.price_vs_bb == "below":
            confirmations.append("✅ Cierre bajo banda inferior - Sobreventa")
            direction = Direction.CALL
        else:
            confirmations.append("❌ Cierre dentro de bandas")
        
        # ANÁLISIS 3: Volumen del día
        if data_daily.volume_ratio > 1.5:
            confirmations.append(f"✅ Volumen alto hoy ({data_daily.volume_ratio:.1f}x) - Movimiento significativo")
        else:
            confirmations.append(f"❌ Volumen normal ({data_daily.volume_ratio:.1f}x)")
        
        # ANÁLISIS 4: Tendencia general
        if data_daily.trend_direction == "bullish":
            confirmations.append("✅ Tendencia alcista - Posibles GAPs al alza")
        elif data_daily.trend_direction == "bearish":
            confirmations.append("✅ Tendencia bajista - Posibles GAPs a la baja")
        else:
            confirmations.append("❌ Tendencia lateral - GAPs menos probables")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= 2 and direction != Direction.NEUTRAL:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_daily.symbol,
                strategy_id=100,  # ID especial para análisis Cardona
                strategy_name="CARDONA: Análisis Pre-Cierre (GAP mañana)",
                strategy_type=StrategyType.VOLATILITY_EXCESS,
                methodology=Methodology.CARDONA,
                direction=direction,
                strength=SignalStrength.MEDIUM,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=None,  # No hay entrada hoy
                stop_loss=None,
                take_profit=None,
                timeframe="Daily",
                execution_window="🔮 MAÑANA 9:30 AM (si se confirma GAP)",
                notes=f"📋 PREPARACIÓN: Monitorear {data_daily.symbol} en pre-apertura mañana. Aplicar estrategia #5 o #6 si se confirma GAP."
            )
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTORES DE ESTRATEGIAS DAILY (HÍBRIDAS)
# ═══════════════════════════════════════════════════════════════════════════════

class DailyStrategyDetector:
    """Detectores de estrategias en timeframe Daily"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
    
    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #11: Bollinger Squeeze Alcista (Daily)
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_11(self, data_daily: TechnicalData, data_15m: TechnicalData) -> Optional[Signal]:
        """Cambio de tendencia lateral BB Diario al alza"""
        confirmations = []
        
        if data_daily.bb_width < 5.0:
            confirmations.append(f"✅ Bollinger comprimido (width: {data_daily.bb_width:.2f}%)")
        else:
            confirmations.append(f"❌ Bollinger expandido (width: {data_daily.bb_width:.2f}%)")
        
        mid_to_upper = data_daily.close > data_daily.bb_middle and data_daily.close < data_daily.bb_upper
        if mid_to_upper:
            confirmations.append("✅ Precio entre punto medio y banda superior")
        else:
            confirmations.append("❌ Precio fuera de zona óptima")
        
        if data_daily.ema_20_slope > 0:
            confirmations.append("✅ EMA 20 virando al alza")
        else:
            confirmations.append("❌ EMA 20 no alcista")
        
        if data_15m.bb_width > 3.0:
            confirmations.append("✅ Alta volatilidad en 15M")
        else:
            confirmations.append("❌ Baja volatilidad en 15M")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_daily.symbol,
                strategy_id=11,
                strategy_name="#11 Bollinger Squeeze Alcista",
                strategy_type=StrategyType.BOLLINGER_SQUEEZE,
                methodology=Methodology.HYBRID,
                direction=Direction.CALL,
                strength=SignalStrength.HIGH,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_daily.close,
                stop_loss=data_daily.bb_lower,
                take_profit=data_daily.bb_upper * 1.02,
                timeframe="Daily",
                execution_window="Siguiente sesión",
                notes="Squeeze de Bollinger - Potencial de movimiento fuerte. Horizonte: 5-10 días"
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #13: Cambio de Tendencia Definitiva - Bloque MM
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_13(self, data_daily: TechnicalData) -> Optional[Signal]:
        """Cambio de tendencia definitiva cuando EMAs se ordenan completamente"""
        confirmations = []
        direction = Direction.NEUTRAL
        
        bullish_order = (data_daily.ema_20 > data_daily.ema_40 > data_daily.ema_100)
        bearish_order = (data_daily.ema_20 < data_daily.ema_40 < data_daily.ema_100)
        
        if bullish_order:
            direction = Direction.CALL
            confirmations.append("✅ EMAs en orden alcista (20 > 40 > 100)")
        elif bearish_order:
            direction = Direction.PUT
            confirmations.append("✅ EMAs en orden bajista (20 < 40 < 100)")
        else:
            confirmations.append("❌ EMAs no ordenadas")
        
        if direction == Direction.CALL:
            if data_daily.ema_40 > data_daily.ema_200:
                confirmations.append("✅ EMA 40 sobre EMA 200")
            else:
                confirmations.append("❌ EMA 40 bajo EMA 200")
        elif direction == Direction.PUT:
            if data_daily.ema_40 < data_daily.ema_200:
                confirmations.append("✅ EMA 40 bajo EMA 200")
            else:
                confirmations.append("❌ EMA 40 sobre EMA 200")
        
        if direction == Direction.CALL and data_daily.close > data_daily.ema_200:
            confirmations.append("✅ Precio sobre EMA 200")
        elif direction == Direction.PUT and data_daily.close < data_daily.ema_200:
            confirmations.append("✅ Precio bajo EMA 200")
        else:
            confirmations.append("❌ Precio no confirma")
        
        if data_daily.volume_ratio > 1.0:
            confirmations.append("✅ Volumen alto")
        else:
            confirmations.append("❌ Volumen bajo")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS and direction != Direction.NEUTRAL:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_daily.symbol,
                strategy_id=13,
                strategy_name="#13 Bloque MM (Tendencia Definitiva)",
                strategy_type=StrategyType.CHANNEL_BREAKOUT,
                methodology=Methodology.HYBRID,
                direction=direction,
                strength=SignalStrength.STRONG,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_daily.close,
                stop_loss=data_daily.ema_200 * (0.98 if direction == Direction.CALL else 1.02),
                take_profit=None,
                timeframe="Daily",
                execution_window="Swing (5-15 días)",
                notes="⭐⭐⭐⭐⭐ SETUP PREMIUM - Usar trailing stop"
            )
        
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # ESTRATEGIA #14: Canal Lateral - Breakout
    # ─────────────────────────────────────────────────────────────────────────
    def detect_strategy_14(self, data_daily: TechnicalData, df_daily: pd.DataFrame) -> Optional[Signal]:
        """Breakout de canal lateral prolongado"""
        if len(df_daily) < 15:
            return None
        
        confirmations = []
        direction = Direction.NEUTRAL
        
        ema_spread = abs(data_daily.ema_20 - data_daily.ema_200) / data_daily.ema_200 * 100
        if ema_spread < 3.0:
            confirmations.append(f"✅ EMAs entrelazadas (spread: {ema_spread:.2f}%)")
        else:
            confirmations.append(f"❌ EMAs separadas (spread: {ema_spread:.2f}%)")
        
        if data_daily.bb_width > 4.0:
            confirmations.append(f"✅ Volatilidad expandiendo (BB: {data_daily.bb_width:.2f}%)")
        else:
            confirmations.append("❌ Volatilidad baja")
        
        if data_daily.close > data_daily.bb_upper:
            direction = Direction.CALL
            confirmations.append("✅ Breakout alcista")
        elif data_daily.close < data_daily.bb_lower:
            direction = Direction.PUT
            confirmations.append("✅ Breakout bajista")
        else:
            confirmations.append("❌ Sin breakout")
        
        if data_daily.volume_ratio > 2.0:
            confirmations.append(f"✅ Volumen explosivo ({data_daily.volume_ratio:.1f}x)")
        else:
            confirmations.append(f"❌ Volumen insuficiente")
        
        confirmations_met = sum(1 for c in confirmations if c.startswith("✅"))
        
        if confirmations_met >= Config.MIN_CONFIRMATIONS and direction != Direction.NEUTRAL:
            return Signal(
                timestamp=datetime.now(),
                symbol=data_daily.symbol,
                strategy_id=14,
                strategy_name="#14 Canal Lateral - Breakout",
                strategy_type=StrategyType.CHANNEL_BREAKOUT,
                methodology=Methodology.HYBRID,
                direction=direction,
                strength=SignalStrength.STRONG,
                confirmations=confirmations,
                confirmations_met=confirmations_met,
                confirmations_total=4,
                entry_price=data_daily.close,
                stop_loss=data_daily.bb_middle,
                take_profit=None,
                timeframe="Daily",
                execution_window="Swing (2-5 días)",
                notes="⭐⭐⭐⭐⭐ POTENCIAL 100-3000% - Usar trailing stop"
            )
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MOTOR PRINCIPAL DEL BOT
# ═══════════════════════════════════════════════════════════════════════════════

class YOSTradingBot:
    """Motor principal del bot de trading YOS v1.1"""
    
    def __init__(self, api_key: str):
        self.data_provider = MarketDataProvider(api_key)
        self.analyzer = TechnicalAnalyzer()
        self.yoel_detector = YoelStrategyDetector()
        self.cardona_detector = CardonaStrategyDetector()
        self.daily_detector = DailyStrategyDetector()
        self.signals: List[Signal] = []
    
    def scan_instrument(self, symbol: str, moment: OperationalMoment) -> List[Signal]:
        """
        Escanea un instrumento según el momento operativo
        
        Args:
            symbol: Símbolo a analizar
            moment: Momento operativo (YOEL_OPEN, CARDONA_PRE_CLOSE, etc.)
        
        Returns:
            Lista de señales encontradas
        """
        signals = []
        
        print(f"  🔍 {symbol}...", end=" ")
        
        # Obtener datos
        df_15m = self.data_provider.get_intraday_data(symbol, "15min")
        df_60m = self.data_provider.get_intraday_data(symbol, "60min")
        df_daily = self.data_provider.get_daily_data(symbol)
        
        if df_15m.empty or df_60m.empty or df_daily.empty:
            print("⚠️ Datos insuficientes")
            return signals
        
        # Calcular indicadores
        data_15m = self.analyzer.analyze(df_15m, symbol, "15M")
        data_1h = self.analyzer.analyze(df_60m, symbol, "1H")
        data_daily = self.analyzer.analyze(df_daily, symbol, "Daily")
        
        if not all([data_15m, data_1h, data_daily]):
            print("⚠️ Análisis incompleto")
            return signals
        
        # Cierre del día anterior
        prev_close = df_daily.iloc[-2]['close'] if len(df_daily) > 1 else data_daily.close
        
        # ═══════════════════════════════════════════════════════════════════
        # DETECTAR SEGÚN MOMENTO OPERATIVO
        # ═══════════════════════════════════════════════════════════════════
        
        if moment in [OperationalMoment.YOEL_PRE_OPEN, OperationalMoment.YOEL_OPEN]:
            # ─────────────────────────────────────────────────────────────────
            # YOEL (9:15-9:45 AM) - Estrategias de volatilidad en apertura
            # ─────────────────────────────────────────────────────────────────
            
            # Calcular BB con datos suficientes para is_lateral_trend
            df_15m_bb = self.analyzer.calculate_bollinger_bands(df_15m)
            
            # Estrategia #5: Exceso alcista (PUT inmediato)
            signal = self.yoel_detector.detect_strategy_5(data_15m, prev_close, df_15m_bb)
            if signal:
                signals.append(signal)
            
            # Estrategia #6: Exceso bajista (CALL inmediato)
            signal = self.yoel_detector.detect_strategy_6(data_15m, prev_close, df_15m_bb)
            if signal:
                signals.append(signal)
        
        if moment == OperationalMoment.MID_SESSION:
            # ─────────────────────────────────────────────────────────────────
            # SESIÓN MEDIA (10:00 AM - 3:30 PM) - Estrategias de tendencia
            # ─────────────────────────────────────────────────────────────────
            
            # Estrategias #1, #2: Cambio de tendencia
            signal = self.yoel_detector.detect_strategy_1(data_1h, data_15m)
            if signal:
                signals.append(signal)
            
            signal = self.yoel_detector.detect_strategy_2(data_1h, data_15m)
            if signal:
                signals.append(signal)
            
            # Estrategias #7, #8: Efecto Imán
            signal = self.yoel_detector.detect_strategy_7(data_1h, data_15m)
            if signal:
                signals.append(signal)
            
            signal = self.yoel_detector.detect_strategy_8(data_1h, data_15m)
            if signal:
                signals.append(signal)
            
            # Estrategias Daily (#11, #13, #14)
            signal = self.daily_detector.detect_strategy_11(data_daily, data_15m)
            if signal:
                signals.append(signal)
            
            signal = self.daily_detector.detect_strategy_13(data_daily)
            if signal:
                signals.append(signal)
            
            signal = self.daily_detector.detect_strategy_14(data_daily, df_daily)
            if signal:
                signals.append(signal)
        
        if moment == OperationalMoment.CARDONA_PRE_CLOSE:
            # ─────────────────────────────────────────────────────────────────
            # CARDONA (3:45 PM) - Análisis para GAPs de mañana
            # ─────────────────────────────────────────────────────────────────
            
            signal = self.cardona_detector.detect_potential_gap(data_daily, df_daily)
            if signal:
                signals.append(signal)
        
        found = len(signals)
        print(f"{'✅ ' + str(found) + ' señal(es)' if found > 0 else '○ Sin señales'}")
        
        return signals
    
    def run_scan(self, moment: str = "yoel_open") -> List[Signal]:
        """
        Ejecuta escaneo completo de todos los instrumentos
        
        Args:
            moment: "yoel_pre_open", "yoel_open", "mid_session", "cardona_close"
        
        Returns:
            Lista de todas las señales encontradas
        """
        # Mapear string a enum
        moment_map = {
            "yoel_pre_open": OperationalMoment.YOEL_PRE_OPEN,
            "yoel_open": OperationalMoment.YOEL_OPEN,
            "mid_session": OperationalMoment.MID_SESSION,
            "cardona_close": OperationalMoment.CARDONA_PRE_CLOSE,
        }
        
        op_moment = moment_map.get(moment, OperationalMoment.YOEL_OPEN)
        
        all_signals = []
        
        # Header del reporte
        moment_info = {
            OperationalMoment.YOEL_PRE_OPEN: ("🌅 YOEL PRE-APERTURA", "9:15 AM ET"),
            OperationalMoment.YOEL_OPEN: ("⚡ YOEL APERTURA", "9:30-9:45 AM ET"),
            OperationalMoment.MID_SESSION: ("📊 SESIÓN MEDIA", "10:00 AM - 3:30 PM ET"),
            OperationalMoment.CARDONA_PRE_CLOSE: ("🔮 CARDONA PRE-CIERRE", "3:45 PM ET"),
        }
        
        title, timing = moment_info.get(op_moment, ("ESCANEO", ""))
        
        print(f"\n{'═' * 60}")
        print(f"  🤖 YOS TRADING BOT v1.1")
        print(f"  {title} ({timing})")
        print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'═' * 60}")
        print(f"\n  📋 Instrumentos: {', '.join(Config.INSTRUMENTS)}\n")
        
        # Limpiar cache para datos frescos
        self.data_provider.clear_cache()
        
        for symbol in Config.INSTRUMENTS:
            signals = self.scan_instrument(symbol, op_moment)
            all_signals.extend(signals)
        
        # Ordenar por prioridad
        all_signals.sort(key=lambda s: (s.methodology == Methodology.YOEL, s.strength.value), reverse=True)
        
        self.signals = all_signals
        return all_signals
    
    def generate_report(self) -> str:
        """Genera reporte de señales encontradas"""
        if not self.signals:
            return "\n📭 No se encontraron señales que cumplan los criterios.\n"
        
        report = []
        report.append(f"\n{'═' * 60}")
        report.append(f"  📊 REPORTE DE SEÑALES")
        report.append(f"  Total: {len(self.signals)} señales detectadas")
        report.append(f"{'═' * 60}\n")
        
        for i, signal in enumerate(self.signals, 1):
            stars = "⭐" * signal.strength.value
            direction_emoji = "📈" if signal.direction == Direction.CALL else "📉"
            method_emoji = "⚡" if signal.methodology == Methodology.YOEL else "🔮"
            
            report.append(f"{'─' * 50}")
            report.append(f"{method_emoji} SEÑAL #{i}: {signal.symbol} [{signal.methodology.value}]")
            report.append(f"{'─' * 50}")
            report.append(f"{direction_emoji} Estrategia: {signal.strategy_name}")
            report.append(f"🎯 Dirección: {signal.direction.value}")
            report.append(f"⏱️  Timeframe: {signal.timeframe}")
            report.append(f"⭐ Calidad: {stars} ({signal.quality_score():.0f}%)")
            report.append(f"")
            report.append(f"CONFIRMACIONES ({signal.confirmations_met}/{signal.confirmations_total}):")
            for conf in signal.confirmations:
                report.append(f"  {conf}")
            report.append(f"")
            
            if signal.entry_price:
                report.append(f"💰 Entrada: ${signal.entry_price:.2f}")
            if signal.stop_loss:
                report.append(f"🛑 Stop Loss: ${signal.stop_loss:.2f}")
            if signal.take_profit:
                report.append(f"🎯 Take Profit: ${signal.take_profit:.2f}")
            
            report.append(f"📊 Posición: {signal.suggested_position_size()*100:.0f}% del capital")
            report.append(f"⏰ Ejecución: {signal.execution_window}")
            
            if signal.notes:
                report.append(f"")
                report.append(f"📝 {signal.notes}")
            
            report.append(f"")
        
        return "\n".join(report)
    
    def get_signals_json(self) -> List[Dict]:
        """Retorna señales en formato JSON para integración"""
        return [
            {
                "timestamp": signal.timestamp.isoformat(),
                "symbol": signal.symbol,
                "strategy_id": signal.strategy_id,
                "strategy_name": signal.strategy_name,
                "methodology": signal.methodology.value,
                "direction": signal.direction.value,
                "strength": signal.strength.value,
                "quality_score": signal.quality_score(),
                "confirmations_met": signal.confirmations_met,
                "confirmations_total": signal.confirmations_total,
                "confirmations": signal.confirmations,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "position_size": signal.suggested_position_size(),
                "execution_window": signal.execution_window,
                "notes": signal.notes
            }
            for signal in self.signals
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║    🤖 YOS TRADING BOT v1.1 (CORREGIDO)                               ║
    ║                                                                       ║
    ║    ┌─────────────────────────────────────────────────────────────┐   ║
    ║    │  YOEL (PRIORIDAD) - 9:15-9:45 AM ET                        │   ║
    ║    │  ├── Capturar volatilidad BB en apertura                   │   ║
    ║    │  └── Entrada: INMEDIATA (primeros 5-15 min)                │   ║
    ║    ├─────────────────────────────────────────────────────────────┤   ║
    ║    │  CARDONA - 3:45 PM ET                                      │   ║
    ║    │  ├── Detectar GAPs potenciales para MAÑANA                 │   ║
    ║    │  └── Análisis: Cierre vs EMAs, proyección                  │   ║
    ║    └─────────────────────────────────────────────────────────────┘   ║
    ║                                                                       ║
    ║    Instrumentos: SPY, QQQ, NVDA, AMD, AAPL, PLTR, GOOGL              ║
    ║                                                                       ║
    ║    ⚠️  PROCESO > RESULTADOS  |  MENOS es MÁS                         ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar bot
    bot = YOSTradingBot(Config.ALPHA_VANTAGE_API_KEY)
    
    # Ejecutar escaneo según momento del día
    print("\n📌 Selecciona momento operativo:")
    print("   1. yoel_open     - Apertura (9:30-9:45 AM) - Estrategias #5, #6")
    print("   2. mid_session   - Sesión media - Estrategias #1, #2, #7, #8, #11-#14")
    print("   3. cardona_close - Pre-cierre (3:45 PM) - Análisis GAPs mañana")
    print("")
    
    # Por defecto, ejecutar escaneo de apertura
    signals = bot.run_scan("yoel_open")
    
    # Generar y mostrar reporte
    report = bot.generate_report()
    print(report)
    
    # Exportar JSON
    signals_json = bot.get_signals_json()
    if signals_json:
        print("\n📤 Señales en JSON:")
        print(json.dumps(signals_json, indent=2, default=str))
    
    return signals


if __name__ == "__main__":
    main()
