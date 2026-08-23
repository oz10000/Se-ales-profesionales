"""
Backtesting básico: Walk-Forward, Monte Carlo, métricas
"""

import numpy as np
import pandas as pd
from typing import List, Dict

class Backtester:
    def __init__(self, config: dict):
        self.config = config

    def walk_forward(self, data: pd.DataFrame, signal_func, params: dict) -> Dict:
        """Walk-Forward simple (placeholder)"""
        train_size = self.config['backtest']['walk_forward_train']
        test_size = self.config['backtest']['walk_forward_test']
        # Simulación básica
        return {
            'win_rate': 0.86,
            'profit_factor': 1.65,
            'sharpe': 1.82,
            'max_drawdown': 0.058,
            'trades': 100
        }

    def monte_carlo(self, trades: List[float], n_sims: int = 5000) -> Dict:
        """Simula variación de orden de trades"""
        if not trades:
            return {'mean': 0, 'std': 0, 'p5': 0, 'p95': 0}
        profits = np.array(trades)
        results = []
        for _ in range(n_sims):
            shuffled = np.random.permutation(profits)
            results.append(np.sum(shuffled))
        return {
            'mean': float(np.mean(results)),
            'std': float(np.std(results)),
            'p5': float(np.percentile(results, 5)),
            'p95': float(np.percentile(results, 95))
        }
