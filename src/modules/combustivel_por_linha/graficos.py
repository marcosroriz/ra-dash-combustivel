#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão de combustível por linha

# Imports básicos
import matplotlib.colors as mcolors
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

    # Obtem os modelos
    modelos = df_linha_agg["vec_model"].unique()

    # Plota o intervalo (buffer) para cada modelo
    for i, modelo in enumerate(modelos):
        # Filtra df_linha_agg para o modelo atual
        df_linha_modelo = df_linha_agg[df_linha_agg["vec_model"] == modelo]

        # Cor do modelo
        i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]
        i_cor_rgba = "rgba" + str(mcolors.to_rgba(i_cor_hex, alpha=0.2))

        # Gera o gráfico de área para o intervalo (buffer) do modelo 
        fig.add_trace(
            go.Scatter(
                x=df_linha_modelo["time_bin_formatado"].tolist() + df_linha_modelo["time_bin_formatado"].tolist()[::-1],
                y=df_linha_modelo["max"].tolist() + df_linha_modelo["min"].tolist()[::-1],
                connectgaps=False,
                fill="toself",
                fillcolor=i_cor_rgba,
                line=dict(color="rgba(0,0,0,0)"),  # Sem borda
                name="Intervalo Min-Max " + modelo,
            )
        )

    # Plota a linha média do modelo
    for i, modelo in enumerate(modelos):
        # Filtra df_linha_agg para o modelo atual
        df_linha_modelo = df_linha_agg[df_linha_agg["vec_model"] == modelo]

        # Cor do modelo
        i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]
        i_cor_rgb = mcolors.to_rgb(i_cor_hex)

        # Gera o gráfico de linha para o modelo
        fig.add_trace(
            go.Scatter(
                x=df_linha_modelo["time_bin_formatado"],
                y=df_linha_modelo["mean"],
                mode="lines+markers",
                connectgaps=False,
                line=dict(color=i_cor_hex, width=2),
                name=modelo,
            )
        )

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
