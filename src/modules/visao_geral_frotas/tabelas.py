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


tbl_regras_monitoramento = [
    {"field": "id", "headerName": "ID", "minWidth": 80, "type": ["numericColumn"], "pinned": "left"},
    {"field": "nome_regra", "headerName": "Nome da Regra", "minWidth": 200, "type": ["text"]},
    {"field": "criado_em", "headerName": "Criado em", "minWidth": 220, "type": ["dateColumn"]},
    {"field": "atualizado_em", "headerName": "Atualizado em", "minWidth": 220, "type": ["dateColumn"]},
    {"field": "dias_analise", "headerName": "Dias Análise", "minWidth": 50, "type": ["numericColumn"]},
    {"field": "motoristas", "headerName": "Motoristas", "minWidth": 200, "type": ["text"], "pinned": "left"},
    {"field": "qtd_viagens", "headerName": "Qtd. Viagens", "minWidth": 120, "type": ["numericColumn"]},
    
    {
        "field": "mediana_viagem",
        "headerName": "Mediana da Viagem",
        "minWidth": 150,
        "type": ["numericColumn"],
        "valueFormatter": {
            "function": "function(params) { const val = parseFloat(params.value); return isNaN(val) ? '0' : val.toFixed(2); }"
        },
    },
    {"field": "usar_mediana_viagem", "headerName": "Usar Mediana", "minWidth": 120, "type": ["booleanColumn"]},
    {"field": "indicativo_performace", "headerName": "Indicativo Performance", "minWidth": 160, "type": ["numericColumn"]},
    {"field": "usar_indicativo_performace", "headerName": "Usar Indicativo Perf.", "minWidth": 160, "type": ["booleanColumn"]},
    {"field": "erro_telemetria", "headerName": "Erro Telemetria", "minWidth": 140, "type": ["numericColumn"]},
    {"field": "usar_erro_telemetria", "headerName": "Usar Erro Telemetria", "minWidth": 160, "type": ["booleanColumn"]},

    {"field": "regra_padronizada", "headerName": "Regra Padronizada", "minWidth": 150, "type": ["text"]},
    {"field": "criar_os_automatica", "headerName": "Criar OS Automática", "minWidth": 160, "type": ["booleanColumn"]},
    {"field": "enviar_email", "headerName": "Enviar Email", "minWidth": 120, "type": ["booleanColumn"]},
    {"field": "enviar_whatsapp", "headerName": "Enviar WhatsApp", "minWidth": 140, "type": ["booleanColumn"]},

    {"field": "periodo", "headerName": "Período", "minWidth": 120, "type": ["text"]},
    {"field": "modelos", "headerName": "Modelos", "minWidth": 200, "type": ["text"]},

    {"field": "whatsapp_usuario1", "headerName": "WhatsApp Usuário 1", "minWidth": 200, "type": ["text"]},
    {"field": "whatsapp_usuario2", "headerName": "WhatsApp Usuário 2", "minWidth": 200, "type": ["text"]},
    {"field": "whatsapp_usuario3", "headerName": "WhatsApp Usuário 3", "minWidth": 200, "type": ["text"]},
    {"field": "whatsapp_usuario4", "headerName": "WhatsApp Usuário 4", "minWidth": 200, "type": ["text"]},
    {"field": "whatsapp_usuario5", "headerName": "WhatsApp Usuário 5", "minWidth": 200, "type": ["text"]},

    {"field": "email_usuario1", "headerName": "Email Usuário 1", "minWidth": 200, "type": ["text"]},
    {"field": "email_usuario2", "headerName": "Email Usuário 2", "minWidth": 200, "type": ["text"]},
    {"field": "email_usuario3", "headerName": "Email Usuário 3", "minWidth": 200, "type": ["text"]},
    {"field": "email_usuario4", "headerName": "Email Usuário 4", "minWidth": 200, "type": ["text"]},
    {"field": "email_usuario5", "headerName": "Email Usuário 5", "minWidth": 200, "type": ["text"]},
]