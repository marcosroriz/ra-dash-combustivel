#!/usr/bin/env python
# coding: utf-8

# Tela para apresentar relatório de uma regra para detecção de problemas de consumo


import plotly.express as px
import plotly.graph_objects as go


##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
import pandas as pd
from datetime import date, datetime, timedelta
import re

# Importar bibliotecas para manipulação de URL
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
from modules.entities_utils import get_regras_monitoramento_combustivel

# Imports específicos
from modules.regras.regras_service import RegrasService

# import modules.regras.graficos as regras_graficos
import modules.regras.tabela as regras_tabelas

# Preço do diesel
from modules.preco_combustivel_api import get_preco_diesel

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
regra_service = RegrasService(pgEngine)

# Obtem a lista de regras de monitoramento de OS
df_regras_monitoramento_comb = get_regras_monitoramento_combustivel(pgEngine)
lista_regras_monitoramento_comb = df_regras_monitoramento_comb.to_dict(orient="records")


# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################


# Converte para int, se não for possível, retorna None
def safe_int(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


# Preenche os dados via URL
@callback(
    Output("relatorio-input-select-regra-retrabalho", "value"),
    Output("relatorio-input-data-relatorio-regra-retrabalho", "value"),
    Input("url", "href"),
)
def cb_pag_rel_regra_callback_receber_campos_via_url(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_regra = safe_int(query_params.get("id_regra", [None])[0])
    data_relatorio = query_params.get("data_relatorio", [None])[0]

    # Verifica se a regra existe
    lista_id_regras = [regra["value"] for regra in lista_regras_monitoramento_comb]
    if id_regra is not None and id_regra not in lista_id_regras:
        id_regra = None
        data_relatorio = None

    if id_regra is not None and data_relatorio is None:
        df_ultima_data_regra = regra_service.get_ultima_data_regra(id_regra)
        if not df_ultima_data_regra.empty:
            data_relatorio = df_ultima_data_regra["ultimo_dia"].iloc[0]

    return id_regra, data_relatorio


# Sincroniza o store com os valores dos inputs
@callback(
    [
        Output("store-relatorio-relatorio-regra", "data"),
        Output("relatorio-card-input-select-regra-retrabalho", "style"),
        Output("relatorio-card-input-data-relatorio-regra-retrabalho", "style"),
        Output("relatorio-input-select-regra-retrabalho-error", "style"),
        Output("relatorio-input-data-relatorio-regra-retrabalho-error", "style"),
    ],
    Input("relatorio-input-select-regra-retrabalho", "value"),
    Input("relatorio-input-data-relatorio-regra-retrabalho", "value"),
    running=[(Output("loading-overlay-guia-relatorio-regra", "visible"), True, False)],
)
def cb_pag_rel_regra_sincroniza_input_store_relatorio_regra(id_regra, dia_execucao):
    # Flags para validação
    input_regra_valido = True
    input_data_valido = True

    # Store padrão
    store_payload = {"valido": False}

    # Validação muda a borda e também mostra campo de erro
    # Estilos das bordas dos inputs
    style_borda_ok = {
        "border": "2px solid #198754",  # verde bootstrap
    }
    style_borda_erro = {
        "border": "2px solid #dc3545",  # vermelho bootstrap
    }

    # Estilho das bordas dos inputs
    style_borda_input_regra = style_borda_erro
    style_borda_input_data = style_borda_erro

    # Estilos dos erros dos inputs
    style_campo_erro_visivel = {"display": "block"}
    style_campo_erro_oculto = {"display": "none"}
    style_campo_erro_input_regra = style_campo_erro_visivel
    style_campo_erro_input_data = style_campo_erro_visivel

    # Valida primeiro se há regra
    if id_regra:
        style_borda_input_regra = style_borda_ok
        style_campo_erro_input_regra = style_campo_erro_oculto
    else:
        input_regra_valido = False

    # Valida a data
    if dia_execucao and regra_service.existe_execucao_regra_no_dia(id_regra, dia_execucao):
        style_borda_input_data = style_borda_ok
        style_campo_erro_input_data = style_campo_erro_oculto
    else:
        input_data_valido = False

    if input_regra_valido and input_data_valido:
        # Pega os campos da regra
        df_regra = regra_service.get_regra_by_id(id_regra)
        dados_regra = df_regra.to_dict(orient="records")[0]

        id_regra = dados_regra["id"]
        nome_regra = dados_regra["nome_regra"]

        # Pega o resultado da regra
        df_resultado_regra = regra_service.get_resultado_regra(id_regra, dia_execucao)

        # Ação de visualização
        df_resultado_regra["acao"] = "🔍 Detalhar"

        # Atualiza o store
        store_payload = {
            "valido": input_regra_valido and input_data_valido and not df_resultado_regra.empty,
            "id_regra": id_regra,
            "nome_regra": nome_regra,
            "df_resultado_regra": df_resultado_regra.to_dict(orient="records"),
            "dados_regra": dados_regra,
        }

    return (
        store_payload,
        style_borda_input_regra,
        style_borda_input_data,
        style_campo_erro_input_regra,
        style_campo_erro_input_data,
    )


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


@callback(
    [
        Output("card-regra-nome", "children"),
        Output("card-regra-periodo-monitoramento", "children"),
        Output("card-regra-modelos", "children"),
        Output("card-regra-qtd-min-viagens", "children"),
        Output("card-regra-qtd-min-motoristas", "children"),
        Output("card-regra-dias-marcados", "children"),
        Output("card-regra-limite-mediana", "children"),
        Output("card-regra-limite-baixa-perfomance", "children"),
        Output("card-regra-limite-erro-telemetria", "children"),
        Output("card-regra-criar-os-automatica", "children"),
        Output("card-regra-alvos-email", "children"),
        Output("card-regra-alvos-whatsapp", "children"),
    ],
    Input("store-relatorio-relatorio-regra", "data"),
)
def cb_rel_regra_atualiza_dados_card_descricao(store_relatorio_regra):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not store_relatorio_regra or not store_relatorio_regra["valido"]:
        return [
            "🔍 Nome da regra: Não Informado",
            "🕒 Período de monitoramento: Não Informado",
            "🚗 Modelos: Não Informado",
            "🛣️ Mínimo de viagens: Não Informado",
            "👨‍✈️ Mínimo de motoristas: Não Informado",
            "📅 Dias marcados: Não Informado",
            "📉 % Viagens Abaixo da Mediana: Não Informado",
            "📉 % Viagens Baixa Perfomance: Não Informado",
            "📉 % Viagens com Erro de Telemetria: Não Informado",
            "🤖 Criar OS Automática: Não Informado",
            "📧 Alvos de E-mail: Não Informado",
            "📱 Alvos de WhatsApp: Não Informado",
        ]

    # Obtem os dados da regra
    dados_regra = store_relatorio_regra["dados_regra"]

    html_nome_regra = f"🔍 Nome da regra: {dados_regra['nome_regra']}"
    html_periodo_monitoramento = f"🕒 Período de monitoramento: {dados_regra['periodo']}"
    html_modelos = f"🚗 Modelos: {", ".join(dados_regra['modelos_veiculos'])}"
    html_min_viagens = f"🛣️ Mínimo de viagens: {dados_regra['qtd_min_motoristas']}"
    html_min_motoristas = f"👨‍✈️ Mínimo de motoristas: {dados_regra['qtd_min_viagens']}"
    html_dias_marcados = f"📅 Dias marcados: {dados_regra['dias_marcados']}"

    html_abaixo_mediana = ("📉 % Viagens Abaixo da Mediana ≥ 0%",)
    if dados_regra["limite_mediana"]:
        html_abaixo_mediana = f"📉 % Viagens Abaixo da Mediana ≥ {dados_regra['limite_mediana']}%"

    html_baixa_perfomance = ("📉 % Viagens Baixa Perfomance ≥ 0%",)
    if dados_regra["limite_baixa_perfomance"]:
        html_baixa_perfomance = f"📉 % Viagens Baixa Perfomance ≥ {dados_regra['limite_mediana']}%"

    html_erro_telemetria = ("📉 % Viagens com Erro de Telemetria ≥ 0%",)
    if dados_regra["limite_erro_telemetria"]:
        html_erro_telemetria = f"📉 % Viagens com Erro de Telemetria ≥ {dados_regra['limite_mediana']}%"

    html_criar_os_automatica = f"🤖 Criar OS Automática: ❌"
    if (
        dados_regra["criar_os_automatica"] == "TRUE"
        or dados_regra["criar_os_automatica"] == "True"
        or dados_regra["criar_os_automatica"] == True
    ):
        html_criar_os_automatica = f"🤖 Criar OS Automática: ✅"

    if dados_regra["target_email"]:
        email_destinos = []
        email_destinos.append(dados_regra["target_email_dest1"])
        email_destinos.append(dados_regra["target_email_dest2"])
        email_destinos.append(dados_regra["target_email_dest3"])
        email_destinos.append(dados_regra["target_email_dest4"])
        email_destinos.append(dados_regra["target_email_dest5"])

        html_email = html.Div([html.Span("📧 Alvos de email:"), html.Ul([html.Li(e) for e in email_destinos if e])])

    html_whatsapp = "📱 Alvos de WhatsApp: Não Informado"
    if dados_regra["target_wpp"]:
        wpp_destinos = []
        wpp_destinos.append(dados_regra["target_wpp_dest1"])
        wpp_destinos.append(dados_regra["target_wpp_dest2"])
        wpp_destinos.append(dados_regra["target_wpp_dest3"])
        wpp_destinos.append(dados_regra["target_wpp_dest4"])
        wpp_destinos.append(dados_regra["target_wpp_dest5"])

        html_whatsapp = html.Div([html.Span("📱 Alvos de WhatsApp:"), html.Ul([html.Li(w) for w in wpp_destinos if w])])

    return [
        html_nome_regra,
        html_periodo_monitoramento,
        html_modelos,
        html_min_viagens,
        html_min_motoristas,
        html_dias_marcados,
        html_abaixo_mediana,
        html_baixa_perfomance,
        html_erro_telemetria,
        html_criar_os_automatica,
        html_email,
        html_whatsapp,
    ]


@callback(
    [
        Output("card-relatorio-resultado-total-veiculos", "children"),
        Output("card-relatorio-resultado-media-km-por-litro", "children"),
        Output("card-relatorio-resultado-litros-excedentes", "children"),
        Output("card-relatorio-resultado-gasto-combustivel", "children"),
        # Output("card-relatorio-resultado-os", "children"),
    ],
    Input("store-relatorio-relatorio-regra", "data"),
)
def cb_rel_regra_atualiza_dados_card_resultado_regra_relatorio(store_relatorio_regra):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not store_relatorio_regra or not store_relatorio_regra["valido"]:
        return [
            "🚍 Total de veículos: Não Informado",
            "🕒 Média km/L dos veículos: Não Informado",
            "⛽ Litros Excedentes: Não Informado",
            "💸 Custo: Não Informado",
        ]

    # Obtem o resultado da regra
    df_resultado_regra = pd.DataFrame(store_relatorio_regra["df_resultado_regra"])

    # Obtem os dados do dataframe
    total_veiculos = df_resultado_regra["vec_num_id"].nunique()
    html_total_veiculos = html.Div([html.Span("🚍 Total de veículos: "), html.Strong(total_veiculos)])

    media_km_l = str(df_resultado_regra["media_km_por_litro"].round(2).values[0])
    html_media_km_l = html.Div([html.Span("🕒 Média km/L dos veículos: "), html.Strong(media_km_l.replace(".", ","),)])

    litros_excedentes = str(df_resultado_regra["litros_excedentes"].round(2).values[0])
    html_litros_excedentes = html.Div([html.Span("⛽ Litros Excedentes: "), html.Strong(litros_excedentes.replace(".", ","),)])

    custo_excedente = str(round(preco_diesel * float(litros_excedentes), 2))
    html_custo = html.Div([html.Span("💸 Custo: R$ "), html.Strong(custo_excedente.replace(".", ","),)])

    return [
        html_total_veiculos,
        html_media_km_l,
        html_litros_excedentes,
        html_custo,
    ]


##############################################################################
# Callbacks para a tabela ####################################################
##############################################################################


##############################################################################
# Callbacks para o botão de detalhamento #####################################
##############################################################################


##############################################################################
# Callbacks para o gráfico #####################################################
##############################################################################


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-relatorio-relatorio-regra"),
        # Loading
        dmc.LoadingOverlay(
            # visible=True,
            id="loading-overlay-guia-relatorio-regra",
            loaderProps={"size": "xl"},
            overlayProps={
                "radius": "lg",
                "blur": 2,
                "style": {
                    "top": 0,  # Start from the top of the viewport
                    "left": 0,  # Start from the left of the viewport
                    "width": "100vw",  # Cover the entire width of the viewport
                    "height": "100vh",  # Cover the entire height of the viewport
                },
            },
            zIndex=10,
        ),
        # Cabeçalho e Inputs
        html.Hr(),
        # Título Desktop
        dmc.Box(
            dbc.Row(
                [
                    dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                    dbc.Col(
                        html.H1(
                            [
                                "Relatório da \u00a0",
                                html.Strong("regra"),
                                "\u00a0 de monitoramento do retrabalho",
                            ],
                            className="align-self-center",
                        ),
                        width=True,
                    ),
                ],
                align="center",
            ),
            visibleFrom="sm",
        ),
        # Titulo Mobile
        dmc.Box(
            dbc.Row(
                [
                    dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                    dbc.Col(
                        html.H1(
                            "Relatório da regra",
                            className="align-self-center",
                        ),
                        width=True,
                    ),
                ],
                align="center",
            ),
            hiddenFrom="sm",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Nome da Regra de Monitoramento"),
                                dcc.Dropdown(
                                    id="relatorio-input-select-regra-retrabalho",
                                    options=[regra for regra in lista_regras_monitoramento_comb],
                                    placeholder="Selecione uma regra...",
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Regra não encontrada",
                                        id="relatorio-input-select-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-select-regra-retrabalho",
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Data do relatório"),
                                dmc.DateInput(
                                    id="relatorio-input-data-relatorio-regra-retrabalho",
                                    minDate=date(2020, 8, 5),
                                    valueFormat="DD/MM/YYYY",
                                    value=(datetime.now() - timedelta(days=10)).date(),
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Período inválido",
                                        id="relatorio-input-data-relatorio-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-data-relatorio-regra-retrabalho",
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
            ]
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(DashIconify(icon="wpf:statistics", width=45), width="auto"),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                html.H4(
                                                    "Resumo da Regra",
                                                    className="align-self-center",
                                                ),
                                            ]
                                        ),
                                        width=True,
                                    ),
                                ],
                            ),
                            dmc.Space(h=40),
                            dbc.Row(
                                [
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem("", id="card-regra-nome", active=True),
                                            dbc.ListGroupItem("", id="card-regra-periodo-monitoramento"),
                                            dbc.ListGroupItem("", id="card-regra-modelos"),
                                            dbc.ListGroupItem("", id="card-regra-qtd-min-viagens"),
                                            dbc.ListGroupItem("", id="card-regra-qtd-min-motoristas"),
                                            dbc.ListGroupItem("", id="card-regra-dias-marcados"),
                                            dbc.ListGroupItem("", id="card-regra-limite-mediana"),
                                            dbc.ListGroupItem("", id="card-regra-limite-baixa-perfomance"),
                                            dbc.ListGroupItem("", id="card-regra-limite-erro-telemetria"),
                                            dbc.ListGroupItem("", id="card-regra-criar-os-automatica"),
                                            dbc.ListGroupItem("", id="card-regra-alvos-email"),
                                            dbc.ListGroupItem("", id="card-regra-alvos-whatsapp"),
                                        ],
                                        className="m-0",
                                    ),
                                ],
                                className="m-0",
                            ),
                        ],
                        className="m-0 m-md-1",  # margem só no desktop
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(DashIconify(icon="mdi:bomb", width=45), width="auto"),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                html.H4(
                                                    "Resumo do relatório",
                                                    className="align-self-center",
                                                ),
                                            ]
                                        ),
                                        width=True,
                                    ),
                                ],
                            ),
                            dmc.Space(h=40),
                            dbc.Row(
                                [
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-total-veiculos", active=True),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-media-km-por-litro"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-litros-excedentes"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-gasto-combustivel"),
                                        ],
                                        className="m-0",
                                    ),
                                ],
                                className="m-0",
                            ),
                        ],
                        className="m-0 m-md-1",  # margem só no desktop
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
            ],
        ),
        dmc.Space(h=40),
        # Gráfico da Regra por Serviço
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:fleet", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Top 10 problemas detectados pela regra",
                                className="align-self-center",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-relatorio-regra-por-servico"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "OSs detectadas pela regra",
                                className="align-self-center",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=40),
        # dag.AgGrid(
        #     id="tabela-relatorio-regra",
        #     columnDefs=crud_regra_tabelas.tbl_detalhamento_relatorio_regra,
        #     rowData=[],
        #     defaultColDef={"filter": True, "floatingFilter": True},
        #     columnSize="autoSize",
        #     dashGridOptions={
        #         "localeText": locale_utils.AG_GRID_LOCALE_BR,
        #         "enableCellTextSelection": True,
        #         "ensureDomOrder": True,
        #     },
        #     style={"height": 500, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        # ),
        dmc.Space(h=40),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__, name="Relatório de Regra", path="/regra-relatorio", icon="carbon:rule-data-quality", hide_page=True
)
