"""
Scanner Universal — Analiza el universo de activos y genera señales
"""

import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from universe_engine import UniverseEngine
from engine import SignalEngine
from risk_engine import RiskEngine
from indicators import calculate_atr, calculate_adx, calculate_ker, calculate_ema

class Scanner:
    def __init__(self, config: dict):
        if not config:
            raise ValueError("Configuración vacía o inválida")
        self.config = config
        self.universe = UniverseEngine(config)
        self.signal_engine = SignalEngine(config)
        self.risk_engine = RiskEngine(config)
        self.results = []

    def scan(self) -> List[Dict]:
        """Escanea todos los activos del universo y retorna señales válidas"""
        assets = self.universe.get_universe()
        print(f"Analizando {len(assets)} activos...")

        signals = []
        for asset in assets:
            try:
                # Obtener datos OHLCV (reutilizando lógica de Fast and Trash)
                df = self._fetch_ohlcv(asset, limit=200)
                if df is None or df.empty:
                    continue

                # Calcular indicadores
                indicators = self._compute_indicators(df)

                # Evaluar señal
                signal = self.signal_engine.evaluate(asset, df, indicators)
                if signal is None:
                    continue

                # Aplicar riesgo
                risk = self.risk_engine.calculate(asset, indicators, signal)

                # Combinar y validar
                full_signal = self._build_signal(asset, signal, risk)
                if full_signal:
                    signals.append(full_signal)
            except Exception as e:
                print(f"Error analizando {asset}: {e}")

        # Ordenar por score descendente
        signals.sort(key=lambda x: x['score'], reverse=True)
        self.results = signals
        return signals

    def _fetch_ohlcv(self, asset: str, limit: int = 200):
        """Reutiliza la descarga de velas de Fast and Trash (ccxt)"""
        import ccxt
        exchange = ccxt.binance({'enableRateLimit': True})
        try:
            ohlcv = exchange.fetch_ohlcv(asset, '15m', limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching {asset}: {e}")
            return None

    def _compute_indicators(self, df: pd.DataFrame) -> dict:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        volume = df['volume'].values

        # Validar datos suficientes
        if len(close) < 50:
            return {}

        return {
            'adx': calculate_adx(high, low, close, 14),
            'ker': calculate_ker(close, 10),
            'atr': calculate_atr(high, low, close, 14),
            'rsi': 50,  # placeholder
            'ema_fast': calculate_ema(close, 20),
            'ema_slow': calculate_ema(close, 50),
            'momentum': (close[-1] / close[-6] - 1) * 100 if len(close) > 5 else 0,
            'volume': np.mean(volume[-20:]) if len(volume) >= 20 else 0,
            'avg_volume': np.mean(volume[-50:]) if len(volume) >= 50 else 1,
            'current_price': close[-1],
            'high': high[-1],
            'low': low[-1],
        }

    def _build_signal(self, asset: str, signal: dict, risk: dict) -> Optional[dict]:
        if signal['direction'] == 'NEUTRAL':
            return None
        return {
            'asset': asset,
            'direction': signal['direction'],
            'score': signal['score'],
            'reasons': signal['reasons'],
            'entry': signal['entry'],
            'sl': risk['sl'],
            'tp': risk['tp'],
            'rr': risk['rr'],
            'trailing_activation': risk['trailing_activation'],
            'trailing_distance': risk['trailing_distance']
        }
