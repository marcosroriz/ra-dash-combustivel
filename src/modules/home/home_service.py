#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de home

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel


class HomeService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def get_estatistica_consumo_por_veiculo(self):
        query = f"""
            WITH base AS (
            SELECT 
                *,
                (
                DATE_TRUNC('hour', TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours') +
                MAKE_INTERVAL(mins => (
                    FLOOR(EXTRACT(minute FROM TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours') / 30.0) * 30
                )::int)
                )::time AS slot_horario,
                CASE
                WHEN vec_model ILIKE 'MB OF 1721%%' THEN 'MB OF 1721 MPOLO TORINO U'
                WHEN vec_model ILIKE 'IVECO/MASCA%%' THEN 'IVECO/MASCA GRAN VIA'
                WHEN vec_model ILIKE 'VW 17230 APACHE VIP%%' THEN 'VW 17230 APACHE VIP-SC'
                WHEN vec_model ILIKE 'O500%%' THEN 'O500'
                WHEN vec_model ILIKE 'ELETRA INDUSCAR MILLENNIUM%%' THEN 'ELETRA INDUSCAR MILLENNIUM'
                WHEN vec_model ILIKE 'Induscar%%' THEN 'INDUSCAR'
                WHEN vec_model ILIKE 'VW 22.260 CAIO INDUSCAR%%' THEN 'VW 22.260 CAIO INDUSCAR'
                ELSE 'NÃO FORNECIDO'
                END AS vec_model_padronizado,
                (TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours')::date AS data_local
            FROM 
                rmtc_viagens_analise
            WHERE 
                encontrou_linha = TRUE
                AND km_por_litro > 0
                AND km_por_litro <= 10
            ),
            amostras_validas AS (
            SELECT 
                *
            FROM 
                base
            WHERE 
                EXTRACT(DOW FROM data_local) BETWEEN 1 AND 5
                AND NOT EXISTS (
                SELECT 1
                FROM feriados_goias fg
                WHERE fg.data = base.data_local
                    AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                )
            ),
            quartis AS (
            SELECT
                vec_model_padronizado,
                encontrou_numero_linha,
                encontrou_numero_sublinha,
                encontrou_sentido_linha,
                slot_horario,
                COUNT(*) as n_amostras,
                AVG(km_por_litro) as quartil_media,
                stddev_pop(km_por_litro) as quartil_desvpadrao, 
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY km_por_litro) AS q1,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY km_por_litro) AS mediana,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY km_por_litro) AS q3
            FROM 
                amostras_validas
            GROUP BY 
                vec_model_padronizado, encontrou_numero_linha, encontrou_numero_sublinha, encontrou_sentido_linha, slot_horario
            ),
            classificados AS (
            SELECT a.*,
                    q.n_amostras,
                    q.quartil_media,
                    q.quartil_desvpadrao,
                    q.q1,
                    q.q3,
                    q.mediana,
                    (q.q3 - q.q1) AS iqr,
                    (a.km_por_litro - q.mediana) AS diferenca_mediana,
                    CASE
                        WHEN a.km_por_litro < q.q1 - 1.5 * (q.q3 - q.q1) THEN 'BAIXA PERFORMANCE'
                        WHEN a.km_por_litro < q.q1 - 1.0 * (q.q3 - q.q1) THEN 'SUSPEITA BAIXA PERFOMANCE'
                        WHEN a.km_por_litro > q.q3 + 1.5 * (q.q3 - q.q1) THEN 'ERRO TELEMETRIA'
                    ELSE 
                        'REGULAR'
                    END AS status_consumo
            FROM 
                amostras_validas a
            JOIN 
                quartis q
            ON 
                a.vec_model_padronizado = q.vec_model_padronizado
                AND a.encontrou_numero_linha = q.encontrou_numero_linha
                AND a.encontrou_numero_sublinha = q.encontrou_numero_sublinha
                AND a.encontrou_sentido_linha = q.encontrou_sentido_linha
                AND a.slot_horario = q.slot_horario
            ),
            classificados_filtrados AS (
                SELECT * 
                FROM classificados
                WHERE data_local >= '2025-04-10'
            ),
            resumo_por_veiculo AS (
                SELECT 
                    vec_num_id,
                    vec_model_padronizado,
                    status_consumo,
                    COUNT(*) AS total_status
                FROM classificados_filtrados
                GROUP BY vec_num_id, vec_model_padronizado, status_consumo
            ),
            total_por_veiculo AS (
                SELECT 
                    vec_num_id,
                    AVG(km_por_litro) as media_consumo_por_km,
                    COUNT(*) AS total_geral
                FROM classificados_filtrados
                GROUP BY vec_num_id
            )
            SELECT 
                r.vec_num_id,
                r.vec_model_padronizado,
                r.status_consumo,
                r.total_status,
                t.media_consumo_por_km,
                ROUND(100.0 * r.total_status / t.total_geral, 2) AS percentual
            FROM 
                resumo_por_veiculo r
            JOIN 
                total_por_veiculo t
            ON 
                r.vec_num_id = t.vec_num_id

        """
        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        # Seta modelo null para Não Fornecido
        df["vec_model_padronizado"] = df["vec_model_padronizado"].fillna("Não Fornecido")
        
        # Arredonda a media
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # Pivota a tabela
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model_padronizado", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual"],
            fill_value=0,
        )

        # Ajustar os nomes das colunas para algo mais limpo
        df_pivot.columns = [f'{col[0]}_{col[1].lower().replace(" ", "_")}' for col in df_pivot.columns]

        # Resetar o índice para voltar com 'vec_num_id' como coluna normal
        df_pivot = df_pivot.reset_index()

        # Soma os valores de total_status
        df_pivot["total_viagens"] = df_pivot.filter(like="total_status").sum(axis=1)

        # Dividir pelo número de dias
        df_pivot["media_viagens_dia"] = (
            # df_pivot["total_viagens"] / (pd.to_datetime(data_fim_str) - pd.to_datetime(data_inicio_str)).days
            df_pivot["total_viagens"]
        )

        return df_pivot

    


    def get_consumo_por_modelo(self):
        query = f"""
        WITH base AS (
            SELECT 
                *,
                (
                DATE_TRUNC('hour', TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours') +
                MAKE_INTERVAL(mins => (
                    FLOOR(EXTRACT(minute FROM TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours') / 30.0) * 30
                )::int)
                )::time AS slot_horario,
                CASE
                WHEN vec_model ILIKE 'MB OF 1721%%' THEN 'MB OF 1721 MPOLO TORINO U'
                WHEN vec_model ILIKE 'IVECO/MASCA%%' THEN 'IVECO/MASCA GRAN VIA'
                WHEN vec_model ILIKE 'VW 17230 APACHE VIP%%' THEN 'VW 17230 APACHE VIP-SC'
                WHEN vec_model ILIKE 'O500%%' THEN 'O500'
                WHEN vec_model ILIKE 'ELETRA INDUSCAR MILLENNIUM%%' THEN 'ELETRA INDUSCAR MILLENNIUM'
                WHEN vec_model ILIKE 'Induscar%%' THEN 'INDUSCAR'
                WHEN vec_model ILIKE 'VW 22.260 CAIO INDUSCAR%%' THEN 'VW 22.260 CAIO INDUSCAR'
                ELSE vec_model
                END AS vec_model_padronizado,
                (TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours')::date AS data_local
            FROM 
                rmtc_viagens_analise
            WHERE 
                encontrou_linha = TRUE
                AND km_por_litro > 0
                AND km_por_litro <= 10
            ),
        amostras_validas AS (
            SELECT 
                *
            FROM 
                base
            WHERE 
                EXTRACT(DOW FROM data_local) BETWEEN 1 AND 5
                AND NOT EXISTS (
                    SELECT 1
                    FROM feriados_goias fg
                    WHERE fg.data = base.data_local
                        AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                )
        ),
        classificados_filtrados AS (
            SELECT * 
            FROM amostras_validas
            WHERE data_local >= '2025-05-10'
        ),
        resumo_por_veiculo AS (
            SELECT 
                vec_num_id,
                vec_model_padronizado,
                AVG(km_por_litro) as media_consumo_km,
                COUNT(*) AS total_viagens
            FROM classificados_filtrados
            GROUP BY vec_num_id, vec_model_padronizado
        )
        SELECT 
            *
        FROM 
            resumo_por_veiculo
        """
        df = pd.read_sql(query, self.pgEngine)
        df["vec_model_padronizado"] = df["vec_model_padronizado"].fillna("Não Fornecido")

        return df

    def get_consumo_por_linha(self):
        query = f"""
            WITH base AS (
                SELECT 
                    *,
                    (TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours')::date AS data_local
                FROM 
                    rmtc_viagens_analise
                WHERE 
                    encontrou_linha = TRUE
                    AND km_por_litro > 0
                    AND km_por_litro <= 10
            ),
            amostras_validas AS (
                SELECT 
                    *
                FROM 
                    base
                WHERE 
                    EXTRACT(DOW FROM data_local) BETWEEN 1 AND 5
                    AND NOT EXISTS (
                        SELECT 1
                        FROM feriados_goias fg
                        WHERE fg.data = base.data_local
                        AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                    )
                    AND data_local >= '2025-02-10'
            ),
            media_consumo_por_linha AS (
                SELECT
                    encontrou_numero_linha AS linha,
                    encontrou_numero_sublinha AS sublinha,
                    COUNT(*) AS total_viagens,
                    AVG(km_por_litro) AS media_km_por_litro
                FROM amostras_validas
                GROUP BY encontrou_numero_linha, encontrou_numero_sublinha, encontrou_sentido_linha
            )

            SELECT
                linha,
                sublinha,
                total_viagens,
                ROUND(media_km_por_litro::numeric, 2) AS media_km_por_litro
            FROM media_consumo_por_linha
            ORDER BY media_km_por_litro DESC;
        """
        df = pd.read_sql(query, self.pgEngine)
        return df
