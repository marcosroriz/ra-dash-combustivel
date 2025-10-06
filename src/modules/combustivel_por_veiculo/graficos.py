#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão geral por veículo

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
def gerar_grafico_pizza_sinteze_veiculo(df, labels, values, metadata_browser):
    """Gera o gráfico de pizza com síntese do total de viagens da tela do veículo"""

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

def gerar_grafico_timeline_consumo_veiculo(df, metadata_browser):
    status_colors = {
        "NORMAL": tema.COR_NORMAL,
        "SUSPEITA BAIXA PERFORMANCE (<= 1.0 STD)": tema.COR_COMB_10_STD,
        "BAIXA PERFORMANCE (<= 1.5 STD)": tema.COR_COMB_15_STD,
        "BAIXA PERFOMANCE (<= 2 STD)": tema.COR_COMB_20_STD,
        'ERRO TELEMETRIA (>= 2.0 STD)': tema.COR_COMB_ERRO,
    }

    # Inicia o gráfico
    fig = go.Figure()

    # Adiciona a linha horizontal do valor esperado
    fig.add_trace(
        go.Scatter(
            x=df["timestamp_br_inicio"],
            y=df["analise_valor_mediana_90_dias"],
            mode="lines",
            name="Valor Esperado (Mediana)",
            line=dict(color="gray", width=2, dash="dash")
        )
    )

    # Adiciona os dados por categoria de status
    for status, color in status_colors.items():
        df_filtrado = df[df["analise_status_90_dias"] == status]

        fig.add_trace(
            go.Scatter(
                x=df_filtrado["timestamp_br_inicio"],
                y=df_filtrado["km_por_litro"],
                mode="markers",
                marker=dict(color=color, size=10, sizemode="diameter", sizeref=1),
                line=dict(color=color),
                name=status,
                customdata=df_filtrado[
                    [
                        "km_por_litro",
                        "analise_valor_mediana_90_dias",
                        "analise_diff_mediana_90_dias",
                        "encontrou_numero_sublinha",
                        "encontrou_sentido_linha",
                        "encontrou_tempo_viagem_minutos",
                        "nome_motorista",
                    ]
                ],
                hovertemplate=(
                    "<b>Horário:</b> %{x}<br>"
                    + "<b>km/L Viagem:</b> %{customdata[0]:.2f}<br>"
                    + "<b>km/L Esperado:</b> %{customdata[1]:.2f} km/L<br>"
                    + "<b>Diferença da Mediana (km/L):</b> %{customdata[2]:.2f} km/L<br>"
                    + "<b>Linha:</b> %{customdata[3]}<br>"
                    + "<b>Sentido:</b> %{customdata[4]}<br>"
                    + "<b>Duração da viagem:</b> %{customdata[5]:.0f} minutos<br>"
                    + "<b>Motorista:</b> %{customdata[6]}<br><extra></extra>"
                ),

            ),
        )


    # Adicional labels
    fig.update_layout(
        xaxis_title="Dia",
        yaxis_title="km/L",
        legend=dict(
            title="Status",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),

    )

    # Seta x dinâmico
    x_max = df["timestamp_br_inicio"].max() + pd.Timedelta(hours=2)
    x_start = x_max - pd.DateOffset(day=1)

    fig.update_xaxes(
        range=[x_start, x_max],
        rangeslider_visible=True,
        rangeslider=dict(borderwidth=2),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 dia", step="day", stepmode="backward"),
                dict(count=7, label="1 semana", step="day", stepmode="backward"),
                dict(count=1, label="1 mês", step="month", stepmode="backward"),
                dict(step="all", label="tudo")
            ])
        )
    )

    fig.update_layout(
        height=600,
    )

    return fig

