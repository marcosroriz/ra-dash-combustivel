#!/usr/bin/env python
# coding: utf-8

# Tela do dashboard com o detalhamento do consumo de um veículo

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd
import json

# Importar bibliotecas para manipulação de URL
import ast
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output
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
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import (
    get_linhas_possui_info_combustivel,
    get_modelos_veiculos_com_combustivel,
    get_veiculos_com_combustivel,
    get_tipos_eventos_telemetria_mix_com_data,
    get_tipos_eventos_telemetria_mix_com_gps,
)

# Imports específicos
from modules.combustivel_por_veiculo.veiculo_service import VeiculoService
import modules.combustivel_por_veiculo.graficos as veiculo_graficos
import modules.combustivel_por_veiculo.tabela as veiculo_tabela

# Preço do diesel
from modules.preco_combustivel_api import get_preco_diesel

import tema

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

# Modelos e Veiculos
df_modelos = get_modelos_veiculos_com_combustivel(pgEngine)

# Pega o preço do diesel via API
preco_diesel = get_preco_diesel()

# Lista de eventos com data
df_eventos_com_data = get_tipos_eventos_telemetria_mix_com_data(pgEngine)
df_eventos_com_data = df_eventos_com_data.sort_values(by="label")

df_eventos_com_gps = get_tipos_eventos_telemetria_mix_com_gps(pgEngine)
df_eventos_com_gps = df_eventos_com_gps.sort_values(by="label")
lista_eventos_com_gps = df_eventos_com_gps["EventTypeId"].unique()

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################


# Função auxiliar para transformar string '[%27A%27,%20%27B%27]' → ['A', 'B']
def parse_list_param_pag_veiculo(param):
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


def gera_labels_inputs_pag_veiculo(campo):
    # Cria o callback
    @callback(
        Output(component_id=f"{campo}-labels", component_property="children"),
        Input("pag-veiculo-store-input-dados-veiculo", "data"),
    )
    def pag_veiculo_atualiza_labels_inputs_veiculo(data):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]

        # Obtem os dados
        datas = data["datas"]
        vec_num_id = data["id_veiculo"]
        vec_model = data["vec_model"]
        lista_linha = data["lista_linhas"]
        km_l_min = data["km_l_min"]
        km_l_max = data["km_l_max"]

        datas_label = []
        if not (datas is None or not datas) and datas[0] is not None and datas[1] is not None:
            # Formata as datas
            data_inicio_str = pd.to_datetime(datas[0]).strftime("%d/%m/%Y")
            data_fim_str = pd.to_datetime(datas[1]).strftime("%d/%m/%Y")

            datas_label = [dmc.Badge(f"{data_inicio_str} a {data_fim_str}", variant="outline")]

        dados_veiculos_labels = []
        lista_linha_labels = []
        km_l_labels = []

        dados_veiculos_labels.append(dmc.Badge(str(vec_num_id), variant="outline"))
        dados_veiculos_labels.append(dmc.Badge(str(vec_model), variant="outline"))

        if lista_linha is None or not lista_linha or "TODAS" in lista_linha:
            lista_linha_labels.append(dmc.Badge("Todas as linhas", variant="outline"))
        else:
            for linha in lista_linha:
                lista_linha_labels.append(dmc.Badge(linha, variant="dot"))

        km_l_labels.append(dmc.Badge(f"{km_l_min} ≤ km/L ≤ {km_l_max} ", variant="outline"))

        return [dmc.Group(labels_antes + datas_label + dados_veiculos_labels + lista_linha_labels + km_l_labels)]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[], className="labels-filtro")


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
        "vec_model": "",
        "vec_asset_id": "",
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

    # Modelos
    if not df_modelos[df_modelos["vec_num_id"] == id_veiculo].empty:
        input_dict["vec_model"] = df_modelos[df_modelos["vec_num_id"] == id_veiculo]["LABEL"].values[0]
        input_dict["vec_asset_id"] = str(df_modelos[df_modelos["vec_num_id"] == id_veiculo]["vec_asset_id"].values[0])

    return input_dict


@callback(
    Output("pag-veiculo-store-historico-viagens-veiculo", "data"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
)
def cb_sincroniza_input_historico_timeline(data):
    # Input padrão
    state_dict = {"valido": False, "df": []}

    if not data or not data["valido"]:
        return state_dict

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    df = veiculo_service.get_historico_viagens(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    state_dict["valido"] = True
    state_dict["df"] = df.to_dict(orient="records")

    return state_dict


def formata_float_para_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("pag-veiculo-tabela-consumo-linhas-visao-veiculo", "rowData"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
)
def cb_pag_veiculo_tabela_lista_viagens(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return []

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    # Obtem os dados
    df = veiculo_service.get_tabela_lista_viagens_veiculo(datas, vec_num_id, lista_linha, km_l_min, km_l_max)

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    return df.to_dict(orient="records")


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

    # Obtem o valor do indicador
    valor = df_indicador.iloc[0]["media_km_por_l"]

    if pd.isna(valor) or valor is None:
        return ""
    else:
        return str(round(valor, 2)).replace(".", ",") + " km/L"


# Callback para o indicador de consumo médio de km/L
@callback(
    [
        Output("pag-veiculo-indicador-total-litros-excedente-visao-veiculo", "children"),
        Output("pag-veiculo-indicador-total-gasto-combustivel-excedente-visao-veiculo", "children"),
    ],
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
)
def cb_pag_veiculo_indicador_total_consumo_excedente_visao_veiculo(data):
    if not data or not data["valido"]:
        return "", "", ""

    # Obtem os dados
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    # Obtem os dados
    df_indicador = veiculo_service.get_indicador_consumo_litros_excedente(
        datas, vec_num_id, lista_linha, km_l_min, km_l_max
    )

    if df_indicador.empty:
        return "", ""

    # Obtém o valor do indicador
    valor = df_indicador.iloc[0]["litros_excedentes"]

    if pd.isna(valor) or valor is None:
        return "", ""
    else:
        return (
            f"{int(valor):,} L".replace(",", "."),
            f"R$ {int(preco_diesel * valor):,}".replace(",", "."),
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
    Input("pag-veiculo-store-historico-viagens-veiculo", "data"),
    Input("store-window-size", "data"),
    Input("pag-veiculo-graph-timeline-consumo-veiculo", "clickData"),
    Input("pag-veiculo-graph-timeline-consumo-veiculo", "relayoutData"),
    Input("pag-veiculo-anotacoes-timeline", "value"),
)
def cb_plota_grafico_timeline_consumo_veiculo(
    data, metadata_browser, ponto_selecionado, range_selecionado, anotacao_no_grafico
):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados
    df = pd.DataFrame(data["df"])
    if df.empty:
        return go.Figure()

    # Formata datas no df, pois a serialização converte para string
    df["encontrou_timestamp_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"])
    df["encontrou_timestamp_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"])
    df["timestamp_br_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
    df["timestamp_br_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"]) - pd.Timedelta(hours=3)
    df["encontrou_tempo_viagem_segundos"] = df["encontrou_tempo_viagem_segundos"].astype(int)
    df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_segundos"] / 60
    df["dia_dt"] = pd.to_datetime(df["dia"]).dt.date

    # Obtem o ponto selecionado (se houver)
    df_ponto_selecionado = None
    if ponto_selecionado is not None:
        df_ponto_selecionado = df[df["timestamp_br_inicio"] == ponto_selecionado["points"][0]["x"]]

    # Gera o gráfico
    fig = veiculo_graficos.gerar_grafico_timeline_consumo_veiculo(
        df, metadata_browser, df_ponto_selecionado, range_selecionado, anotacao_no_grafico
    )
    return fig


@callback(
    Output("pag-veiculo-graph-histograma-viagens-veiculo", "figure"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
    Input("store-window-size", "data"),
    Input("pag-veiculo-graph-timeline-consumo-veiculo", "clickData"),
)
def cb_plota_histograma_viagem_selecionada(data, metadata_browser, ponto_selecionado):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Caso não tenha ponto selecionado, retorna gráfico nulo
    if ponto_selecionado is None:
        return go.Figure()

    # Obtem os dados do store
    datas = data["datas"]
    vec_num_id = data["id_veiculo"]
    lista_linha = data["lista_linhas"]
    km_l_min = data["km_l_min"]
    km_l_max = data["km_l_max"]

    # Extraí os dados do ponto
    ponto_custom_data = ponto_selecionado["points"][0]["customdata"]
    viagem_consumo_kml = ponto_custom_data[0]
    viagem_linha = ponto_custom_data[3]
    viagem_sentido = ponto_custom_data[4]
    viagem_time_slot = ponto_custom_data[8]
    viagem_vec_model = ponto_custom_data[9]
    viagem_dia = ponto_custom_data[10]
    viagem_eh_feriado = ponto_custom_data[11]
    viagem_data_inicio = ponto_custom_data[13]

    # Executa a consulta
    df = veiculo_service.get_histograma_viagens_veiculo(
        km_l_min,
        km_l_max,
        viagem_data_inicio,
        viagem_vec_model,
        viagem_linha,
        viagem_sentido,
        viagem_time_slot,
        viagem_dia,
        viagem_eh_feriado,
    )

    # Gera o gráfico
    fig = veiculo_graficos.gerar_grafico_histograma_viagens(
        df, viagem_atual_consumo=viagem_consumo_kml, metadata_browser=metadata_browser
    )

    return fig


##############################################################################
# Callback para os eventos ###################################################
##############################################################################
@callback(
    Output("card-detalhamento-eventos-viagem-veiculo", "children"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
    Input("pag-veiculo-graph-timeline-consumo-veiculo", "clickData"),
)
def cb_pag_veiculo_lista_eventos_viagem(data, ponto_selecionado):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"] or ponto_selecionado is None:
        return "Nenhuma viagem selecionada"

    # Obtem os dados do store
    vec_asset_id = data["vec_asset_id"]
    vec_num_id = data["id_veiculo"]
    vec_model = data["vec_model"]

    # Extraí os dados do ponto
    ponto_custom_data = ponto_selecionado["points"][0]["customdata"]
    inicio_viagem = (pd.to_datetime(ponto_custom_data[13])).strftime("%Y-%m-%d %H:%M:%S")
    fim_viagem = (pd.to_datetime(ponto_custom_data[14])).strftime("%Y-%m-%d %H:%M:%S")
    viagem_km_l = ponto_custom_data[0]
    viagem_linha = ponto_custom_data[3]
    viagem_sentido = ponto_custom_data[4]
    viagem_tempo_minutos = ponto_custom_data[5]
    viagem_nome_motorista = ponto_custom_data[6]
    viagem_velocidade = ponto_custom_data[7]
    viagem_combustivel_gasto = ponto_custom_data[15]

    dados_veiculo_list = [
        html.Li(f"🚍 Veículo: {vec_num_id}"),
        html.Li(f"⚙️ Modelo: {vec_model}"),
        html.Li(f"👨🏻‍✈️ Motorista: {viagem_nome_motorista}"),
        html.Li(f"🟢 Início da Viagem: {inicio_viagem}"),
        html.Li(f"🔴 Fim da Viagem: {fim_viagem}"),
        html.Li(f"🚏 Linha: {viagem_linha} - {viagem_sentido}"),
        html.Li(f"📈 Consumo: {viagem_km_l:.2f} km/L"),
        html.Li(f"⏳ Duração da viagem: {viagem_tempo_minutos:.2f} minutos"),
        html.Li(f"🕓 Velocidade média: {viagem_velocidade:.2f} km/h"),
        html.Li(f"⛽ Combustível gasto: {viagem_combustivel_gasto:.2f} L"),
    ]

    df_eventos_viagem = veiculo_service.get_agg_eventos_ocorreram_viagem(inicio_viagem, fim_viagem, vec_asset_id)
    eventos_list = []
    for _, evt in df_eventos_viagem.iterrows():
        evt_label = evt["event_label"]
        total_eventos = evt["total_eventos"]
        eventos_list.append(html.Li(f"💣 {evt_label}: {total_eventos} eventos"))

    if len(eventos_list) > 0:
        return html.Ul(dados_veiculo_list + eventos_list)
    else:
        return html.Ul(dados_veiculo_list + [html.Li("💣 Viagem não gerou nenhum evento da Mix")])


##############################################################################
# Callback para o mapa #######################################################
##############################################################################


@callback(
    Output("pag-veiculo-layer-control-eventos-detalhe-viagem", "children"),
    Input("pag-veiculo-store-input-dados-veiculo", "data"),
    Input("pag-veiculo-graph-timeline-consumo-veiculo", "clickData"),
)
def cb_pag_veiculo_mapa_eventos_mix_viagem(data, ponto_selecionado):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"] or ponto_selecionado is None:
        return dash.no_update

    # Obtem os dados do store
    vec_asset_id = data["vec_asset_id"]

    # Extraí os dados do ponto
    ponto_custom_data = ponto_selecionado["points"][0]["customdata"]
    inicio_viagem = (pd.to_datetime(ponto_custom_data[13])).strftime("%Y-%m-%d %H:%M:%S")
    fim_viagem = (pd.to_datetime(ponto_custom_data[14])).strftime("%Y-%m-%d %H:%M:%S")
    viagem_linha = ponto_custom_data[3]
    viagem_sentido = ponto_custom_data[4]

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


def gera_layer_posicao(df_pos, cor_icone):
    lista_marcadores = []

    # Itera em cada evento
    for _, row in df_pos.iterrows():
        evt_lon = row["Longitude"]
        evt_lat = row["Latitude"]
        evt_timestamp = (pd.to_datetime(row["Timestamp"]) - pd.Timedelta(hours=3)).strftime("%H:%M:%S - %Y-%m-%d")

        marcador = dl.CircleMarker(
            center=[evt_lat, evt_lon],
            radius=10,
            color="black",
            fillColor=cor_icone,
            fillOpacity=0.75,
            children=dl.Popup(
                html.Div(
                    [
                        html.H6("Posição GPS"),
                        html.Ul([html.Li(f"Hora: {evt_timestamp}")]),
                    ]
                )
            ),
        )

        # Adiciona o marcador
        lista_marcadores.append(marcador)

    return lista_marcadores


def gera_layer_eventos_mix(df_eventos_mix, evt_name, cor_icone):
    lista_marcadores = []

    # Seta nome não conhecido para os motoristas que não tiverem dado
    df_eventos_mix["Name"] = df_eventos_mix["Name"].fillna("Não informado")

    # Itera em cada evento
    for _, row in df_eventos_mix.iterrows():
        evt_lon = row["StartPosition_Longitude"]
        evt_lat = row["StartPosition_Latitude"]
        evt_driver_name = row["Name"]
        evt_timestamp = (pd.to_datetime(row["StartDateTime"]) - pd.Timedelta(hours=3)).strftime("%H:%M:%S - %Y-%m-%d")

        if pd.notna(evt_lat) and pd.notna(evt_lon):
            marcador = dl.CircleMarker(
                center=[evt_lat, evt_lon],
                radius=10,
                color="black",
                fillColor=cor_icone,
                fillOpacity=0.75,
                children=dl.Popup(
                    html.Div(
                        [
                            html.H6(evt_name),
                            html.Ul([html.Li(f"Motorista: {evt_driver_name}"), html.Li(f"Hora: {evt_timestamp}")]),
                        ]
                    )
                ),
            )

            # Adiciona o marcador
            lista_marcadores.append(marcador)

    return lista_marcadores


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Combustível por Veículo", path="/combustivel-por-veiculo")


##############################################################################
# Layout #####################################################################
##############################################################################
def getMapaFundo():
    return [
        # OpenStreetMap (ruas padrão)
        dl.BaseLayer(
            dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
            name="OpenStreetMap",
            checked=False,
        ),
        # ESRI Satellite (sem nomes de rua)
        dl.BaseLayer(
            dl.TileLayer(
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attribution="Tiles © Esri",
            ),
            name="ESRI Satellite",
            checked=True,
        ),
    ]


layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="pag-veiculo-store-input-dados-veiculo"),
        dcc.Store(id="pag-veiculo-store-historico-viagens-veiculo"),
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
                                    className="mb-3 mb-md-0",
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
                                                    [
                                                        f"Total gasto com combustível excedente (R$), considerando o litro do Diesel = R$ {preco_diesel:,.2f}".replace(
                                                            ".", ","
                                                        ),
                                                    ],
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
                            dbc.Col(
                                # gera_labels_inputs_pag_veiculo("pag-veiculo-labels-grafico-historico-veiculo"),
                                dbc.Row(
                                    [
                                        dmc.RadioGroup(
                                            children=dmc.Group(
                                                [
                                                    dmc.Badge("Filtro", color="gray", variant="outline"),
                                                    dmc.Radio("Sem anotações", value="anotacoes_sem"),
                                                    dmc.Radio("Motoristas", value="anotacoes_motoristas"),
                                                    dmc.Radio("Linhas", value="anotacoes_linhas"),
                                                ],
                                                my=10,
                                            ),
                                            id="pag-veiculo-anotacoes-timeline",
                                            value="anotacoes_sem",
                                            size="sm",
                                            mb=10,
                                        ),
                                    ]
                                ),
                                width=True,
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="pag-veiculo-graph-timeline-consumo-veiculo"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento das viagens do veículo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(
                                gera_labels_inputs_pag_veiculo("pag-veiculo-labels-grafico-detalhamento-veiculo"),
                                width=True,
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
                    dbc.Row(
                        [
                            html.H5("Dados da viagem"),
                            dbc.ListGroup(
                                [
                                    dbc.ListGroupItem("", id="card-detalhamento-eventos-viagem-veiculo"),
                                ],
                                className="m-0",
                            ),
                        ]
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H5("Boxplot de viagens na mesma configuração"),
                            dcc.Graph(
                                id="pag-veiculo-graph-histograma-viagens-veiculo",
                                config=locale_utils.plotly_locale_config,
                            ),
                        ]
                    ),
                    md=6,
                ),
            ]
        ),
        dl.Map(
            children=dl.LayersControl(
                getMapaFundo(), id="pag-veiculo-layer-control-eventos-detalhe-viagem", collapsed=False
            ),
            id="pag-veiculo-mapa-eventos-detalhe-viagem",
            center=(-16.665136, -49.286041),
            zoom=11,
            style={
                "height": "60vh",
                "border": "2px solid gray",
                "borderRadius": "6px",
            },
        ),
        dmc.Space(h=40),
    ]
)
