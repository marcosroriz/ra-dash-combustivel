#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

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

# Imports específicos
from modules.monitoramento.monitoramento_service import MonitoramentoService
import modules.monitoramento.tabela as monitoramento_tabela
import modules.monitoramento.graficos as monitoramento_graficos

from modules.combustivel_por_linha.combustivel_por_linha_service import CombustivelPorLinhaService
from modules.regras.regras_service import RegrasService
import modules.combustivel_por_linha.graficos as combustivel_graficos
import modules.combustivel_por_linha.tabela as combustivel_linha_tabela

# Imports gerais
from modules.entities_utils import get_linhas_possui_info_combustivel, get_modelos_veiculos_com_combustivel


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


regra_service = RegrasService(pgEngine)
# Cria o serviço
comb_por_linha_service = CombustivelPorLinhaService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    Output("tabela-regras-viagens-monitoramento", "rowData"),
    [
        Input("input-periodo-dias-monitoramento-regra", "value"),
        Input("input-modelos-monitoramento-regra", "value"),
        Input("input-select-linhas-monitoramento-regra", "value"),
        Input("input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("input-select-dia-linha-combustivel-regra", "value"),
        Input("input-excluir-km-l-menor-que-monitoramento-regra", "value"),
        Input("input-excluir-km-l-maior-que-monitoramento-regra", "value"),
        Input("select-mediana", "value"),
        Input("select-baixa-performace-suspeita", "value"),
        Input("select-baixa-performace-indicativo", "value"),
        Input("select-erro-telemetria", "value"),
    ],
)
def atualiza_tabela_regra_viagens_monitoramento(
    dia, modelos, linha,
    quantidade_de_viagens, dias_marcados, 
    excluir_km_l_menor_que, excluir_km_l_maior_que,
    mediana_viagem, suspeita_performace,
    indicativo_performace, erro_telemetria
):
    print("Datas: ", dia)
    print("Modelos: ", modelos)
    print("Linha: ", linha)
    print("Quantidade de viagens: ", quantidade_de_viagens)
    print("Dias marcados: ", dias_marcados)
    print("Excluir km/L menor que: ", excluir_km_l_menor_que)
    print("Excluir km/L maior que: ", excluir_km_l_maior_que)
    print("Mediana: ", excluir_km_l_maior_que)
    print("suspeita: ", excluir_km_l_maior_que)
    print("indicativo: ", excluir_km_l_maior_que)
    print("erro telemetria: ", excluir_km_l_maior_que)

    df = regra_service.get_estatistica_veiculos(dia, linha, dias_marcados)

    return df.to_dict(orient="records")

##############################################################################
# Callbacks para switch ######################################################
##############################################################################

@callback(
    Output("container-mediana", "style"),
    Input("switch-mediana", "checked"),
)
def input_mediana(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-baixa-performace-suspeita", "style"),
    Input("switch-baixa-performace-suspeita", "checked"),
)
def input_baixa_performace_suspeita(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-baixa-performace-indicativo", "style"),
    Input("switch-baixa-performace-indicativo", "checked"),
)
def input_baixa_performace_indicativo(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-erro-telemetria", "style"),
    Input("switch-erro-telemetria", "checked"),
)
def input_erro_telemetria(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-maior", "style"),
    Input("switch-kml-maior", "checked"),
)
def input_kml_maior(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-menor", "style"),
    Input("switch-kml-menor", "checked"),
)
def input_kml_menor(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        dcc.Store(id="dash-monitoramento-por-linha-store"),
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
                                                    html.Strong("Regras de Monitoramento da Frota"),
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
                                                    dbc.Label("Periodo (Dias)"),
                                                    dbc.Input(
                                                        id="input-periodo-dias-monitoramento-regra",
                                                        type="number",
                                                        placeholder="km/L",
                                                        value=5,
                                                        step=1,
                                                        min=1,
                                                        max=10,
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
                                                        id="input-modelos-monitoramento-regra",
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
                                                    dbc.Label("Linha"),
                                                    dcc.Dropdown(
                                                        id="input-select-linhas-monitoramento-regra",
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
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Quantidade de viagens por dia"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="input-quantidade-de-viagens-monitoramento-regra",
                                                                type="number",
                                                                placeholder="km/L",
                                                                value=5,
                                                                step=1,
                                                                min=1,
                                                                max=10,
                                                            ),
                                                        ]
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
                                                        id="input-select-dia-linha-combustivel-regra",
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
                                                className="dash-bootstrap h-100",
                                            ),
                                        ],
                                        className="h-100",
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card([
                                        dmc.Switch(
                                            id="switch-kml-menor",
                                            label="Excluir km/L menor que",
                                            checked=False
                                        ),
                                        dmc.Space(h=10),
                                        html.Div(
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id="input-excluir-km-l-menor-que-monitoramento-regra",
                                                    type="number",
                                                    min=0,
                                                    step=0.1,
                                                    value=1,
                                                ),
                                                dbc.InputGroupText("km/L")
                                            ]),
                                            id="container-kml-menor",
                                            style={"display": "none", "marginTop": "10px"}
                                        )
                                    ], body=True),
                                    md=3
                                ),

                                # Coluna MAIOR QUE
                                dbc.Col(
                                    dbc.Card([
                                        dmc.Switch(
                                            id="switch-kml-maior",
                                            label="Excluir km/L maior que",
                                            checked=False
                                        ),
                                        dmc.Space(h=10),
                                        html.Div(
                                            dbc.InputGroup([
                                                dbc.Input(
                                                    id="input-excluir-km-l-maior-que-monitoramento-regra",
                                                    type="number",
                                                    min=0,
                                                    step=0.1,
                                                    value=1,
                                                ),
                                                dbc.InputGroupText("km/L")
                                            ]),
                                            id="container-kml-maior",
                                            style={"display": "none", "marginTop": "10px"}
                                        )
                                    ], body=True),
                                    md=3
                                ),
                                dmc.Space(h=10),

                                dbc.Col(
                                    dbc.Card([
                                        html.Div([
                                            dmc.Switch(id="switch-mediana", label="Viagens abaixo da mediana ", checked=False),
                                            dmc.Space(h=10),
                                            html.Div(
                                                dbc.InputGroup([
                                                    dbc.Input(
                                                        id="select-mediana",
                                                        type="number",
                                                        placeholder="Digite a porcentagem",
                                                        min=10,
                                                        max=100,
                                                        step=1,
                                                        value=10,
                                                    ),
                                                    dbc.InputGroupText("%")
                                                ]),
                                                id="container-mediana",
                                                style={"display": "none", "marginTop": "10px"}
                                            )
                                        ])
                                    ], body=True),
                                    md=3
                                ),

                                dbc.Col(
                                    dbc.Card([
                                        html.Div([
                                            dmc.Switch(id="switch-baixa-performace-suspeita", label="Viagens suspeita baixa performance", checked=False),
                                            dmc.Space(h=10),
                                            html.Div(
                                                dbc.InputGroup([
                                                    dbc.Input(
                                                        id="select-baixa-performace-suspeita",
                                                        type="number",
                                                        placeholder="Digite a porcentagem",
                                                        min=10,
                                                        max=100,
                                                        step=1,
                                                        value=10,
                                                    ),
                                                    dbc.InputGroupText("%")
                                                ]),
                                                id="container-baixa-performace-suspeita",
                                                style={"display": "none", "marginTop": "10px"}
                                            )
                                        ])
                                    ], body=True),
                                    md=3
                                ),

                                dbc.Col(
                                    dbc.Card([
                                        html.Div([
                                            dmc.Switch(id="switch-baixa-performace-indicativo", label="Viagens indicativo baixa performance", checked=False),
                                            dmc.Space(h=10),
                                            html.Div(
                                                dbc.InputGroup([
                                                    dbc.Input(
                                                        id="select-baixa-performace-indicativo",
                                                        type="number",
                                                        placeholder="Digite a porcentagem",
                                                        min=10,
                                                        max=100,
                                                        step=1,
                                                        value=10,
                                                    ),
                                                    dbc.InputGroupText("%")
                                                ]),
                                                id="container-baixa-performace-indicativo",
                                                style={"display": "none", "marginTop": "10px"}
                                            )
                                        ])
                                    ], body=True),
                                    md=3
                                ),

                                dbc.Col(
                                    dbc.Card([
                                        html.Div([
                                            dmc.Switch(id="switch-erro-telemetria", label="Viagens suspeita erro de telemetria", checked=False),
                                            dmc.Space(h=10),
                                            html.Div(
                                                dbc.InputGroup([
                                                    dbc.Input(
                                                        id="select-erro-telemetria",
                                                        type="number",
                                                        placeholder="Digite a porcentagem",
                                                        min=10,
                                                        max=100,
                                                        step=1,
                                                        value=10,
                                                    ),
                                                    dbc.InputGroupText("%")
                                                ]),
                                                id="container-erro-telemetria",
                                                style={"display": "none", "marginTop": "10px"}
                                            )
                                        ])
                                    ], body=True),
                                    md=3
                                ),
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-regras-viagens-monitoramento",
            columnDefs=monitoramento_tabela.tbl_perc_viagens_monitoramento,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=20),
    ]
)

dash.register_page(__name__, name="Regras de monitoramento", path="/regras-monitoramento")
