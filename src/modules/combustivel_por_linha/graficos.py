#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão de combustível por linha

# Imports básicos
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports gráficos
import plotly.express as px
import plotly.graph_objects as go

# Imports do tema
import tema

def gerar_grafico_consumo_combustivel_por_linha(df_linha_agg, periodo_agrupar="30T"):
    """
    Função que gera o gráfico de consumo de combustível por linha
    """

    fig = go.Figure()

    # Gera o intervalo
    fig.add_trace(go.Scatter(
        x=df_linha_agg["time_bin_formatado"].tolist() + df_linha_agg["time_bin_formatado"].tolist()[::-1],
        y=df_linha_agg["max"].tolist() + df_linha_agg["min"].tolist()[::-1],
        connectgaps=False,
        fill="toself",
        fillcolor="rgba(0, 100, 255, 0.2)",  # Light blue transparent buffer
        line=dict(color="rgba(0,0,0,0.2)"),  # No outline
        name="Intervalo Min-Max"
    ))

    # # Agrupa os dados por linha e data
    # fig = px.line(
    #         df_linha_agg,
    #         x="time_bin_only_time",
    #         y="mean",
    #         # error_y=df_agg["max"] - df_agg["mean"],  # Upper error bar
    #         # error_y_minus=df_agg["mean"] - df_agg["min"],  # Lower error bar
    #     )

    # Depois, adicione a linha da média por cima
    fig.add_trace(go.Scatter(
        x=df_linha_agg["time_bin_formatado"],
        y=df_linha_agg["mean"],
        mode="lines+markers",
        connectgaps=False,
        line=dict(color="blue", width=2),
        name="Média"
    ))

    fig.update_layout(
        xaxis_title="Hora",
        yaxis_title="Consumo de Combustível (km/l)",
    )

    fig.update_layout(
        xaxis=dict(
            tickformat="%H:%M",
            dtick=1800000,  # 30 minutos em milissegundos,
        )
    )

    return fig