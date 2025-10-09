#!/usr/bin/env python
# coding: utf-8

# Tela para criar uma regra para detecção de problemas de consumo de combustível

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime, timedelta
import pandas as pd
import re

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
from modules.entities_utils import  get_modelos_veiculos_regras


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

##################################################################################
# LOADER #####################################################################
###################################################################################

##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    [
        Output("tabela-regras-viagens-monitoramento", "rowData"),
        Output("indicador-quantidade-de-veiculos", "children"),
        Output("indicador-quantidade-gasto-combustivel", "children"),
        Output("indicador-media-gasto-combustivel", "children"),
    ],
    [
        Input("pag-criar-regra-input-periodo-dias-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-modelos-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-quantidade-de-motoristas", "value"),
        Input("pag-criar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-select-dia-linha-combustivel-regra", "value"),
        Input("pag-criar-regra-select-mediana", "value"),
        Input("pag-criar-regra-select-baixa-performace-indicativo", "value"),
        Input("pag-criar-regra-select-erro-telemetria", "value"),
    ],
)
def atualiza_tabela_regra_viagens_monitoramento(
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

    df['comb_excedente_l'] = df['comb_excedente_l'].astype(float)

    quantidade_veiculo = df['vec_num_id'].nunique()

    total_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].sum():,.2f}L"

    media_combustivel = f"{df[df['comb_excedente_l'] > 0]['comb_excedente_l'].mean():,.2f}L"

    return df.to_dict(orient="records"), quantidade_veiculo, total_combustivel, media_combustivel



@callback(
    Output("mensagem-sucesso-criar", "children"),
    [
        Input("btn-criar-regra-monitoramento", "n_clicks"),
        Input("pag-criar-regra-input-nome-regra-monitoramento", "value"),
        Input("pag-criar-regra-input-periodo-dias-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-modelos-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-quantidade-de-motoristas", "value"),
        Input("pag-criar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("pag-criar-regra-input-select-dia-linha-combustivel-regra", "value"),
        Input("pag-criar-regra-select-mediana", "value"),
        Input("pag-criar-regra-select-baixa-performace-indicativo", "value"),
        Input("pag-criar-regra-select-erro-telemetria", "value"),
        Input("switch-os-automatica", "checked"),
        Input("pag-criar-regra-switch-enviar-email-regra-criar-combustivel", "checked"),
        Input("switch-enviar-wpp-regra-criar-combustivel", "checked"),
        # Emails
        Input("input-email-1-regra-criar-combustivel", "value"),
        Input("input-email-2-regra-criar-combustivel", "value"),
        Input("input-email-3-regra-criar-combustivel", "value"),
        Input("input-email-4-regra-criar-combustivel", "value"),
        Input("input-email-5-regra-criar-combustivel", "value"),
        # WhatsApps
        Input("input-wpp-1-regra-criar-combustivel", "value"),
        Input("input-wpp-2-regra-criar-combustivel", "value"),
        Input("input-wpp-3-regra-criar-combustivel", "value"),
        Input("input-wpp-4-regra-criar-combustivel", "value"),
        Input("input-wpp-5-regra-criar-combustivel", "value"),
    ],
    prevent_initial_call=True
)
def salvar_regra_monitoramento(
    n_clicks, nome_regra,
    data, modelos, motoristas,
    quantidade_de_viagens, dias_marcados, 
    mediana_viagem, 
    indicativo_performace, erro_telemetria,
    criar_os_automatica, enviar_email, enviar_whatsapp,
    email1, email2, email3, email4, email5,
    wpp1, wpp2, wpp3, wpp4, wpp5
): 
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id != "btn-criar-regra-monitoramento":
        return dash.no_update

    if not n_clicks or n_clicks <= 0: 
        return dash.no_update

    # Monta listas de emails e WhatsApps
    email_list = [e for e in [email1, email2, email3, email4, email5] if e]
    wpp_list = [w for w in [wpp1, wpp2, wpp3, wpp4, wpp5] if w]

    try:
        regra_service.salvar_regra_monitoramento(
            nome_regra, data, modelos, motoristas,
            quantidade_de_viagens, dias_marcados, 
            mediana_viagem,
            indicativo_performace, erro_telemetria,
            criar_os_automatica, enviar_email, 
            enviar_whatsapp, wpp_list, email_list
        )
        return "✅ Regra salva com sucesso!"
    except Exception as e:
        return f"❌ Erro ao salvar a regra: {e}"



@callback(
    Output("tabela-regras-viagens-monitoramento", "style"),
    Output("row-labels-adicionais", "style"),
    Input("btn-preview-regra-monitoramento", "n_clicks"),
    prevent_initial_call=True
)
def toggle_tabela(n_clicks):
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
        Output("pag-criar-regra-container-mediana", "style"),
        Output("pag-criar-regra-select-mediana", "value"),
    ],
    [
        Input("pag-criar-regra-switch-mediana", "checked"),
        Input("pag-criar-regra-select-mediana", "value"),
    ]
)
def input_mediana(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None

    return activate, value

@callback(
    [
        Output("pag-criar-regra-container-baixa-performace-indicativo", "style"),
        Output("pag-criar-regra-select-baixa-performace-indicativo", "value"),
    ],
    [
        Input("pag-criar-regra-switch-baixa-performace-indicativo", "checked"),
        Input("pag-criar-regra-select-baixa-performace-indicativo", "value"),
    ]
)
def input_baixa_performace_indicativo(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None
    return activate, value

@callback(
    [
        Output("pag-criar-regra-container-erro-telemetria", "style"),
        Output("pag-criar-regra-select-erro-telemetria", "value"),
    ],
    [
        Input("pag-criar-regra-switch-erro-telemetria", "checked"),
        Input("pag-criar-regra-select-erro-telemetria", "value"),
    ]
)
def input_erro_telemetria(ativado, value):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}
    if not ativado:
        value = None
    return activate, value

# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("input-wpp-destino-container-regra-criar-combustivel", "style"),
    Input("switch-enviar-wpp-regra-criar-combustivel", "checked"),
)
def mostra_input_wpp_destino(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}
    
# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("pag-criar-regra-input-email-destino-container-regra-criar-combustivel", "style"),
    Input("pag-criar-regra-switch-enviar-email-regra-criar-combustivel", "checked"),
)
def mostra_input_email_destino(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}
##############################################################################
# Labels #####################################################################
##############################################################################
def gera_labels_inputs(campo):
    @callback(
        Output(f"{campo}-labels", "children"),
        [
            Input("pag-criar-regra-input-periodo-dias-monitoramento-regra", "value"),  # datas
            Input("pag-criar-regra-input-modelos-monitoramento-regra", "value"),        # modelos
            Input("pag-criar-regra-input-quantidade-de-motoristas", "value"), # Motoristas
            Input("pag-criar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),  # qtd viagens
            Input("pag-criar-regra-input-select-dia-linha-combustivel-regra", "value"),         # dias marcados
            Input("pag-criar-regra-select-mediana", "value"),
            Input("pag-criar-regra-select-baixa-performace-indicativo", "value"),
            Input("pag-criar-regra-select-erro-telemetria", "value"),
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


@callback(
    Output("pag-criar-regra-input-modelos-monitoramento-regra", "value"),
    Input("pag-criar-regra-input-modelos-monitoramento-regra", "value"),
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
    Output("input-email-1-regra-criar-combustivel", "error"),
    Input("input-email-1-regra-criar-combustivel", "value"),
)
def verifica_erro_email_1(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("input-email-2-regra-criar-combustivel", "error"),
    Input("input-email-2-regra-criar-combustivel", "value"),
)
def verifica_erro_email_2(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("input-email-3-regra-criar-combustivel", "error"),
    Input("input-email-3-regra-criar-combustivel", "value"),
)
def verifica_erro_email_3(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("input-email-4-regra-criar-combustivel", "error"),
    Input("input-email-4-regra-criar-combustivel", "value"),
)
def verifica_erro_email_4(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("input-email-5-regra-criar-combustivel", "error"),
    Input("input-email-5-regra-criar-combustivel", "value"),
)
def verifica_erro_email_5(email_destino):
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
    Output("input-wpp-1-regra-criar-combustivel", "error"),
    Input("input-wpp-1-regra-criar-combustivel", "value"),
)
def verifica_erro_wpp_1(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("input-wpp-2-regra-criar-combustivel", "error"),
    Input("input-wpp-2-regra-criar-combustivel", "value"),
)
def verifica_erro_wpp_2(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("input-wpp-3-regra-criar-combustivel", "error"),
    Input("input-wpp-3-regra-criar-combustivel", "value"),
)
def verifica_erro_wpp_3(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("input-wpp-4-regra-criar-combustivel", "error"),
    Input("input-wpp-4-regra-criar-combustivel", "value"),
)
def verifica_erro_wpp_4(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("input-wpp-5-regra-criar-combustivel", "error"),
    Input("input-wpp-5-regra-criar-combustivel", "value"),
)
def verifica_erro_wpp_5(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
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
                                                    id="pag-criar-regra-input-nome-regra-monitoramento",
                                                    type="text",
                                                    placeholder="Digite o nome da regra...",
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
                                                            id="pag-criar-regra-input-periodo-dias-monitoramento-regra",
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
                                                    id="pag-criar-regra-input-modelos-monitoramento-regra",
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
                                                            id="pag-criar-regra-input-quantidade-de-motoristas",
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
                                                            id="pag-criar-regra-input-quantidade-de-viagens-monitoramento-regra",
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
                                                    id="pag-criar-regra-input-select-dia-linha-combustivel-regra",
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
                                                    id="pag-criar-regra-switch-mediana",
                                                    label="% Mínima de Viagens Abaixo da Mediana",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-criar-regra-select-mediana",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-criar-regra-container-mediana",
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
                                                    id="pag-criar-regra-switch-baixa-performace-indicativo",
                                                    label="% Mínima de Viagens com Supeita ou Baixa Performance",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-criar-regra-select-baixa-performace-indicativo",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=0,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-criar-regra-container-baixa-performace-indicativo",
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
                                                    id="pag-criar-regra-switch-erro-telemetria",
                                                    label="% Mínima de Viagens com Erro de Telemetria",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-criar-regra-select-erro-telemetria",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-criar-regra-container-erro-telemetria",
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
                                                            id="pag-criar-regra-switch-enviar-email-regra-criar-combustivel",
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
                                                                        id="input-email-1-regra-criar-combustivel",
                                                                        placeholder="email1@odilonsantos.com",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="mdi:email"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-email-2-regra-criar-combustivel",
                                                                        placeholder="email2@odilonsantos.com",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="mdi:email"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-email-3-regra-criar-combustivel",
                                                                        placeholder="email3@odilonsantos.com",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="mdi:email"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-email-4-regra-criar-combustivel",
                                                                        placeholder="email4@odilonsantos.com",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="mdi:email"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-email-5-regra-criar-combustivel",
                                                                        placeholder="email5@odilonsantos.com",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="mdi:email"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                            ],
                                                            align="center",
                                                        ),
                                                        id="pag-criar-regra-input-email-destino-container-regra-criar-combustivel",
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
                                                            id="switch-enviar-wpp-regra-criar-combustivel",
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
                                                                        id="input-wpp-1-regra-criar-combustivel",
                                                                        placeholder="(62) 99999-9999",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-wpp-2-regra-criar-combustivel",
                                                                        placeholder="(62) 99999-9999",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-wpp-3-regra-criar-combustivel",
                                                                        placeholder="(62) 99999-9999",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-wpp-4-regra-criar-combustivel",
                                                                        placeholder="(62) 99999-9999",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                                dmc.Space(h=10),
                                                                dbc.Col(
                                                                    dmc.TextInput(
                                                                        id="input-wpp-5-regra-criar-combustivel",
                                                                        placeholder="(62) 99999-9999",
                                                                        value="",
                                                                        leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                    ),
                                                                    md=12,
                                                                ),
                                                            ],
                                                            align="center",
                                                        ),
                                                        id="input-wpp-destino-container-regra-criar-combustivel",
                                                        md=12,
                                                    ),
                                                ],
                                                align="center",
                                            ),
                                            body=True,
                                        ),
                                ),
                                dmc.Space(h=10),
                                # OS automática
                                dbc.Col(
                                    dbc.Card(
                                        dbc.Row(
                                            dbc.Col(
                                                dmc.Switch(
                                                    id="switch-os-automatica",
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
                                    md=12,  # <-- Mantém o mesmo tamanho
                                ),
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),

        dmc.Space(h=10),

       # Botões de Preview e Criar Regra
        dbc.Row(
            [
                # Botão Preview
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Preview da Regra",
                                id="btn-preview-regra-monitoramento",
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
                                id="mensagem-sucesso-preview",
                                style={"marginTop": "10px", "fontWeight": "bold"}
                            ),
                        ],
                        style={"textAlign": "center"},
                    ),
                    width="auto",
                ),

                # Botão Criar
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Criar Regra",
                                id="btn-criar-regra-monitoramento",
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
                        ],
                        style={"textAlign": "center"},
                    ),
                    width="auto",
                ),
                html.Div(
                    id="mensagem-sucesso-criar",
                    style={"marginTop": "10px", "fontWeight": "bold"}
                ),

            ],
            justify="center",      # Centraliza horizontalmente
            align="center",        # Alinha verticalmente
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
                                        dmc.Title(id="indicador-quantidade-gasto-combustivel", order=2),
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
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-media-gasto-combustivel", order=2),
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
                dbc.Col(gera_labels_inputs("labels-regra-service"), width=True),
            ],
                style={"display": "none"},  # começa escondido
                id="row-labels-adicionais"
        ),

        dmc.Space(h=20),

        # Tabela de regras
        html.Div(
            id="container-tabela-regras",
            children=[
                dag.AgGrid(
                    id="tabela-regras-viagens-monitoramento",
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
                        "display": "none"  # começa escondida
                    },
                )
            ]
        ),

    ],
    style={"margin-top": "20px", "margin-bottom": "20px"},
)

dash.register_page(__name__, name="Regras de monitoramento", path="/regras-monitoramento",  icon="carbon:rule-draft", hide_page=True)
