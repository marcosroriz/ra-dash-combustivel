#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime, timedelta
import pandas as pd
import re
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
from dash import html, dcc, callback, Input, Output, State
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
from modules.regras.regras_service import RegrasService
import modules.regras.tabela as regras_tabela

# Imports gerais
from modules.entities_utils import get_modelos_veiculos_regras

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
regra_service = RegrasService(pgEngine)

# Modelos de veículos
df_modelos_veiculos = get_modelos_veiculos_regras(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"LABEL": "TODOS"})

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################

@callback(
    [
        Output("store-editar-input-id-editar-regra", "data"),
        Output("loading-overlay-guia-editar-regra", "visible"),
        Output("editar-input-nome-regra-monitoramento", "value"),
        Output("editar-input-periodo-dias-monitoramento-regra", "value"),
        Output("editar-input-modelos-monitoramento-regra", "value", allow_duplicate=True),
        Output("editar-input-quantidade-de-motoristas", "value"),
        Output("editar-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Output("editar-input-select-dia-linha-combustivel-regra", "value"),
        Output("editar-switch-mediana", "checked"),
        Output("editar-select-mediana", "value", allow_duplicate=True),
        Output("editar-switch-baixa-performace-indicativo", "checked"),
        Output("editar-select-baixa-performace-indicativo", "value", allow_duplicate=True),
        Output("editar-switch-erro-telemetria", "checked"),
        Output("editar-select-erro-telemetria", "value", allow_duplicate=True),
        Output("editar-switch-os-automatica", "checked"),
        Output("editar-switch-enviar-email-regra-criar-combustivel", "checked"),
        Output("editar-input-email-1-regra-criar-combustivel", "value"),
        Output("editar-input-email-2-regra-criar-combustivel", "value"),
        Output("editar-input-email-3-regra-criar-combustivel", "value"),
        Output("editar-input-email-4-regra-criar-combustivel", "value"),
        Output("editar-input-email-5-regra-criar-combustivel", "value"),
        Output("editar-switch-enviar-wpp-regra-criar-combustivel", "checked"),
        Output("editar-input-wpp-1-regra-criar-combustivel", "value"),
        Output("editar-input-wpp-2-regra-criar-combustivel", "value"),
        Output("editar-input-wpp-3-regra-criar-combustivel", "value"),
        Output("editar-input-wpp-4-regra-criar-combustivel", "value"),
        Output("editar-input-wpp-5-regra-criar-combustivel", "value"),
    ],
    Input("url", "href"),
    running=[(Output("loading-overlay-guia-editar-regra", "visible"), True, False)],
    prevent_initial_call=True,
)
def callback_receber_campos_via_url_editar_regra(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    
    regra_id = query_params.get("id", [None])[0]

    if regra_id:
        regra = regra_service.get_regra_by_id(regra_id)
        if regra:
            return (
                regra["id"],
                False,
                regra["nome_regra"],
                regra["data_periodo_dias"],
                regra["modelos"],
                regra["quantidade_motoristas"],
                regra["quantidade_viagens"],
                regra["dias_marcados"],
                regra["mediana_ativado"],
                regra["mediana_valor"],
                regra["baixa_performance_ativado"],
                regra["baixa_performance_valor"],
                regra["erro_telemetria_ativado"],
                regra["erro_telemetria_valor"],
                regra["criar_os_automatica"],
                regra["enviar_email"],
                regra["email_1"],
                regra["email_2"],
                regra["email_3"],
                regra["email_4"],
                regra["email_5"],
                regra["enviar_wpp"],
                regra["wpp_1"],
                regra["wpp_2"],
                regra["wpp_3"],
                regra["wpp_4"],
                regra["wpp_5"],
            )
    return (
        None, False, "", 30, ["TODOS"], 3, 5, "SEG_SEX", False, None, False, None, False, None, False, False, "", "", "", "", "", False, "", "", "", "", ""
    )


##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    [
        Output("editar-tabela-regras-viagens-monitoramento", "rowData"),
        Output("editar-indicador-quantidade-de-veiculos", "children"),
        Output("editar-indicador-quantidade-gasto-combustivel", "children"),
        Output("editar-indicador-media-gasto-combustivel", "children"),
    ],
    [
        Input("editar-input-periodo-dias-monitoramento-regra", "value"),
        Input("editar-input-modelos-monitoramento-regra", "value"),
        Input("editar-input-quantidade-de-motoristas", "value"),
        Input("editar-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("editar-input-select-dia-linha-combustivel-regra", "value"),
        Input("editar-select-mediana", "value"),
        Input("editar-select-baixa-performace-indicativo", "value"),
        Input("editar-select-erro-telemetria", "value"),
    ],
)
def editar_atualiza_tabela_regra_viagens_monitoramento(
    data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem,
    indicativo_performace, erro_telemetria
):
    df = regra_service.get_estatistica_regras(
        data, modelos, motoristas,
        quantidade_de_viagens, dias_marcados, 
        mediana_viagem,
        indicativo_performace, erro_telemetria
    )

    if df.empty:
        return [], 0, 0, 0

    df["comb_excedente_l"] = df["comb_excedente_l"].astype(float)

    quantidade_veiculo = df["vec_num_id"].nunique()

    total_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].sum():,.2f}L"

    media_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].mean():,.2f}L"

    return df.to_dict(orient="records"), quantidade_veiculo, total_combustivel, media_combustivel


@callback(
    [
        Output("editar-tabela-regras-viagens-monitoramento", "style"),
        Output("editar-row-labels-adicionais", "style"),
    ],
    Input("editar-btn-preview-regra-monitoramento", "n_clicks"),
    prevent_initial_call=True
)
def editar_toggle_tabela(n_clicks):
    base_style = {
        "height": 400,
        "resize": "vertical",
        "overflow": "hidden",
    }
    if n_clicks % 2 == 1:
        return {**base_style, "display": "block"}, {"display": "block"}
    return {**base_style, "display": "none"}, {"display": "none"}


##############################################################################
# Callbacks para switch ######################################################
##############################################################################

@callback(
    [
        Output("editar-container-mediana", "style"),
        Output("editar-select-mediana", "value"),
    ],
    [
        Input("editar-switch-mediana", "checked"),
        Input("editar-select-mediana", "value"),
    ]
)
def editar_input_mediana(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None

    return activate, value

@callback(
    [
        Output("editar-container-baixa-performace-indicativo", "style"),
        Output("editar-select-baixa-performace-indicativo", "value"),
    ],
    [
        Input("editar-switch-baixa-performace-indicativo", "checked"),
        Input("editar-select-baixa-performace-indicativo", "value"),
    ]
)
def editar_input_baixa_performace_indicativo(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None
    return activate, value

@callback(
    [
        Output("editar-container-erro-telemetria", "style"),
        Output("editar-select-erro-telemetria", "value"),
    ],
    [
        Input("editar-switch-erro-telemetria", "checked"),
        Input("editar-select-erro-telemetria", "value"),
    ]
)
def editar_input_erro_telemetria(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None
    return activate, value

# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("editar-input-wpp-destino-container-regra-editar-combustivel", "style"),
    Input("editar-switch-enviar-wpp-regra-criar-combustivel", "checked"),
)
def editar_mostra_input_wpp_destino(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}
    
# Função para mostrar o input de Email de destino
@callback(
    Output("editar-input-email-destino-container-regra-editar-combustivel", "style"),
    Input("editar-switch-enviar-email-regra-criar-combustivel", "checked"),
)
def editar_mostra_input_email_destino(email_ativo):
    if email_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}

##############################################################################
# Labels #####################################################################
##############################################################################
def gera_labels_inputs_editar(campo):
    @callback(
        Output(f"editar-{campo}-labels", "children"),
        [
            Input("editar-input-periodo-dias-monitoramento-regra", "value"),  # datas
            Input("editar-input-modelos-monitoramento-regra", "value"),        # modelos
            Input("editar-input-quantidade-de-motoristas", "value"), # Motoristas
            Input("editar-input-quantidade-de-viagens-monitoramento-regra", "value"),  # qtd viagens
            Input("editar-input-select-dia-linha-combustivel-regra", "value"),         # dias marcados
            Input("editar-select-mediana", "value"),
            Input("editar-select-baixa-performace-indicativo", "value"),
            Input("editar-select-erro-telemetria", "value"),
        ]
    )
    def editar_atualiza_labels_inputs(
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
    return dmc.Group(id=f"editar-{campo}-labels", children=[], gap="xs")


@callback(
    Output("editar-input-modelos-monitoramento-regra", "value", allow_duplicate=True),
    Input("editar-input-modelos-monitoramento-regra", "value"),
    prevent_initial_call=True,
)
def editar_atualizar_modelos_selecao(valores_selecionados):
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

######################## Corrigir input #############################
# Função para validar o input de email de destino
def verifica_erro_email(email_destino):
    if not email_destino:
        return False

    email_limpo = email_destino.strip()

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email_limpo):
        return True

    return False


@callback(
    Output("editar-input-email-1-regra-criar-combustivel", "error"),
    Input("editar-input-email-1-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_email_1(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("editar-input-email-2-regra-criar-combustivel", "error"),
    Input("editar-input-email-2-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_email_2(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("editar-input-email-3-regra-criar-combustivel", "error"),
    Input("editar-input-email-3-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_email_3(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("editar-input-email-4-regra-criar-combustivel", "error"),
    Input("editar-input-email-4-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_email_4(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("editar-input-email-5-regra-criar-combustivel", "error"),
    Input("editar-input-email-5-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_email_5(email_destino):
    return verifica_erro_email(email_destino)


# Função para validar o input de telefone
def verifica_erro_wpp(wpp_telefone):
    # Se estive vazio, não considere erro
    if not wpp_telefone:
        return False

    wpp_limpo = wpp_telefone.replace(" ", "")

    padroes_validos = [
        r"^\(\d{2}\)\d{5}-\d{4}$",  # (62)99999-9999
        r"^\(\d{2}\)\d{4}-\d{4}$",  # (62)9999-9999
        r"^\d{2}\d{5}-\d{4}$",  # 6299999-9999
        r"^\d{2}\d{4}-\d{4}$",  # 629999-9999
        r"^\d{10}$",  # 6299999999 (fixo)
        r"^\d{11}$",  # 62999999999 (celular)
    ]

    if not any(re.match(padrao, wpp_limpo) for padrao in padroes_validos):
        return True

    return False


@callback(
    Output("editar-input-wpp-1-regra-criar-combustivel", "error"),
    Input("editar-input-wpp-1-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_wpp_1(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("editar-input-wpp-2-regra-criar-combustivel", "error"),
    Input("editar-input-wpp-2-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_wpp_2(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("editar-input-wpp-3-regra-criar-combustivel", "error"),
    Input("editar-input-wpp-3-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_wpp_3(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("editar-input-wpp-4-regra-criar-combustivel", "error"),
    Input("editar-input-wpp-4-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_wpp_4(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("editar-input-wpp-5-regra-criar-combustivel", "error"),
    Input("editar-input-wpp-5-regra-criar-combustivel", "value"),
)
def editar_verifica_erro_wpp_5(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


##############################################################################
# Callbacks para atualizar a regra ###########################################
##############################################################################

@callback(
    Output("editar-mensagem-sucesso", "children"),
    [
        Input("editar-btn-atualizar-regra-monitoramento", "n_clicks"),
    ],
    [
        State("editar-input-nome-regra-monitoramento", "value"),
        State("editar-input-periodo-dias-monitoramento-regra", "value"),
        State("editar-input-modelos-monitoramento-regra", "value"),
        State("editar-input-quantidade-de-motoristas", "value"),
        State("editar-input-quantidade-de-viagens-monitoramento-regra", "value"),
        State("editar-input-select-dia-linha-combustivel-regra", "value"),
        State("editar-select-mediana", "value"),
        State("editar-select-baixa-performace-indicativo", "value"),
        State("editar-select-erro-telemetria", "value"),
        State("editar-switch-os-automatica", "checked"),
        State("editar-switch-enviar-email-regra-criar-combustivel", "checked"),
        State("editar-switch-enviar-wpp-regra-criar-combustivel", "checked"),
        # Emails
        State("editar-input-email-1-regra-criar-combustivel", "value"),
        State("editar-input-email-2-regra-criar-combustivel", "value"),
        State("editar-input-email-3-regra-criar-combustivel", "value"),
        State("editar-input-email-4-regra-criar-combustivel", "value"),
        State("editar-input-email-5-regra-criar-combustivel", "value"),
        # WhatsApps
        State("editar-input-wpp-1-regra-criar-combustivel", "value"),
        State("editar-input-wpp-2-regra-criar-combustivel", "value"),
        State("editar-input-wpp-3-regra-criar-combustivel", "value"),
        State("editar-input-wpp-4-regra-criar-combustivel", "value"),
        State("editar-input-wpp-5-regra-criar-combustivel", "value"),
        State("store-editar-input-id-editar-regra", "data"),
    ],
    prevent_initial_call=True
)
def editar_atualizar_regra_monitoramento(
    n_clicks,
    nome_regra, data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem,
    indicativo_performace, erro_telemetria,
    criar_os_automatica, enviar_email, enviar_whatsapp,
    email1, email2, email3, email4, email5,
    wpp1, wpp2, wpp3, wpp4, wpp5,
    id_regra
): 
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "editar-btn-atualizar-regra-monitoramento":
        return dash.no_update

    if not n_clicks or n_clicks <= 0: 
        return dash.no_update

    # Monta listas de emails e WhatsApps
    email_list = [e for e in [email1, email2, email3, email4, email5] if e]
    wpp_list = [w for w in [wpp1, wpp2, wpp3, wpp4, wpp5] if w]

    try:
        regra_service.atualizar_regra_monitoramento(
            id_regra,
            nome_regra, data, modelos, motoristas,
            quantidade_de_viagens, dias_marcados, 
            mediana_viagem,
            indicativo_performace, erro_telemetria,
            criar_os_automatica, enviar_email, 
            enviar_whatsapp, wpp_list, email_list
        )
        return "✅ Regra atualizada com sucesso!"
    except Exception as e:
        return f"❌ Erro ao atualizar a regra: {e}"


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # URL e Store
        dcc.Location(id='url', refresh=False),
        
        # Estado
        dcc.Store(id="store-editar-input-id-editar-regra"),
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-editar-regra",
            loaderProps={"size": "xl"},
            overlayProps={
                "radius": "lg",
                "blur": 2,
                "style": {
                    "top": 0,
                    "left": 0,
                    "width": "100vw",
                    "height": "100vh",
                },
            },
            zIndex=10,
        ),

        # Cabeçalho
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
                                                [html.Strong("Editar Regra de Monitoramento da Frota")],
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
                                                dbc.Label("ID da Regra (somente leitura)"),
                                                dbc.Input(
                                                    id="editar-input-id-regra-monitoramento",
                                                    type="text",
                                                    placeholder="ID da Regra",
                                                    value="",
                                                    disabled=True,
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
                                                dbc.Label("Nome da Regra de Monitoramneto"),
                                                dbc.Input(
                                                    id="editar-input-nome-regra-monitoramento",
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
                                                            id="editar-input-periodo-dias-monitoramento-regra",
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
                                                    id="editar-input-modelos-monitoramento-regra",
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
                                                            id="editar-input-quantidade-de-motoristas",
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
                                                            id="editar-input-quantidade-de-viagens-monitoramento-regra",
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
                                                    id="editar-input-select-dia-linha-combustivel-regra",
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
                                                    id="editar-switch-mediana",
                                                    label="% Mínima de Viagens Abaixo da Mediana",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="editar-select-mediana",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="editar-container-mediana",
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
                                                    id="editar-switch-baixa-performace-indicativo",
                                                    label="% Mínima de Viagens com Supeita ou Baixa Performance",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="editar-select-baixa-performace-indicativo",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=0,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="editar-container-baixa-performace-indicativo",
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
                                                    id="editar-switch-erro-telemetria",
                                                    label="% Mínima de Viagens com Erro de Telemetria",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="editar-select-erro-telemetria",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="editar-container-erro-telemetria",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),

                                dbc.Col(
                                    dbc.Card(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dmc.Switch(
                                                        id="editar-switch-enviar-email-regra-criar-combustivel",
                                                        label="Enviar email",
                                                        checked=False,
                                                        size="md",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Row(
                                                        [
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dbc.Label("Emails de destino (Digite até 5 emails)"),
                                                                md=12,
                                                            ),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-email-1-regra-criar-combustivel",
                                                                    placeholder="email1@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-email-2-regra-criar-combustivel",
                                                                    placeholder="email2@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-email-3-regra-criar-combustivel",
                                                                    placeholder="email3@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-email-4-regra-criar-combustivel",
                                                                    placeholder="email4@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-email-5-regra-criar-combustivel",
                                                                    placeholder="email5@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                        ],
                                                        align="center",
                                                    ),
                                                    id="editar-input-email-destino-container-regra-editar-combustivel",
                                                    md=12,
                                                ),
                                            ],
                                            align="center",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dmc.Switch(
                                                        id="editar-switch-enviar-wpp-regra-criar-combustivel",
                                                        label="Enviar WhatsApp",
                                                        checked=False,
                                                        size="md",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(
                                                    dbc.Row(
                                                        [
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dbc.Label("WhatsApp de destino (Digite até 5 números)"),
                                                                md=12,
                                                            ),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-wpp-1-regra-criar-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-wpp-2-regra-criar-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-wpp-3-regra-criar-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-wpp-4-regra-criar-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="editar-input-wpp-5-regra-criar-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                        ],
                                                        align="center",
                                                    ),
                                                    id="editar-input-wpp-destino-container-regra-editar-combustivel",
                                                    md=12,
                                                ),
                                            ],
                                            align="center",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                # OS automática
                                dbc.Col(
                                    dbc.Card(
                                        dbc.Row(
                                            dbc.Col(
                                                dmc.Switch(
                                                    id="editar-switch-os-automatica",
                                                    label="Criar OS automática",
                                                    checked=False,
                                                    size="md",
                                                ),
                                                width="auto",
                                                style={"margin": "0 auto"},
                                            ),
                                            justify="center",
                                            align="center",
                                        ),
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

        dmc.Space(h=10),

        # Botões de Preview e Atualizar Regra
        dbc.Row(
            [
                # Botão Preview
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Preview da Regra",
                                id="editar-btn-preview-regra-monitoramento",
                                n_clicks=0,
                                style={
                                    "background-color": "#f9a704",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "16px 32px",
                                    "border-radius": "8px",
                                    "cursor": "pointer",
                                    "font-size": "20px",
                                    "font-weight": "bold",
                                    "width": "250px",
                                    "height": "60px",
                                },
                            ),
                            html.Div(
                                id="editar-mensagem-sucesso-preview",
                                style={"marginTop": "10px", "fontWeight": "bold"}
                            ),
                        ],
                        style={"textAlign": "center"},
                    ),
                    width="auto",
                ),

                # Botão Atualizar
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Atualizar Regra",
                                id="editar-btn-atualizar-regra-monitoramento",
                                n_clicks=0,
                                style={
                                    "background-color": "#007bff",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "16px 32px",
                                    "border-radius": "8px",
                                    "cursor": "pointer",
                                    "font-size": "20px",
                                    "font-weight": "bold",
                                    "width": "250px",
                                    "height": "60px",
                                },
                            ),
                            html.Div(
                                id="editar-mensagem-sucesso",
                                style={"marginTop": "10px", "fontWeight": "bold"}
                            ),
                        ],
                        style={"textAlign": "center"},
                    ),
                    width="auto",
                ),
            ],
            justify="center",
            align="center",
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
                                        dmc.Title(id="editar-indicador-quantidade-gasto-combustivel", order=2),
                                        DashIconify(icon="mdi:gas-station", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de combustível a mais utilizado"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="editar-indicador-quantidade-de-veiculos", order=2),
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
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="editar-indicador-media-gasto-combustivel", order=2),
                                        DashIconify(icon="mdi:gas-station", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média de combustível a mais utilizado"),
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
                dbc.Col(gera_labels_inputs_editar("labels-regra-service"), width=True),
            ],
            style={"display": "none"},
            id="editar-row-labels-adicionais"
        ),

        dmc.Space(h=20),

        # Tabela de regras
        html.Div(
            id="editar-container-tabela-regras",
            children=[
                dag.AgGrid(
                    id="editar-tabela-regras-viagens-monitoramento",
                    columnDefs=regras_tabela.tbl_perc_viagens_monitoramento,
                    rowData=[],
                    defaultColDef={"filter": True, "floatingFilter": True},
                    columnSize="autoSize",
                    dashGridOptions={
                        "localeText": locale_utils.AG_GRID_LOCALE_BR,
                        "rowSelection": "multiple",
                        "enableCellTextSelection": True,
                        "ensureDomOrder": True,
                    },
                    style={
                        "height": 400,
                        "resize": "vertical",
                        "overflow": "hidden",
                        "display": "none"
                    },
                )
            ]
        ),
    ],
)

# Registrar página
dash.register_page(__name__, name="Editar Regra", path="/regra-editar", icon="carbon:rule-draft", hide_page=True)