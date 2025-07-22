tbl_perc_viagens_monitoramento = [
    # {
    #     "headerName": "ABRIR OS AUTOMATICA",
    #     "checkboxSelection": True,
    #     "headerCheckboxSelection": True,
    #     "width": 50,
    #     "pinned": "left",
    # },
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
    {"field": "total_viagens", "headerName": "Quantidade de Viagens", "minWidth": 150, "type": ["numericColumn"]},
    {"field": "total_status_regular", "headerName": "Regular", "minWidth": 150, "type": ["numericColumn"]},
    {
        "field": "total_status_suspeita_baixa_performance",
        "headerName": "Suspeita Baixa Performance",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {
        "field": "total_status_baixa_performance",
        "headerName": "Baixa Performance",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {
        "field": "total_status_erro_telemetria",
        "headerName": "Supeita Erro Telemetria",
        "minWidth": 150,
        "type": ["numericColumn"],
    },
    {
        "field": "percentual_regular",
        "headerName": "% Viagens Regular",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "params => (isNaN(parseFloat(params.value)) ? '0.00%' : parseFloat(params.value).toFixed(2) + '%')"
        }
    },
    {
        "field": "percentual_suspeita_baixa_performance",
        "headerName": "% Viagens Suspeita de Baixa Performance",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "params => (isNaN(parseFloat(params.value)) ? '0.00%' : parseFloat(params.value).toFixed(2) + '%')"
        }
    },
    {
        "field": "percentual_baixa_performance",
        "headerName": "% Viagens Baixa Performnce ",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "params => (isNaN(parseFloat(params.value)) ? '0.00%' : parseFloat(params.value).toFixed(2) + '%')"
        }
    },
    {
        "field": "percentual_erro_telemetria",
        "headerName": "% Viagens Supeita Erro",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "params => (isNaN(parseFloat(params.value)) ? '0.00%' : parseFloat(params.value).toFixed(2) + '%')"
        }
    },
]

tbl_regras_monitoramento = [
    {"field": "nome_regra", "headerName": "Nome da Regra", "minWidth": 200, "type": ["text"], "pinned": "left"},
    {"field": "periodo", "headerName": "Período", "minWidth": 150, "type": ["text"], "pinned": "left"},
    {"field": "modelos", "headerName": "Modelos", "minWidth": 200, "type": ["text"], "pinned": "left"},
    {"field": "linha", "headerName": "Linha", "minWidth": 150, "type": ["text"]},
    {"field": "dias_analise", "headerName": "Dias de Análise", "minWidth": 150, "type": ["text"]},
    {"field": "qtd_viagens", "headerName": "Qtd. Viagens", "minWidth": 130, "type": ["numericColumn"]},
    
    {
        "field": "km_l_min",
        "headerName": "Km/L Mínimo",
        "minWidth": 130,
        "type": ["numericColumn"],
        "valueFormatter": {"function": "params => Number(params.value).toFixed(2)"}
    },
    {
        "field": "usar_km_l_min",
        "headerName": "Usar Km/L Min",
        "minWidth": 130,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "km_l_max",
        "headerName": "Km/L Máximo",
        "minWidth": 130,
        "type": ["numericColumn"],
        "valueFormatter": {"function": "params => Number(params.value).toFixed(2)"}
    },
    {
        "field": "usar_km_l_max",
        "headerName": "Usar Km/L Max",
        "minWidth": 130,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "mediana_viagem",
        "headerName": "Mediana Viagem",
        "minWidth": 150,
        "type": ["numericColumn"]
    },
    {
        "field": "usar_mediana_viagem",
        "headerName": "Usar Mediana",
        "minWidth": 130,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "suspeita_performace",
        "headerName": "Suspeita Performance",
        "minWidth": 180,
        "type": ["numericColumn"]
    },
    {
        "field": "usar_suspeita_performace",
        "headerName": "Usar Suspeita Perf.",
        "minWidth": 150,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "indicativo_performace",
        "headerName": "Indicativo Performance",
        "minWidth": 180,
        "type": ["numericColumn"]
    },
    {
        "field": "usar_indicativo_performace",
        "headerName": "Usar Indicativo Perf.",
        "minWidth": 150,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "erro_telemetria",
        "headerName": "Erro Telemetria",
        "minWidth": 150,
        "type": ["numericColumn"]
    },
    {
        "field": "usar_erro_telemetria",
        "headerName": "Usar Erro Telemetria",
        "minWidth": 150,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"}
    },
    {
        "field": "criado_em",
        "headerName": "Criado Em",
        "minWidth": 200,
        "type": ["dateColumnFilter"],
        "valueFormatter": {"function": "params => new Date(params.value).toLocaleString()"}
    },
]
