#!/usr/bin/env python
# coding: utf-8

##############################################################################
# IMPORTS ####################################################################
##############################################################################
from dash import html, callback, Input, Output, dcc, ctx, State, callback_context
import dash
import re

import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Utilitários internos
import locale_utils
from db import PostgresSingleton
from modules.regras.regras_service import RegrasService
import modules.regras.tabela as regras_tabela
from modules.entities_utils import get_regras


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com o banco
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Serviço de regras
regra_service = RegrasService(pgEngine)

# Carregar regras existentes
df_regras = get_regras(pgEngine)
lista_todas_regras = df_regras.to_dict(orient="records")
lista_todas_regras.insert(0, {"LABEL": "TODAS"})


##############################################################################
# FUNÇÕES AUXILIARES #########################################################
##############################################################################
def prepara_dados_tabela(df_regras):
    """Adiciona colunas de ação para edição e exclusão na tabela"""
    df_regras["acao_editar"] = "✏️ Editar"
    df_regras["acao_apagar"] = "❌ Apagar"
    return df_regras


def get_lista_regras(df=None):
    """Converte DataFrame em lista de dicts para tabela"""
    if df is None:
        df = regra_service.get_regras()
    if not df.empty:
        df = prepara_dados_tabela(df)
        return df.to_dict(orient="records")
    return []


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

# Atualizar tabela de regras existentes
@callback(
    Output("tabela-de-regras-existentes", "rowData"),
    Input("input-nome-regra-existentes", "value"),
)
def atualizar_tabela_regras(filtro):
    df = regra_service.get_regras(filtro)
    return get_lista_regras(df)


# Ajustar seleção no dropdown
@callback(
    Output("input-nome-regra-existentes", "value"),
    Input("input-nome-regra-existentes", "value"),
)
def atualizar_filtro_dropdown(valores):
    if not valores:
        return ["TODAS"]

    ctx = callback_context
    if not ctx.triggered:
        return valores

    ultimo_valor = ctx.triggered[0]["value"]

    if "TODAS" in valores and len(valores) > 1:
        if ultimo_valor == ["TODAS"]:
            return ["TODAS"]
        return [v for v in valores if v != "TODAS"]

    return valores


# Cancelar exclusão
@callback(
    Output("modal-confirma-apagar-gerenciar-regra", "opened", allow_duplicate=True),
    Input("btn-cancelar-apagar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cancelar_exclusao(n_clicks):
    return False if n_clicks else dash.no_update


# Confirmar exclusão
@callback(
    [
        Output("modal-confirma-apagar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("modal-sucesso-apagar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("tabela-de-regras-existentes", "rowData", allow_duplicate=True),
    ],
    Input("btn-confirma-apagar-regra", "n_clicks"),
    Input("nome-regra-apagar-gerenciar-regra", "children"),
    Input("input-nome-regra-existentes", "value"),
    prevent_initial_call=True
)
def confirmar_exclusao(n_clicks, nome_regra, filtro):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    match = re.search(r"ID:\s*(\d+)", nome_regra)
    print(match)
    if not match:
        return dash.no_update, dash.no_update, dash.no_update

    id_regra = int(match.group(1))
    regra_service.deletar_regra_monitoramento(id_regra)

    df = regra_service.get_regras(filtro)
    
    return False, True, get_lista_regras(df)


# Fechar modal de sucesso
@callback(
    Output("modal-sucesso-apagar-gerenciar-regra", "opened", allow_duplicate=True),
    Input("btn-close-modal-sucesso-apagar-gerenciar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fechar_modal_sucesso(n_clicks):
    return False if n_clicks else dash.no_update


# Ações da tabela (editar ou apagar)
@callback(
    Output("url", "href", allow_duplicate=True),
    Output("modal-confirma-apagar-gerenciar-regra", "opened"),
    Output("nome-regra-apagar-gerenciar-regra", "children"),
    Input("tabela-de-regras-existentes", "cellRendererData"),
    Input("tabela-de-regras-existentes", "virtualRowData"),
    prevent_initial_call=True,
)
def acoes_tabela(linha, linha_virtual):
    ctx = callback_context
    if not ctx.triggered or ctx.triggered[0]["prop_id"].split(".")[1] != "cellRendererData":
        return dash.no_update, dash.no_update, dash.no_update

    if not linha or not linha_virtual:
        return dash.no_update, dash.no_update, dash.no_update

    dados_regra = linha_virtual[linha["rowIndex"]]
    nome_regra, id_regra = dados_regra["nome_regra"], dados_regra["id"]
    acao = linha["colId"]

    if acao == "acao_editar":
        return f"/regra-editar?id_regra={id_regra}", dash.no_update, dash.no_update
    if acao == "acao_apagar":
        return dash.no_update, True, f"{nome_regra} (ID: {id_regra})"

    return dash.no_update, dash.no_update, dash.no_update


# Salvar alterações de edição
@callback(
    Output("mensagem-sucesso-editar", "children"),
    Input("btn-editar-regra", "n_clicks"),
    State("tabela-de-regras-existentes", "rowData"),
    prevent_initial_call=True,
)
def salvar_edicoes(n_clicks, dados_editados):
    if not dados_editados:
        return "Nenhuma alteração detectada."

    try:
        for regra in dados_editados:
            regra_service.atualizar_regra_monitoramento(
                id_regra=regra.get("id"),
                nome_regra=regra.get("nome_regra"),
                data=regra.get("periodo"),
                modelos=regra.get("modelos"),
                numero_de_motoristas=regra.get("motoristas"),
                quantidade_de_viagens=regra.get("qtd_viagens"),
                dias_marcados=regra.get("dias_analise"),
                mediana_viagem=regra.get("mediana_viagem"),
                indicativo_performace=regra.get("indicativo_performace"),
                erro_telemetria=regra.get("erro_telemetria"),
            )
        return "Alterações salvas com sucesso!"
    except Exception as e:
        return f"Erro ao salvar alterações: {str(e)}"
    
# Callback botão criar regra
@callback(
    Output("url", "href", allow_duplicate=True),
    Input("btn-criar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_criar_regra(n_clicks):
    if n_clicks is None:
        return dash.no_update
    
    print("Clicou no botão criar regra")

    return "/regras-monitoramento"


##############################################################################
# LAYOUT #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Modais
        dmc.Modal(
            id="modal-confirma-apagar-gerenciar-regra",
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
                        color="red",
                        variant="light",
                        children=DashIconify(icon="material-symbols:delete", width=128, height=128),
                    ),
                    dmc.Title("Apagar Regra?", order=1),
                    dmc.Text("Você tem certeza que deseja apagar a regra?"),
                    dmc.List([dmc.ListItem(id="nome-regra-apagar-gerenciar-regra")]),
                    dmc.Text("Esta ação não poderá ser desfeita."),
                    dmc.Group(
                        [
                            dmc.Button("Cancelar", id="btn-cancelar-apagar-regra", variant="default"),
                            dmc.Button("Apagar", color="red", variant="outline", id="btn-confirma-apagar-regra"),
                        ],
                        justify="flex-end",
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-sucesso-apagar-gerenciar-regra",
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
                    dmc.Text("A regra foi apagada com sucesso."),
                    dmc.Group([dmc.Button("Fechar", color="green", variant="outline", id="btn-close-modal-sucesso-apagar-gerenciar-regra")]),
                ],
                align="center",
                gap="md",
            ),
        ),

        # Cabeçalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="carbon:rule", width=45), width="auto"),
                dbc.Col(html.H1([html.Strong("Regras"), "\u00a0 de Monitoramento"]), width=True),
                dbc.Col(
                    dbc.Button(
                        [DashIconify(icon="mdi:plus", className="me-1"), "Criar Regra"],
                        id="btn-criar-regra",
                        color="success",
                        style={"padding": "1em"},
                    ),
                    width="auto",
                ),
            ],
            align="center",
        ),
        html.Hr(),

        # Filtro
        dbc.Card(
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            dbc.Label("Nome da Regra de Monitoramento"),
                            dcc.Dropdown(
                                id="input-nome-regra-existentes",
                                options=[{"label": regra['LABEL'], "value": regra['LABEL']} for regra in lista_todas_regras],
                                placeholder="Digite o nome da regra...",
                                value=["TODAS"],
                                multi=True,
                            ),
                        ]
                    )
                )
            ),
            body=True,
        ),
        dmc.Space(h=15),

        # Tabela
        dag.AgGrid(
            id="tabela-de-regras-existentes",
            columnDefs=regras_tabela.tbl_regras_existentes,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="responsiveSizeToFit",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "enableCellTextSelection": True,
                "ensureDomOrder": True,
            },
            style={"height": 500, "resize": "vertical", "overflow": "hidden"},
        ),
    ]
)

##############################################################################
# REGISTRO DA PÁGINA #########################################################
##############################################################################
dash.register_page(__name__, name="Regras Existentes", path="/regras-existentes")
