#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado a estatística geral das rotas e da frota

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd
import json

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
import dash_iconify
from dash_iconify import DashIconify


# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_linhas_possui_info_combustivel, get_modelos_veiculos_com_combustivel

# Imports específicos
from modules.home.home_service import HomeService
from modules.monitoramento.monitoramento_service import MonitoramentoService
import modules.monitoramento.tabela as monitoramento_tabela
import modules.monitoramento.graficos as monitoramento_graficos

from modules.combustivel_por_linha.combustivel_por_linha_service import CombustivelPorLinhaService
import modules.combustivel_por_linha.graficos as combustivel_graficos
import modules.combustivel_por_linha.tabela as combustivel_linha_tabela


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
home_service = HomeService(pgEngine)
monitoramento_service = MonitoramentoService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")
lista_todas_linhas.insert(0, {"LABEL": "TODAS"})

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(datas, lista_modelos, linha, lista_sentido, lista_dias_semana):
    if datas is None or not datas or None in datas:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    if linha is None:
        return False

    if lista_sentido is None or not lista_sentido or None in lista_sentido:
        return False

    if lista_dias_semana is None or not lista_dias_semana or None in lista_dias_semana:
        return False

    return True


##############################################################################
# Callbacks para os estados ##################################################
##############################################################################


@callback(
    Output("dash-home-estastistica-consumo-linha", "data"),
    Input("input-intervalo-datas-home", "value"),
)
def computa_dados_consumo_por_linha_home(datas):
    df = home_service.get_consumo_por_linha()
    return {
        "valid": True,
        "dados": df.to_dict(orient="records"),
    }


@callback(
    Output("dash-home-estastistica-consumo-modelo", "data"),
    Input("input-intervalo-datas-home", "value"),
)
def computa_dados_consumo_por_modelo_home(datas):
    df = home_service.get_estatistica_consumo_por_veiculo()
    return {
        "valid": True,
        "dados": df.to_dict(orient="records"),
    }


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################

@callback(
    Output("graph-boxplot-consumo-por-modelo", "figure"),
    Input("dash-home-estastistica-consumo-modelo", "data"),
)
def plota_boxplot_consumo_por_modelo(payload_consumo_por_modelo):
    if "valid" not in payload_consumo_por_modelo or not payload_consumo_por_modelo["valid"]:
        return go.Figure()
    
    df = pd.DataFrame(payload_consumo_por_modelo["dados"])
    
    df['hover_text'] = (
        'Veículo: ' + df['vec_num_id'] + 
        '<br>Modelo: ' + df['vec_model_padronizado'] +
        '<br>Consumo: ' + df['media_consumo_por_km'].astype(str) + ' km/L' +
        '<br>Total de viagens: ' + df['total_viagens'].astype(str)
    )
    modelos = df['vec_model_padronizado'].unique()


    cores = tema.PALETA_CORES_DISCRETA  # ou outras paletas: D3, Pastel, etc.

    fig = go.Figure()

    for i, modelo in enumerate(modelos):
        dados_modelo = df[df['vec_model_padronizado'] == modelo]
        cor = cores[i % len(cores)]  # repete as cores se tiver mais modelos do que cores disponíveis

        fig.add_trace(go.Box(
            x=dados_modelo['media_consumo_por_km'],
            name=modelo,
            boxpoints='all',
            marker=dict(
                opacity=0.5,
                color=cor
            ),
            line=dict(color=cor),
            orientation='h',
            text=dados_modelo['hover_text'],
            hovertemplate='%{text}<extra></extra>'
        ))

    # Layout do gráfico
    fig.update_layout(
        xaxis_title='Consumo médio do veículo (km/L)',
        yaxis_title='Modelo do Veículo',
        yaxis_title_standoff=50,
        margin=dict(t=50, l=200)
    )

    fig

    return fig


@callback(
    Output("graph-boxplot-consumo-por-linha", "figure"),
    Input("dash-home-estastistica-consumo-linha", "data"),
)
def plota_boxplot_consumo_por_linha(payload_consumo_por_linha):
    if "valid" not in payload_consumo_por_linha or not payload_consumo_por_linha["valid"]:
        return go.Figure()

    df = pd.DataFrame(payload_consumo_por_linha["dados"])
    df["label"] = (
        "Linha: "
        + df["linha"]
        + "<br>Sublinha: "
        + df["sublinha"]
        + "<br>Total viagens: "
        + df["total_viagens"].astype(str)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Box(
            x=df["media_km_por_litro"],  # muda para eixo x
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.8,
            marker=dict(
                opacity=0.5,
            ),
            name="Consumo",
            text=df["label"],
            hovertemplate="%{text}<br>Consumo: %{x:.2f} km/l<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(t=0, b=40, l=40, r=20),  # Reduz o espaço superior (t=top)
        showlegend=False,  # Remove legenda (que pode estar vazia)
    )
    fig.update_layout(xaxis_title="Consumo da Linha (km/L)")  # se o boxplot for horizontal

    return fig


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Home (Visão Geral)", path="/")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        dcc.Store(id="dash-home-estastistica-consumo-linha"),
        dcc.Store(id="dash-home-estastistica-consumo-modelo"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Cabeçalho e Inputs
                        dbc.Row(
                            [
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            DashIconify(icon="mdi:gas-station", width=45),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    html.Strong("Visão Geral do Consumo de Combustível"),
                                                ],
                                                className="align-self-center",
                                            ),
                                            width=True,
                                        ),
                                    ],
                                    align="center",
                                ),
                                dmc.Space(h=15),
                                html.Hr(),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Data"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-home",
                                                        # allowSingleDateInRange=True,
                                                        minDate=date(2025, 1, 1),
                                                        maxDate=date.today(),
                                                        type="range",
                                                        value=[date.today() - pd.DateOffset(days=30), date.today()],
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Modelos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos-home",
                                                        multi=True,
                                                        options=[
                                                            {
                                                                "label": modelo["LABEL"],
                                                                "value": modelo["LABEL"],
                                                            }
                                                            for modelo in lista_todos_modelos_veiculos
                                                        ],
                                                        value=["TODOS"],
                                                        placeholder="Selecione um ou mais modelos...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                            ]
                        ),
                        dmc.Space(h=10),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Dias"),
                                                    dbc.RadioItems(
                                                        id="input-select-dia-linha-combustivel",
                                                        options=[
                                                            {
                                                                "label": "Seg-Sexta",
                                                                "value": "SEG_SEX",
                                                            },
                                                            {
                                                                "label": "Sabado",
                                                                "value": "SABADO",
                                                            },
                                                            {
                                                                "label": "Domingo",
                                                                "value": "DOMINGO",
                                                            },
                                                            {
                                                                "label": "Feriado",
                                                                "value": "FERIADO",
                                                            },
                                                        ],
                                                        value="SEG_SEX",
                                                        inline=True,
                                                    ),
                                                ],
                                                className="dash-bootstrap h-200",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Linha"),
                                                    dcc.Dropdown(
                                                        id="input-select-linhas-monitoramento",
                                                        options=[
                                                            {
                                                                "label": linha["LABEL"],
                                                                "value": linha["LABEL"],
                                                            }
                                                            for linha in lista_todas_linhas
                                                        ],
                                                        value="TODAS",
                                                        placeholder="Selecione a linha",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                            ]
                        ),
                        dmc.Space(h=10),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(
                    DashIconify(icon="material-symbols:insights", width=45),
                    width="auto",
                ),
                dbc.Col(
                    html.H4("Indicadores", className="align-self-center"),
                ),
                dmc.Space(h=20),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-quantidade-de-viagens-comb-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="tabler:road",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Viagens"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-quantidade-de-veiculos-diferentes-comb-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:bus",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Veículos diferentes"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-quantidade-de-modelos-diferentes-comb-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:car-multiple",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Quantidade de modelos diferentes"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
            ]
        ),
        dbc.Row(dmc.Space(h=40)),
        # Grafico geral de consumo por modelo
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Consumo de combustível por modelo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="graph-boxplot-consumo-por-modelo"),
                    md=12,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="graph-boxplot-consumo-por-linha"),
                    md=12,
                ),
            ]
        ),
    ]
)
