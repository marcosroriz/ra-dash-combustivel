#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos de monitoramento de viagens por veículo

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

def gerar_grafico_monitoramento_viagens_veiculo(df, opcoes_detalhamento):
    """
    Função que gera o gráfico de monitoramento de viagens por veículo
    """

    # Define as cores para cada status
    status_colors = {
        "REGULAR": "green",
        "SUSPEITA BAIXA PERFOMANCE": "orange",
        "BAIXA PERFORMANCE": "red",
        "ERRO TELEMETRIA": "purple",
    }

    # Inicia o gráfico
    fig = go.Figure()

    # Adiciona a linha horizontal tracejada em y = 0
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=0,
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
        name="Referência zero",
    )

    # Arredonda o consumo para 2 casas decimais
    df["km_redondo"] = df["km_por_litro"].round(2)
    df["tempo_minutos"] = (df["encontrou_tempo_viagem_segundos"] / 60).round(1)

    # Adiciona os dados por categoria de status
    for status, color in status_colors.items():
        df_filtrado = df[df["status_consumo"] == status]

        fig.add_trace(
            go.Scatter(
                x=df_filtrado["time_bin_formatado"],
                y=df_filtrado["km_redondo"],
                mode="markers",
                marker=dict(color=color, size=16, sizemode="diameter", sizeref=1),
                line=dict(color=color),
                name=status,
                customdata=df_filtrado[
                    [
                        "km_redondo",
                        "diferenca_mediana",
                        "encontrou_numero_sublinha",
                        "tempo_minutos",
                        "nome_motorista",
                        "encontrou_sentido_linha",
                    ]
                ],
                hovertemplate=(
                    "<b>Horário:</b> %{x}<br>"
                    + "<b>km/L Viagem:</b> %{customdata[0]:.2f}<br>"
                    + "<b>Diferença da Mediana (km/L):</b> %{customdata[1]:.2f}<br>"
                    + "<b>Linha:</b> %{customdata[2]}<br>"
                    + "<b>Sentido:</b> %{customdata[5]}<br>"
                    + "<b>Duração da viagem:</b> %{customdata[3]}<br>"
                    + "<b>Motorista:</b> %{customdata[4]}<br><extra></extra>"
                ),
            )
        )

    # Vamos lidar agora com as opções de detalhamento
    if opcoes_detalhamento == "MOTORISTA":
        # Adicionando por motorista
        motoristas = df["nome_motorista"].dropna().unique()

        for i, nome in enumerate(motoristas):
            i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]
            i_cor_rgb = "rgb" + str(mcolors.to_rgb(i_cor_hex))
            i_cor_rgba = "rgba" + str(mcolors.to_rgba(i_cor_hex, alpha=0.2))
            
            df_motorista = df[df["nome_motorista"] == nome]
            if df_motorista.empty:
                continue

            x0 = df_motorista["time_bin_formatado"].min() - pd.Timedelta(minutes=10)
            x1 = df_motorista["time_bin_formatado"].max() + pd.Timedelta(minutes=10)
            y0 = df["km_redondo"].min() - 0.25
            y1 = df["km_redondo"].max() + 0.25

            fig.add_shape(
                type="rect",
                xref="x", yref="y",
                x0=x0, x1=x1 + pd.Timedelta(minutes=10),
                y0=y0, y1=y1,
                line=dict(color=i_cor_rgb, width=1.5, dash="dot"),
                fillcolor=i_cor_rgba,
                layer="below"
            )

            fig.add_annotation(
                x=x0,
                y=y1,
                text=f"{nome.split()[0]}",
                showarrow=False,
                font=dict(size=10, color=i_cor_rgb),
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.7)"
            )
    # Se opção de detalhamento for linha, adiciona a linha
    elif opcoes_detalhamento == "LINHA":
        # identifica os grupos contínuos de linhas
        groups_linha = (df['rmtc_linha_prevista'] != df['rmtc_linha_prevista'].shift()).cumsum()

        # agrupa pelos blocos contínuos e extrai valor, início e fim
        blocos = df.groupby(groups_linha).apply(lambda g: {
            'valor': g['rmtc_linha_prevista'].iloc[0],
            'inicio': g.index[0],
            'fim': g.index[-1]
        }).reset_index(drop=True)

        # transforma em DataFrame
        df_blocos = pd.DataFrame(blocos.tolist())
        
        # Adicionando por motorista
        linha_cor = {}

        # Para cada bloco (linha)
        for i, row in df_blocos.iterrows():
            linha = row["valor"]
            nome = str(row["valor"])
            lim_inferior = row["inicio"]
            lim_superior = row["fim"]

            # Pega cor
            i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]

            if linha in linha_cor:
                i_cor_hex = linha_cor[linha]
            else:
                # Seta cor
                linha_cor[linha] = i_cor_hex
            
            i_cor_rgb = "rgb" + str(mcolors.to_rgb(i_cor_hex))
            i_cor_rgba = "rgba" + str(mcolors.to_rgba(i_cor_hex, alpha=0.2))

            
            df_filtro = df.iloc[lim_inferior:lim_superior + 1]
            if df_filtro.empty:
                continue

            x0 = df_filtro["time_bin_formatado"].min() - pd.Timedelta(minutes=10)
            x1 = df_filtro["time_bin_formatado"].max() + pd.Timedelta(minutes=10)
            y0 = df["km_redondo"].min() - 0.25
            y1 = df["km_redondo"].max() + 0.25

            fig.add_shape(
                type="rect",
                xref="x", yref="y",
                x0=x0, x1=x1 + pd.Timedelta(minutes=10),
                y0=y0, y1=y1,
                line=dict(color=i_cor_rgb, width=1.5, dash="dot"),
                fillcolor=i_cor_rgba,
                layer="below"
            )

            fig.add_annotation(
                x=x0,
                y=y1,
                text=nome,
                showarrow=False,
                font=dict(size=10, color=i_cor_rgb),
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.7)"
            )


    # Gera a linha de consumo esperada
    fig.add_trace(
        go.Scatter(
            x=df["time_bin_formatado"],
            y=df["mediana"],
            mode="lines",
            line=dict(color="gray", width=3, shape="spline", dash="dot"),
            name="Consumo Mediana",
            opacity=0.5,
            showlegend=True,  # ou True se quiser a legenda da linha também
            hoverinfo="skip"  # se quiser que a linha não tenha hover
        )
    )

    # Configurações finais do gráfico (labels e ticks)
    fig.update_layout(
        xaxis_title="Horário",
        yaxis_title="Consumo (km/l)",
        legend_title="Status de Consumo",
    )

    # Cálculo dos limites com margem de 0.5 para cima e para baixo
    y_min = min(df["mediana"].min(), df["km_redondo"].min()) - 0.5
    y_max = max(df["mediana"].max(), df["km_redondo"].max()) + 0.5

    fig.update_layout(
        xaxis=dict(
            tickformat="%H:%M",
            dtick=1800000,  # 30 minutos em milissegundos,
        ),
        yaxis=dict(title="Consumo (km/L)", range=[y_min, y_max]),
    )

    # Remove um pouco do espaçamento entre o gráfico e o título
    fig.update_layout(
        margin=dict(t=50),
    )

    return fig


def gerar_grafico_monitoramento_viagens_veiculo_desvio_padrao(df, opcoes_detalhamento):
    """
    Função que gera o gráfico de monitoramento de viagens por veículo
    """

    # Define as cores para cada status
    status_colors = {
        "REGULAR": "green",
        "SUSPEITA BAIXA PERFOMANCE": "orange",
        "BAIXA PERFORMANCE": "red",
        "ERRO TELEMETRIA": "purple",
    }

    # Inicia o gráfico
    fig = go.Figure()

    # Adiciona a linha horizontal tracejada em y = 0
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=0,
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
        name="Referência zero",
    )

    # Adiciona os dados por categoria de status
    for status, color in status_colors.items():
        df_filtrado = df[df["status_consumo"] == status]
        df_filtrado["km_redondo"] = df_filtrado["km_por_litro"].round(2)
        df_filtrado["tempo_minutos"] = (df_filtrado["encontrou_tempo_viagem_segundos"] / 60).round(1)

        fig.add_trace(
            go.Scatter(
                x=df_filtrado["time_bin_formatado"],
                y=df_filtrado["diferenca_mediana"],
                mode="markers",
                marker=dict(color=color, size=16, sizemode="diameter", sizeref=1),
                line=dict(color=color),
                name=status,
                customdata=df_filtrado[
                    [
                        "km_redondo",
                        "diferenca_mediana",
                        "encontrou_numero_sublinha",
                        "tempo_minutos",
                        "nome_motorista",
                        "encontrou_sentido_linha",
                    ]
                ],
                hovertemplate=(
                    "<b>Horário:</b> %{x}<br>"
                    + "<b>km/L Viagem:</b> %{customdata[0]:.2f}<br>"
                    + "<b>Diferença da Mediana (km/L):</b> %{y:.2f}<br>"
                    + "<b>Linha:</b> %{customdata[2]}<br>"
                    + "<b>Sentido:</b> %{customdata[5]}<br>"
                    + "<b>Duração da viagem:</b> %{customdata[3]}<br>"
                    + "<b>Motorista:</b> %{customdata[4]}<br><extra></extra>"
                ),
            )
        )

    # Vamos lidar agora com as opções de detalhamento
    if opcoes_detalhamento == "MOTORISTA":
        # Adicionando por motorista
        motoristas = df["nome_motorista"].dropna().unique()

        for i, nome in enumerate(motoristas):
            i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]
            i_cor_rgb = "rgb" + str(mcolors.to_rgb(i_cor_hex))
            i_cor_rgba = "rgba" + str(mcolors.to_rgba(i_cor_hex, alpha=0.2))
            
            df_motorista = df[df["nome_motorista"] == nome]
            if df_motorista.empty:
                continue

            x0 = df_motorista["time_bin_formatado"].min() - pd.Timedelta(minutes=10)
            x1 = df_motorista["time_bin_formatado"].max() + pd.Timedelta(minutes=10)
            y0 = df["diferenca_mediana"].min() - 0.25
            y1 = df["diferenca_mediana"].max() + 0.25

            fig.add_shape(
                type="rect",
                xref="x", yref="y",
                x0=x0, x1=x1 + pd.Timedelta(minutes=10),
                y0=y0, y1=y1,
                line=dict(color=i_cor_rgb, width=1.5, dash="dot"),
                fillcolor=i_cor_rgba,
                layer="below"
            )

            fig.add_annotation(
                x=x0,
                y=y1,
                text=f"{nome.split()[0]}",
                showarrow=False,
                font=dict(size=10, color=i_cor_rgb),
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.7)"
            )
    # Se opção de detalhamento for linha, adiciona a linha
    elif opcoes_detalhamento == "LINHA":
        # identifica os grupos contínuos de linhas
        groups_linha = (df['rmtc_linha_prevista'] != df['rmtc_linha_prevista'].shift()).cumsum()

        # agrupa pelos blocos contínuos e extrai valor, início e fim
        blocos = df.groupby(groups_linha).apply(lambda g: {
            'valor': g['rmtc_linha_prevista'].iloc[0],
            'inicio': g.index[0],
            'fim': g.index[-1]
        }).reset_index(drop=True)

        # transforma em DataFrame
        df_blocos = pd.DataFrame(blocos.tolist())
        
        # Adicionando por motorista
        linha_cor = {}

        # Para cada bloco (linha)
        for i, row in df_blocos.iterrows():
            linha = row["valor"]
            nome = str(row["valor"])
            lim_inferior = row["inicio"]
            lim_superior = row["fim"]

            # Pega cor
            i_cor_hex = tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)]

            if linha in linha_cor:
                i_cor_hex = linha_cor[linha]
            else:
                # Seta cor
                linha_cor[linha] = i_cor_hex
            
            i_cor_rgb = "rgb" + str(mcolors.to_rgb(i_cor_hex))
            i_cor_rgba = "rgba" + str(mcolors.to_rgba(i_cor_hex, alpha=0.2))

            
            df_filtro = df.iloc[lim_inferior:lim_superior + 1]
            if df_filtro.empty:
                continue

            x0 = df_filtro["time_bin_formatado"].min() - pd.Timedelta(minutes=10)
            x1 = df_filtro["time_bin_formatado"].max() + pd.Timedelta(minutes=10)
            y0 = df["diferenca_mediana"].min() - 0.25
            y1 = df["diferenca_mediana"].max() + 0.25

            fig.add_shape(
                type="rect",
                xref="x", yref="y",
                x0=x0, x1=x1 + pd.Timedelta(minutes=10),
                y0=y0, y1=y1,
                line=dict(color=i_cor_rgb, width=1.5, dash="dot"),
                fillcolor=i_cor_rgba,
                layer="below"
            )

            fig.add_annotation(
                x=x0,
                y=y1,
                text=nome,
                showarrow=False,
                font=dict(size=10, color=i_cor_rgb),
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.7)"
            )


    # Configurações finais do gráfico (labels e ticks)
    fig.update_layout(
        xaxis_title="Horário",
        yaxis_title="Diferença da Mediana (km/l)",
        legend_title="Status de Consumo",
    )

    # Cálculo dos limites com margem de 0.5 para cima e para baixo
    y_min = df["diferenca_mediana"].min() - 0.5
    y_max = df["diferenca_mediana"].max() + 0.5

    fig.update_layout(
        xaxis=dict(
            tickformat="%H:%M",
            dtick=1800000,  # 30 minutos em milissegundos,
        ),
        yaxis=dict(title="Diferença da Mediana (km/L)", range=[y_min, y_max]),
    )

    # Remove um pouco do espaçamento entre o gráfico e o título
    fig.update_layout(
        margin=dict(t=50),
    )

    return fig

# Veiculso por modelo
def plot_veiculos_por_modelo(df):

    contagem = df['vec_model'].value_counts()


    # Transforma em DataFrame
    contagem_df = contagem.reset_index()
    contagem_df.columns = ['vec_model', 'quantidade']

    # Cria gráfico
    fig = px.bar(
        contagem_df,
        x='vec_model',
        y='quantidade',
        title='Quantidade de Veículos por Modelo',
        text='quantidade',
        labels={'vec_model': 'Modelo do Veículo', 'quantidade': 'Quantidade'}
    )

    return fig
