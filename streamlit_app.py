"""
Interfaz Streamlit para visualización de señales y velas (opcional)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scanner import Scanner
import yaml

st.set_page_config(layout="wide", page_title="DAPS-SIGNALS Ω X10 ULTRA")
st.title("📊 DAPS-SIGNALS Ω X10 ULTRA — Visualizador")

@st.cache_resource
def load_scanner():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return Scanner(config)

scanner = load_scanner()
signals = scanner.scan()

if signals:
    df = pd.DataFrame(signals)
    st.dataframe(df[['asset', 'direction', 'score', 'entry', 'sl', 'tp', 'rr']])

    # Gráfico de ejemplo para el primer activo
    if len(signals) > 0:
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
                name='OHLC'
            ), row=1, col=1)
            fig.add_trace(go.Bar(x=df_ohlcv.index, y=df_ohlcv['volume'], name='Volumen'), row=2, col=1)
            fig.update_layout(height=600, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay señales en este momento.")
