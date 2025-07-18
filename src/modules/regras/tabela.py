tbl_perc_viagens_monitoramento = [
        {
        "headerName": "ABRIR OS",  # sem título
        "checkboxSelection": True,
        "headerCheckboxSelection": True,  # checkbox no header para selecionar tudo
        "width": 50,
        "pinned": "left",  # fixa a coluna na esquerda
    },
    {"field": "vec_num_id", "headerName": "VEÍCULO", "minWidth": 150, "pinned": "left"},

    {"field": "vec_model", "headerName": "MODELO", "minWidth": 300, "type": ["text"], "pinned": "left"},
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
        "headerName": "# Suspeita Baixa Performance",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {"field": "total_status_baixa_performance", "headerName": "# Baixa Performance", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_erro_telemetria", "headerName": "# Supeita Erro", "minWidth": 150, "type": ["numericColumn"]},
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
    {"field": "percentual_erro_telemetria", "headerName": "% Viagens Supeita Erro", "minWidth": 150, "type": ["numericColumn"]},

]
