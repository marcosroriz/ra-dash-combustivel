#!/usr/bin/env python
# coding: utf-8

# Imports básicos
import pandas as pd
import io

# Importar bibliotecas do dash básicas
from dash import html

# Imports de mapa
import dash_leaflet as dl

# Imports do tema
import tema

# Funções utilitárias para trabalhar com mapa

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
