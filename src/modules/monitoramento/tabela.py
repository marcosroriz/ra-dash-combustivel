tbl_perc_viagens_monitoramento = [
    {"field": "vec_num_id", "headerName": "VEÍCULO", "minWidth": 150},
    {"field": "vec_model", "headerName": "MODELO", "minWidth": 300, "type": ["text"]},
    {
        "field": "media_consumo_por_km",
        "headerName": "Média km/L",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
    },
    {"field": "total_viagens", "headerName": "# Viagens", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_regular", "headerName": "# Regular", "minWidth": 150, "type": ["numericColumn"]},
    {
        "field": "total_status_suspeita_baixa_perfomance",
        "headerName": "# Suspeita",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {"field": "total_status_baixa_performance", "headerName": "# Baixo", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_erro_telemetria", "headerName": "# Erro", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "percentual_regular", "headerName": "% Viagens Regular", "minWidth": 150, "type": ["numericColumn"]},
    {
        "field": "percentual_suspeita_baixa_perfomance",
        "headerName": "% Viagens Suspeita",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {
        "field": "percentual_baixa_performance",
        "headerName": "% Viagens Baixo",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {"field": "percentual_erro_telemetria", "headerName": "% Viagens Erro", "minWidth": 150, "type": ["numericColumn"]},
]


tbl_detalhamento_viagens_monitoramento = [
    {"field": "dia", "headerName": "DIA", "minWidth": 200},
    {"field": "vec_num_id", "headerName": "VEÍCULO", "minWidth": 200},
    {"field": "vec_model", "headerName": "MODELO", "minWidth": 300, "type": ["text"]},
    {"field": "STATUS_CONSUMO_POR_KM", "headerName": "STATUS", "minWidth": 200, "type": ["text"]},
    {
        "field": "media_consumo_por_km",
        "headerName": "Média km/L",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "type": ["numericColumn"],
    },
    {"field": "VIAGENS_HTML", "headerName": "ÚLTIMAS VIAGENS", "cellRenderer": "dagcomponentfuncs.MultiButtonRenderer"},
]
