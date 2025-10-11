#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado os indicadores de gasto de combustível, bem como a evolução do gasto

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

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
from modules.entities_utils import get_linhas_possui_info_combustivel, get_modelos_veiculos_com_combustivel, gerar_excel

# Imports específicos
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
home_service = HomeService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")
lista_todas_linhas.insert(0, {"LABEL": "TODAS"})

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
df_modelos_veiculos_latest = df_modelos_veiculos.drop_duplicates(subset="LABEL", keep="first")
lista_todos_modelos_veiculos = df_modelos_veiculos_latest.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
    if datas is None or not datas or None in datas or len(datas) != 2:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    if lista_linha is None or not lista_linha or None in lista_linha:
        return False

    if km_l_min < 0 or km_l_min >= km_l_max or km_l_max >= 20:
        return False

    return True


def gera_labels_inputs_visao_geral(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("pag-home-intervalo-datas-visao-geral", "value"),
            Input("pag-home-select-modelos-visao-geral", "value"),
            Input("pag-home-select-linhas-monitoramento", "value"),
            Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
            Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
        ],
    )
    def atualiza_labels_inputs_visal_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]

        datas_label = []
        if not (datas is None or not datas) and datas[0] is not None and datas[1] is not None:
            # Formata as datas
            data_inicio_str = pd.to_datetime(datas[0]).strftime("%d/%m/%Y")
            data_fim_str = pd.to_datetime(datas[1]).strftime("%d/%m/%Y")

            datas_label = [dmc.Badge(f"{data_inicio_str} a {data_fim_str}", variant="outline")]

        lista_modelos_labels = []
        lista_linha_labels = []
        km_l_labels = []

        if lista_modelos is None or not lista_modelos or "TODOS" in lista_modelos:
            lista_modelos_labels.append(dmc.Badge("Todos os modelos", variant="outline"))
        else:
            for modelo in lista_modelos:
                lista_modelos_labels.append(dmc.Badge(modelo, variant="dot"))

        if lista_linha is None or not lista_linha or "TODAS" in lista_linha:
            lista_linha_labels.append(dmc.Badge("Todas as linhas", variant="outline"))
        else:
            for linha in lista_linha:
                lista_linha_labels.append(dmc.Badge(linha, variant="dot"))

        km_l_labels.append(dmc.Badge(f"{km_l_min} ≤ km/L ≤ {km_l_max} ", variant="outline"))

        return [dmc.Group(labels_antes + datas_label + lista_modelos_labels + lista_linha_labels + km_l_labels)]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[], className="labels-filtro")


# Corrige o input para garantir que o termo para todas ("TODAS") não seja selecionado junto com outras opções
def corrige_input(lista, termo_all="TODAS"):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return [termo_all]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and termo_all in lista[1:]:
        return [termo_all]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if termo_all in lista and len(lista) > 1:
        return [value for value in lista if value != termo_all]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


@callback(
    Output("pag-home-select-modelos-visao-geral", "value", allow_duplicate=True),
    Input("pag-home-select-modelos-visao-geral", "value"),
    prevent_initial_call=True,
)
def corrige_input_modelos(lista_modelos):
    return corrige_input(lista_modelos, "TODOS")


@callback(
    Output("pag-home-select-linhas-monitoramento", "value", allow_duplicate=True),
    Input("pag-home-select-linhas-monitoramento", "value"),
    prevent_initial_call=True,
)
def corrige_input_linhas(lista_linhas):
    return corrige_input(lista_linhas)


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("tabela-consumo-veiculo-visao-geral", "rowData"),
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_tabela_consumo_veiculos_visal_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return []

    df = home_service.get_tabela_consumo_veiculos(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    # Ação de visualização
    df["acao"] = "🔍 Detalhar"

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    return df.to_dict(orient="records")


@callback(
    Output("tabela-consumo-linhas-visao-geral", "rowData"),
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_tabela_consumo_linhas_visal_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return []

    df = home_service.get_tabela_consumo_linhas(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    # Ação de visualização
    df["acao"] = "🔍 Detalhar"

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    return df.to_dict(orient="records")


# Callback para fazer o download quando o botão exportar para excel for clicado
@callback(
    Output("download-excel-tabela-combustivel-visao-geral", "data"),
    [
        Input("btn-exportar-excel-tabela-combustivel-visao-geral", "n_clicks"),
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
    prevent_initial_call=True,
)
def cb_download_excel_tabela_consumo_veiculos_visal_geral(
    n_clicks, datas, lista_modelos, lista_linha, km_l_min, km_l_max
):
    if not n_clicks or n_clicks <= 0:  # Garantre que ao iniciar ou carregar a page, o arquivo não seja baixado
        return dash.no_update

    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return dash.no_update

    # Obtem os dados
    df = home_service.get_tabela_consumo_veiculos(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    # Gera a coluna de custo
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    # Gera o excel
    excel_data = gerar_excel(df)

    # Dia de hoje formatado
    dia_hoje_str = date.today().strftime("%d-%m-%Y")

    return dcc.send_bytes(excel_data, f"tabela_consumo_combustivel_{dia_hoje_str}.xlsx")


@callback(
    Output("download-excel-tabela-linhas-visao-geral", "data"),
    [
        Input("btn-exportar-excel-tabela-linhas-visao-geral", "n_clicks"),
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
    prevent_initial_call=True,
)
def cb_download_excel_tabela_consumo_linhas_visal_geral(
    n_clicks, datas, lista_modelos, lista_linha, km_l_min, km_l_max
):
    if not n_clicks or n_clicks <= 0:  # Garantre que ao iniciar ou carregar a page, o arquivo não seja baixado
        return dash.no_update

    # Obtem os dados
    df = home_service.get_tabela_consumo_linhas(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    # Gera a coluna de custo
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    # Gera o excel
    excel_data = gerar_excel(df)

    # Dia de hoje formatado
    dia_hoje_str = date.today().strftime("%d-%m-%Y")

    return dcc.send_bytes(excel_data, f"tabela_consumo_linhas_{dia_hoje_str}.xlsx")


# Callback para redirecionar o usuário para outra página ao clicar no botão detalhar
@callback(
    Output("url", "href", allow_duplicate=True),
    Input("tabela-consumo-veiculo-visao-geral", "cellRendererData"),
    Input("tabela-consumo-veiculo-visao-geral", "virtualRowData"),
    Input("pag-home-intervalo-datas-visao-geral", "value"),
    Input("pag-home-select-modelos-visao-geral", "value"),
    Input("pag-home-select-linhas-monitoramento", "value"),
    Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
    Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    prevent_initial_call=True,
)
def cb_botao_detalhar_tabela_consumo_veiculos_visal_geral(
    tabela_linha, tabela_linha_virtual, datas, lista_modelos, lista_linha, km_l_min, km_l_max
):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update

    tabela_linha_alvo = tabela_linha_virtual[tabela_linha["rowIndex"]]

    url_params = [
        f"vec_num_id={tabela_linha_alvo['vec_num_id']}",
        f"data_inicio={pd.to_datetime(datas[0]).strftime('%Y-%m-%d')}",
        f"data_fim={pd.to_datetime(datas[1]).strftime('%Y-%m-%d')}",
        f"lista_linhas={lista_linha}",
        f"km_l_min={km_l_min}",
        f"km_l_max={km_l_max}",
    ]
    url_params_str = "&".join(url_params)

    return f"/combustivel-por-veiculo?{url_params_str}"


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("tabela-consumo-linhas-visao-geral", "cellRendererData"),
    Input("tabela-consumo-linhas-visao-geral", "virtualRowData"),
    Input("pag-home-intervalo-datas-visao-geral", "value"),
    Input("pag-home-select-modelos-visao-geral", "value"),
    Input("pag-home-select-linhas-monitoramento", "value"),
    Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
    Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    prevent_initial_call=True,
)
def cb_botao_detalhar_tabela_consumo_linha_visal_geral(
    tabela_linha, tabela_linha_virtual, datas, lista_modelos, lista_linha, km_l_min, km_l_max
):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update

    tabela_linha_alvo = tabela_linha_virtual[tabela_linha["rowIndex"]]

    url_params = [
        f"linha={tabela_linha_alvo['encontrou_numero_linha']}",
        f"data_inicio={pd.to_datetime(datas[0]).strftime('%Y-%m-%d')}",
        f"data_fim={pd.to_datetime(datas[1]).strftime('%Y-%m-%d')}",
        f"lista_modelos={lista_modelos}",
        f"km_l_min={km_l_min}",
        f"km_l_max={km_l_max}",
    ]
    url_params_str = "&".join(url_params)

    return f"/combustivel-por-linha?{url_params_str}"


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


# Callback para o indicador de consumo médio de km/L
@callback(
    Output("indicador-consumo-km-l-visao-geral", "children"),
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_indicador_consumo_km_l_visao_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return ""

    # Obtem os dados
    df_indicador = home_service.get_indicador_consumo_medio_km_l(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    if df_indicador.empty:
        return ""
    
    # Obtem o valor do indicador
    valor = df_indicador.iloc[0]["media_km_por_l"]

    if pd.isna(valor) or valor is None:
        return ""
    else:
        return str(round(valor, 2)).replace(".", ",") + " km/L"


# Callback para o indicador de consumo médio de km/L
@callback(
    [
        Output("indicador-total-litros-excedente-visao-geral", "children"),
        Output("indicador-total-gasto-combustivel-excedente-visao-geral", "children"),
        Output("card-footer-preco-diesel", "children"),
    ],
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
    ],
)
def cb_indicador_total_consumo_excedente_visao_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return "", "", ""

    # Obtem os dados
    df_indicador = home_service.get_indicador_consumo_litros_excedente(
        datas, lista_modelos, lista_linha, km_l_min, km_l_max
    )

    if df_indicador.empty:
        return "", "", ""

    # Obtém o valor do indicador    
    valor = df_indicador.iloc[0]["litros_excedentes"]

    if pd.isna(valor) or valor is None:
        return "", "", ""
    else:
        return (
            f"{int(valor):,} L".replace(",", "."),
            f"R$ {int(preco_diesel * valor):,}".replace(",", "."),
            f"Total gasto com combustível excedente (R$), considerando o litro do Diesel = R$ {preco_diesel:,.2f}".replace(
                ".", ","
            ),
        )


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("graph-pizza-sintese-viagens-geral", "figure"),
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
        Input("store-window-size", "data"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, lista_modelos, lista_linha, km_l_min, km_l_max, metadata_browser):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_sinteze_status_viagens(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

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


# Callback para o grafico de modelo
@callback(
    Output("graph-barra-consumo-modelo-visao-geral", "figure"),
    [
        Input("pag-home-intervalo-datas-visao-geral", "value"),
        Input("pag-home-select-modelos-visao-geral", "value"),
        Input("pag-home-select-linhas-monitoramento", "value"),
        Input("pag-home-excluir-km-l-menor-que-visao-geral", "value"),
        Input("pag-home-excluir-km-l-maior-que-visao-geral", "value"),
        Input("store-window-size", "data"),
    ],
)
def plota_grafico_barra_consumo_modelo(datas, lista_modelos, lista_linha, km_l_min, km_l_max, metadata_browser):
    # Valida input
    if not input_valido(datas, lista_modelos, lista_linha, km_l_min, km_l_max):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_sinteze_consumo_modelos(datas, lista_modelos, lista_linha, km_l_min, km_l_max)

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_barra_consumo_modelos_geral(df, metadata_browser)
    return fig


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Visão Geral", path="/")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
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
                                                    "Visão Geral da \u00a0",
                                                    html.Strong("Frota"),
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
                                                        id="pag-home-intervalo-datas-visao-geral",
                                                        allowSingleDateInRange=True,
                                                        minDate=date(2025, 1, 1),
                                                        maxDate=date.today(),
                                                        type="range",
                                                        value=[date(2025, 1, 1), date.today()],
                                                        # value=[date.today() - pd.DateOffset(days=30), date.today()],
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Modelos"),
                                                    dcc.Dropdown(
                                                        id="pag-home-select-modelos-visao-geral",
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
                                    className="mb-3 mb-md-0",
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
                                                        id="pag-home-select-linhas-monitoramento",
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
                                    className="mb-3 mb-md-0",
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
                                                                id="pag-home-excluir-km-l-menor-que-visao-geral",
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
                                    className="mb-3 mb-md-0",
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
                                                                id="pag-home-excluir-km-l-maior-que-visao-geral",
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
                                    className="mb-3 mb-md-0",
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
        # Grafico geral de combustível por modelo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Consumo de combustível por modelo",
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
        dcc.Graph(id="graph-barra-consumo-modelo-visao-geral"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento do consumo dos veículos",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_visao_geral("labels-tabela-veiculos-visao-geral"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-excel-tabela-combustivel-visao-geral",
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
                                            className="btnExcel"
                                        ),
                                        dcc.Download(id="download-excel-tabela-combustivel-visao-geral"),
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
            # enableEnterpriseModules=True,
            id="tabela-consumo-veiculo-visao-geral",
            columnDefs=home_tabela.tbl_consumo_veiculo_visao_geral,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento do consumo das linhas",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_visao_geral("labels-tabela-linhas-visao-geral"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-excel-tabela-linhas-visao-geral",
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
                                            className="btnExcel"
                                        ),
                                        dcc.Download(id="download-excel-tabela-linhas-visao-geral"),
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
            # enableEnterpriseModules=True,
            id="tabela-consumo-linhas-visao-geral",
            columnDefs=home_tabela.tbl_consumo_linhas_visao_geral,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
    ]
)
