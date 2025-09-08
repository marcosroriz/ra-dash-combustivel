#!/usr/bin/env python
# coding: utf-8

# Dashboard principal, aqui é listado as últimas viagens dos veículos

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
# Importar bibliotecas do dash básicas e plotly
from dash import html, callback, Input, Output, dcc, ctx, State
import dash

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

# Imports específicos
from modules.regras.regras_service import RegrasService
import modules.regras.tabela as regras_tabela



# Imports gerais
from modules.entities_utils import get_regras


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


regra_service = RegrasService(pgEngine)

# Preparando inputs
df_regras = get_regras(pgEngine)
lista_todas_regras = df_regras.to_dict(orient="records")
lista_todas_regras.insert(0, {"LABEL": "TODAS"})
##############################################################################
# Callbacks para dados ######################################################
##############################################################################


@callback(
    Output("tabela-de-regras-existentes", "rowData"),
    [
        Input("input-nome-regra-existentes", "value"),
    ],
)
def atualiza_tabela_regra_existentes(
    lista_regras
):

    df = regra_service.get_regras(lista_regras)

    return df.to_dict(orient="records")

# Callbacks para input
@callback(
    Output("input-nome-regra-existentes", "value"),
    Input("input-nome-regra-existentes", "value"),
    prevent_initial_call=True
)
def filtra_todas_opcao(valor_selecionado):
    if not valor_selecionado:
        return []

    # Se "TODAS" estiver selecionado junto com outras opções, remove "TODAS"
    if "TODAS" in valor_selecionado and len(valor_selecionado) > 1:
        return [v for v in valor_selecionado if v != "TODAS"]

    return valor_selecionado

@callback(
    Output("mensagem-sucesso-deletar", "children"),
    Input('btn-deletar-regra', 'n_clicks'),
    State("tabela-de-regras-existentes", "selectedRows"),
    prevent_initial_call=True
)
def deletar_regra(n_clicks, linhas):
    if not n_clicks:
        return ""

    if not linhas:
        return "Selecione uma regra para deletar."

    try:
        regra_nome = linhas[0].get('nome_regra')
        if linhas[0].get('id') is None:
            return "ID da regra não encontrado."

        regra_service.deletar_regra_monitoramento(id_regra=linhas[0].get('id'))
        return f"Regra {regra_nome} deletada com sucesso."

    except Exception as e:
        print(f"[ERRO] Falha ao deletar regra: {e}")
        return "Erro ao deletar a regra. Verifique os logs."



@callback(
    Output("mensagem-sucesso-editar", "children"),
    Input("btn-editar-regra", "n_clicks"),
    State("tabela-de-regras-existentes", "rowData"),
    prevent_initial_call=True
)
def salvar_alteracoes(n_clicks, dados_editados):
    if not dados_editados:
        return "Nenhuma alteração detectada."

    try:
        for regra in dados_editados:
            # Renomear as chaves para os parâmetros do método
            kwargs = {
                "id_regra": regra.get("id"),
                "nome_regra": regra.get("nome_regra"),
                "data": regra.get("periodo"),
                "modelos": regra.get("modelos"),
                "numero_de_motoristas": regra.get("motoristas"),
                "quantidade_de_viagens": regra.get("qtd_viagens"),
                "dias_marcados": regra.get("dias_analise"),
                "mediana_viagem": regra.get("mediana_viagem"),
                "indicativo_performace": regra.get("indicativo_performace"),
                "erro_telemetria": regra.get("erro_telemetria"),
            }
            regra_service.atualizar_regra_monitoramento(**kwargs)

        return "Alterações salvas com sucesso!"
    except Exception as e:
        return f"Erro ao salvar alterações: {str(e)}"



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
                                                    html.Strong("Regras Existentes de Monitoramento da Frota"),
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

                        # Campo de busca
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Nome da Regra de Monitoramento"),
                                                    dcc.Dropdown(
                                                        id="input-nome-regra-existentes",
                                                        options=[
                                                            {
                                                                "label": regra['LABEL'],
                                                                "value": regra['LABEL'],
                                                            }
                                                            for regra in lista_todas_regras
                                                        ],
                                                        placeholder="Digite o nome da regra...",
                                                        value=['TODAS'],
                                                        multi=True,
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
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

        # Título e Espaçamento
        dmc.Space(h=10),
        dmc.Title("Regras Existentes", order=3),
        dmc.Space(h=20),

        # Tabela AG Grid
        dag.AgGrid(
            id="tabela-de-regras-existentes",
            columnDefs=regras_tabela.tbl_regras_monitoramento_editavel,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True, "editable": True,},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "rowSelection": "single",
            },
            style={
                "height": 400,
                "resize": "vertical",
                "overflow": "hidden",
            },
        ),
        dbc.Row(
            [
                dmc.Space(h=10),
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Deletar Regra",
                                id="btn-deletar-regra",
                                n_clicks=0,
                                style={
                                    "background-color": "#d30000",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "10px 20px",
                                    "border-radius": "8px",
                                    "cursor": "pointer",
                                    "font-size": "16px",
                                    "font-weight": "bold",
                                },
                            ),
                            html.Div(id="mensagem-sucesso-deletar", style={"marginTop": "10px", "fontWeight": "bold"}),
                        ],
                        style={
                            "text-align": "left",
                            "height": 400,
                        },
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.Button(
                                "Editar Regra",
                                id="btn-editar-regra",  # corrigi o id para não repetir
                                n_clicks=0,
                                style={
                                    "background-color": "#085ff5",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "10px 20px",
                                    "border-radius": "8px",
                                    "cursor": "pointer",
                                    "font-size": "16px",
                                    "font-weight": "bold",
                                },
                            ),
                            html.Div(id="mensagem-sucesso-editar", style={"marginTop": "10px", "fontWeight": "bold"}),
                        ],
                        style={
                            "text-align": "right",
                            "height": 400,
                        },
                    ),
                    width=8,
                ),
                dmc.Space(h=10),
            ],
            align="center",
            style={
                "text-align": "center",
                "height": 400,
            },
        ),
    ]
)


dash.register_page(__name__, name="Regras Existentes", path="/regras-existentes")
