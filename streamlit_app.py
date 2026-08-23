"""
Interfaz Streamlit — Ranking completo y Top LONG/SHORT con tiempo hasta próximo trade
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import yaml
from datetime import datetime

# ============================================================
# CONFIGURACIÓN COMPLETA CON TODAS LAS CLAVES
# ============================================================
DEFAULT_CONFIG = {
    "system": {"name": "DAPS-SIGNALS Ω X10 ULTRA", "version": "2.0", "mode": "production"},
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

def merge_config(base, override):
    """Fusiona recursivamente dos diccionarios"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            merge_config(base[key], value)
        else:
            base[key] = value
    return base

# ============================================================
# CARGA DEL SCANNER
# ============================================================
@st.cache_resource
def load_scanner():
    config = DEFAULT_CONFIG.copy()
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    merge_config(config, user_config)
        else:
            st.warning("⚠️ config.yaml no encontrado. Usando configuración por defecto.")
    except Exception as e:
        st.warning(f"⚠️ Error al leer config.yaml: {e}. Usando defaults.")

    from scanner import Scanner
    return Scanner(config)

# ============================================================
# INICIALIZACIÓN DE ESTADO
# ============================================================
st.set_page_config(layout="wide", page_title="DAPS-SIGNALS Ω X10 ULTRA")
st.title("📊 DAPS-SIGNALS Ω X10 ULTRA — Ranking y Señales")

if 'last_update' not in st.session_state:
    st.session_state.last_update = 0
if 'all_signals' not in st.session_state:
    st.session_state.all_signals = []

# ============================================================
# CARGA DEL SCANNER
# ============================================================
scanner = load_scanner()
if scanner is None:
    st.error("❌ No se pudo inicializar el scanner. Revisa los logs.")
    st.stop()

# ============================================================
# ACTUALIZACIÓN DE DATOS
# ============================================================
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Actualizar ahora", use_container_width=True):
        with st.spinner("Analizando activos..."):
            st.session_state.all_signals = scanner.scan_all()
            st.session_state.last_update = time.time()
            st.rerun()

with col_info:
    elapsed = int(time.time() - st.session_state.last_update) if st.session_state.last_update > 0 else 0
    remaining = max(0, 300 - elapsed)
    st.caption(f"Última actualización: hace {elapsed//60}m {elapsed%60}s | Próximo escaneo: {remaining//60}m {remaining%60}s")

# Si no hay datos o pasó más de 5 min, actualizar automáticamente
if not st.session_state.all_signals or (time.time() - st.session_state.last_update > 300):
    with st.spinner("Analizando activos..."):
        st.session_state.all_signals = scanner.scan_all()
        st.session_state.last_update = time.time()

signals = st.session_state.all_signals

# ============================================================
# MÉTRICAS DE RESUMEN
# ============================================================
total = len(signals)
longs = len([s for s in signals if s['direction'] == 'LONG'])
shorts = len([s for s in signals if s['direction'] == 'SHORT'])
approved = len([s for s in signals if s['score'] >= 30])

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Activos analizados", total)
col2.metric("🟢 LONG", longs)
col3.metric("🔴 SHORT", shorts)
col4.metric("✅ Aprobados (score≥30)", approved)

# ============================================================
# TOP 1 LONG y SHORT
# ============================================================
top_long = scanner.get_top_long()
top_short = scanner.get_top_short()

col_long, col_short = st.columns(2)

with col_long:
    st.subheader("🏆 TOP 1 LONG")
    if top_long:
        st.markdown(f"""
        **Activo:** `{top_long['asset']}`  
        **Score:** {top_long['score']:.1f}%  
        **Entrada:** ${top_long['entry']:.4f}  
        **SL:** ${top_long['sl']:.4f}  |  **TP:** ${top_long['tp']:.4f}  |  **R:R:** {top_long['rr']:.2f}  
        **Trailing activation:** ${top_long['trailing_activation']:.4f}  
        **Trailing distance:** ${top_long['trailing_distance']:.4f}  
        **⏱️ Tiempo estimado:** {top_long.get('time_to_entry', 'N/A')}  
        **Razones:** {', '.join(top_long.get('reasons', ['Sin condiciones']))}
        """)
    else:
        st.info("No hay señales LONG activas")

with col_short:
    st.subheader("🏆 TOP 1 SHORT")
    if top_short:
        st.markdown(f"""
        **Activo:** `{top_short['asset']}`  
        **Score:** {top_short['score']:.1f}%  
        **Entrada:** ${top_short['entry']:.4f}  
        **SL:** ${top_short['sl']:.4f}  |  **TP:** ${top_short['tp']:.4f}  |  **R:R:** {top_short['rr']:.2f}  
        **Trailing activation:** ${top_short['trailing_activation']:.4f}  
        **Trailing distance:** ${top_short['trailing_distance']:.4f}  
        **⏱️ Tiempo estimado:** {top_short.get('time_to_entry', 'N/A')}  
        **Razones:** {', '.join(top_short.get('reasons', ['Sin condiciones']))}
        """)
    else:
        st.info("No hay señales SHORT activas")

# ============================================================
# RANKING COMPLETO
# ============================================================
st.subheader("📋 Ranking completo de activos")

if signals:
    df = pd.DataFrame(signals)
    df_display = df[['asset', 'direction', 'score', 'entry', 'sl', 'tp', 'rr', 'time_to_entry']].copy()
    df_display.columns = ['Activo', 'Dir.', 'Score', 'Entrada', 'SL', 'TP', 'R:R', '⏱️ Tiempo estimado']

    # Colorear según dirección
    def color_row(row):
        if row['Dir.'] == 'LONG':
            return ['background-color: #00ff8822'] * len(row)
        elif row['Dir.'] == 'SHORT':
            return ['background-color: #ff444422'] * len(row)
        else:
            return [''] * len(row)

    st.dataframe(
        df_display.style.apply(color_row, axis=1),
        use_container_width=True,
        height=500
    )
else:
    st.info("No hay datos de activos")

# ============================================================
# GRÁFICO DEL TOP 1
# ============================================================
selected_asset = None
if top_long and top_short:
    selected_asset = st.selectbox("📈 Ver gráfico de:", [top_long['asset'], top_short['asset']])
elif top_long:
    selected_asset = top_long['asset']
elif top_short:
    selected_asset = top_short['asset']

if selected_asset:
    st.subheader(f"📈 Gráfico de {selected_asset}")
    df_ohlcv = scanner._fetch_ohlcv(selected_asset, limit=100)
    if df_ohlcv is not None and not df_ohlcv.empty:
        signal = next((s for s in signals if s['asset'] == selected_asset), None)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(
            x=df_ohlcv.index,
            open=df_ohlcv['open'],
            high=df_ohlcv['high'],
            low=df_ohlcv['low'],
            close=df_ohlcv['close'],
            name='OHLC',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ), row=1, col=1)

        if signal:
            fig.add_hline(y=signal['entry'], line_dash="dash", line_color="#00aaff",
                          annotation_text="Entrada", row=1, col=1)
            fig.add_hline(y=signal['sl'], line_dash="dash", line_color="#ff4444",
                          annotation_text="SL", row=1, col=1)
            fig.add_hline(y=signal['tp'], line_dash="dash", line_color="#00ff88",
                          annotation_text="TP", row=1, col=1)

        fig.add_trace(go.Bar(x=df_ohlcv.index, y=df_ohlcv['volume'],
                             name='Volumen', marker_color='#4488ff', opacity=0.6), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudieron obtener datos de velas para el gráfico.")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(f"🔬 DAPS-SIGNALS Ω X10 ULTRA · Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
