#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de monitoramento

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel


class MonitoramentoService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def get_subquery_dias(self, dias_marcados):
        dias_subquery = ""

        if "SEG_SEX" in dias_marcados:
            dias_subquery = "EXTRACT(DOW FROM data_local) BETWEEN 1 AND 5"
        elif "SABADO" in dias_marcados:
            dias_subquery = "EXTRACT(DOW FROM data_local) = 6"
        elif "DOMINGO" in dias_marcados:
            dias_subquery = "EXTRACT(DOW FROM data_local) = 0"

        if "FERIADO" not in dias_marcados:
            dias_subquery += """
                AND NOT EXISTS (
                    SELECT 1
                    FROM feriados_goias fg
                    WHERE fg.data = data_local AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                )
                """
        else:
            dias_subquery += """
                AND EXISTS (
                    SELECT 1
                    FROM feriados_goias fg
                    WHERE fg.data = data_local AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                )
            """

        return dias_subquery

    def get_estatistica_veiculos(self, dia, linha, dias_marcados):
        # Extraí as datas (já em string)
        data_str = pd.to_datetime(dia).strftime("%Y-%m-%d")

        # Subquery para os dias selecionados
        subquery_dias_marcados = self.get_subquery_dias(dias_marcados)

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
            {subquery_dias_marcados}
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
            WHERE data_local = '{data_str}'
        ),
        resumo_por_veiculo AS (
            SELECT 
                vec_num_id,
                vec_model,
                status_consumo,
                COUNT(*) AS total_status
            FROM classificados_filtrados
            GROUP BY vec_num_id, vec_model, status_consumo
        ),
        total_por_veiculo AS (
            SELECT 
                vec_num_id,
                AVG(km_por_litro) as MEDIA_CONSUMO_POR_KM,
                COUNT(*) AS total_geral
            FROM classificados_filtrados
            GROUP BY vec_num_id
        )
        SELECT 
            r.vec_num_id,
            r.vec_model,
            r.status_consumo,
            r.total_status,
            t.MEDIA_CONSUMO_POR_KM,
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

        # Arredonda a media
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # Pivota a tabela
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
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



    def get_veiculos_rodaram_no_dia(self, dia):
        # Extraí as datas (já em string)
        data_str = pd.to_datetime(dia).strftime("%Y-%m-%d")

        query = f"""
            SELECT DISTINCT
                vec_num_id,
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
                COUNT(*) as total_viagens
            FROM
                rmtc_viagens_analise
            WHERE
                (TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours')::date = '{data_str}'
            GROUP BY vec_num_id, vec_model
            ORDER BY vec_num_id
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        # Criar label concatenando vec_num_id e vec_model com o total de viagens
        df["label"] = df["vec_num_id"].astype(str) + " - " + df["vec_model_padronizado"]# + " (VIAGENS: " + df["total_viagens"].astype(str) + ")"
        df["value"] = df["vec_num_id"].astype(str)

        # Remove as colunas que possuem dados nulos
        df = df.dropna(subset=["label", "value"])

        return df


    def get_viagens_do_veiculo(self, dia, vec_num_id):
        # Extraí as datas (já em string)
        data_str = pd.to_datetime(dia).strftime("%Y-%m-%d")

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
            FROM amostras_validas
            GROUP BY vec_model_padronizado, encontrou_numero_linha, encontrou_numero_sublinha, encontrou_sentido_linha, slot_horario
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
                    ELSE 'REGULAR'
                    END AS status_consumo
            FROM amostras_validas a
            JOIN quartis q
                ON a.vec_model_padronizado = q.vec_model_padronizado
            AND a.encontrou_numero_linha = q.encontrou_numero_linha
            AND a.encontrou_numero_sublinha = q.encontrou_numero_sublinha
            AND a.encontrou_sentido_linha = q.encontrou_sentido_linha
            AND a.slot_horario = q.slot_horario
        ),
        classificados_filtrados AS (
            SELECT * 
            FROM classificados
            WHERE 
                data_local = '{data_str}' AND vec_num_id = '{vec_num_id}'
        )
        SELECT 
            c.*, 
            t."TripId", 
            t."DriverId",
            m."Name" AS nome_motorista
        FROM 
            classificados_filtrados c
        LEFT JOIN LATERAL (
            SELECT "TripId", "DriverId"
            FROM trips_api t
            WHERE 
                t."AssetId" = c.vec_asset_id::bigint
                AND TO_TIMESTAMP(t."StartPosition_Timestamp", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') - INTERVAL '3 hours'
                <= TO_TIMESTAMP(c.rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') + INTERVAL '10 minutes'
                ORDER BY ABS(
                    EXTRACT(EPOCH FROM (
                    TO_TIMESTAMP(t."StartPosition_Timestamp", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') - INTERVAL '3 hours' - 
                    TO_TIMESTAMP(c.rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
                ))
            )
            LIMIT 1
        ) t ON true
        LEFT JOIN 
            motoristas_api m ON m."DriverId" = t."DriverId"
        ORDER BY c.rmtc_timestamp_inicio;
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)


        # Pega as viagens que não foram analisadas
        query_nao_analisadas = f"""
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
            where
                encontrou_linha = FALSE
                and (TO_TIMESTAMP(rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') - INTERVAL '3 hours')::date = '2025-05-29' 
                AND vec_num_id = '50524'
        )
        select c.*,
            t."TripId",
            t."DriverId",
            m."Name" AS nome_motorista
        FROM
            base c
        LEFT JOIN LATERAL (
            SELECT "TripId", "DriverId"
            FROM trips_api t
            WHERE
                t."AssetId" = c.vec_asset_id::bigint
                AND TO_TIMESTAMP(t."StartPosition_Timestamp", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') - INTERVAL '3 hours'
                <= TO_TIMESTAMP(c.rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') + INTERVAL '10 minutes'
                ORDER BY ABS(
                    EXTRACT(EPOCH FROM (
                    TO_TIMESTAMP(t."StartPosition_Timestamp", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') - INTERVAL '3 hours' -
                    TO_TIMESTAMP(c.rmtc_timestamp_inicio, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
                ))
            )
            LIMIT 1
        ) t ON true
        LEFT JOIN
            motoristas_api m ON m."DriverId" = t."DriverId"
        """

        # Converte o slot_horario para datetime
        df["slot_horario_dt"] = pd.to_datetime(df["slot_horario"], format="%H:%M:%S")
        df["time_bin_formatado"] = df["slot_horario_dt"]

        # Calcula o tempo da viagem em minutos
        df["tempo_minutos"] = (df["encontrou_tempo_viagem_segundos"] / 60).round(1)

        # Adiciona os labels para hora de inicio e fim da viagem
        df["encontrou_timestamp_inicio_dt"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["encontrou_timestamp_fim_dt"] = pd.to_datetime(df["encontrou_timestamp_fim"]) - pd.Timedelta(hours=3)
        df["hora_inicio"] = df["encontrou_timestamp_inicio_dt"].dt.strftime("%H:%M")
        df["hora_fim"] = df["encontrou_timestamp_fim_dt"].dt.strftime("%H:%M")

        # Adiciona o dia da semana, mas como label em cima do dia
        df["dia_semana"] = df["encontrou_timestamp_inicio_dt"].dt.dayofweek
        df["dia_semana_label"] = df["dia_semana"].map({0: "Domingo", 1: "Segunda", 2: "Terça", 3: "Quarta", 4: "Quinta", 5: "Sexta", 6: "Sábado"})
        df["dia_label"] = df["dia_semana_label"] + " - " + df["encontrou_timestamp_inicio_dt"].dt.strftime("%d/%m/%Y")

        # Arredonda o consumo para 2 casas decimais
        df["km_redondo"] = df["km_por_litro"].round(2)

        return df



    def get_ultimas_viagens(self, n_viagens):
        """
        Função que retorna as últimas viagens de todos os veículos
        """

        # Query
        query = f"""
        SELECT 
            *
        FROM 
        (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY vec_num_id ORDER BY rmtc_timestamp_inicio DESC) AS rn
            FROM 
                public.rmtc_viagens_analise_via_ra
        ) sub
        WHERE 
            rn <= {n_viagens};
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df

    def normaliza_modelos(self, df):
        # Faz um DE / PARA para os seguintes elementos
        de_para_dict = {
            "IVECO/MASCA ": "IVECO",
            "IVECO/MASCA GRAN VIA U": "IVECO",
            "VW 17230 APACHE VIP-SC": "VW 17230",
            "VW 17230 APACHE VIP-SC ": "VW 17230",
            "VW 22.260 CAIO INDUSCAR APACHE U": "VW 22260",
            "MB OF 1721 L59 E6 MPOLO TORINO U": "MB 1721",
            "MB OF 1721 MPOLO TORINO U": "MB 1721",
            "ELETRA INDUSCAR MILLENNIUM": "INDUSCAR",
            "Induscar": "INDUSCAR",
        }

        # Aplica
        df["vec_model"] = df["vec_model"].replace(de_para_dict)

        return df
