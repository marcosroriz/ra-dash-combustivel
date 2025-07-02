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
from dash import callback_context

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
lista_todas_linhas .insert(0, {"LABEL": "TODAS"})

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    Output("tabela-regras-viagens-monitoramento", "rowData"),
    Output("indicador-quantidade-de-veiculos", "children"),
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
    data, modelos, linha,
    quantidade_de_viagens, dias_marcados, 
    excluir_km_l_menor_que, excluir_km_l_maior_que,
    mediana_viagem, suspeita_performace,
    indicativo_performace, erro_telemetria
):

    df = regra_service.get_estatistica_veiculos(
        data, modelos, linha,
        quantidade_de_viagens, dias_marcados, 
        excluir_km_l_menor_que, excluir_km_l_maior_que,
        mediana_viagem, suspeita_performace,
        indicativo_performace, erro_telemetria
    )

    #indicador de quantidade de veiculo
    quantidade_veiculo = df['vec_num_id'].count()

    return df.to_dict(orient="records"), quantidade_veiculo

@callback(
        Output("mensagem-sucesso", "children"),
    [
        Input("btn-criar-regra-monitoramento", "n_clicks"),
        Input("input-nome-regra-monitoramento", "value"),
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
    prevent_initial_call=True
)
def salvar_regra_monitoramento(
    n_clicks, nome_regra,
    data, modelos, linha,
    quantidade_de_viagens, dias_marcados, 
    excluir_km_l_menor_que, excluir_km_l_maior_que,
    mediana_viagem, suspeita_performace,
    indicativo_performace, erro_telemetria
): 
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:  
        return dash.no_update  # Evita execução desnecessária
    
    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id != "btn-criar-regra-monitoramento":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0: 
        return dash.no_update

    regra_service.salvar_regra_monitoramento(
        nome_regra, data, modelos, linha,
        quantidade_de_viagens, dias_marcados, 
        excluir_km_l_menor_que, excluir_km_l_maior_que,
        mediana_viagem, suspeita_performace,
        indicativo_performace, erro_telemetria
    )
    return "✅ Regra salva com sucesso!"

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
                                                    dbc.Label("Nome da Regra de Monitoramneto"),
                                                    dbc.Input(
                                                        id="input-nome-regra-monitoramento",
                                                        type="text",  # Alterado de "number" para "text"
                                                        placeholder="Digite algo...",
                                                        value="",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ), 
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Data"),
                                                    dmc.DatePicker(
                                                        id="input-periodo-dias-monitoramento-regra",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2025, 1, 1),
                                                        maxDate=date.today(),
                                                        value=[
                                                            date(2025, 1, 1),
                                                            date.today(),
                                                        ],
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
                                                        multi=True,
                                                        value=["TODAS"],
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
                                                    dbc.Label("Quantidade minima de viagens"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="input-quantidade-de-viagens-monitoramento-regra",
                                                                type="number",
                                                                placeholder="km/L",
                                                                value=5,
                                                                step=1,
                                                                min=1,
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
                                                    min=1,
                                                    step=0.1,
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
                                                    min=1,
                                                    step=0.1,
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
                                                        min=0,
                                                        max=100,
                                                        step=1,
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
        dmc.Space(h=10),
        dbc.Row(
            [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-quantidade-de-veiculos", order=2),
                                        DashIconify(
                                            icon="mdi:bomb",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de veiculos"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},  # Adicione espaçamento inferior
                ),
            ],
            justify="center",
        ),
    ],
    style={"margin-top": "20px", "margin-bottom": "20px"},
    ),
        dmc.Space(h=10),
        dbc.Row(
                [
                # dbc.Col(gera_labels_inputs_veiculos("input-geral-combustivel-1"), width=True),
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Cria regra",
                                id="btn-criar-regra-monitoramento",
                                n_clicks=0,
                                style={
                                    "background-color": "#007bff",  # Azul
                                    "color": "white",
                                    "border": "none",
                                    "padding": "10px 20px",
                                    "border-radius": "8px",
                                    "cursor": "pointer",
                                    "font-size": "16px",
                                    "font-weight": "bold",
                                },
                            ),
                            
                        ],
                        style={"text-align": "right"},
                    ),
                    width="auto",
                ),
                html.Div(id="mensagem-sucesso", style={"color": "green"})
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
