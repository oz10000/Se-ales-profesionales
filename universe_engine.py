"""
Universe Engine — Selección dinámica de activos desde Binance
"""

import ccxt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

class UniverseEngine:
    def __init__(self, config: dict):
        self.config = config
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.min_volume = config['universe']['min_volume_usdt']
        self.max_assets = config['universe']['max_assets']
        self.assets = []

    def get_universe(self) -> List[str]:
        """Retorna lista de activos operables (top por volumen)"""
        if self.assets:
            return self.assets

        try:
            markets = self.exchange.load_markets()
            # Filtrar USDT pairs activos
            symbols = [s for s in markets if s.endswith('/USDT') and markets[s]['active']]

            # Obtener tickers para volumen
            tickers = self.exchange.fetch_tickers(symbols)
            volumes = []
            for sym in symbols:
                ticker = tickers.get(sym)
                if ticker and ticker.get('quoteVolume'):
                    vol = float(ticker['quoteVolume'])
                    if vol >= self.min_volume:
                        volumes.append((sym, vol))

            # Ordenar por volumen descendente
            volumes.sort(key=lambda x: x[1], reverse=True)
            self.assets = [sym for sym, _ in volumes[:self.max_assets]]
            return self.assets

        except Exception as e:
            print(f"Error obteniendo universo: {e}")
            # Fallback: activos conocidos
            self.assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
                           'ADA/USDT', 'LINK/USDT', 'AVAX/USDT', 'DOGE/USDT']
            return self.assets
