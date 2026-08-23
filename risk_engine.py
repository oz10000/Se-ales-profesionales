"""
Gestión de riesgo: SL/TP fijo y Trailing Stop optimizado
"""

import numpy as np

class RiskEngine:
    def __init__(self, config: dict):
        self.config = config
        risk_cfg = config.get('risk', {})
        self.sl_multiplier = risk_cfg.get('sl_multiplier', 1.0)
        self.tp_multiplier = risk_cfg.get('tp_multiplier', 2.5)
        self.trailing_activation = risk_cfg.get('trailing_activation', 0.5)
        self.trailing_distance = risk_cfg.get('trailing_distance', 1.0)
        self.max_leverage = risk_cfg.get('max_leverage', 1.5)
        self.default_rr = risk_cfg.get('default_rr', 2.5)

    def calculate(self, asset: str, indicators: dict, signal: dict) -> dict:
        entry = signal['entry']
        atr = indicators.get('atr', 0.01)
        direction = signal['direction']

        if atr <= 0:
            atr = entry * 0.01

        if direction == 'LONG':
            sl = entry - atr * self.sl_multiplier
            tp = entry + atr * self.tp_multiplier
        elif direction == 'SHORT':
            sl = entry + atr * self.sl_multiplier
            tp = entry - atr * self.tp_multiplier
        else:
            sl = entry * 0.98
            tp = entry * 1.02

        if direction == 'LONG':
            rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else self.default_rr
        else:
            rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else self.default_rr

        # Trailing stop
        if direction == 'LONG':
            trailing_activation = entry + (tp - entry) * self.trailing_activation
            trailing_distance = atr * self.trailing_distance
        else:
            trailing_activation = entry - (entry - tp) * self.trailing_activation
            trailing_distance = atr * self.trailing_distance

        return {
            'sl': sl,
            'tp': tp,
            'rr': rr,
            'trailing_activation': trailing_activation,
            'trailing_distance': trailing_distance,
            'leverage_recommended': min(self.max_leverage, 1.0 / (atr / entry * 3))
        }
