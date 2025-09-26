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

def gera_grafico_regras_comb(df):
    """
    Gera gráfico de barras mostrando a proporção de veículos com e sem regra
    de monitoramento de combustível por modelo.
    
    df deve ter as colunas:
    'vec_model', 'perc_com_regra', 'perc_sem_regra', 'CATEGORIA' (opcional)
    """

    # Converte os dados para formato long
    id_vars = ["vec_model"]
    if "CATEGORIA" in df.columns:
        id_vars.append("CATEGORIA")

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=["perc_com_regra", "perc_sem_regra"],
        var_name="Tipo",
        value_name="PERC"
    )

    # Renomeia valores para melhor legibilidade
    df_long["Tipo"] = df_long["Tipo"].map({
        "perc_com_regra": "Com Regra",
        "perc_sem_regra": "Sem Regra"
    })

    # Cria gráfico de barras empilhadas (um retângulo por modelo)
    fig = px.bar(
        df_long,
        x="vec_model",
        y="PERC",
        color="Tipo",
        barmode="stack",  # empilhado
        text="PERC",
        facet_col="CATEGORIA" if "CATEGORIA" in df.columns else None,
        facet_col_spacing=0.05,
        labels={"vec_model": "Modelo", "PERC": "%"},
        title="Proporção de Veículos com/sem Regra por Modelo",
        color_discrete_map={
        "Com Regra": "red",
        "Sem Regra": "green"}
    )

    # Mostra os valores dentro das barras
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='inside')

    # Ajusta visual
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_tickfont_size=15,
        height=700,
        legend_title_text="Tipo",
        margin=dict(b=200),
        autosize=True
    )

    # Ajusta para permitir que rótulos longos apareçam
    fig.update_xaxes(automargin=True)

    return fig