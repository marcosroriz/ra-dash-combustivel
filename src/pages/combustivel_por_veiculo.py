#!/usr/bin/env python
# coding: utf-8

# Tela do dashboard com o detalhamento do consumo de um veículo

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd

# Importar bibliotecas para manipulação de URL
import ast
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State, callback_context
import plotly.graph_objects as go

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
from modules.entities_utils import (
    get_linhas_possui_info_combustivel,
    get_modelos_veiculos_com_combustivel,
    gerar_excel,
    get_veiculos_com_combustivel,
)

# Imports específicos
from modules.combustivel_por_veiculo.veiculo_service import VeiculoService
import modules.combustivel_por_veiculo.graficos  as veiculo_graficos

from modules.home.home_service import HomeService
import modules.home.graficos as home_graficos
import modules.home.tabela as home_tabela

# Preço do diesel
from modules.preco_combustivel_api import get_preco_diesel

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
veiculo_service = VeiculoService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")
lista_todas_linhas.insert(0, {"LABEL": "TODAS"})

# Veículos
df_veiculos = get_veiculos_com_combustivel(pgEngine)
lista_todos_veiculos = df_veiculos.to_dict(orient="records")

# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################


# Função auxiliar para transformar string '[%27A%27,%20%27B%27]' → ['A', 'B']
def parse_list_param_pag_veiculo(param):
    if param:
        try:
            return ast.literal_eval(param)
        except:
            return []
    return []


# Preenche os dados via URL
@callback(
    Output("pag-veiculo-input-select-veiculo-visao-veiculo", "value"),
    Output("pag-veiculo-input-intervalo-datas-visao-veiculo", "value"),
    Output("pag-veiculo-input-select-linhas-veiculo", "value"),
    Output("pag-veiculo-input-excluir-km-l-menor-que-visao-veiculo", "value"),
    Output("pag-veiculo-input-excluir-km-l-maior-que-visao-veiculo", "value"),
    Input("url", "href"),
)
def cb_receber_campos_via_url_pag_veiculo(href):
    if not href or "/combustivel-por-veiculo" not in href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    # Pega os parâmetros
    vec_num_id = query_params.get("vec_num_id", ["50000"])[0]
    # Converte para int, se não for possível, retorna None
    if vec_num_id is not None:
        try:
            vec_num_id = str(vec_num_id)
        except ValueError:
            vec_num_id = None

    # Datas
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    datas = [query_params.get("data_inicio", ["2025-01-01"])[0], query_params.get("data_fim", [data_hoje])[0]]

    # Lista de linhas
    lista_linhas = parse_list_param_pag_veiculo(query_params.get("lista_linhas", [["TODAS"]])[0])

    # Velocidade
    km_l_min = int(query_params.get("km_l_min", [1])[0])
    km_l_max = int(query_params.get("km_l_max", [10])[0])

    return vec_num_id, datas, lista_linhas, km_l_min, km_l_max


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(datas, vec_num_id, lista_linha, km_l_min, km_l_max):
    if datas is None or not datas or None in datas or len(datas) != 2:
        return False

    if vec_num_id is None or str(vec_num_id) not in df_veiculos["LABEL"].unique():
        return False

    if lista_linha is None or not lista_linha or None in lista_linha:
        return False

    if km_l_min < 0 or km_l_min >= km_l_max or km_l_max >= 20:
        return False

    return True


##############################################################################
# Callbacks para o estado ####################################################
##############################################################################


@callback(
    Output("pag-veiculo-store-input-dados-veiculo", "data"),
    [
        Input("pag-veiculo-input-select-veiculo-visao-veiculo", "value"),
        Input("pag-veiculo-input-intervalo-datas-visao-veiculo", "value"),
        Input("pag-veiculo-input-select-linhas-veiculo", "value"),
        Input("pag-veiculo-input-excluir-km-l-menor-que-visao-veiculo", "value"),
        Input("pag-veiculo-input-excluir-km-l-maior-que-visao-veiculo", "value"),
    ],
)
def cb_sincroniza_input_veiculo_store(
    id_veiculo,
    datas=None,
    lista_linhas=["TODAS"],
    km_l_min=1,
    km_l_max=10,
):
    # Input padrão
    input_dict = {
        "valido": False,
        "id_veiculo": id_veiculo,
        "datas": datas,
        "lista_linhas": lista_linhas,
        "km_l_min": km_l_min,
        "km_l_max": km_l_max,
    }

    # Validação dos inputs
    if input_valido(datas, id_veiculo, lista_linhas, km_l_min, km_l_max):
        input_dict["valido"] = True
    else:
        input_dict["valido"] = False

    return input_dict


def formata_float_para_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################



# Callback para o indicador de consumo médio de km/L
@callback(
    Output("pag-veiculo-indicador-consumo-km-l-visao-veiculo", "children"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
)
def cb_pag_veiculo_indicador_consumo_km_l_visao_veiculo(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return ""

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]


    # Obtem os dados
    df_indicador = veiculo_service.get_indicador_consumo_medio_km_l(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    if df_indicador.empty:
        return ""
    else:
        return str(round(df_indicador.iloc[0]["media_km_por_l"], 2)).replace(".", ",") + " km/L"


# Callback para o indicador de consumo médio de km/L
@callback(
    [
        Output("pag-veiculo-indicador-total-litros-excedente-visao-veiculo", "children"),
        Output("pag-veiculo-indicador-total-gasto-combustivel-excedente-visao-veiculo", "children"),
        Output("pag-veiculo-card-footer-preco-diesel", "children"),
    ],
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
)
def cb_pag_veiculo_indicador_total_consumo_excedente_visao_veiculo(data):
    if not data or not data["valido"]:
        return ""

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    # Obtem os dados
    df_indicador = veiculo_service.get_indicador_consumo_litros_excedente(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    if df_indicador.empty:
        return "", "", ""
    else:
        return (
            f"{int(df_indicador.iloc[0]["litros_excedentes"]):,} L".replace(",", "."),
            f"R$ {int(preco_diesel * df_indicador.iloc[0]["litros_excedentes"]):,}".replace(",", "."),
            f"Total gasto com combustível excedente (R$), considerando o litro do Diesel = R$ {preco_diesel:,.2f}".replace(
                ".", ","
            ),
        )

##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("pag-veiculo-graph-pizza-sintese-viagens-veiculo", "figure"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
    Input("store-window-size", "data"),
)
def cb_plota_grafico_pizza_sintese_veiculo(data, metadata_browser):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    df = veiculo_service.get_sinteze_status_viagens(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    # Prepara os dados para o gráfico
    labels = [
        "NORMAL",
        "SUSPEITA BAIXA PERFORMANCE (<= 1.0 STD)",
        "BAIXA PERFORMANCE (<= 1.5 STD)",
        "BAIXA PERFOMANCE (<= 2 STD)",
        "ERRO TELEMETRIA (>= 2.0 STD)",
    ]
    values = []
    for l in labels:
        if l in df["analise_status_90_dias"].values:
            values.append(df[df["analise_status_90_dias"] == l]["total_viagens"].values[0])
        else:
            values.append(0)

    # Gera o gráfico
    fig = veiculo_graficos.gerar_grafico_pizza_sinteze_veiculo(df, labels, values, metadata_browser)
    return fig


# Callback para o grafico de historico de viagens
@callback(
    Output("pag-veiculo-graph-timeline-consumo-veiculo", "figure"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
    Input("store-window-size", "data"),
)
def cb_plota_grafico_timeline_consumo_veiculo(data, metadata_browser):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    df = veiculo_service.get_historico_viagens(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    # Gera o gráfico
    fig = veiculo_graficos.gerar_grafico_timeline_consumo_veiculo(df, metadata_browser)
    return fig


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Veículo", path="/combustivel-por-veiculo")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="pag-veiculo-store-input-dados-veiculo"),
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
                                            DashIconify(icon="material-symbols:bus-alert", width=45),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Consumo do \u00a0",
                                                    html.Strong("Veículo"),
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
                                                    dbc.Label("Data (intervalo de análise)"),
                                                    dmc.DatePicker(
                                                        id="pag-veiculo-input-intervalo-datas-visao-veiculo",
                                                        allowSingleDateInRange=True,
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
                                                    dbc.Label("Veículo"),
                                                    dcc.Dropdown(
                                                        id="pag-veiculo-input-select-veiculo-visao-veiculo",
                                                        options=[
                                                            {
                                                                "label": veiculo["LABEL"],
                                                                "value": veiculo["LABEL"],
                                                            }
                                                            for veiculo in lista_todos_veiculos
                                                        ],
                                                        value=["50000"],
                                                        placeholder="Selecione o veículo...",
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
                                                        id="pag-veiculo-input-select-linhas-veiculo",
                                                        multi=True,
                                                        options=[
                                                            {
                                                                "label": linha["LABEL"],
                                                                "value": linha["LABEL"],
                                                            }
                                                            for linha in lista_todas_linhas
                                                        ],
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
                                                    dbc.Label("Excluir km/L menor que"),
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-veiculo-input-excluir-km-l-menor-que-visao-veiculo",
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
                                                                id="pag-veiculo-input-excluir-km-l-maior-que-visao-veiculo",
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
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        DashIconify(icon="material-symbols:insights", width=45),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        html.H4("Indicadores", className="align-self-center"),
                                    ),
                                ]
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
                                                                id="pag-veiculo-indicador-consumo-km-l-visao-veiculo",
                                                                order=2,
                                                            ),
                                                            DashIconify(
                                                                icon="material-symbols:speed-outline-rounded",
                                                                width=48,
                                                                color="black",
                                                            ),
                                                        ],
                                                        justify="center",
                                                        mt="md",
                                                        mb="xs",
                                                    ),
                                                ),
                                                dbc.CardFooter(["Consumo médio (km/L)"]),
                                            ],
                                            class_name="card-box-shadow",
                                        ),
                                        md=6,
                                        className="mb-3 mb-md-0",
                                    ),
                                    dbc.Col(
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    dmc.Group(
                                                        [
                                                            dmc.Title(
                                                                id="pag-veiculo-indicador-total-litros-excedente-visao-veiculo",
                                                                order=2,
                                                            ),
                                                            DashIconify(
                                                                icon="bi:fuel-pump-fill",
                                                                width=48,
                                                                color="black",
                                                            ),
                                                        ],
                                                        justify="center",
                                                        mt="md",
                                                        mb="xs",
                                                    ),
                                                ),
                                                dbc.CardFooter(["Total de litros excedentes (≤ 2 STD)"]),
                                            ],
                                            class_name="card-box-shadow",
                                        ),
                                        md=6,
                                        className="mb-3 mb-md-0",
                                    ),
                                ]
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
                                                                id="pag-veiculo-indicador-total-gasto-combustivel-excedente-visao-veiculo",
                                                                order=2,
                                                            ),
                                                            DashIconify(
                                                                icon="emojione-monotone:money-with-wings",
                                                                width=48,
                                                                color="black",
                                                            ),
                                                        ],
                                                        justify="center",
                                                        mt="md",
                                                        mb="xs",
                                                    ),
                                                ),
                                                dbc.CardFooter(
                                                    ["Total gasto com combustível excedente (R$)"],
                                                    id="pag-veiculo-card-footer-preco-diesel",
                                                ),
                                            ],
                                            class_name="card-box-shadow",
                                        ),
                                        md=12,
                                        className="mb-3 mb-md-0",
                                    ),
                                ]
                            ),
                        ]
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(id="pag-veiculo-graph-pizza-sintese-viagens-veiculo"),
                    md=6,
                ),
            ]
        ),
        # Grafico geral de combustível por modelo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Linha do tempo do consumo de combustível do veículo",
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
        dcc.Graph(id="pag-veiculo-graph-timeline-consumo-veiculo"),
        dmc.Space(h=40),
    ]
)
