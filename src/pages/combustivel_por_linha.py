#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o combustível utilizado por determinada linha

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

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
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_linhas_possui_info_combustivel, get_modelos_veiculos_com_combustivel

# Imports específicos
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
comb_por_linha_service = CombustivelPorLinhaService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")

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
# Callbacks para os gráficos #################################################
##############################################################################


@callback(
    Output("dash-combustivel-por-linha-store", "data"),
    [
        Input("input-intervalo-datas-combustivel-linha", "value"),
        Input("input-select-modelos-combustivel-linha", "value"),
        Input("input-select-linhas-combustivel", "value"),
        Input("input-select-sentido-da-linha-combustivel", "value"),
        Input("input-select-dia-linha-combustivel", "value"),
        Input("input-linha-combustivel-remover-outliers-menor-que", "value"),
        Input("input-linha-combustivel-remover-outliers-maior-que", "value"),
    ],
)
def computa_dados_combustivel_por_linha(
    datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
):
    # Valida input
    print("Resultado de input válido:", input_valido(datas, lista_modelos, linha, lista_sentido, lista_dias_semana))
    if not input_valido(datas, lista_modelos, linha, lista_sentido, lista_dias_semana):
        return {
            "valid": False,
            "dados": [],
        }

    if limite_km_l_menor is None or limite_km_l_menor < 0:
        limite_km_l_menor = 0

    if limite_km_l_maior is None or limite_km_l_maior < 0:
        limite_km_l_maior = 10

    # Obtém os dados
    df = comb_por_linha_service.get_combustivel_por_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    )

    # Retorna os dados
    return {
        "valid": True,
        "dados": df.to_dict(orient="records"),
    }


@callback(
    [
        Output("indicador-quantidade-de-viagens-comb-linha", "children"),
        Output("indicador-quantidade-de-veiculos-diferentes-comb-linha", "children"),
        Output("indicador-quantidade-de-modelos-diferentes-comb-linha", "children"),
    ],
    Input("dash-combustivel-por-linha-store", "data"),
)
def atualiza_indicadores_combustivel_por_linha(payload_linhas):
    if not payload_linhas["valid"]:
        return ["", "", ""]

    # Obtém os dados
    df = pd.DataFrame(payload_linhas["dados"])

    # Verifica se o dataframe está vazio
    if df.empty:
        return ["0", "0", "0"]

    # Calcula os indicadores
    num_viagens = df.shape[0]
    num_veiculos = df["vec_num_id"].nunique()
    num_modelos = df["vec_model"].nunique()


    return [f"{num_viagens}", f"{num_veiculos}", f"{num_modelos}"]


@callback(
    Output("graph-combustivel-linha-por-hora", "figure"),
    Input("dash-combustivel-por-linha-store", "data"),
)
def plota_grafico_combustivel_linha_por_hora(payload_linhas):
    # Valida
    if not payload_linhas["valid"]:
        return go.Figure()

    # Obtém os dados
    df = pd.DataFrame(payload_linhas["dados"])

    # Verifica se o dataframe está vazio
    if df.empty:
        return go.Figure()

    # Prepara os dados para agrupa pelo período de análise (30 minutos é o padrão)
    df["rmtc_timestamp_inicio"] = pd.to_datetime(df["rmtc_timestamp_inicio"])
    df["time_bin"] = df["rmtc_timestamp_inicio"].dt.floor("30T")
    df["time_bin_only_time"] = df["time_bin"].dt.time
    # df_agg = df.groupby("time_bin_only_time")["km_por_litro"].agg(["mean", "std", "min", "max"]).reset_index()

    # Agrupa por modelo e período
    df_agg = (
        df.groupby(["time_bin_only_time", "vec_model"])["km_por_litro"].agg(["mean", "std", "min", "max"]).reset_index()
    )
    df_agg["time_bin_formatado"] = pd.to_datetime(df_agg["time_bin_only_time"].astype(str), format="%H:%M:%S")

    # Arredonda os valores
    df_agg["mean"] = df_agg["mean"].round(2)
    df_agg["std"] = df_agg["std"].round(2)
    df_agg["min"] = df_agg["min"].round(2)
    df_agg["max"] = df_agg["max"].round(2)

    # Gera o gráfico
    fig = combustivel_graficos.gerar_grafico_consumo_combustivel_por_linha(df_agg)
    return fig


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Combustível por Linha", path="/combustivel-linha")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        dcc.Store(id="dash-combustivel-por-linha-store"),
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
                                                    html.Strong("Combustível por Linha"),
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
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Data"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-combustivel-linha",
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
                                                        id="input-select-modelos-combustivel-linha",
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
                        dbc.Row(
                            [
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Linha"),
                                                    dcc.Dropdown(
                                                        id="input-select-linhas-combustivel",
                                                        options=[
                                                            {
                                                                "label": linha["LABEL"],
                                                                "value": linha["LABEL"],
                                                            }
                                                            for linha in lista_todas_linhas
                                                        ],
                                                        value="021",
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
                                                    dbc.Label("Sentido"),
                                                    dcc.Dropdown(
                                                        id="input-select-sentido-da-linha-combustivel",
                                                        options=[
                                                            {
                                                                "label": "IDA",
                                                                "value": "IDA",
                                                            },
                                                            {
                                                                "label": "VOLTA",
                                                                "value": "VOLTA",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["IDA", "VOLTA"],
                                                        placeholder="Selecione o sentido...",
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
                        dbc.Row(
                            [
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Dias"),
                                                    dbc.Checklist(
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
                                                        value=["SEG_SEX"],
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
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Excluir km/L menor que"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="input-linha-combustivel-remover-outliers-menor-que",
                                                                type="number",
                                                                placeholder="km/L",
                                                                value=1,
                                                                step=0.1,
                                                                min=0,
                                                            ),
                                                            dbc.InputGroupText("km/L"),
                                                        ]
                                                    ),
                                                ],
                                                className="dash-bootstrap h-100",
                                            ),
                                        ],
                                        className="h-100",
                                        body=True,
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Excluir km/L maior que"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="input-linha-combustivel-remover-outliers-maior-que",
                                                                type="number",
                                                                placeholder="km/L",
                                                                value=10,
                                                                step=0.1,
                                                                min=0,
                                                            ),
                                                            dbc.InputGroupText("km/L"),
                                                        ]
                                                    ),
                                                ],
                                                className="dash-bootstrap h-100",
                                            ),
                                        ],
                                        className="h-100",
                                        body=True,
                                    ),
                                    md=3,
                                ),
                            ]
                        ),
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
        # Grafico geral de combustível por linha
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Gráfico: Consumo de combustível por linha",
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
        dcc.Graph(id="graph-combustivel-linha-por-hora"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento de viagens nesta linha",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            # dbc.Col(gera_labels_inputs_veiculos("input-geral-combustivel-1"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-comb",
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
                                        dcc.Download(id="download-excel-tabela-combustivel-1"),
                                    ],
                                    style={"text-align": "right"},
                                ),
                                width="auto",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-combustivel",
            columnDefs=combustivel_linha_tabela.tbl_detalhamento_viagens_km_l,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:map", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Mapa da Linha",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            # dbc.Col(gera_labels_inputs_veiculos("input-geral-mapa-linha"), width=True),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        html.Div(id="mapa-linha-onibus"),
        dmc.Space(h=60),
    ]
)
