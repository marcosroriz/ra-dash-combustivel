#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado os indicadores de gasto de combustível, bem como a evolução do gasto

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
from modules.entities_utils import *

# Imports específicos
from modules.home.home_service import HomeService
import modules.home.graficos as home_graficos
from modules.monitoramento.monitoramento_service import MonitoramentoService
import modules.monitoramento.tabela as monitoramento_tabela
import modules.monitoramento.graficos as monitoramento_graficos

from modules.combustivel_por_linha.combustivel_por_linha_service import CombustivelPorLinhaService
import modules.combustivel_por_linha.graficos as combustivel_graficos
import modules.combustivel_por_linha.tabela as combustivel_linha_tabela

from modules.regras.regras_service import RegrasService
from modules.preco_combustivel_api import get_preco_diesel

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
home_service = HomeService(pgEngine)
monitoramento_service = MonitoramentoService(pgEngine)
regras_service = RegrasService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")
lista_todas_linhas.insert(0, {"LABEL": "TODAS"})

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

# Lista de regras padronizadas
# Preparando inputs
df_regras = get_regras_padronizadas(pgEngine)
lista_todas_regras = df_regras.to_dict(orient="records")

# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()


##############################################################################
# CALLBACKS ##################################################################
##############################################################################
# Callbacks para input
@callback(
    Output("input-nome-regra-padronizada", "value"),
    Input("input-nome-regra-padronizada", "value"),
    prevent_initial_call=True,
)
def filtra_todas_opcao(valor_selecionado):
    if valor_selecionado is None:
        return None
    return valor_selecionado


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


# @callback(
#     Output("input-select-veiculos-monitoramento", "options"),
#     [
#         Input("input-intervalo-datas-monitorameto", "value"),
#         Input("input-select-modelos-monitoramento", "value"),
#         Input("input-select-linhas-monitoramento", "value"),
#         Input("input-select-dia-linha-combustivel", "value"),
#         Input("input-excluir-km-l-menor-que-monitoramento", "value"),
#         Input("input-excluir-km-l-maior-que-monitoramento", "value"),
#     ],
# )
# def atualiza_veiculos_dia(dia, modelos, linha, dias_marcados, excluir_km_l_menor_que, excluir_km_l_maior_que):
#     if dia is None:
#         return []

#     df = monitoramento_service.get_veiculos_rodaram_no_dia(dia)

#     return [{"label": veiculo["label"], "value": veiculo["value"]} for veiculo in df.to_dict(orient="records")]


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


# @callback(
#     Output("tabela-perc-viagens-monitoramento", "rowData"),
#     [
#         Input("input-intervalo-datas-monitorameto", "value"),
#         Input("input-select-modelos-monitoramento", "value"),
#         Input("input-select-linhas-monitoramento", "value"),
#         Input("input-quantidade-de-viagens-monitoramento", "value"),
#         Input("input-select-dia-linha-combustivel", "value"),
#         Input("input-excluir-km-l-menor-que-monitoramento", "value"),
#         Input("input-excluir-km-l-maior-que-monitoramento", "value"),
#     ],
# )
# def atualiza_tabela_perc_viagens_monitoramento(
#     dia, modelos, linha, quantidade_de_viagens, dias_marcados, excluir_km_l_menor_que, excluir_km_l_maior_que
# ):
#     print("Datas: ", dia)
#     print("Modelos: ", modelos)
#     print("Linha: ", linha)
#     print("Quantidade de viagens: ", quantidade_de_viagens)
#     print("Dias marcados: ", dias_marcados)
#     print("Excluir km/L menor que: ", excluir_km_l_menor_que)
#     print("Excluir km/L maior que: ", excluir_km_l_maior_que)

#     df = monitoramento_service.get_estatistica_veiculos(dia, linha, dias_marcados)

#     return df.to_dict(orient="records")

##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


# Callback para o indicador de consumo médio de km/L
@callback(
    Output("indicador-consumo-km-l-visao-geral", "children"),
    [
        Input("input-intervalo-datas-visao-geral", "value"),
        Input("input-select-modelos-visao-geral", "value"),
        Input("input-select-linhas-monitoramento", "value"),
        Input("input-excluir-km-l-menor-que-visao-geral", "value"),
        Input("input-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_indicador_consumo_km_l_visao_geral(datas, lista_modelos, linha, km_l_min, km_l_max):
    # Valida input
    # if not input_valido(datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    #     return go.Figure()

    # Obtem os dados
    df_indicador = home_service.get_indicador_consumo_medio_km_l(datas, lista_modelos, linha, km_l_min, km_l_max)

    if df_indicador.empty:
        return "-"
    else:
        return str(round(df_indicador.iloc[0]["media_km_por_l"], 2)).replace(".", ",") + " km/L"


# Callback para o indicador de consumo médio de km/L
@callback(
    [
        Output("indicador-total-litros-excedente-visao-geral", "children"),
        Output("indicador-total-gasto-combustivel-excedente-visao-geral", "children"),
        Output("card-footer-preco-diesel", "children"),
    ],
    [
        Input("input-intervalo-datas-visao-geral", "value"),
        Input("input-select-modelos-visao-geral", "value"),
        Input("input-select-linhas-monitoramento", "value"),
        Input("input-excluir-km-l-menor-que-visao-geral", "value"),
        Input("input-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_indicador_total_consumo_excedente_visao_geral(datas, lista_modelos, linha, km_l_min, km_l_max):
    # Valida input
    # if not input_valido(datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    #     return go.Figure()

    # Obtem os dados
    df_indicador = home_service.get_indicador_consumo_litros_excedente(datas, lista_modelos, linha, km_l_min, km_l_max)

    if df_indicador.empty:
        return "", "", ""
    else:
        return (
            f"{int(df_indicador.iloc[0]["litros_excedentes"]):,} L".replace(",", "."),
            f"R$ {int(preco_diesel * df_indicador.iloc[0]["litros_excedentes"]):,}".replace(",", "."),
            f"Total gasto com combustível excedente (R$) / Considerando o litro do Diesel = R$ {preco_diesel:,.2f}".replace(".", ",")
        )


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("graph-pizza-sintese-viagens-geral", "figure"),
    [
        Input("input-intervalo-datas-visao-geral", "value"),
        Input("input-select-modelos-visao-geral", "value"),
        Input("input-select-linhas-monitoramento", "value"),
        Input("input-excluir-km-l-menor-que-visao-geral", "value"),
        Input("input-excluir-km-l-maior-que-visao-geral", "value"),
        Input("store-window-size", "data"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, lista_modelos, linha, km_l_min, km_l_max, metadata_browser):
    # Valida input
    # if not input_valido(datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    #     return go.Figure()

    print("PARAMETROS:")
    print("Datas: ", datas)
    print("Modelos: ", lista_modelos)
    print("Linha: ", linha)
    print("km/L mínimo: ", km_l_min)
    print("km/L máximo: ", km_l_max)
    print("Metadata browser: ", metadata_browser)

    # Obtem os dados
    df = home_service.get_sinteze_status_viagens(datas, lista_modelos, linha, km_l_min, km_l_max)

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
    fig = home_graficos.gerar_grafico_pizza_sinteze_geral(df, labels, values, metadata_browser)
    return fig


# Callback para grafico de total de Veiculos por modelo
@callback(
    Output("grafico-veiculos-modelo-regra", "figure"),
    Input("input-nome-regra-padronizada", "value"),
    prevent_initial_call=True,
)
def grafico_veiculos_por_modelo_regra(valor_selecionado):

    regra = regras_service.get_regras([valor_selecionado])

    if regra.empty:
        return go.Figure()

    regra_dict = regra.to_dict(orient="records")

    for regra in regra_dict:
        kwargs = {
            "data": int(regra.get("periodo")),
            "modelos": regra.get("modelos"),
            "numero_de_motoristas": regra.get("motoristas"),
            "quantidade_de_viagens": regra.get("qtd_viagens"),
            "dias_marcados": regra.get("dias_analise"),
            "mediana_viagem": regra.get("mediana_viagem"),
            "indicativo_performace": regra.get("indicativo_performace"),
            "erro_telemetria": regra.get("erro_telemetria"),
        }
        result = regras_service.get_estatistica_regras(**kwargs)

    fig = monitoramento_graficos.plot_veiculos_por_modelo(result)

    return fig


# Callback para gráfico de combustível por veículo ao longo do dia
@callback(
    [
        Output("graph-monitoramento-viagens-veiculo", "figure"),
        Output("tabela-monitoramento-viagens-veiculo", "rowData"),
    ],
    [
        Input("input-select-veiculos-monitoramento", "value"),
        Input("input-select-detalhamento-monitoramento-grafico-viagens", "value"),
    ],
    State("input-intervalo-datas-monitorameto", "value"),
)
def atualiza_grafico_monitoramento_viagens_veiculo(veiculo, opcoes_detalhamento, dia):
    if veiculo is None or veiculo == "" or dia is None:
        return go.Figure(), []

    # Pega as viagens do veículo
    df = monitoramento_service.get_viagens_do_veiculo(dia, veiculo)

    # Gera o gráfico
    fig = monitoramento_graficos.gerar_grafico_monitoramento_viagens_veiculo(df, opcoes_detalhamento)

    return fig, df.to_dict(orient="records")


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Home (Monitoramento)", path="/")

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
                                                    html.Strong("Monitoramento da Frota"),
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
                                                        id="input-intervalo-datas-visao-geral",
                                                        allowSingleDateInRange=True,
                                                        minDate=date(2025, 1, 1),
                                                        maxDate=date.today(),
                                                        type="range",
                                                        value=[date.today() - pd.DateOffset(days=30), date.today()],
                                                        # value=date.today() - pd.DateOffset(days=5),
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
                                                        id="input-select-modelos-visao-geral",
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
                                                        id="input-select-linhas-monitoramento",
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
                                                                id="input-excluir-km-l-menor-que-visao-geral",
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
                                                                id="input-excluir-km-l-maior-que-visao-geral",
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
                                                                id="indicador-consumo-km-l-visao-geral",
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
                                                                id="indicador-total-litros-excedente-visao-geral",
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
                                                                id="indicador-total-gasto-combustivel-excedente-visao-geral",
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
                                                    id="card-footer-preco-diesel",
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
                    dcc.Graph(id="graph-pizza-sintese-viagens-geral"),
                    md=6,
                ),
            ]
        ),
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
            id="tabela-perc-viagens-monitoramento",
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
        # Detalhamaento por Veículo
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:bus-wrench", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento por veículo ",
                                className="align-self-center",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Veículo"),
                                    dcc.Dropdown(
                                        id="input-select-veiculos-monitoramento",
                                        options=[],
                                        placeholder="Veículo",
                                        value="",
                                    ),
                                ],
                                className="dash-bootstrap",
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
                                    dbc.Label("Anotações"),
                                    dbc.RadioItems(
                                        id="input-select-detalhamento-monitoramento-grafico-viagens",
                                        options=[
                                            {
                                                "label": "Padrão",
                                                "value": "PADRÃO",
                                            },
                                            {
                                                "label": "Motorista",
                                                "value": "MOTORISTA",
                                            },
                                            {
                                                "label": "Linha",
                                                "value": "LINHA",
                                            },
                                        ],
                                        value="PADRÃO",
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
            ],
            className="dash-bootstrap",
        ),
        dcc.Graph(id="graph-monitoramento-viagens-veiculo"),
        dag.AgGrid(
            id="tabela-monitoramento-viagens-veiculo",
            columnDefs=monitoramento_tabela.tbl_detalhamento_viagens_monitoramento,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        html.Div(id="custom-component-dmc-btn-value-changed"),
        # dag.AgGrid(
        #     id="tabela-combustivel",
        #     dangerously_allow_code=True,
        #     columnDefs=column_defs,
        #     rowData=data,
        #     defaultColDef={"filter": True, "floatingFilter": True},
        #     columnSize="autoSize",
        #     dashGridOptions={
        #         "localeText": locale_utils.AG_GRID_LOCALE_BR,
        #     },
        #     style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        # ),
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
        dmc.Space(h=20),
        # Campo de busca
        dbc.Row(
            [
                html.H2("Regras Padronizadas"),
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Regra de Monitoramento"),
                                    dcc.Dropdown(
                                        id="input-nome-regra-padronizada",
                                        options=[
                                            {
                                                "label": regra["LABEL"],
                                                "value": regra["LABEL"],
                                            }
                                            for regra in lista_todas_regras
                                        ],
                                        placeholder="Selecione a regra...",
                                        value=None,
                                        multi=False,
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        body=True,
                    ),
                    md=12,
                ),
                dmc.Space(h=20),
                html.Div([html.H2("Quantidade de Veiculos por Modelo"), dcc.Graph(id="grafico-veiculos-modelo-regra")]),
            ]
        ),
    ]
)
