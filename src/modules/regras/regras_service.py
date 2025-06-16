# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

from datetime import datetime, timedelta
from modules.sql_utils import *

# Imports auxiliares


class RegrasService:

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

    def get_estatistica_veiculos(
        self, dia, modelos, linha,
        quantidade_de_viagens, dias_marcados, 
        excluir_km_l_menor_que=0, excluir_km_l_maior_que=10,
        mediana_viagem=0, suspeita_performace=0,
        indicativo_performace=0, erro_telemetria=0         
    ):
        # Extraí as datas (já em string)
        data_atual_str = pd.to_datetime(datetime.now()).strftime("%Y-%m-%d")
        data_passada_str = pd.to_datetime(datetime.now()-timedelta(days=dia)).strftime("%Y-%m-%d")

        # Subquery para os dias selecionados
        subquery_dias_marcados = self.get_subquery_dias(dias_marcados)
        subquery_modelo = subquery_modelos_combustivel(modelos)
        subquery_linhas = subquery_linha_combustivel(linha)

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
            {subquery_modelo}
            {subquery_linhas}

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
            WHERE data_local between '{data_passada_str}' and '{data_atual_str}'
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
        print(query)
        # Executa a query
        df = pd.read_sql(query, self.pgEngine)
        if df.empty:
                return pd.DataFrame(columns=df.columns)

        # Arredonda a media
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # Pivot table
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual"],
            fill_value=0,
        )

        df_pivot.columns = [f'{col[0]}_{col[1].lower().replace(" ", "_")}' for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        df_pivot["total_viagens"] = df_pivot.filter(like="total_status").sum(axis=1)

        df_pivot["media_viagens_dia"] = df_pivot["total_viagens"]

        # Filtros com checagem de existência de colunas

        
        print(excluir_km_l_menor_que, excluir_km_l_maior_que)
        # Filtro por média de consumo
        df_pivot = df_pivot[
            (df_pivot["media_consumo_por_km"] >= excluir_km_l_menor_que) &
            (df_pivot["media_consumo_por_km"] <= excluir_km_l_maior_que)
        ]
        
        erro_telemetria = float(erro_telemetria) if erro_telemetria is not None else 0
        suspeita_performace = float(suspeita_performace) if suspeita_performace is not None else 0
        indicativo_performace = float(indicativo_performace) if indicativo_performace is not None else 0
        mediana_viagem = float(mediana_viagem) if mediana_viagem is not None else 0
        quantidade_de_viagens = int(quantidade_de_viagens) if quantidade_de_viagens is not None else 0


        if 'percentual_erro_telemetria' in df_pivot.columns:
            df_pivot = df_pivot[df_pivot['percentual_erro_telemetria'] >= erro_telemetria ]

        if 'percentual_suspeita_baixa_perfomance' in df_pivot.columns:
            df_pivot = df_pivot[df_pivot['percentual_suspeita_baixa_perfomance'] >= suspeita_performace]

        if 'percentual_baixa_performance' in df_pivot.columns:
            df_pivot = df_pivot[df_pivot['percentual_baixa_performance'] >= indicativo_performace]

        if 'percentual_regular' in df_pivot.columns:
            df_pivot = df_pivot[df_pivot['percentual_regular'] >= mediana_viagem]

        if quantidade_de_viagens > 0:
            df_pivot = df_pivot[df_pivot['total_viagens'] == quantidade_de_viagens]

        print(df_pivot)
        return df_pivot