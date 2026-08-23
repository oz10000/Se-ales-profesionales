"""
Scanner Universal — Analiza el universo de activos y genera ranking completo
"""

import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

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
        self.last_scan_time = None
        self.scan_interval = 300  # 5 minutos

    def scan_all(self) -> List[Dict]:
        """
        Escanea todos los activos y retorna ranking completo con todos los detalles.
        Incluye activos que no alcanzan el umbral (score bajo).
        """
        assets = self.universe.get_universe()
        print(f"Analizando {len(assets)} activos...")
        self.last_scan_time = time.time()

        all_signals = []
        for asset in assets:
            try:
                df = self._fetch_ohlcv(asset, limit=200)
                if df is None or df.empty:
                    continue

                indicators = self._compute_indicators(df)
                signal = self.signal_engine.evaluate(asset, df, indicators)
                if signal is None:
                    # Aun así, creamos un registro con score 0 y dirección NEUTRAL
                    signal = {
                        'direction': 'NEUTRAL',
                        'score': 0,
                        'reasons': ['Sin condiciones claras'],
                        'entry': indicators.get('current_price', 0),
                        'atr': indicators.get('atr', 0.01)
                    }

                # Aplicar riesgo (siempre, aunque sea NEUTRAL)
                risk = self.risk_engine.calculate(asset, indicators, signal)

                # Estimar tiempo hasta entrada
                time_to_entry = self._estimate_time_to_entry(asset, signal['entry'], indicators)

                full_signal = {
                    'asset': asset,
                    'direction': signal['direction'],
                    'score': signal['score'],
                    'reasons': signal['reasons'],
                    'entry': signal['entry'],
                    'sl': risk['sl'],
                    'tp': risk['tp'],
                    'rr': risk['rr'],
                    'trailing_activation': risk['trailing_activation'],
                    'trailing_distance': risk['trailing_distance'],
                    'time_to_entry': time_to_entry,
                    'atr': indicators.get('atr', 0),
                    'current_price': indicators.get('current_price', 0)
                }
                all_signals.append(full_signal)

            except Exception as e:
                print(f"Error analizando {asset}: {e}")

        # Ordenar por score descendente (absoluto)
        all_signals.sort(key=lambda x: abs(x['score']), reverse=True)
        self.results = all_signals
        return all_signals

    def get_top_long(self) -> Optional[Dict]:
        """Retorna el mejor LONG (score > 0 y más alto)"""
        longs = [s for s in self.results if s['direction'] == 'LONG']
        return longs[0] if longs else None

    def get_top_short(self) -> Optional[Dict]:
        """Retorna el mejor SHORT (score > 0 y más alto)"""
        shorts = [s for s in self.results if s['direction'] == 'SHORT']
        return shorts[0] if shorts else None

    def get_all_ranked(self) -> List[Dict]:
        """Retorna todos los activos rankeados"""
        return self.results

    def _estimate_time_to_entry(self, asset: str, entry: float, indicators: dict) -> str:
        """Estima el tiempo hasta que el precio alcance el nivel de entrada"""
        current_price = indicators.get('current_price', 0)
        atr = indicators.get('atr', 0.01)
        if current_price == 0 or entry == 0:
            return "N/A"
        distance = abs(entry - current_price)
        if distance < 0.001 * current_price:
            return "Inmediato (dentro de 1-2 velas)"
        # Velocidad estimada: 2 ATR por hora (promedio)
        speed_per_hour = atr * 2
        if speed_per_hour == 0:
            return "Indeterminado"
        hours = distance / speed_per_hour
        if hours < 0.5:
            return f"{int(hours*60)} minutos"
        elif hours < 24:
            return f"{hours:.1f} horas"
        else:
            return f"{hours/24:.1f} días"

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

        if len(close) < 50:
            return {}

        return {
            'adx': calculate_adx(high, low, close, 14),
            'ker': calculate_ker(close, 10),
            'atr': calculate_atr(high, low, close, 14),
            'rsi': 50,
            'ema_fast': calculate_ema(close, 20),
            'ema_slow': calculate_ema(close, 50),
            'momentum': (close[-1] / close[-6] - 1) * 100 if len(close) > 5 else 0,
            'volume': np.mean(volume[-20:]) if len(volume) >= 20 else 0,
            'avg_volume': np.mean(volume[-50:]) if len(volume) >= 50 else 1,
            'current_price': close[-1],
            'high': high[-1],
            'low': low[-1],
        }

    def time_since_last_scan(self) -> str:
        if self.last_scan_time is None:
            return "Nunca"
        elapsed = int(time.time() - self.last_scan_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes}m {seconds}s"

    def next_scan_in(self) -> str:
        if self.last_scan_time is None:
            return "5m 0s"
        elapsed = int(time.time() - self.last_scan_time)
        remaining = max(0, self.scan_interval - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes}m {seconds}s"
