#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão geral (home)

# Imports básicos
import pandas as pd
import numpy as np

# Imports gráficos
import plotly.express as px
import plotly.graph_objects as go

# Imports do tema
import tema

# Funções para formatação
from modules.str_utils import truncate_label


# Rotinas para gerar os Gráficos
def gerar_grafico_pizza_sinteze_geral(df, labels, values, metadata_browser):
    """Gera o gráfico de pizza com síntese do total de viagens da tela inicial"""

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                direction="clockwise",
                marker_colors=[
                    tema.COR_NORMAL,
                    tema.COR_COMB_10_STD,
                    tema.COR_COMB_15_STD,
                    tema.COR_COMB_20_STD,
                    tema.COR_COMB_ERRO,
                ],
                sort=True,
            )
        ]
    )

    # Arruma legenda e texto
    fig.update_traces(textinfo="value+percent", sort=False)

    # Total numérico de OS, para o título
    total_viagens = df["total_viagens"].sum()
    total_num_viagens_str = f"{total_viagens:,}".replace(",", ".")
    fig.update_layout(
        title=dict(
            text=f"Total de Viagens: {total_num_viagens_str}",
            y=0.97,  # Posição vertical do título
            x=0.5,  # Centraliza o título horizontalmente
            xanchor="center",
            yanchor="top",
            font=dict(size=18),  # Tamanho do texto
        ),
        separators=",.",
    )

    # Remove o espaçamento em torno do gráfico
    fig.update_layout(
        margin=dict(t=100, b=0),  # Remove as margens
        height=420,  # Ajuste conforme necessário
        # legend=dict(
        #     orientation="h",  # Legenda horizontal
        #     yanchor="top",  # Ancora no topo
        #     xanchor="center",  # Centraliza
        #     y=-0.1,  # Coloca abaixo
        #     x=0.5,  # Alinha com o centro
        # ),
    )

    # Remove o espaçamento lateral do gráfico no dispositivo móvel
    if metadata_browser and metadata_browser["device"] == "Mobile":
        fig.update_layout(margin=dict(t=100, b=20, l=20, r=20))
        fig.update_layout(
            legend=dict(
                orientation="h",  # Legenda horizontal
                yanchor="top",  # Ancora no topo
                xanchor="center",  # Centraliza
                y=-0.1,  # Coloca abaixo
                x=0.5,  # Alinha com o centro
            ),
        )

    # Retorna o gráfico
    return fig


# Rotinas para gerar os Gráficos
def gerar_grafico_barra_consumo_modelos_geral(df, metadata_browser):
    """Gera o gráfico de barra com o consumo dos modelos"""

    fig = px.bar(
        df,
        x="vec_model",
        y="media_km_litro",
        color="vec_model",
        text="media_km_litro",
        labels={"media_km_litro": "km/L médio", "vec_model": "Modelo"},
    )

    # Remove o espaçamento lateral do gráfico no dispositivo móvel
    if metadata_browser and metadata_browser["device"] == "Mobile":
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        fig.update_layout(
            legend=dict(
                orientation="h",  # Legenda horizontal
                yanchor="top",  # Ancora no topo
                xanchor="center",  # Centraliza
                y=-0.1,  # Coloca abaixo
                x=0.5,  # Alinha com o centro
            ),
        )

    # Retorna o gráfico
    return fig
