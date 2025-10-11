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
from modules.entities_utils import get_modelos_veiculos_com_combustivel

# Imports específicos
from modules.regras.regras_service import RegrasService
import modules.regras.tabela as regras_tabela

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
# Callbacks para os inputs via URL ###########################################
##############################################################################
@callback(
    [
        Output("store-pag-editar-regra-input-id-pag-editar-regra", "data"),
        Output("pag-editar-regra-input-nome-regra-monitoramento", "value"),
        Output("pag-editar-regra-input-periodo-dias-monitoramento-regra", "value"),
        Output("pag-editar-regra-input-modelos-monitoramento-regra", "value"),
        Output("pag-editar-regra-input-quantidade-de-motoristas", "value"),
        Output("pag-editar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Output("pag-editar-regra-input-select-dia-linha-combustivel-regra", "value"),
        Output("pag-editar-regra-switch-mediana", "checked"),
        Output("pag-editar-regra-select-mediana", "value"),
        Output("pag-editar-regra-switch-baixa-performace-indicativo", "checked"),
        Output("pag-editar-regra-select-baixa-performace-indicativo", "value"),
        Output("pag-editar-regra-switch-erro-telemetria", "checked"),
        Output("pag-editar-regra-select-erro-telemetria", "value"),
        Output("pag-editar-regra-switch-os-automatica", "checked"),
        Output("pag-editar-regra-switch-enviar-email-regra-edit-combustivel", "checked"),
        Output("pag-editar-regra-input-email-1-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-email-2-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-email-3-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-email-4-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-email-5-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-switch-enviar-wpp-regra-edit-combustivel", "checked"),
        Output("pag-editar-regra-input-wpp-1-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-wpp-2-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-wpp-3-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-wpp-4-regra-edit-combustivel", "value"),
        Output("pag-editar-regra-input-wpp-5-regra-edit-combustivel", "value"),
    ],
    Input("url", "href"),
    running=[(Output("loading-overlay-guia-pag-editar-regra", "visible"), True, False)],
)
def callback_receber_campos_via_url_editar_regra(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    if not parsed_url.path.startswith("/regra-editar"):
        raise dash.exceptions.PreventUpdate

    # Store da regra padrão
    store_id_regra = {"id_regra": -1, "valido": False}
    # Resposta padrão
    resposta_padrao = [store_id_regra] + [dash.no_update] * 25

    id_regra = query_params.get("id_regra", [0])[0]

    if not id_regra or int(id_regra) == 0:
        return resposta_padrao

    # Busca a regra no banco
    regra = regra_service.get_regra_by_id(id_regra)

    if regra.empty:
        return resposta_padrao

    # Pega a primeira linha do DataFrame
    linha = regra.iloc[0]

    # Monta o retorno com os valores reais
    store_id = {"id_regra": linha["id"], "valido": True}

    return [
        store_id,
        linha["nome_regra"],
        int(linha["periodo"]),
        linha["modelos_veiculos"] if linha["modelos_veiculos"] else ["TODOS"],
        linha["qtd_min_motoristas"],
        linha["qtd_min_viagens"],
        linha["dias_marcados"] if linha["dias_marcados"] else "SEG_SEX",
        linha["usar_mediana_viagem"],
        linha["limite_mediana"],
        linha["usar_indicativo_baixa_performace"],
        linha["limite_baixa_perfomance"],
        linha["usar_erro_telemetria"],
        linha["limite_erro_telemetria"],
        linha["criar_os_automatica"],
        linha["target_email"],
        linha["target_email_dest1"] or "",
        linha["target_email_dest2"] or "",
        linha["target_email_dest3"] or "",
        linha["target_email_dest4"] or "",
        linha["target_email_dest5"] or "",
        linha["target_wpp"],
        linha["target_wpp_dest1"] or "",
        linha["target_wpp_dest2"] or "",
        linha["target_wpp_dest3"] or "",
        linha["target_wpp_dest4"] or "",
        linha["target_wpp_dest5"] or "",
    ]


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(dias_monitoramento, qtd_min_motoristas, qtd_min_viagens, lista_modelos):
    if dias_monitoramento is None or dias_monitoramento <= 0:
        return False

    if qtd_min_motoristas is None or qtd_min_motoristas <= 0:
        return False

    if qtd_min_viagens is None or qtd_min_viagens <= 0:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    return True


def verifica_erro_email(email_destino):
    if not email_destino:
        return False

    email_limpo = email_destino.strip()

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email_limpo):
        return True

    return False


@callback(
    Output("pag-editar-regra-input-email-1-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-email-1-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_email_1(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-editar-regra-input-email-2-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-email-2-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_email_2(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-editar-regra-input-email-3-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-email-3-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_email_3(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-editar-regra-input-email-4-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-email-4-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_email_4(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-editar-regra-input-email-5-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-email-5-regra-edit-combustivel", "value"),
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
    Output("pag-editar-regra-input-wpp-1-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-wpp-1-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_wpp_1(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-editar-regra-input-wpp-2-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-wpp-2-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_wpp_2(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-editar-regra-input-wpp-3-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-wpp-3-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_wpp_3(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-editar-regra-input-wpp-4-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-wpp-4-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_wpp_4(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-editar-regra-input-wpp-5-regra-edit-combustivel", "error"),
    Input("pag-editar-regra-input-wpp-5-regra-edit-combustivel", "value"),
)
def editar_verifica_erro_wpp_5(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-editar-regra-input-modelos-monitoramento-regra", "value", allow_duplicate=True),
    Input("pag-editar-regra-input-modelos-monitoramento-regra", "value"),
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


##############################################################################
# Labels #####################################################################
##############################################################################
def gera_labels_inputs_editar(campo):
    @callback(
        Output(f"pag-editar-regra-{campo}-labels", "children"),
        [
            Input("pag-editar-regra-input-periodo-dias-monitoramento-regra", "value"),  # datas
            Input("pag-editar-regra-input-modelos-monitoramento-regra", "value"),  # modelos
            Input("pag-editar-regra-input-quantidade-de-motoristas", "value"),  # Motoristas
            Input("pag-editar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),  # qtd viagens
            Input("pag-editar-regra-input-select-dia-linha-combustivel-regra", "value"),  # dias marcados
            Input("pag-editar-regra-select-mediana", "value"),
            Input("pag-editar-regra-select-baixa-performace-indicativo", "value"),
            Input("pag-editar-regra-select-erro-telemetria", "value"),
        ],
    )
    def editar_atualiza_labels_inputs(
        datas, modelos, motoristas, qtd_viagens, dias_marcados, mediana, indicativo, erro
    ):
        badges = [
            dmc.Badge(
                "Filtro", color="gray", variant="outline", size="lg", style={"fontSize": 16, "padding": "6px 12px"}
            )
        ]

        # Datas
        if datas:
            data_inicio = pd.to_datetime(datetime.now() - timedelta(days=datas)).strftime("%d/%m/%Y")
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
    return dmc.Group(id=f"pag-editar-regra-{campo}-labels", children=[], gap="xs")


##############################################################################
# Callbacks para dados ######################################################
##############################################################################
@callback(
    [
        Output("pag-editar-regra-tabela-preview-viagens-monitoramento", "rowData"),
        Output("pag-editar-regra-indicador-quantidade-de-veiculos", "children"),
        Output("pag-editar-regra-indicador-consumo-km-l", "children"),
        Output("pag-editar-regra-indicador-litros-excedentes", "children"),
        Output("pag-editar-regra-indicador-gasto-combustivel-excedente", "children"),
    ],
    [
        Input("pag-editar-regra-input-periodo-dias-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-modelos-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-quantidade-de-motoristas", "value"),
        Input("pag-editar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-select-dia-linha-combustivel-regra", "value"),
        Input("pag-editar-regra-select-mediana", "value"),
        Input("pag-editar-regra-select-baixa-performace-indicativo", "value"),
        Input("pag-editar-regra-select-erro-telemetria", "value"),
    ],
)
def cb_editar_regra_preview_regra(
    dias_monitoramento,
    lista_modelos,
    qtd_min_motoristas,
    qtd_min_viagens,
    dias_marcados,
    limite_mediana,
    limite_baixa_perfomance,
    limite_erro_telemetria,
):
    # Valida input
    if not input_valido(dias_monitoramento, qtd_min_motoristas, qtd_min_viagens, lista_modelos):
        return [], 0, 0, 0, 0

    df = regra_service.get_preview_regra(
        dias_monitoramento,
        lista_modelos,
        qtd_min_motoristas,
        qtd_min_viagens,
        dias_marcados,
        limite_mediana,
        limite_baixa_perfomance,
        limite_erro_telemetria,
    )

    if df.empty:
        return [], 0, 0, 0, 0

    # Ação de visualização
    df["acao"] = "🔍 Detalhar"

    # Preço
    df["custo_excedente"] = df["litros_excedentes"] * preco_diesel

    quantidade_veiculo = df["vec_num_id"].nunique()
    media_km_por_litro = str(round(df["media_km_por_litro"].mean(), 2)).replace(".", ",") + " km/L"
    total_combustivel = (f"{int(df['litros_excedentes'].sum()):,} L".replace(",", "."),)
    media_combustivel = f"R$ {int(df['custo_excedente'].sum()):,} L".replace(",", ".")

    return df.to_dict(orient="records"), quantidade_veiculo, media_km_por_litro, total_combustivel, media_combustivel


@callback(
    [
        Output("pag-editar-regra-tabela-preview-viagens-monitoramento", "style"),
        Output("pag-editar-regra-row-labels-adicionais", "style"),
    ],
    Input("pag-editar-regra-btn-preview-regra-monitoramento", "n_clicks"),
    prevent_initial_call=True,
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
    Output("pag-editar-regra-container-mediana", "style"),
    Input("pag-editar-regra-switch-mediana", "checked"),
)
def editar_input_mediana(ativado):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}

    return activate


@callback(
    Output("pag-editar-regra-container-baixa-performace-indicativo", "style"),
    Input("pag-editar-regra-switch-baixa-performace-indicativo", "checked"),
)
def editar_input_baixa_performace_indicativo(ativado):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}

    return activate


@callback(
    Output("pag-editar-regra-container-erro-telemetria", "style"),
    Input("pag-editar-regra-switch-erro-telemetria", "checked"),
)
def editar_input_erro_telemetria(ativado):
    # Se ativado (True): display block; se desativado: none
    activate = {"display": "block"} if ativado else {"display": "none"}

    return activate


# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("pag-editar-regra-input-wpp-destino-container-regra-pag-editar-regra-combustivel", "style"),
    Input("pag-editar-regra-switch-enviar-wpp-regra-edit-combustivel", "checked"),
)
def editar_mostra_input_wpp_destino(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


# Função para mostrar o input de Email de destino
@callback(
    Output("pag-editar-regra-input-email-destino-container-regra-pag-editar-regra-combustivel", "style"),
    Input("pag-editar-regra-switch-enviar-email-regra-edit-combustivel", "checked"),
)
def editar_mostra_input_email_destino(email_ativo):
    if email_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


##############################################################################
# Callbacks para atualizar ###################################################
##############################################################################


# Callback para ABRIR o modal de confirmação de atualização
@callback(
    [
        Output("modal-confirma-atualizar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("nome-regra-atualizar-gerenciar-regra", "children"),
    ],
    Input("pag-editar-regra-btn-atualizar-regra-monitoramento", "n_clicks"),
    State("pag-editar-regra-input-nome-regra-monitoramento", "value"),
    prevent_initial_call=True,
)
def abrir_modal_confirmacao_atualizar(n_clicks, nome_regra):
    if n_clicks is None or n_clicks == 0:
        return False, dash.no_update

    # Exibe o nome da regra no modal para confirmação
    nome_formatado = f'Nome da Regra: "{nome_regra}"'

    return True, nome_formatado


# Callback para FECHAR o modal de confirmação com o botão "Cancelar"
@callback(
    Output("modal-confirma-atualizar-gerenciar-regra", "opened", allow_duplicate=True),
    Input("btn-cancelar-atualizar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fechar_modal_confirmacao_atualizar(n_clicks):
    return False


# Callback para EXECUTAR a atualização e mostrar o modal de sucesso/erro
@callback(
    [
        Output("modal-confirma-atualizar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("modal-sucesso-atualizar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("modal-pag-editar-regra-erro-atualizar-regra", "opened", allow_duplicate=True),
    ],
    [
        Input("btn-confirma-atualizar-regra", "n_clicks"),
        Input("pag-editar-regra-input-nome-regra-monitoramento", "value"),
        Input("pag-editar-regra-input-periodo-dias-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-modelos-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-quantidade-de-motoristas", "value"),
        Input("pag-editar-regra-input-quantidade-de-viagens-monitoramento-regra", "value"),
        Input("pag-editar-regra-input-select-dia-linha-combustivel-regra", "value"),
        Input("pag-editar-regra-select-mediana", "value"),
        Input("pag-editar-regra-select-baixa-performace-indicativo", "value"),
        Input("pag-editar-regra-select-erro-telemetria", "value"),
        Input("pag-editar-regra-switch-os-automatica", "checked"),
        Input("pag-editar-regra-switch-enviar-email-regra-edit-combustivel", "checked"),
        Input("pag-editar-regra-switch-enviar-wpp-regra-edit-combustivel", "checked"),
        Input("pag-editar-regra-input-email-1-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-email-2-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-email-3-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-email-4-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-email-5-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-wpp-1-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-wpp-2-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-wpp-3-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-wpp-4-regra-edit-combustivel", "value"),
        Input("pag-editar-regra-input-wpp-5-regra-edit-combustivel", "value"),
        Input("store-pag-editar-regra-input-id-pag-editar-regra", "data"),
    ],
    prevent_initial_call=True,
)
def cb_atualiza_regra(
    n_clicks,
    nome_regra,
    dias_monitoramento,
    lista_modelos,
    qtd_min_motoristas,
    qtd_min_viagens,
    dias_marcados,
    limite_mediana,
    limite_baixa_perfomance,
    limite_erro_telemetria,
    criar_os_automatica,
    enviar_email,
    enviar_whatsapp,
    email_destino_1,
    email_destino_2,
    email_destino_3,
    email_destino_4,
    email_destino_5,
    wpp_telefone_1,
    wpp_telefone_2,
    wpp_telefone_3,
    wpp_telefone_4,
    wpp_telefone_5,
    id_regra_data,
):
    if n_clicks is None or n_clicks == 0:
        return False, False, False

    # Valida Resto do input
    if not input_valido(dias_monitoramento, qtd_min_motoristas, qtd_min_viagens, lista_modelos):
        return False, False, True

    # Valida nome da regra
    if not nome_regra:
        return False, False, True

    # Verifica se pelo menos um email ou wpp está ativo
    if not enviar_email and not enviar_whatsapp:
        return False, False, True

    # Verifica se há id de regra
    if id_regra_data.get("id_regra") is None:
        return False, False, True

    # Obtém id_regra
    id_regra = int(id_regra_data.get("id_regra"))

    # Valida se há pelo menos um telefone de whatsapp válido caso esteja ativo
    wpp_telefones = [wpp_telefone_1, wpp_telefone_2, wpp_telefone_3, wpp_telefone_4, wpp_telefone_5]
    wpp_tel_validos = []
    if enviar_whatsapp:
        wpp_tel_validos = [wpp for wpp in wpp_telefones if wpp != "" and not verifica_erro_wpp(wpp)]
        if len(wpp_tel_validos) == 0:
            return [True, False]

    # Valida se há pelo menos um email válido caso esteja ativo
    email_destinos = [email_destino_1, email_destino_2, email_destino_3, email_destino_4, email_destino_5]
    email_destinos_validos = []
    if enviar_email:
        email_destinos_validos = [email for email in email_destinos if email != "" and not verifica_erro_email(email)]
        if len(email_destinos_validos) == 0:
            return [True, False]

    target_wpp_telefones = wpp_telefones
    target_wpp_telefones_validos = [wpp if wpp and not verifica_erro_wpp(wpp) else None for wpp in target_wpp_telefones]

    target_email_destinos = email_destinos
    target_email_destinos_validos = [
        email if email and not verifica_erro_email(email) else None for email in target_email_destinos
    ]

    try:
        payload = {
            "nome_regra": nome_regra,
            "periodo": dias_monitoramento,
            "modelos_veiculos": lista_modelos,
            "qtd_min_motoristas": qtd_min_motoristas,
            "dias_marcados": dias_marcados,
            "qtd_min_viagens": qtd_min_viagens,
            "limite_mediana": limite_mediana,
            "usar_mediana_viagem": limite_mediana is not None,
            "limite_baixa_perfomance": limite_baixa_perfomance,
            "usar_indicativo_baixa_performace": limite_baixa_perfomance is not None,
            "limite_erro_telemetria": limite_erro_telemetria,
            "usar_erro_telemetria": limite_erro_telemetria is not None,
            "criar_os_automatica": criar_os_automatica,
            "target_email": enviar_email,
            "target_email_dest1": target_email_destinos_validos[0],
            "target_email_dest2": target_email_destinos_validos[1],
            "target_email_dest3": target_email_destinos_validos[2],
            "target_email_dest4": target_email_destinos_validos[3],
            "target_email_dest5": target_email_destinos_validos[4],
            "target_wpp": enviar_whatsapp,
            "target_wpp_dest1": target_wpp_telefones_validos[0],
            "target_wpp_dest2": target_wpp_telefones_validos[1],
            "target_wpp_dest3": target_wpp_telefones_validos[2],
            "target_wpp_dest4": target_wpp_telefones_validos[3],
            "target_wpp_dest5": target_wpp_telefones_validos[4],
        }

        regra_service.atualizar_regra_monitoramento(id_regra, payload)

        # Fecha o modal de confirmação e abre o de sucesso
        return False, True, False
    except Exception as e:
        print(f"Erro ao atualizar a regra: {e}")
        # Fecha o modal de confirmação e abre o de erro
        return False, False, True


# Callback para FECHAR os modais de sucesso e erro
@callback(
    [
        Output("modal-sucesso-atualizar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("modal-pag-editar-regra-erro-atualizar-regra", "opened", allow_duplicate=True),
    ],
    [
        Input("btn-close-modal-sucesso-atualizar-gerenciar-regra", "n_clicks"),
        Input("btn-close-pag-editar-regra-modal-erro-atualizar-regra", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def fechar_modais_resultado(n_sucesso, n_erro):
    return False, False


# Callback para REDIRECIONAR APÓS SUCESSO
@callback(
    Output("url", "href", allow_duplicate=True),
    Input("btn-close-modal-sucesso-atualizar-gerenciar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_close_modal_erro_carregar_dados_editar_regra(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    return "/regras-gerenciar"


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-pag-editar-regra-input-id-pag-editar-regra"),
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-pag-editar-regra",
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
        # Modais
        dmc.Modal(
            id="modal-confirma-atualizar-gerenciar-regra",
            centered=True,
            radius="lg",
            size="md",
            opened=False,
            closeOnClickOutside=False,
            closeOnEscape=True,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="lg",
                        size=128,
                        color="blue",
                        variant="light",
                        children=DashIconify(icon="material-symbols:edit-document", width=128, height=128),
                    ),
                    dmc.Title("Atualizar Regra?", order=1),
                    dmc.Text("Você tem certeza que deseja atualizar a regra com as novas informações?"),
                    dmc.List(
                        [
                            dmc.ListItem(id="nome-regra-atualizar-gerenciar-regra"),
                        ],
                    ),
                    dmc.Text("Esta ação aplicará as novas configurações imediatamente."),
                    dmc.Group(
                        [
                            dmc.Button("Cancelar", id="btn-cancelar-atualizar-regra", variant="default", color="red"),
                            dmc.Button(
                                "Atualizar",
                                color="blue",
                                variant="outline",
                                id="btn-confirma-atualizar-regra",
                            ),
                        ],
                        justify="flex-end",
                    ),
                    dmc.Space(h=20),
                ],
                align="center",
                gap="md",
            ),
        ),
        # Modal de sucesso para ATUALIZAÇÃO da regra
        dmc.Modal(
            id="modal-sucesso-atualizar-gerenciar-regra",
            centered=True,
            radius="lg",
            size="lg",
            opened=False,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="xl",
                        size=128,
                        color="green",
                        variant="light",
                        children=DashIconify(icon="material-symbols:check-circle-rounded", width=128, height=128),
                    ),
                    dmc.Title("Sucesso!", order=1),
                    dmc.Text("A regra foi atualizada com sucesso."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="green",
                                variant="outline",
                                id="btn-close-modal-sucesso-atualizar-gerenciar-regra",
                            ),
                        ],
                        justify="center",
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-pag-editar-regra-erro-atualizar-regra",
            centered=True,
            radius="lg",
            size="lg",
            opened=False,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="xl",
                        size=128,
                        color="red",
                        variant="light",
                        children=DashIconify(icon="mdi:alert-circle-outline", width=128, height=128),
                    ),
                    dmc.Title("Erro!", order=1),
                    dmc.Text("Não foi possível atualizar a regra. Verifique os dados e tente novamente."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="red",
                                variant="outline",
                                id="btn-close-pag-editar-regra-modal-erro-atualizar-regra",
                            ),
                        ],
                        justify="center",
                    ),
                ],
                align="center",
                gap="md",
            ),
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
                                                dbc.Label("Nome da Regra de Monitoramento"),
                                                dbc.Input(
                                                    id="pag-editar-regra-input-nome-regra-monitoramento",
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
                                                            id="pag-editar-regra-input-periodo-dias-monitoramento-regra",
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
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Modelos"),
                                                dcc.Dropdown(
                                                    id="pag-editar-regra-input-modelos-monitoramento-regra",
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
                                                            id="pag-editar-regra-input-quantidade-de-motoristas",
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
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Quantidade mínima de viagens no período"),
                                                dbc.InputGroup(
                                                    [
                                                        dbc.Input(
                                                            id="pag-editar-regra-input-quantidade-de-viagens-monitoramento-regra",
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
                                                    id="pag-editar-regra-input-select-dia-linha-combustivel-regra",
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
                                    className="mb-3 mb-md-0",
                                ),
                                # Mediana
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="pag-editar-regra-switch-mediana",
                                                    label="% Mínima de Viagens Abaixo da Mediana",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-editar-regra-select-mediana",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-editar-regra-container-mediana",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                    className="mb-3 mb-md-0",
                                ),
                                dmc.Space(h=10),
                                # Baixa performance indicativo
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="pag-editar-regra-switch-baixa-performace-indicativo",
                                                    label="% Mínima de Viagens com Supeita ou Baixa Performance",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-editar-regra-select-baixa-performace-indicativo",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=0,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-editar-regra-container-baixa-performace-indicativo",
                                                    style={"display": "none", "marginTop": "10px"},
                                                ),
                                            ]
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                    className="mb-3 mb-md-0",
                                ),
                                # Erro telemetria
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dmc.Switch(
                                                    id="pag-editar-regra-switch-erro-telemetria",
                                                    label="% Mínima de Viagens com Erro de Telemetria",
                                                    checked=False,
                                                ),
                                                dmc.Space(h=10),
                                                html.Div(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="pag-editar-regra-select-erro-telemetria",
                                                                type="number",
                                                                placeholder="Digite a porcentagem",
                                                                min=10,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            dbc.InputGroupText("%"),
                                                        ]
                                                    ),
                                                    id="pag-editar-regra-container-erro-telemetria",
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
                                                        id="pag-editar-regra-switch-enviar-email-regra-edit-combustivel",
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
                                                                    id="pag-editar-regra-input-email-1-regra-edit-combustivel",
                                                                    placeholder="email1@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-email-2-regra-edit-combustivel",
                                                                    placeholder="email2@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-email-3-regra-edit-combustivel",
                                                                    placeholder="email3@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-email-4-regra-edit-combustivel",
                                                                    placeholder="email4@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-email-5-regra-edit-combustivel",
                                                                    placeholder="email5@odilonsantos.com",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="mdi:email"),
                                                                ),
                                                                md=12,
                                                            ),
                                                        ],
                                                        align="center",
                                                    ),
                                                    id="pag-editar-regra-input-email-destino-container-regra-pag-editar-regra-combustivel",
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
                                                        id="pag-editar-regra-switch-enviar-wpp-regra-edit-combustivel",
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
                                                                    id="pag-editar-regra-input-wpp-1-regra-edit-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-wpp-2-regra-edit-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-wpp-3-regra-edit-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-wpp-4-regra-edit-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                            dmc.Space(h=10),
                                                            dbc.Col(
                                                                dmc.TextInput(
                                                                    id="pag-editar-regra-input-wpp-5-regra-edit-combustivel",
                                                                    placeholder="(62) 99999-9999",
                                                                    value="",
                                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                                ),
                                                                md=12,
                                                            ),
                                                        ],
                                                        align="center",
                                                    ),
                                                    id="pag-editar-regra-input-wpp-destino-container-regra-pag-editar-regra-combustivel",
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
                                                    id="pag-editar-regra-switch-os-automatica",
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
                dbc.Col(
                    dbc.Button(
                        "Preview da Regra",
                        id="pag-editar-regra-btn-preview-regra-monitoramento",
                        color="info",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Button(
                        "Atualizar Regra",
                        id="pag-editar-regra-btn-atualizar-regra-monitoramento",
                        color="success",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
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
                                        dmc.Title(id="pag-editar-regra-indicador-quantidade-de-veiculos", order=2),
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
                    md=6,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="pag-editar-regra-indicador-consumo-km-l", order=2),
                                        DashIconify(
                                            icon="material-symbols:speed-outline-rounded", width=48, color="black"
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Consumo médio (km/L)"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
                    style={"margin-bottom": "20px"},
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="pag-editar-regra-indicador-litros-excedentes",
                                            order=2,
                                        ),
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
                    md=6,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="pag-editar-regra-indicador-gasto-combustivel-excedente", order=2),
                                        DashIconify(icon="emojione-monotone:money-with-wings", width=48, color="black"),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter(
                                f"Total gasto com combustível excedente (R$), considerando o litro do Diesel = R$ {preco_diesel:,.2f}".replace(
                                    ".", ","
                                )
                            ),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=6,
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
            id="pag-editar-regra-row-labels-adicionais",
        ),
        dmc.Space(h=20),
        # Tabela de regras
        html.Div(
            id="pag-editar-regra-container-tabela-regras",
            children=[
                dag.AgGrid(
                    id="pag-editar-regra-tabela-preview-viagens-monitoramento",
                    columnDefs=regras_tabela.tbl_consumo_veiculos,
                    rowData=[],
                    defaultColDef={"filter": True, "floatingFilter": True},
                    columnSize="autoSize",
                    dashGridOptions={
                        "localeText": locale_utils.AG_GRID_LOCALE_BR,
                        "rowSelection": "multiple",
                        "enableCellTextSelection": True,
                        "ensureDomOrder": True,
                    },
                    style={"height": 400, "resize": "vertical", "overflow": "hidden", "display": "none"},
                )
            ],
        ),
    ],
)

# Registrar página
dash.register_page(__name__, name="Editar Regra", path="/regra-editar", icon="carbon:rule-draft", hide_page=True)
