#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import io


# Funções utilitárias para obtenção das principais entidades do sistema


def get_linhas(dbEngine):
    # Linhas
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "linhanumero" AS "LABEL"
        FROM 
            rmtc_linha_info
        ORDER BY
            "linhanumero"
        """,
        dbEngine,
    )


def get_veiculos_com_combustivel(dbEngine):
    # Veículos que possuem informações de consumo
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "vec_num_id" AS "LABEL"
        FROM 
            rmtc_viagens_analise_mix rva 
        WHERE 
            "vec_num_id" IS NOT NULL
        ORDER BY
            "vec_num_id"
        """,
        dbEngine,
    )


def get_modelos_veiculos_com_combustivel(dbEngine):
    # Modelos de veículos que possuem informações de consumo
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "vec_model" AS "LABEL",
            "vec_num_id",
            "vec_asset_id"
        FROM 
            rmtc_viagens_analise_mix rva 
        WHERE 
            "vec_model" IS NOT NULL
        ORDER BY
            "vec_model"
        """,
        dbEngine,
    )


def get_modelos_veiculos_regras(dbEngine):
    # Modelos de veículos que possuem informações de consumo
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "vec_model" AS "LABEL"
        FROM 
            mat_view_viagens_classificadas_dia_semana 
        WHERE 
            "vec_model" IS NOT NULL
        ORDER BY
            "vec_model"
        """,
        dbEngine,
    )


def get_linhas_possui_info_combustivel(dbEngine):
    # Linhas que possuem informações de consumo
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "encontrou_numero_linha" as "LABEL"
        FROM 
            rmtc_viagens_analise_mix rva 
        WHERE 
            "encontrou_numero_linha" IS NOT NULL
        ORDER BY
            "encontrou_numero_linha"
        """,
        dbEngine,
    )


def get_oficinas(dbEngine):
    # Oficinas
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "DESCRICAO DA OFICINA" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        """,
        dbEngine,
    )


def get_secoes(dbEngine):
    # Seções
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "DESCRICAO DA SECAO" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd
        """,
        dbEngine,
    )


def get_mecanicos(dbEngine):
    # Colaboradores / Mecânicos
    return pd.read_sql("SELECT * FROM colaboradores_frotas_os", dbEngine)


def get_lista_os(dbEngine):
    # Lista de OS
    return pd.read_sql(
        """
        SELECT DISTINCT
            "DESCRICAO DA SECAO" as "SECAO",
            "DESCRICAO DO SERVICO" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        ORDER BY
            "DESCRICAO DO SERVICO"
        """,
        dbEngine,
    )


def get_modelos(dbEngine):
    # Lista de Modelos
    return pd.read_sql(
        """
        SELECT DISTINCT
            "DESCRICAO DO MODELO" AS "MODELO"
        FROM 
            mat_view_retrabalho_10_dias mvrd
        """,
        dbEngine,
    )


def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output.getvalue()


def get_regras(dbEngine):
    # Lista de regras
    return pd.read_sql(
        """
        SELECT DISTINCT
            nome_regra AS "LABEL"
        FROM 
            regras_monitoramento
        """,
        dbEngine,
    )


def get_regras_padronizadas(dbEngine):

    return pd.read_sql(
        """
        SELECT 
            nome_regra AS "LABEL"
        FROM public.regras_monitoramento 
        WHERE regra_padronizada = true
        ORDER BY nome_regra;
        """,
        dbEngine,
    )

def get_regras_monitoramento_combustivel(dbEngine):
    # Lista de regras
    return pd.read_sql(
        """
        SELECT nome_regra as "label", id as "value" FROM regra_monitoramento_combustivel
        ORDER BY nome_regra;
        """,
        dbEngine,
    )


def get_tipos_eventos_telemetria_mix_com_data(dbEngine):
    # Retorna os tipos de eventos de telemetria que possuem StartDateTime
    query = """
    WITH eventos_aptos AS (
        SELECT DISTINCT table_name AS evt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND column_name = 'StartDateTime'
    )
    SELECT 
        t."Description" AS "label", 
        t."DescriptionCLEAN" AS "value",
        t."EventTypeId" AS "EventTypeId"
    FROM 
        tipos_eventos_api t
    WHERE 
        t."DescriptionCLEAN" IN ( SELECT evt_name FROM eventos_aptos );
    """
    return pd.read_sql(query, dbEngine)


def get_tipos_eventos_telemetria_mix_com_gps(dbEngine):
    # Retorna os tipos de eventos de telemetria que possuem Localização
    query = """
    WITH eventos_aptos AS (
        SELECT DISTINCT table_name AS evt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND column_name = 'StartPosition_Latitude'
    )
    SELECT 
        t."Description" AS "label", 
        t."DescriptionCLEAN" AS "value",
        t."EventTypeId" AS "EventTypeId"
    FROM 
        tipos_eventos_api t
    WHERE 
        t."DescriptionCLEAN" IN ( SELECT evt_name FROM eventos_aptos)
    """
    return pd.read_sql(query, dbEngine)
