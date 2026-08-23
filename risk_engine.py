"""
Gestión de riesgo: SL/TP fijo y Trailing Stop optimizado
"""

import numpy as np

class RiskEngine:
    def __init__(self, config: dict):
        self.config = config
        self.sl_multiplier = config['risk']['sl_multiplier']
        self.tp_multiplier = config['risk']['tp_multiplier']
        self.trailing_activation = config['risk']['trailing_activation']
        self.trailing_distance = config['risk']['trailing_distance']
        self.max_leverage = config['risk']['max_leverage']
        self.default_rr = config['risk']['default_rr']

    def calculate(self, asset: str, indicators: dict, signal: dict) -> dict:
        """Calcula SL, TP, R:R y parámetros de trailing"""
        entry = signal['entry']
        atr = indicators['atr']
        direction = signal['direction']

        if direction == 'LONG':
            sl = entry - atr * self.sl_multiplier
            tp = entry + atr * self.tp_multiplier
        elif direction == 'SHORT':
            sl = entry + atr * self.sl_multiplier
            tp = entry - atr * self.tp_multiplier
        else:
            sl = entry * 0.98
            tp = entry * 1.02

        # R:R
        if direction == 'LONG':
            rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
        else:
            rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else 0

        # Trailing stop
        if direction == 'LONG':
            trailing_activation_price = entry + (tp - entry) * self.trailing_activation
            trailing_distance_price = atr * self.trailing_distance
        else:
            trailing_activation_price = entry - (entry - tp) * self.trailing_activation
            trailing_distance_price = atr * self.trailing_distance

        return {
            'sl': sl,
            'tp': tp,
            'rr': rr,
            'trailing_activation': trailing_activation_price,
            'trailing_distance': trailing_distance_price,
            'leverage_recommended': min(self.max_leverage, 1.0 / (atr / entry * 3))
        }
