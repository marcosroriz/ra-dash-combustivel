#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
from dash import html, dcc, callback, Input, Output
import dash
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import callback_context


# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify


# Importar nossas constantes e funções utilitárias
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais

# Imports específicos
import modules.visao_geral_frotas.tabelas as regras_tabela
from modules.visao_geral_frotas.visao_geral_service import RegrasServiceVisaoGeral
from modules.visao_geral_frotas.graficos import gera_grafico_regras_comb


from modules.visao_geral_frotas.entities_utils import get_regras, get_regra_where, calcular_proporcao_regras_modelos




##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


visão_regra_service = RegrasServiceVisaoGeral(pgEngine)
# Cria o serviço

df_regras = get_regras(pgEngine)
lista_todos_regras = df_regras.to_dict(orient="records")




##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    Output("tabela-regras-viagens-analise-performance-frota-regra", "rowData"),
    Output("indicador-veiculos-com-problemas-visao-geral-frota", "children"),
    Output("indicador-combustivel-excedente-total-visao-geral-frota", "children"),
    Output("indicador-combustivel-excedente-por-veiculo-visao-geral-frota", "children"),
    Output("graph-regras-modelo", "figure"),
    [
        Input("input-select-regra-visao-geral", "value"),
    ],
)

def atualiza_tabela_regra_viagens_monitoramento(regra):

    if not regra:
        return [], 0, 0, 0, go.Figure()
    
    df = visão_regra_service.get_estatistica_veiculos_analise_performance(regra)

    if df.empty:
        return [], 0, 0, 0, go.Figure()

    df['comb_excedente_l'] = df['comb_excedente_l'].astype(float)

    quantidade_veiculo = df['vec_num_id'].nunique()

    total_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].sum():,.2f}L"

    media_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].mean():,.2f}L"


    #######################################################
    df_veiculos_modelo = df[['vec_num_id']]
    
    df_proporcao = calcular_proporcao_regras_modelos(pgEngine, df_veiculos_modelo)
    print(df_proporcao)

    fig_regras_modelo = gera_grafico_regras_comb(df_proporcao)

    return df.to_dict(orient="records"), quantidade_veiculo, total_combustivel, media_combustivel, fig_regras_modelo

@callback(
    Output("tabela-regras-viagens-analise", "rowData"),
    [
        Input("input-select-regra-visao-geral", "value"),
    ],
)

def atualiza_tabela_regra(regra):

    if not regra:
        return []
    df_regra = get_regra_where(pgEngine, regra)

    
    return df_regra.to_dict(orient="records")

##############################################################################
# Callbacks para switch ######################################################
##############################################################################

@callback(
    Output("container-baixa-performace-suspeita-analise-performance-frota-regra", "style"),
    Input("switch-baixa-performace-suspeita-analise-performance", "checked"),
)
def input_baixa_performace_suspeita(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-maior-analise-performance-frota-regra", "style"),
    Input("switch-kml-maior-analise-performancer", "checked"),
)
def input_kml_maior(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-menor-analise-performance-frota-regra", "style"),
    Input("switch-kml-menor-analise-performance", "checked"),
)
def input_kml_menor(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
        # dmc.Overlay(...),  # Comentado

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
                                                [html.Strong("Visão geral da frota (interna)")],
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

                        # Filtros principais
                        dbc.Row(
                            [
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Selecione a regra:"),
                                                dcc.Dropdown(
                                                    id="input-select-regra-visao-geral",
                                                    options=[
                                                        {
                                                            "label": os["nome_regra"] + " | Últimos: " + os["periodo"] + " dias",
                                                            "value": os["id"],
                                                        }
                                                        for os in lista_todos_regras
                                                    ],
                                                    multi=True,
                                                    value=[],
                                                    placeholder="Selecione uma regra...",
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=12,
                                ),
                            ]
                        ),
                    ],
                ),
            ]
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Parâmetros da regra",
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
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-regras-viagens-analise",
            columnDefs=regras_tabela.tbl_regras_monitoramento,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "rowSelection": "multiple",
            },
            style={"height": 250, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Indicadores",
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
        dmc.Space(h=20),
        # Indicador de total
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-veiculos-com-problemas-visao-geral-frota", order=2),
                                        DashIconify(icon="mdi:bomb", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Veículos com problemas"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-combustivel-excedente-total-visao-geral-frota", order=2),
                                        DashIconify(icon="mdi:gas-station", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Combustível excedente (Total)"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-combustivel-excedente-por-veiculo-visao-geral-frota", order=2),
                                        DashIconify(icon="mdi:gas-station", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Combustível excedente (por veículo)"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
            ],
            justify="center",
        ),

        dmc.Space(h=20),
        dcc.Graph(id="graph-regras-modelo"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Veículos que entraram na regra",
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
        dmc.Space(h=20),
        # Tabela
        dag.AgGrid(
            id="tabela-regras-viagens-analise-performance-frota-regra",
            columnDefs=regras_tabela.tbl_regras_viagens_visao_geral_frota,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "rowSelection": "multiple",
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
    ],
    style={"margin-top": "20px", "margin-bottom": "20px"},
)


dash.register_page(__name__, name="Visão geral da frota", path="/visao-geral-da-frota")
