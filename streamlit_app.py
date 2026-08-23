"""
Interfaz Streamlit para visualización de señales y velas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import os

st.set_page_config(layout="wide", page_title="DAPS-SIGNALS Ω X10 ULTRA")
st.title("📊 DAPS-SIGNALS Ω X10 ULTRA — Visualizador")

@st.cache_resource
def load_scanner():
    """Carga el scanner con manejo de errores para config.yaml"""
    try:
        if not os.path.exists("config.yaml"):
            st.error("❌ Archivo config.yaml no encontrado. Crea uno con la configuración requerida.")
            return None
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        from scanner import Scanner
        return Scanner(config)
    except yaml.YAMLError as e:
        st.error(f"❌ Error en config.yaml: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error al cargar el scanner: {e}")
        return None

scanner = load_scanner()

if scanner is None:
    st.stop()

# Ejecutar escáner
with st.spinner("🔍 Analizando activos..."):
    signals = scanner.scan()

if signals:
    # Tabla de señales
    df = pd.DataFrame(signals)
    st.subheader("📋 Señales encontradas")
    st.dataframe(df[['asset', 'direction', 'score', 'entry', 'sl', 'tp', 'rr']],
                 use_container_width=True)

    # Gráfico para el primer activo
    if len(signals) > 0:
        st.subheader(f"📈 Gráfico de {signals[0]['asset']}")
        asset = signals[0]['asset']
        df_ohlcv = scanner._fetch_ohlcv(asset, limit=100)
        if df_ohlcv is not None and not df_ohlcv.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                                 row_heights=[0.7, 0.3])
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

            # Agregar niveles de entrada, SL y TP
            signal = signals[0]
            fig.add_hline(y=signal['entry'], line_dash="dash", line_color="#00aaff",
                          annotation_text="Entrada", row=1, col=1)
            fig.add_hline(y=signal['sl'], line_dash="dash", line_color="#ff4444",
                          annotation_text="SL", row=1, col=1)
            fig.add_hline(y=signal['tp'], line_dash="dash", line_color="#00ff88",
                          annotation_text="TP", row=1, col=1)

            fig.add_trace(go.Bar(x=df_ohlcv.index, y=df_ohlcv['volume'],
                                 name='Volumen', marker_color='#4488ff', opacity=0.6), row=2, col=1)
            fig.update_layout(height=600, template="plotly_dark", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("🔍 No hay señales en este momento. Esperando nuevas oportunidades.")
