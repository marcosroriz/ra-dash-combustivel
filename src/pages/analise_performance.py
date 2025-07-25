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
from modules.combustivel_por_linha.combustivel_por_linha_service import CombustivelPorLinhaService
import modules.regras.tabela as regras_tabela
from modules.regras.regras_service import RegrasService

# Imports gerais
from modules.entities_utils import  get_modelos_veiculos_regras



##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


regra_service = RegrasService(pgEngine)
# Cria o serviço

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_regras(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})




##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    Output("tabela-regras-viagens-analise-performance", "rowData"),
    Output("indicador-quantidade-de-veiculos-analise-performance", "children"),
    [
        Input("input-periodo-dias-analise-performance", "value"),
        Input("input-modelos-analise-performance", "value"),
        Input("input-quantidade-de-motorista-analise-performance", "value"),
        Input("input-quantidade-de-viagens-analise-performance", "value"),
        Input("input-select-dia-linha-combustivel-regra", "value"),
        Input("select-mediana-analise-performance", "value"),
        Input("select-baixa-performace-indicativo-analise-performance", "value"),
        Input("select-erro-telemetria-analise-performance", "value"),
    ],
)
def atualiza_tabela_regra_viagens_monitoramento(
    data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem,
    indicativo_performace, erro_telemetria
):


    df = regra_service.get_estatistica_veiculos_analise_performance(
        data, modelos, motoristas,
        quantidade_de_viagens, dias_marcados, 
        mediana_viagem,indicativo_performace, erro_telemetria
    )

    #indicador de quantidade de veiculo
    quantidade_veiculo = df['vec_num_id'].count()

    return df.to_dict(orient="records"), quantidade_veiculo


##############################################################################
# Callbacks para switch ######################################################
##############################################################################

@callback(
    Output("container-mediana-analise-peformance", "style"),
    Input("switch-mediana-analise-performance", "checked"),
)
def input_mediana(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-baixa-performace-suspeita-analise-performance", "style"),
    Input("switch-baixa-performace-suspeita-analise-performance", "checked"),
)
def input_baixa_performace_suspeita(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-baixa-performace-indicativo-analise-performance", "style"),
    Input("switch-baixa-performace-indicativo-analise-performance", "checked"),
)
def input_baixa_performace_indicativo(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-erro-telemetria-analise-performance", "style"),
    Input("switch-erro-telemetria-analise-performance", "checked"),
)
def input_erro_telemetria(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-maior-analise-performance", "style"),
    Input("switch-kml-maior-analise-performancer", "checked"),
)
def input_kml_maior(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}

@callback(
    Output("container-kml-menor-analise-performance", "style"),
    Input("switch-kml-menor-analise-performance", "checked"),
)
def input_kml_menor(ativado):
    # Se ativado (True): display block; se desativado: none
    return {"display": "block"} if ativado else {"display": "none"}


##############################################################################
# Labels #####################################################################
##############################################################################
def gera_labels_inputs(campo):
    @callback(
        Output(f"{campo}-labels", "children"),
        [
            Input("input-periodo-dias-analise-performance", "value"),  # datas
            Input("input-modelos-analise-performance", "value"),        # modelos
            Input("input-quantidade-de-motorista-analise-performance", "value"), # linhas
            Input("input-quantidade-de-viagens-analise-performance", "value"),  # qtd viagens
            Input("input-select-dia-linha-combustivel-regra", "value"),         # dias marcados
            Input("select-mediana-analise-performance", "value"),
            Input("select-baixa-performace-indicativo-analise-performance", "value"),
            Input("select-erro-telemetria-analise-performance", "value"),
        ]
    )
    def atualiza_labels_inputs(
        datas, modelos, motoristas,
        qtd_viagens, dias_marcados,
        mediana, indicativo, erro
    ):
        badges = [
            dmc.Badge(
            "Filtro",
            color="gray",
            variant="outline",
            size="lg",
            style={"fontSize": 16, "padding": "6px 12px"}
        )
        ]

        # Datas
        if datas and datas[0] and datas[1]:
            data_inicio = pd.to_datetime(datas[0]).strftime("%d/%m/%Y")
            data_fim = pd.to_datetime(datas[1]).strftime("%d/%m/%Y")
            badges.append(dmc.Badge(f"{data_inicio} a {data_fim}", variant="outline"))
        # Modelos
        if modelos and "TODOS" not in modelos:
            for m in modelos:
                badges.append(dmc.Badge(f"Modelo: {m}", variant="dot"))
        else:
            badges.append(dmc.Badge("Todos os modelos", variant="outline"))


        # Outras métricas
        if qtd_viagens:
            badges.append(dmc.Badge(f"Min. {qtd_viagens} viagens", variant="outline"))

        if motoristas:
            badges.append(dmc.Badge(f"Min. {motoristas} motoristas", variant="outline"))

        if dias_marcados:
            badges.append(dmc.Badge(f"{dias_marcados}", variant="outline"))

        if mediana:
            badges.append(dmc.Badge(f"Abaixo da Mediana: {mediana}%", color="yellow", variant="outline"))

        if indicativo:
            badges.append(dmc.Badge(f"Indicativo Baixa Performance: {indicativo}%", color="yellow", variant="outline"))
        if erro:
            badges.append(dmc.Badge(f"Supeita de Erro Telemetria: {erro}%", color="pink", variant="outline"))

        return [dmc.Group(badges, gap="xs")]

    # Componente de saída
    return dmc.Group(id=f"{campo}-labels", children=[], gap="xs")


@callback(
    Output("input-modelos-analise-performance", "value"),
    Input("input-modelos-analise-performance", "value"),
)
def atualizar_modelos_selecao(valores_selecionados):
    if not valores_selecionados:
        # Nada selecionado -> assume "TODOS"
        return ["TODOS"]

    ctx = callback_context
    if not ctx.triggered:
        return valores_selecionados

    ultimo_valor = ctx.triggered[0]["value"]

    # Se "TODOS" foi selecionado junto com outros, deixa apenas "TODOS"
    if "TODOS" in valores_selecionados and len(valores_selecionados) > 1:
        if ultimo_valor == ["TODOS"]:
            return ["TODOS"]
        else:
            return [v for v in valores_selecionados if v != "TODOS"]

    # Se nada for selecionado, mantém vazio (não retorna "TODOS")
    return valores_selecionados


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
                                                [html.Strong("Analise de Performance")],
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
                                                dbc.Label("Período de Monitoramento"),
                                                dmc.DatePicker(
                                                    id="input-periodo-dias-analise-performance",
                                                    type="range",
                                                    allowSingleDateInRange=True,
                                                    minDate=date(2025, 1, 1),
                                                    maxDate=date.today(),
                                                    value=[date(2025, 1, 1), date.today()],
                                                    dropdownType="modal",
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),

                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Modelos"),
                                                dcc.Dropdown(
                                                    id="input-modelos-analise-performance",
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
                                        html.Div(
                                            [
                                                dbc.Label("Quantidade mínima de motoristas diferentes"),
                                                dbc.InputGroup(
                                                    [
                                                        dbc.Input(
                                                            id="input-quantidade-de-motorista-analise-performance",
                                                            type="number",
                                                            placeholder="digite um valor...",
                                                            value=3,
                                                            step=1,
                                                            min=1,
                                                        ),
                                                        dbc.InputGroupText("Motoristas"),
                                                    ]
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),

                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Quantidade mínima de viagens no período"),
                                                dbc.InputGroup(
                                                    [
                                                        dbc.Input(
                                                            id="input-quantidade-de-viagens-analise-performance",
                                                            type="number",
                                                            placeholder="digite um valor...",
                                                            value=5,
                                                            step=1,
                                                            min=1,
                                                        ),
                                                        dbc.InputGroupText("viagens"),
                                                    ]
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                            ]
                        ),

                        dmc.Space(h=10),

                        # Filtros adicionais
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Dias"),
                                                dbc.RadioItems(
                                                    id="input-select-dia-linha-combustivel-regra",
                                                    options=[
                                                        {"label": "Seg-Sexta", "value": "SEG_SEX"},
                                                        {"label": "Sabado", "value": "SABADO"},
                                                        {"label": "Domingo", "value": "DOMINGO"},
                                                        {"label": "Feriado", "value": "FERIADO"},
                                                    ],
                                                    value="SEG_SEX",
                                                    inline=True,
                                                ),
                                            ],
                                            className="dash-bootstrap h-100",
                                        ),
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
                                                    dmc.Switch(
                                                        id="switch-mediana-analise-performance",
                                                        label="% Mínima de Viagens Abaixo da Mediana",
                                                        checked=False,
                                                    ),
                                                    dmc.Space(h=10),
                                                    html.Div(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.Input(
                                                                    id="select-mediana-analise-performance",
                                                                    type="number",
                                                                    placeholder="Digite a porcentagem",
                                                                    min=10,
                                                                    max=100,
                                                                    step=1,
                                                                ),
                                                                dbc.InputGroupText("%"),
                                                            ]
                                                        ),
                                                        id="container-mediana-analise-peformance",
                                                        style={"display": "none", "marginTop": "10px"},
                                                    ),
                                                ]
                                            )
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dmc.Switch(
                                                        id="switch-baixa-performace-indicativo-analise-performance",
                                                        label="% Mínima de Viagens com Supeita ou Baixa Performance",
                                                        checked=False,
                                                    ),
                                                    dmc.Space(h=10),
                                                    html.Div(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.Input(
                                                                    id="select-baixa-performace-indicativo-analise-performance",
                                                                    type="number",
                                                                    placeholder="Digite a porcentagem",
                                                                    min=0,
                                                                    max=100,
                                                                    step=1,
                                                                ),
                                                                dbc.InputGroupText("%"),
                                                            ]
                                                        ),
                                                        id="container-baixa-performace-indicativo-analise-performance",
                                                        style={"display": "none", "marginTop": "10px"},
                                                    ),
                                                ]
                                            )
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
                                                    dmc.Switch(
                                                        id="switch-erro-telemetria-analise-performance",
                                                        label="% Mínima de Viagens com Erro de Telemetria",
                                                        checked=False,
                                                    ),
                                                    dmc.Space(h=10),
                                                    html.Div(
                                                        dbc.InputGroup(
                                                            [
                                                                dbc.Input(
                                                                    id="select-erro-telemetria-analise-performance",
                                                                    type="number",
                                                                    placeholder="Digite a porcentagem",
                                                                    min=10,
                                                                    max=100,
                                                                    step=1,
                                                                ),
                                                                dbc.InputGroupText("%"),
                                                            ]
                                                        ),
                                                        id="container-erro-telemetria-analise-performance",
                                                        style={"display": "none", "marginTop": "10px"},
                                                    ),
                                                ]
                                            )
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
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
                                        dmc.Title(id="indicador-quantidade-de-veiculos-analise-performance", order=2),
                                        DashIconify(icon="mdi:bomb", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de veiculos"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
            ],
            justify="center",
        ),

        dmc.Space(h=10),

        # Labels adicionais
        dbc.Row(
            [
                dbc.Col(gera_labels_inputs("labels-analise-performance"), width=True),
            ]
        ),

        dmc.Space(h=20),

        # Tabela
        dag.AgGrid(
            id="tabela-regras-viagens-analise-performance",
            columnDefs=regras_tabela.tbl_perc_viagens_monitoramento,
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


dash.register_page(__name__, name="Analise Performance/Consumo", path="/analise-performance-consumo")
