"""
Interfaz Streamlit — Ranking completo y Top LONG/SHORT
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
import yaml

st.set_page_config(layout="wide", page_title="DAPS-SIGNALS Ω X10 ULTRA")
st.title("📊 DAPS-SIGNALS Ω X10 ULTRA — Ranking y Señales")

# ============================================================
# CONFIGURACIÓN HARCODEADA
# ============================================================
DEFAULT_CONFIG = {
    "universe": {"max_assets": 25, "min_volume_usdt": 5000000},
    "scoring": {"thresholds": {"strong": 0.70, "good": 0.50, "weak": 0.30}},
    "risk": {"sl_multiplier": 1.0, "tp_multiplier": 2.5,
             "trailing_activation": 0.5, "trailing_distance": 1.0, "max_leverage": 1.5},
    "backtest": {"walk_forward_train": 180, "walk_forward_test": 30,
                 "walk_forward_step": 15, "monte_carlo_sims": 5000},
    "streamlit": {"refresh_seconds": 300}
}

# ============================================================
# CARGA DEL SCANNER
# ============================================================
@st.cache_resource
def load_scanner():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            config = DEFAULT_CONFIG.copy()
        from scanner import Scanner
        return Scanner(config)
    except Exception as e:
        st.error(f"Error al cargar scanner: {e}")
        return None

scanner = load_scanner()
if scanner is None:
    st.stop()

# ============================================================
# LÓGICA DE ACTUALIZACIÓN
# ============================================================
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0

if st.button("🔄 Actualizar ahora") or (time.time() - st.session_state.last_update > 300):
    with st.spinner("Analizando activos..."):
        all_signals = scanner.scan_all()
        st.session_state.all_signals = all_signals
        st.session_state.last_update = time.time()
        st.rerun()

if 'all_signals' not in st.session_state:
    with st.spinner("Primer análisis..."):
        st.session_state.all_signals = scanner.scan_all()
        st.session_state.last_update = time.time()

signals = st.session_state.all_signals

# ============================================================
# INDICADORES DE TIEMPO
# ============================================================
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Última actualización", scanner.time_since_last_scan())
with col2:
    st.metric("Próximo escaneo", scanner.next_scan_in())
with col3:
    total_assets = len(signals)
    approved = len([s for s in signals if s['score'] >= 30])
    st.metric("Activos analizados", f"{total_assets} (aprobados: {approved})")

# ============================================================
# TOP LONG Y TOP SHORT
# ============================================================
top_long = scanner.get_top_long()
top_short = scanner.get_top_short()

col_long, col_short = st.columns(2)

with col_long:
    if top_long:
        st.subheader("🏆 TOP 1 LONG")
        st.markdown(f"""
        **Activo:** {top_long['asset']}
        - **Score:** {top_long['score']:.1f}%
        - **Entrada:** ${top_long['entry']:.4f}
        - **Stop Loss:** ${top_long['sl']:.4f}
        - **Take Profit:** ${top_long['tp']:.4f}
        - **R:R:** {top_long['rr']:.2f}
        - **Trailing activation:** ${top_long['trailing_activation']:.4f}
        - **Trailing distance:** ${top_long['trailing_distance']:.4f}
        - **Tiempo estimado:** {top_long['time_to_entry']}
        - **Razones:** {', '.join(top_long['reasons'])}
        """)
    else:
        st.info("No hay señales LONG activas")

with col_short:
    if top_short:
        st.subheader("🏆 TOP 1 SHORT")
        st.markdown(f"""
        **Activo:** {top_short['asset']}
        - **Score:** {top_short['score']:.1f}%
        - **Entrada:** ${top_short['entry']:.4f}
        - **Stop Loss:** ${top_short['sl']:.4f}
        - **Take Profit:** ${top_short['tp']:.4f}
        - **R:R:** {top_short['rr']:.2f}
        - **Trailing activation:** ${top_short['trailing_activation']:.4f}
        - **Trailing distance:** ${top_short['trailing_distance']:.4f}
        - **Tiempo estimado:** {top_short['time_to_entry']}
        - **Razones:** {', '.join(top_short['reasons'])}
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
    df_display.columns = ['Activo', 'Dir.', 'Score', 'Entrada', 'SL', 'TP', 'R:R', 'Tiempo estimado']
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
        height=400
    )
else:
    st.info("No hay datos de activos")

# ============================================================
# GRÁFICO DEL TOP 1 (opcional)
# ============================================================
selected_asset = None
if top_long and top_short:
    selected_asset = st.selectbox("Ver gráfico de:", [top_long['asset'], top_short['asset']])
elif top_long:
    selected_asset = top_long['asset']
elif top_short:
    selected_asset = top_short['asset']

if selected_asset:
    st.subheader(f"📈 Gráfico de {selected_asset}")
    df_ohlcv = scanner._fetch_ohlcv(selected_asset, limit=100)
    if df_ohlcv is not None and not df_ohlcv.empty:
        # Buscar la señal correspondiente
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
        st.warning("No se pudieron obtener datos de velas.")
