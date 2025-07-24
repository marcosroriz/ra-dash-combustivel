#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime, timedelta
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
from dash import html, dcc, callback, Input, Output
import dash


# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import callback_context

# Importar nossas constantes e funções utilitárias
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais

# Imports específicos
from modules.combustivel_por_linha.combustivel_por_linha_service import CombustivelPorLinhaService
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


# Cria o serviço
regra_service = RegrasService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")
lista_todas_linhas .insert(0, {"LABEL": "TODAS"})

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

##################################################################################
# LOADER #####################################################################
###################################################################################

##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    Output("tabela-regras-viagens-monitoramento", "rowData"),
    Output("indicador-quantidade-de-veiculos", "children"),
    [
        Input("input-periodo-dias-monitoramento-regra", "value"),
        Input("input-modelos-monitoramento-regra", "value"),
        Input("input-quantidade-de-motoristas", "value"),
        Input("input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("input-select-dia-linha-combustivel-regra", "value"),
        Input("select-mediana", "value"),
        Input("select-baixa-performace-indicativo", "value"),
        Input("select-erro-telemetria", "value"),
    ],
)
def atualiza_tabela_regra_viagens_monitoramento(
    data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem,
    indicativo_performace, erro_telemetria
):
    # Exibe overlay (inicial)
    # style_overlay = {"display": "block"}

    df = regra_service.get_estatistica_regras(
        data, modelos, motoristas,
        quantidade_de_viagens, dias_marcados, 
        mediana_viagem,
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
        Input("input-quantidade-de-motoristas", "value"),
        Input("input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("input-select-dia-linha-combustivel-regra", "value"),
        Input("select-mediana", "value"),
        Input("select-baixa-performace-indicativo", "value"),
        Input("select-erro-telemetria", "value"),
    ],
    prevent_initial_call=True
)
def salvar_regra_monitoramento(
    n_clicks, nome_regra,
    data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem, 
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
        nome_regra, data, modelos, motoristas,
        quantidade_de_viagens, dias_marcados, 
        mediana_viagem,
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


##############################################################################
# Labels #####################################################################
##############################################################################
def gera_labels_inputs(campo):
    @callback(
        Output(f"{campo}-labels", "children"),
        [
            Input("input-periodo-dias-monitoramento-regra", "value"),  # datas
            Input("input-modelos-monitoramento-regra", "value"),        # modelos
            Input("input-quantidade-de-motoristas", "value"), # Motoristas
            Input("input-quantidade-de-viagens-monitoramento-regra", "value"),  # qtd viagens
            Input("input-select-dia-linha-combustivel-regra", "value"),         # dias marcados
            Input("select-mediana", "value"),
            Input("select-baixa-performace-indicativo", "value"),
            Input("select-erro-telemetria", "value"),
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
        if datas:
            data_inicio = pd.to_datetime(datetime.now()- timedelta(days=datas)).strftime("%d/%m/%Y")
            data_fim = pd.to_datetime(datetime.now()).strftime("%d/%m/%Y")
            badges.append(dmc.Badge(f"{data_inicio} a {data_fim}", variant="outline"))

        # Modelos
        if modelos and "TODOS" not in modelos:
            for m in modelos:
                badges.append(dmc.Badge(f"Modelo: {m}", variant="dot"))
        else:
            badges.append(dmc.Badge("Todos os modelos", variant="outline"))

        # Outras métricas
        if motoristas:
            badges.append(dmc.Badge(f"Min. {motoristas} motoristas diferentes", variant="outline"))

         # Outras métricas
        if qtd_viagens:
            badges.append(dmc.Badge(f"Min. {qtd_viagens} viagens", variant="outline"))

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


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
        # dmc.Overlay(...)  # Overlay comentado

        dbc.Row(
            [
                dbc.Col(
                    [
                        # Cabeçalho e Título
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
                                                [html.Strong("Regras de Monitoramento da Frota")],
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

                        # Nome da Regra e Período
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Nome da Regra de Monitoramneto"),
                                                dbc.Input(
                                                    id="input-nome-regra-monitoramento",
                                                    type="text",
                                                    placeholder="Digite algo...",
                                                    value="",
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Período de Monitoramento (últimos X dias)"),
                                                dbc.InputGroup(
                                                    [
                                                        dbc.Input(
                                                            id="input-periodo-dias-monitoramento-regra",
                                                            type="number",
                                                            placeholder="Dias",
                                                            value=30,
                                                            step=1,
                                                            min=1,
                                                        ),
                                                        dbc.InputGroupText("dias"),
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
                                                dbc.Label("Modelos"),
                                                dcc.Dropdown(
                                                    id="input-modelos-monitoramento-regra",
                                                    multi=True,
                                                    options=[
                                                        {"label": modelo["LABEL"], "value": modelo["LABEL"]}
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

                        # Linha e Viagens
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
                                                            id="input-quantidade-de-motoristas",
                                                            type="number",
                                                            placeholder="Viagens",
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
                                                            id="input-quantidade-de-viagens-monitoramento-regra",
                                                            type="number",
                                                            placeholder="Viagens",
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

                        # Filtros e Switches
                        dbc.Row(
                            [
                                # Dias
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
                                
                                # Mediana
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="switch-mediana",
                                                    label="% Mínima de Viagens Abaixo da Mediana ",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="select-mediana",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="container-mediana",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                # Baixa performance indicativo
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="switch-baixa-performace-indicativo",
                                                    label="% Mínima de Viagens com Supeita ou Baixa Performance",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="select-baixa-performace-indicativo",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=0,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="container-baixa-performace-indicativo",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),

                                # Erro telemetria
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="switch-erro-telemetria",
                                                    label="% Mínima de Viagens com Erro de Telemetria",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="select-erro-telemetria",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="container-erro-telemetria",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                # OS automática
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            dmc.Switch(
                                                id="switch-os-automatica",
                                                label="Criar OS automática",
                                                checked=False,
                                            ),
                                        ),
                                        body=True,
                                        style={
                                            "backgroundColor": "#F6B64F",
                                            "color": "black",
                                            "borderRadius": "8px",
                                            "boxShadow": "2px 2px 8px rgba(0,0,0,0.2)",
                                        },
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

        # Botão Criar Regra
        dbc.Col(
            html.Div(
                [
                    html.Button(
                        "Cria regra",
                        id="btn-criar-regra-monitoramento",
                        n_clicks=0,
                        style={
                            "background-color": "#007bff",
                            "color": "white",
                            "border": "none",
                            "padding": "10px 20px",
                            "border-radius": "8px",
                            "cursor": "pointer",
                            "font-size": "16px",
                            "font-weight": "bold",
                        },
                    ),
                    html.Div(id="mensagem-sucesso", style={"marginTop": "10px", "fontWeight": "bold"}),
                ],
                style={"text-align": "center"},
            ),
            width="auto",
        ),

        dmc.Space(h=20),

        # Indicador de veículos
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-quantidade-de-veiculos", order=2),
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
                dbc.Col(gera_labels_inputs("labels-regra-service"), width=True),
            ]
        ),

        dmc.Space(h=20),

        # Tabela de regras
        dag.AgGrid(
            id="tabela-regras-viagens-monitoramento",
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

dash.register_page(__name__, name="Regras de monitoramento", path="/regras-monitoramento")
