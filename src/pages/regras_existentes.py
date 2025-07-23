#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
# Importar bibliotecas do dash básicas e plotly
from dash import html, callback, Input, Output
import dash

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais

# Imports específicos
from modules.regras.regras_service import RegrasService
import modules.regras.tabela as regras_tabela



# Imports gerais
from modules.entities_utils import get_linhas_possui_info_combustivel, get_modelos_veiculos_com_combustivel


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


regra_service = RegrasService(pgEngine)

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

    df = regra_service.get_regras()

    return df.to_dict(orient="records")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
        dbc.Row(
            [
                dbc.Col(
                    [
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

                        # Campo de busca
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Nome da Regra de Monitoramento"),
                                                    dbc.Input(
                                                        id="input-nome-regra-existentes",
                                                        type="text",
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

        # Título e Espaçamento
        dmc.Space(h=10),
        dmc.Title("Regras Existentes", order=3),
        dmc.Space(h=20),

        # Tabela AG Grid
        dag.AgGrid(
            id="tabela-de-regras-existentes",
            columnDefs=regras_tabela.tbl_regras_monitoramento,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={
                "height": 400,
                "resize": "vertical",
                "overflow": "hidden",
            },
        ),
    ]
)


dash.register_page(__name__, name="Regras Existentes", path="/regras-existentes")
