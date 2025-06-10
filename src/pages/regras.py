import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc

dash.register_page(__name__, name="Regras", path="/regras")

layout = html.Div([
    html.Div([
        html.Div([
            html.I(className="bi bi-ui-checks-grid", style={"fontSize": "30px", "marginRight": "10px"}),
            html.H2("Gerenciar Regras", className="mb-0")
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        # Botões ficam no cabeçalho da lista
                        html.Div([
                            dbc.Button("Criar", id="btn-criar", color="primary", className="me-2"),
                            dbc.Button("Apagar", id="btn-apagar", color="danger"),
                        ], style={"display": "flex", "justifyContent": "flex-start", "gap": "10px"})
                    ),
                    dbc.CardBody(
                        # Tabela responsiva para listar as regras
                        dbc.Table(
                            # Cabeçalho da tabela
                            [
                                html.Thead(html.Tr([
                                    html.Th("ID"),
                                    html.Th("Nome da Regra"),
                                    html.Th("Descrição"),
                                ])),
                                html.Tbody([
                                    html.Tr([html.Td("1"), html.Td("Regra 1"), html.Td("Descrição da Regra 1")]),
                                    html.Tr([html.Td("2"), html.Td("Regra 2"), html.Td("Descrição da Regra 2")]),
                                    html.Tr([html.Td("3"), html.Td("Regra 3"), html.Td("Descrição da Regra 3")]),
                                ])
                            ],
                            bordered=True,
                            hover=True,
                            responsive=True,
                            striped=True,
                            style={"maxHeight": "60vh", "overflowY": "auto", "display": "block"}
                        )
                    )
                ], style={"height": "100%", "display": "flex", "flexDirection": "column"})
            ], width=4, style={"height": "80vh"}),

            dbc.Col([
                html.Div(id="formulario-container", children=[], style={"display": "none", "height": "80vh", "overflowY": "auto"})
            ], width=8)
        ], style={"height": "90vh"})
    ], className="container-fluid", style={"padding": "20px"})
])
