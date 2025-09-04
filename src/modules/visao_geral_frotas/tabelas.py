tbl_regras_viagens_visao_geral_frota = [
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
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00' : val.toFixed(2); }"
        },
    },
    {
        "field": "comb_excedente_l",
        "headerName": "Litros Excedentes",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00L' : val.toFixed(2) + 'L'; }"
        },
    },

    {"field": "total_viagens", "headerName": "Quantidade de Viagens", "minWidth": 150, "type": ["numericColumn"]},
    {
    "field": "proporcao_abaixo_mediana",
    "headerName": "% Viagens Abaixo Da Mediana",
    "minWidth": 150,
    "type": ["numericColumn"],
    "valueFormatter": {
        "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00%' : val.toFixed(2) + '%'; }"
    },
    },
    {"field": "total_status_regular", "headerName": "Regular", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_suspeita_baixa_perfomance", "headerName": "Suspeita Baixa Performance", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_baixa_performance", "headerName": "Baixa Performance", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_erro_telemetria", "headerName": "Supeita Erro Telemetria", "minWidth": 150, "type": ["numericColumn"]},

    {
        "field": "percentual_categoria_status_regular",
        "headerName": "% Viagens Regular",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00%' : val.toFixed(2) + '%'; }"
        },
    },
    {
        "field": "percentual_categoria_status_suspeita_baixa_perfomance",
        "headerName": "% Viagens Suspeita de Baixa Performance",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00%' : val.toFixed(2) + '%'; }"
        },
    },
    {
        "field": "percentual_categoria_status_baixa_performance",
        "headerName": "% Viagens Baixa Performnce",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00%' : val.toFixed(2) + '%'; }"
        },
    },
    {
        "field": "percentual_categoria_status_erro_telemetria",
        "headerName": "% Viagens Supeita Erro",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00%' : val.toFixed(2) + '%'; }"
        },
    },
]