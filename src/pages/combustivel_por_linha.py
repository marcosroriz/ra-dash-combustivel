#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o combustível utilizado por determinada linha

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
import pandas as pd
import json
from datetime import date, datetime

# Importar bibliotecas para manipulação de URL
import ast
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Imports de mapa
import dash_leaflet as dl

# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import (
    get_linhas_possui_info_combustivel,
    get_modelos_veiculos_com_combustivel,
    get_tipos_eventos_telemetria_mix_com_data,
    get_tipos_eventos_telemetria_mix_com_gps,
    gerar_excel,
)

# Imports específicos
from modules.combustivel_por_veiculo.veiculo_service import VeiculoService
from modules.combustivel_por_linha.linha_service import LinhaService
import modules.combustivel_por_linha.graficos as linha_graficos
import modules.combustivel_por_linha.tabela as linha_tabela

# Preço do diesel
from modules.preco_combustivel_api import get_preco_diesel

# Mapa
from modules.mapa_utils import getMapaFundo, gera_layer_posicao, gera_layer_eventos_mix

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
linha_service = LinhaService(pgEngine)
veiculo_service = VeiculoService(pgEngine)

# Linhas que possuem informações de combustível
df_todas_linhas = get_linhas_possui_info_combustivel(pgEngine)
lista_todas_linhas = df_todas_linhas.to_dict(orient="records")

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_com_combustivel(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

# Lista de eventos com data e gps
df_eventos_com_data = get_tipos_eventos_telemetria_mix_com_data(pgEngine)
df_eventos_com_data = df_eventos_com_data.sort_values(by="label")

df_eventos_com_gps = get_tipos_eventos_telemetria_mix_com_gps(pgEngine)
df_eventos_com_gps = df_eventos_com_gps.sort_values(by="label")
lista_eventos_com_gps = df_eventos_com_gps["EventTypeId"].unique()

# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################


# Função auxiliar para transformar string '[%27A%27,%20%27B%27]' → ['A', 'B']
def parse_list_param_pag_linha(param):
    if isinstance(param, list):
        return param
    elif isinstance(param, str):
        try:
            return ast.literal_eval(param)
        except:
            return []
    return []


# Preenche os dados via URL
@callback(
    Output("pag-linha-input-select-linhas-combustivel", "value"),
    Output("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
    Output("pag-linha-input-select-modelos-combustivel-linha", "value"),
    Output("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
    Output("pag-linha-input-select-dia-linha-combustivel", "value"),
    Output("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
    Output("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
    Input("url", "href"),
)
def cb_receber_campos_via_url_pag_linha(href):
    if not href or "/combustivel-por-linha" not in href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    # Pega os parâmetros
    linha = str(query_params.get("linha", ["020"])[0])

    # Datas
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    datas = [query_params.get("data_inicio", ["2025-01-01"])[0], query_params.get("data_fim", [data_hoje])[0]]

    # Lista de modelos
    lista_modelos = parse_list_param_pag_linha(query_params.get("lista_modelos", [["TODOS"]])[0])

    # Sentido (por padrão coloca IDA e VOLTA, usuário pode modificar depois)
    sentido = ["IDA", "VOLTA"]

    # Dias marcados (por padrão SEG a SEX, pode modificar depois)
    dia_marcado = ["SEG_SEX"]

    # Velocidade
    km_l_min = int(query_params.get("km_l_min", [1])[0])
    km_l_max = int(query_params.get("km_l_max", [10])[0])

    return linha, datas, lista_modelos, sentido, dia_marcado, km_l_min, km_l_max


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior):
    if datas is None or not datas or None in datas:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    if linha is None:
        return False

    if lista_sentido is None or not lista_sentido or None in lista_sentido:
        return False

    if lista_dias_semana is None or not lista_dias_semana:
        return False

    if limite_km_l_menor is None or limite_km_l_menor < 0:
        return False

    if limite_km_l_maior is None or limite_km_l_maior < 0:
        return False

    return True


def pag_linha_gera_labels_inputs_visao_linha(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
            Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
            Input("pag-linha-input-select-linhas-combustivel", "value"),
            Input("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
            Input("pag-linha-input-select-dia-linha-combustivel", "value"),
            Input("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
            Input("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
        ],
    )
    def atualiza_labels_inputs_visal_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    ):
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
        lista_sentido_labels = []
        lista_dias_semana_labels = []
        km_l_labels = []

        if lista_modelos is None or not lista_modelos or "TODOS" in lista_modelos:
            lista_modelos_labels.append(dmc.Badge("Todos os modelos", variant="outline"))
        else:
            for modelo in lista_modelos:
                lista_modelos_labels.append(dmc.Badge(modelo, variant="dot"))

        if linha is not None:
            lista_linha_labels.append(dmc.Badge(f"Linha {linha}", variant="dot"))

        if lista_sentido is not None:
            for opcao in lista_sentido:
                lista_sentido_labels.append(dmc.Badge(f"Sentido {opcao}", variant="dot"))

        if lista_dias_semana is not None:
            for opcao in lista_dias_semana:
                lista_dias_semana_labels.append(dmc.Badge(f"Dias {opcao}", variant="dot"))

        km_l_labels.append(dmc.Badge(f"{limite_km_l_menor} ≤ km/L ≤ {limite_km_l_maior} ", variant="dot"))

        return [
            dmc.Group(
                labels_antes
                + datas_label
                + lista_modelos_labels
                + lista_linha_labels
                + lista_sentido_labels
                + lista_dias_semana_labels
                + km_l_labels
            )
        ]

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
    Output("pag-linha-input-select-modelos-combustivel-linha", "value", allow_duplicate=True),
    Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
    prevent_initial_call=True,
)
def corrige_input_modelos(lista_modelos):
    return corrige_input(lista_modelos, "TODOS")


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


@callback(
    [
        Output("pag-linha-indicador-qtd-de-viagens-comb-linha", "children"),
        Output("pag-linha-indicador-qtd-de-veiculos-diferentes-comb-linha", "children"),
        Output("pag-linha-indicador-qtd-de-modelos-diferentes-comb-linha", "children"),
        Output("pag-linha-indicador-consumo-medio-linha", "children"),
        Output("pag-linha-indicador-total-litros-excedentes", "children"),
        Output("pag-linha-indicador-total-gasto-comb-excedentes", "children"),
    ],
    [
        Input("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
        Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
        Input("pag-linha-input-select-linhas-combustivel", "value"),
        Input("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
        Input("pag-linha-input-select-dia-linha-combustivel", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
    ],
)
def cb_pag_linha_atualiza_indicadores_combustivel_por_linha(
    datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
):
    # Valida
    if not input_valido(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    ):
        return ["", "", "", "", "", ""]

    # Obtém os dados
    df = linha_service.get_indicadores_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    )

    # Verifica se o dataframe está vazio
    if df.empty:
        return ["", "", "", "", "", ""]

    # Calcula os indicadores
    num_viagens = df["total_num_viagens"].values[0]

    # Antes verifica se houve viagens, caso não tenha, returno nulo
    if num_viagens == 0:
        return ["0", "0", "0", "0", "0", "0"]

    num_veiculos = df["total_num_veiculos"].values[0]
    num_modelos = df["total_num_modelos"].values[0]
    consumo_medio = df["media_consumo_viagem"].values[0]
    total_litros_excedentes = df["total_litros_excedentes"].values[0]
    gasto_excedente = total_litros_excedentes * preco_diesel

    return [
        f"{int(num_viagens):,}".replace(",", "."),
        f"{num_veiculos}",
        f"{num_modelos}",
        f"{str(round(consumo_medio, 2))} km/L".replace(".", ","),
        f"{int(total_litros_excedentes):,} L".replace(",", "."),
        f"R$ {int(gasto_excedente):,}".replace(",", "."),
    ]


@callback(
    Output("graph-combustivel-linha-por-hora", "figure"),
    [
        Input("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
        Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
        Input("pag-linha-input-select-linhas-combustivel", "value"),
        Input("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
        Input("pag-linha-input-select-dia-linha-combustivel", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
    ],
)
def cb_pag_linha_plota_grafico_combustivel_linha_por_hora(
    datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
):
    # Valida
    if not input_valido(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    ):
        return go.Figure()

    # Obtém os dados
    df = linha_service.get_consumo_por_time_slot_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    )

    # Verifica se o dataframe está vazio
    if df.empty:
        return go.Figure()

    # Gera o gráfico
    fig = linha_graficos.gerar_grafico_consumo_combustivel_por_linha(df)
    return fig


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("pag-linha-tabela-detalhamento-viagens-combustivel", "rowData"),
    [
        Input("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
        Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
        Input("pag-linha-input-select-linhas-combustivel", "value"),
        Input("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
        Input("pag-linha-input-select-dia-linha-combustivel", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
    ],
)
def cb_pag_veiculo_tabela_lista_viagens(
    datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
):
    # Valida
    if not input_valido(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    ):
        return []

    # Obtém os dados
    df = linha_service.get_viagens_realizada_na_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    )

    # Verifica se o dataframe está vazio
    if df.empty:
        []

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    # Ação de visualização
    df["acao"] = "🔍 Detalhar"

    return df.to_dict(orient="records")


# Callback para fazer o download quando o botão exportar para excel for clicado
@callback(
    Output("pag-linha-download-excel-tabela-viagens", "data"),
    [
        Input("pag-linha-btn-exportar-tabela-viagens", "n_clicks"),
        Input("pag-linha-input-intervalo-datas-combustivel-linha", "value"),
        Input("pag-linha-input-select-modelos-combustivel-linha", "value"),
        Input("pag-linha-input-select-linhas-combustivel", "value"),
        Input("pag-linha-input-select-sentido-da-linha-combustivel", "value"),
        Input("pag-linha-input-select-dia-linha-combustivel", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-menor-que", "value"),
        Input("pag-linha-input-linha-combustivel-remover-outliers-maior-que", "value"),
    ],
    prevent_initial_call=True,
)
def cb_download_excel_tabela_consumo_veiculos_visal_geral(
    n_clicks, datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
):
    if not n_clicks or n_clicks <= 0:  # Garantre que ao iniciar ou carregar a page, o arquivo não seja baixado
        return dash.no_update

    # Valida input
    if not input_valido(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    ):
        return dash.no_update

    # Obtém os dados
    df = linha_service.get_viagens_realizada_na_linha(
        datas, lista_modelos, linha, lista_sentido, lista_dias_semana, limite_km_l_menor, limite_km_l_maior
    )

    # Verifica se o dataframe está vazio
    if df.empty:
        return dash.no_update

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    # Remove dados de timezone
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    # Gera o excel
    excel_data = gerar_excel(df)

    # Dia de hoje formatado
    dia_hoje_str = date.today().strftime("%d-%m-%Y")

    return dcc.send_bytes(excel_data, f"tabela_viagens_linha_{dia_hoje_str}.xlsx")


##############################################################################
# Callbacks para o mapa de viagem ############################################
##############################################################################


# Callback para detalhar viagem no mapa
@callback(
    Output("pag-linha-layer-control-eventos-detalhe-viagem", "children"),
    Input("pag-linha-tabela-detalhamento-viagens-combustivel", "cellRendererData"),
    Input("pag-linha-tabela-detalhamento-viagens-combustivel", "virtualRowData"),
    prevent_initial_call=True,
)
def cb_pag_linha_botao_detalhar_viagem(tabela_linha, tabela_linha_virtual):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update

    tabela_linha_alvo = tabela_linha_virtual[tabela_linha["rowIndex"]]

    inicio_viagem = (pd.to_datetime(tabela_linha_alvo["timestamp_br_inicio"])).strftime("%Y-%m-%d %H:%M:%S")
    fim_viagem = (pd.to_datetime(tabela_linha_alvo["timestamp_br_fim"])).strftime("%Y-%m-%d %H:%M:%S")
    viagem_linha = tabela_linha_alvo["encontrou_numero_sublinha"]
    viagem_sentido = tabela_linha_alvo["encontrou_sentido_linha"]
    vec_asset_id = tabela_linha_alvo["vec_asset_id"]

    # Lista com as overlays que colocaremos no mapa
    lista_overlays = []

    # Obtem o shape da linha
    df_shape_linha = veiculo_service.get_shape_linha(inicio_viagem, viagem_linha, viagem_sentido)
    linha_geojson_str = df_shape_linha["geojsondata"].values[0]
    linha_geojson = json.loads(linha_geojson_str)

    # Gera a camada
    lista_overlays.append(
        dl.Pane(
            dl.Overlay(
                dl.LayerGroup(
                    dl.GeoJSON(
                        data=linha_geojson,
                        options=dict(
                            style=dict(
                                color=tema.PALETA_CORES_DISCRETA[1],
                                weight=20,  # border thickness
                                opacity=0.8,  # border opacity
                                zIndex=220,
                            )
                        ),
                    ),
                ),
                checked=True,
                id=f"overlay-{viagem_linha}{viagem_sentido}",
                name=f"<span class='mapa-icone-linha'></span>Linha {viagem_linha} / Sentido {viagem_sentido}",
            ),
            name=f"<span class='mapa-icone-linha'></span>Linha {viagem_linha} / Sentido {viagem_sentido} Panel",
            style=dict(zIndex=220),
        )
    )
    lista_overlays.append(
        dl.Pane(
            dl.Overlay(
                dl.LayerGroup(
                    dl.GeoJSON(
                        data=linha_geojson,
                        options=dict(
                            style=dict(
                                color="#FFFFFF",
                                weight=4,  # border thickness
                                opacity=0.8,  # border opacity
                                zIndex=250,
                            )
                        ),
                    ),
                ),
                checked=True,
                id=f"overlay-{viagem_linha}{viagem_sentido}-borda",
                name=f"<span class='mapa-icone-linha'></span>Linha {viagem_linha} / Sentido {viagem_sentido} (BORDA)",
            ),
            name=f"<span class='mapa-icone-linha'></span>Linha {viagem_linha} / Sentido {viagem_sentido} (BORDA) Panel",
            style=dict(zIndex=250),
        )
    )

    # Obtem os eventos que ocorreram na viagem
    df_eventos_viagem = veiculo_service.get_agg_eventos_ocorreram_viagem(inicio_viagem, fim_viagem, vec_asset_id)

    # Adiciona as posições GPS
    df_posicoes_gps = veiculo_service.get_posicao_gps_veiculo(inicio_viagem, fim_viagem, vec_asset_id)
    cor_icone = tema.PALETA_CORES_DISCRETA[2]
    layer_lista_marcadores = gera_layer_posicao(df_posicoes_gps, cor_icone)

    # Gera a camada e salva lat e lon
    lista_overlays.append(
        dl.Overlay(
            dl.LayerGroup(layer_lista_marcadores),
            id=f"overlay-{viagem_linha}{viagem_sentido}-pos-gps",
            name="<span class='mapa-icone mapa-icone-pos-gps'></span>Posição GPS",
            checked=True,
        )
    )

    # Agora, processa cada tipo de evento que ocorreu na viagem
    for i, evt in df_eventos_viagem.iterrows():
        evt_label = evt["event_label"]
        evt_value = evt["event_value"]
        evt_type_id = evt["event_type_id"]

        cor_idx = (i + 3) % len(tema.PALETA_CORES_DISCRETA)
        cor_icone = tema.PALETA_CORES_DISCRETA[cor_idx]

        if evt_type_id in lista_eventos_com_gps:
            df_eventos_viagem_com_gps = veiculo_service.get_detalhamento_evento_mix_veiculo(
                inicio_viagem, fim_viagem, vec_asset_id, evt_value
            )

            layer_lista_marcadores = gera_layer_eventos_mix(df_eventos_viagem_com_gps, evt_label, cor_icone)

            # Gera a camada
            lista_overlays.append(
                dl.Overlay(
                    dl.LayerGroup(layer_lista_marcadores),
                    name=f"<span class='mapa-icone mapa-icone-evt-{cor_idx}'></span>{evt_label}",
                    id=f"overlay-mapa-icone-evt-i-{viagem_linha}{viagem_sentido}",
                    checked=True,
                )
            )

    return getMapaFundo() + lista_overlays


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Combustível por Linha", path="/combustivel-por-linha")

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
                                                    "Combustível por \u00a0",
                                                    html.Strong("Linha"),
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
                                                        id="pag-linha-input-intervalo-datas-combustivel-linha",
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
                                                        id="pag-linha-input-select-modelos-combustivel-linha",
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
                                                        id="pag-linha-input-select-linhas-combustivel",
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
                                                        id="pag-linha-input-select-sentido-da-linha-combustivel",
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
                                                        id="pag-linha-input-select-dia-linha-combustivel",
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
                                                        value=[["SEG_SEX"]],
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
                                                                id="pag-linha-input-linha-combustivel-remover-outliers-menor-que",
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
                                                                id="pag-linha-input-linha-combustivel-remover-outliers-maior-que",
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
                                                    id="pag-linha-indicador-qtd-de-viagens-comb-linha",
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
                                    dbc.CardFooter("Total de Viagens"),
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
                                                    id="pag-linha-indicador-qtd-de-veiculos-diferentes-comb-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:bus-multiple",
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
                                                    id="pag-linha-indicador-qtd-de-modelos-diferentes-comb-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="material-symbols:car-gear-rounded",
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
                                                    id="pag-linha-indicador-consumo-medio-linha",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="material-symbols:speed-outline-rounded",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Consumo médio (km/L)"),
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
                                                    id="pag-linha-indicador-total-litros-excedentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="bi:fuel-pump-fill",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total de litros excedentes (≤ 2 STD)"),
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
                                                    id="pag-linha-indicador-total-gasto-comb-excedentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="emojione-monotone:money-with-wings",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total gasto com combustível excedente (R$)"),
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
                            dbc.Col(pag_linha_gera_labels_inputs_visao_linha("pag-linha-grafico-viagens"), width=True),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-combustivel-linha-por-hora"),
        dmc.Space(h=40),
        dbc.Alert(
            [
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="material-symbols:info-outline-rounded", width=45), width="auto"),
                        dbc.Col(
                            html.P(
                                """
                                A tabela a seguir ilustra cada viagem realizada nesta linha.
                                Você pode clicar no botão detalhar para visualizar as posições GPS e eventos MIX gerados ao longo da viagem.
                                """
                            ),
                            className="mt-2",
                            width=True,
                        ),
                    ],
                    align="center",
                ),
            ],
            dismissable=True,
            color="info",
        ),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento das viagens nesta linha",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(pag_linha_gera_labels_inputs_visao_linha("pag-linha-input-viagens"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="pag-linha-btn-exportar-tabela-viagens",
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
                                        dcc.Download(id="pag-linha-download-excel-tabela-viagens"),
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
            id="pag-linha-tabela-detalhamento-viagens-combustivel",
            columnDefs=linha_tabela.tbl_detalhamento_viagens_km_l,
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
                                "Mapa da Viagem",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            # dbc.Col(gera_labels_inputs_veiculos("pag-linha-input-geral-mapa-linha"), width=True),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dl.Map(
            children=dl.LayersControl(
                getMapaFundo(), id="pag-linha-layer-control-eventos-detalhe-viagem", collapsed=False
            ),
            id="pag-linha-mapa-eventos-detalhe-viagem",
            center=(-16.665136, -49.286041),
            zoom=11,
            style={
                "height": "60vh",
                "border": "2px solid gray",
                "borderRadius": "6px",
            },
        ),
        html.Div(id="mapa-linha-onibus"),
        dmc.Space(h=60),
    ]
)
