tbl_detalhamento_viagens_monitoramento = [
    {"field": "dia", "headerName": "DIA", "minWidth": 200},
    {"field": "vec_num_id", "headerName": "VEÍCULO", "minWidth": 200},
    {"field": "vec_model", "headerName": "MODELO", "minWidth": 300, "type": ["text"]},
    {"field": "STATUS_CONSUMO_POR_KM", "headerName": "STATUS", "minWidth": 200, "type": ["text"]},
    {
        "field": "MEDIA_CONSUMO_POR_KM",
        "headerName": "Média km/L",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "type": ["numericColumn"],
    },
    {"field": "VIAGENS_HTML", "headerName": "ÚLTIMAS VIAGENS", "cellRenderer": "dagcomponentfuncs.MultiButtonRenderer"},
]
