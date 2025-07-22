#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime, timedelta
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
import modules.regras.tabela as regras_tabela
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

##################################################################################
# LOADER #####################################################################
###################################################################################


##############################################################################
# Callbacks para dados ######################################################
##############################################################################


@callback(
    Output("tabela-de-regras-existentes", "rowData"),
    [
        Input("input-nome-regra-existentes", "value"),
    ],
)
def atualiza_tabela_regra_existentes(
    nome
):
    # Exibe overlay (inicial)

    df = regra_service.get_regras()


    return df.to_dict(orient="records")


##############################################################################
# Callbacks para switch ######################################################
##############################################################################


##############################################################################
# Labels #####################################################################
##############################################################################


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # # Cabeçalho
        # dmc.Overlay(
        #     dmc.Loader(size="xl", color="blue", type="ring"),
        #     id="overlay-tabela-monitoramento",
        #     blur=3,
        #     opacity=0.5,
        #     zIndex=9999,
        #     fixed=True,
        #     center=True,
        #     style={
        #         "display": "block",  # Mostrar overlay
        #         "backgroundColor": "rgba(0, 0, 0, 0.3)",  # Fundo semi-transparente escuro para destacar o loader
        #         "width": "100vw",    # Cobrir toda a largura da viewport
        #         "height": "100vh",   # Cobrir toda a altura da viewport
        #         "position": "fixed", # Fixar overlay na tela toda
        #         "top": 0,
        #         "left": 0,
        #     },
        # ),
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
                                                    html.Strong("Regras Existentes de Monitoramento da Frota"),
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
                                                        id="input-nome-regra-existentes",
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
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=10),
        dmc.Title("Regras Existentes", order=3), 
        dmc.Space(h=20),
            dag.AgGrid(
                id="tabela-de-regras-existentes",
                columnDefs=regras_tabela.tbl_regras_monitoramento,
                rowData=[],
                defaultColDef={"filter": True, "floatingFilter": True},
                columnSize="autoSize",
                dashGridOptions={
                    "localeText": locale_utils.AG_GRID_LOCALE_BR,
                },
                # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
                style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        
    ]
)

dash.register_page(__name__, name="Regras Existentes", path="/regras-existentes")
