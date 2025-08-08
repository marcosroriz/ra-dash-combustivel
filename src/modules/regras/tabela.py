tbl_perc_viagens_monitoramento = [
    {"field": "vec_num_id", "headerName": "VEÍCULO", "minWidth": 150, "pinned": "left"},
    {"field": "vec_model", "headerName": "MODELO", "minWidth": 300, "type": ["text"], "pinned": "left"},

    {
        "field": "media_consumo_por_km",
        "headerName": "Média km/L",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0.00' : val.toFixed(2); }"
        },
    },
    {
        "field": "comb_excedente_l",
        "headerName": "Litros Excedentes",
        "filter": "agNumberColumnFilter",
        "minWidth": 150,
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


tbl_regras_monitoramento = [

    {"field": "nome_regra", "headerName": "Nome da Regra", "minWidth": 200, "type": ["text"], "pinned": "left"},
    {"field": "periodo", "headerName": "Período", "minWidth": 150, "type": ["text"], "pinned": "left"},
    {"field": "modelos", "headerName": "Modelos", "minWidth": 200, "type": ["text"]},
    {"field": "motoristas", "headerName": "Qtd. Min. de Motorisas", "minWidth": 150, "type": ["text"]},
    {"field": "dias_analise", "headerName": "Dias de Análise", "minWidth": 150, "type": ["text"]},
    {"field": "qtd_viagens", "headerName": "Qtd. Min .Viagens", "minWidth": 130, "type": ["numericColumn"]},

    {"field": "mediana_viagem", "headerName": "Mediana Viagem", "minWidth": 150, "type": ["numericColumn"]},
    {
        "field": "usar_mediana_viagem",
        "headerName": "Usar Mediana",
        "minWidth": 130,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"},
    },

    {"field": "indicativo_performace", "headerName": "Indicativo Performance", "minWidth": 180, "type": ["numericColumn"]},
    {
        "field": "usar_indicativo_performace",
        "headerName": "Usar Indicativo Perf.",
        "minWidth": 150,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"},
    },

    {"field": "erro_telemetria", "headerName": "Erro Telemetria", "minWidth": 150, "type": ["numericColumn"]},
    {
        "field": "usar_erro_telemetria",
        "headerName": "Usar Erro Telemetria",
        "minWidth": 150,
        "type": ["text"],
        "valueFormatter": {"function": "params => params.value ? '✓' : '✗'"},
    },

    {
        "field": "criado_em",
        "headerName": "Criado Em",
        "minWidth": 200,
        "type": ["dateColumnFilter"],
        "valueFormatter": {"function": "params => new Date(params.value).toLocaleString()"},
    },
    {
        "headerName": "SELEÇÃO",
        "checkboxSelection": True,
        "headerCheckboxSelection": True,  # checkbox no header para selecionar tudo
        "width": 50,
        "pinned": "right",
    },
    
]

tbl_regras_monitoramento_editavel = []

for col in tbl_regras_monitoramento:
    field = col.get("field")  # pega o valor ou None se não existir

    if not field:
        # Coluna sem campo, tipo a coluna de seleção, deixa como está e pula edição
        col.update({"editable": False})
        tbl_regras_monitoramento_editavel.append(col)
        continue

    # Agora só para colunas que têm campo "field"
    if col.get("headerName") in ["SELEÇÃO", "Criado Em"]:
        editable = False
    else:
        editable = True

    if field.startswith("usar_"):
        col.update({
            "editable": editable,
            "cellEditor": "agCheckboxCellEditor",
            "cellRenderer": "agCheckboxCellRenderer",
            "minWidth": col.get("minWidth", 100)
        })
    else:
        col.update({
            "editable": editable,
        })

    tbl_regras_monitoramento_editavel.append(col)

