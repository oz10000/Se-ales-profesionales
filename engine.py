"""
Motor de señales — Evalúa condiciones de entrada LONG/SHORT
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional

class SignalEngine:
    def __init__(self, config: dict):
        self.config = config
        self.threshold_strong = config['scoring']['thresholds']['strong']
        self.threshold_good = config['scoring']['thresholds']['good']
        self.threshold_weak = config['scoring']['thresholds']['weak']

    def evaluate(self, asset: str, df: pd.DataFrame, indicators: dict) -> Optional[dict]:
        """
        Retorna señal si hay condiciones de entrada.
        score: 0-100
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        current_price = close[-1]
        atr = indicators['atr']
        adx = indicators['adx']
        ker = indicators['ker']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        momentum = indicators['momentum']

        # Detección de soporte/resistencia simple (últimos 20 máximos/mínimos)
        resistance = max(high[-20:])
        support = min(low[-20:])

        # Volumen relativo
        volume_ratio = indicators['volume'] / indicators['avg_volume'] if indicators['avg_volume'] > 0 else 1.0

        # Score base
        score = 0.0
        reasons = []
        direction = 'NEUTRAL'
        entry = current_price

        # ---- Evaluación LONG ----
        long_score = 0.0
        # Tendencia alcista
        if ema_fast > ema_slow:
            long_score += 20
            reasons.append("EMA fast > slow (tendencia alcista)")
        # ADX > 25 (tendencia fuerte)
        if adx > 25:
            long_score += 15
            reasons.append(f"ADX fuerte ({adx:.1f})")
        # KER > 0.4 (tendencia eficiente)
        if ker > 0.4:
            long_score += 15
            reasons.append(f"KER eficiente ({ker:.2f})")
        # Retroceso a soporte (precio cerca de soporte)
        distance_to_support = (current_price - support) / current_price
        if distance_to_support < 0.02 and current_price > support:
            long_score += 20
            reasons.append("Retroceso a soporte")
        # Volumen de confirmación
        if volume_ratio > 1.5:
            long_score += 15
            reasons.append(f"Volumen +{volume_ratio:.1f}x promedio")
        # Momentum positivo
        if momentum > 0.5:
            long_score += 10
            reasons.append("Momentum positivo")
        # Rechazo en vela (sombra inferior larga)
        last_candle = df.iloc[-1]
        body = abs(last_candle['close'] - last_candle['open'])
        lower_shadow = min(last_candle['open'], last_candle['close']) - last_candle['low']
        if lower_shadow > body * 0.5:
            long_score += 5
            reasons.append("Rechazo (sombra inferior)")

        # ---- Evaluación SHORT ----
        short_score = 0.0
        short_reasons = []
        if ema_fast < ema_slow:
            short_score += 20
            short_reasons.append("EMA fast < slow (tendencia bajista)")
        if adx > 25:
            short_score += 15
            short_reasons.append(f"ADX fuerte ({adx:.1f})")
        if ker > 0.4:
            short_score += 15
            short_reasons.append(f"KER eficiente ({ker:.2f})")
        # Retroceso a resistencia
        distance_to_resistance = (resistance - current_price) / current_price
        if distance_to_resistance < 0.02 and current_price < resistance:
            short_score += 20
            short_reasons.append("Retroceso a resistencia")
        if volume_ratio > 1.5:
            short_score += 15
            short_reasons.append(f"Volumen +{volume_ratio:.1f}x promedio")
        if momentum < -0.5:
            short_score += 10
            short_reasons.append("Momentum negativo")
        # Rechazo en vela (sombra superior larga)
        upper_shadow = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        if upper_shadow > body * 0.5:
            short_score += 5
            short_reasons.append("Rechazo (sombra superior)")

        # Decidir dirección
        if long_score > short_score and long_score >= self.threshold_weak * 100:
            direction = 'LONG'
            score = long_score
            reasons = reasons[:5]
            entry = support + atr * 0.2  # entrada ligeramente por encima del soporte
        elif short_score > long_score and short_score >= self.threshold_weak * 100:
            direction = 'SHORT'
            score = short_score
            reasons = short_reasons[:5]
            entry = resistance - atr * 0.2  # entrada ligeramente por debajo de la resistencia
        else:
            return None

        # Limitar score a 100
        score = min(100, score)

        return {
            'direction': direction,
            'score': score,
            'reasons': reasons,
            'entry': entry,
            'atr': atr,
        }
