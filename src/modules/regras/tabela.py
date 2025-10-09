#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página relacionado a regras

# Tabela com o consumo dos veículos
tbl_consumo_veiculos = [
    {
        "field": "vec_num_id",
        "headerName": "VEÍCULO",
        "minWidth": 120,
        "maxWidth": 120,
        "pinned": "left",
    },
    {
        "field": "acao",
        "headerName": "Perfil",
        "cellRenderer": "Button",
        "cellRendererParams": {"className": "btn btn-outline-primary btn-sm"},
        "minWidth": 150,
        "pinned": "left",
    },
    {
        "field": "vec_model",
        "headerName": "Modelo",
        "minWidth": 220,
    },
    {
        "field": "media_km_por_litro",
        "headerName": "km/L Médio",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "minWidth": 130,
        "maxWidth": 130,
        "type": ["numericColumn"],
    },
        {
        "field": "total_consumo_litros",
        "headerName": "TOTAL CONSUMIDO (L)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 170,
        "maxWidth": 170,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "litros_excedentes",
        "headerName": "LITROS EXCEDENTES (L)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 170,
        "maxWidth": 170,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "custo_excedente",
        "headerName": "CUSTO EXCEDENTE (R$)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 200,
        "maxWidth": 200,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {
            "function": "'R$ ' + (params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }))"
        },
        "sort": "desc",
        "sortable": True,
        "type": ["numericColumn"],
    },
    {
        "field": "total_viagens",
        "headerName": "TOTAL DE VIAGENS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 140,
        "maxWidth": 140,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "perc_total_abaixo_mediana",
        "headerName": "% ABAIXO DA MEDIANA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "minWidth": 160,
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "perc_baixa_perfomance",
        "headerName": "% BAIXA PERFORMANCE",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "minWidth": 180,
        "maxWidth": 180,
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "perc_erro_telemetria",
        "headerName": "% ERRO TELEMETRIA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 160,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
]


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


# Tabela de regras existentes
tbl_regras_existentes = [
    {"field": "nome_regra", "headerName": "NOME DA REGRA", "minWidth": 250},
    {
        "field": "criado_em",
        "headerName": "DATA DE CRIAÇÃO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 120,
        "filter": "agDateColumnFilter",
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) + ' ' + params.value.slice(11,16) : ''"
        },
    },

    {
        "field": "acao_editar",
        "headerName": "EDITAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "cellRendererParams": {"className": "btn btn-outline-warning btn-sm"},
    },
    {
        "field": "acao_apagar",
        "headerName": "APAGAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "cellRendererParams": {"className": "btn btn-outline-danger btn-sm"},
    },
]

