"""
Interfaz Streamlit para visualización de señales y velas
CONFIGURACIÓN HARCODEADA (no requiere config.yaml)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import os

st.set_page_config(layout="wide", page_title="DAPS-SIGNALS Ω X10 ULTRA")
st.title("📊 DAPS-SIGNALS Ω X10 ULTRA — Visualizador")

# ============================================================
# CONFIGURACIÓN HARCODEADA (fallback si no existe config.yaml)
# ============================================================
DEFAULT_CONFIG = {
    "system": {
        "name": "DAPS-SIGNALS Ω X10 ULTRA",
        "version": "2.0",
        "mode": "production"
    },
    "exchanges": {
        "binance": {"spot": True, "futures": True},
        "okx": {"spot": False},
        "bybit": {"spot": False}
    },
    "universe": {
        "max_assets": 25,
        "min_volume_usdt": 5000000,
        "min_candles": 500,
        "max_spread": 0.0025,
        "markets": ["spot", "futures"]
    },
    "indicators": {
        "adx_period": 14,
        "ker_period": 10,
        "atr_period": 14,
        "rsi_period": 14,
        "ema_fast": 20,
        "ema_slow": 50,
        "momentum_period": 5,
        "volume_ma_period": 20
    },
    "scoring": {
        "weights": {
            "trend": 0.22,
            "strength": 0.18,
            "efficiency": 0.18,
            "volatility": 0.12,
            "momentum": 0.18,
            "volume": 0.12
        },
        "thresholds": {
            "strong": 0.70,
            "good": 0.50,
            "weak": 0.30
        }
    },
    "risk": {
        "default_rr": 2.5,
        "sl_multiplier": 1.0,
        "tp_multiplier": 2.5,
        "trailing_activation": 0.5,
        "trailing_distance": 1.0,
        "max_leverage": 1.5,
        "max_drawdown": 0.10
    },
    "backtest": {
        "walk_forward_train": 180,
        "walk_forward_test": 30,
        "walk_forward_step": 15,
        "monte_carlo_sims": 5000,
        "bootstrap_samples": 1000
    },
    "streamlit": {
        "refresh_seconds": 300
    }
}

# ============================================================
# CARGA DEL SCANNER (con o sin config.yaml)
# ============================================================
@st.cache_resource
def load_scanner():
    """Carga el scanner usando config hardcodeada o desde archivo si existe"""
    config = None
    # Intentar cargar desde archivo
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            st.info("✅ Configuración cargada desde config.yaml")
        else:
            st.warning("⚠️ config.yaml no encontrado. Usando configuración por defecto (hardcodeada).")
            config = DEFAULT_CONFIG.copy()
    except Exception as e:
        st.warning(f"⚠️ Error al leer config.yaml: {e}. Usando configuración por defecto.")
        config = DEFAULT_CONFIG.copy()

    # Validar que la configuración tenga todas las claves necesarias
    if config is None:
        config = DEFAULT_CONFIG.copy()

    # Importar Scanner (se hace aquí para evitar conflictos de dependencias)
    try:
        from scanner import Scanner
        return Scanner(config)
    except Exception as e:
        st.error(f"❌ Error al cargar el scanner: {e}")
        return None

# ============================================================
# MAIN DE LA APP
# ============================================================
scanner = load_scanner()

if scanner is None:
    st.error("❌ No se pudo inicializar el scanner. Revisa los logs.")
    st.stop()

# Ejecutar escáner
with st.spinner("🔍 Analizando activos..."):
    signals = scanner.scan()

if signals:
    df = pd.DataFrame(signals)
    st.subheader("📋 Señales encontradas")
    st.dataframe(
        df[['asset', 'direction', 'score', 'entry', 'sl', 'tp', 'rr']],
        use_container_width=True
    )

    # Gráfico para el primer activo
    if len(signals) > 0:
        st.subheader(f"📈 Gráfico de {signals[0]['asset']}")
        asset = signals[0]['asset']
        df_ohlcv = scanner._fetch_ohlcv(asset, limit=100)
        if df_ohlcv is not None and not df_ohlcv.empty:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3]
            )
            fig.add_trace(
                go.Candlestick(
                    x=df_ohlcv.index,
                    open=df_ohlcv['open'],
                    high=df_ohlcv['high'],
                    low=df_ohlcv['low'],
                    close=df_ohlcv['close'],
                    name='OHLC',
                    increasing_line_color='#00ff88',
                    decreasing_line_color='#ff4444'
                ),
                row=1, col=1
            )

            # Niveles de entrada, SL y TP
            signal = signals[0]
            fig.add_hline(
                y=signal['entry'],
                line_dash="dash",
                line_color="#00aaff",
                annotation_text="Entrada",
                row=1, col=1
            )
            fig.add_hline(
                y=signal['sl'],
                line_dash="dash",
                line_color="#ff4444",
                annotation_text="SL",
                row=1, col=1
            )
            fig.add_hline(
                y=signal['tp'],
                line_dash="dash",
                line_color="#00ff88",
                annotation_text="TP",
                row=1, col=1
            )

            # Volumen
            fig.add_trace(
                go.Bar(
                    x=df_ohlcv.index,
                    y=df_ohlcv['volume'],
                    name='Volumen',
                    marker_color='#4488ff',
                    opacity=0.6
                ),
                row=2, col=1
            )

            fig.update_layout(
                height=600,
                template="plotly_dark",
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No se pudieron obtener datos de velas para el gráfico.")
else:
    st.info("🔍 No hay señales en este momento. Esperando nuevas oportunidades.")
