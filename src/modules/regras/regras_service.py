# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

from datetime import datetime, timedelta
from modules.sql_utils import *
from sqlalchemy import text

# Imports auxiliares


class RegrasService:

    def __init__(self, pgEngine):

        self.pgEngine = pgEngine

    def get_regras(self):

        query = '''
        SELECT * FROM public.regras_monitoramento;
        '''
        return pd.read_sql(query, self.pgEngine)

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
                 EXISTS (
                    SELECT 1
                    FROM feriados_goias fg
                    WHERE fg.data = data_local AND fg.municipio IN ('Brasil', 'Goiás', 'Goiânia')
                )
            """

        return dias_subquery
        
    def get_estatistica_regras(
        self,
        data,
        modelos,
        linha,
        quantidade_de_viagens,
        dias_marcados,
        excluir_km_l_menor_que,
        excluir_km_l_maior_que,
        mediana_viagem,
        suspeita_performace,
        indicativo_performace,
        erro_telemetria         
    ):
        # Datas
        data_inicio_str = pd.to_datetime(datetime.now() - timedelta(days=data)).strftime("%Y-%m-%d")
        data_fim_str = pd.to_datetime(datetime.now()).strftime("%Y-%m-%d")

        # Converte para tipos esperados
        mediana_viagem = int(mediana_viagem or 0)
        erro_telemetria = float(erro_telemetria or 0)
        suspeita_performace = float(suspeita_performace or 0)
        indicativo_performace = float(indicativo_performace or 0)
        quantidade_de_viagens = int(quantidade_de_viagens or 0)
        excluir_km_l_menor_que = float(excluir_km_l_menor_que or 0)
        excluir_km_l_maior_que = float(excluir_km_l_maior_que or 10)

        # Subqueries auxiliares
        subquery_dias_marcados = self.get_subquery_dias(dias_marcados)
        subquery_modelo = subquery_modelos_combustivel(modelos)
        subquery_linhas = subquery_linha_combustivel(linha)

        # Query principal
        query = f"""
            WITH base AS (
                SELECT *,
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
                FROM rmtc_viagens_analise
                WHERE 
                    encontrou_linha = TRUE
                    AND km_por_litro > 0
                    AND km_por_litro <= 10
                    {subquery_modelo}
                    {subquery_linhas}
            ),
            amostras_validas AS (
                SELECT *
                FROM base
                WHERE {subquery_dias_marcados}
            ),
            amostras_filtradas AS (
                SELECT *
                FROM amostras_validas
                WHERE data_local BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            ),
            estatisticas AS (
                SELECT
                    vec_model_padronizado,
                    encontrou_numero_linha,
                    encontrou_numero_sublinha,
                    encontrou_sentido_linha,
                    slot_horario,
                    AVG(km_por_litro) AS media,
                    STDDEV(km_por_litro) AS desvio_padrao
                FROM amostras_filtradas
                GROUP BY vec_model_padronizado, encontrou_numero_linha, encontrou_numero_sublinha, encontrou_sentido_linha, slot_horario
            ),
            classificados AS (
                SELECT a.*, e.media, e.desvio_padrao,
                    CASE
                        WHEN a.km_por_litro > e.media + e.desvio_padrao THEN 'ERRO TELEMETRIA'
                        WHEN a.km_por_litro < e.media - 2 * e.desvio_padrao THEN 'BAIXA PERFORMANCE'
                        WHEN a.km_por_litro < e.media - 1 * e.desvio_padrao THEN 'SUSPEITA BAIXA PERFORMANCE'
                        ELSE 'REGULAR'
                    END AS status_consumo
                FROM amostras_filtradas a
                JOIN estatisticas e
                    ON a.vec_model_padronizado = e.vec_model_padronizado
                    AND a.encontrou_numero_linha = e.encontrou_numero_linha
                    AND a.encontrou_numero_sublinha = e.encontrou_numero_sublinha
                    AND a.encontrou_sentido_linha = e.encontrou_sentido_linha
                    AND a.slot_horario = e.slot_horario
            ),
            resumo_por_veiculo AS (
                SELECT vec_num_id, vec_model, status_consumo, COUNT(*) AS total_status
                FROM classificados
                GROUP BY vec_num_id, vec_model, status_consumo
            ),
            total_por_veiculo AS (
                SELECT 
                    vec_num_id,
                    AVG(km_por_litro) AS media_consumo_por_km,
                    COUNT(*) AS total_geral,
                    AVG(media) AS media_geral,
                    (100.0 * COUNT(*) FILTER (WHERE km_por_litro < media) / COUNT(*)) AS percentual_abaixo
                FROM classificados
                GROUP BY vec_num_id
            )
            SELECT 
                r.vec_num_id,
                r.vec_model,
                r.status_consumo,
                r.total_status,
                t.media_consumo_por_km,
                ROUND(100.0 * r.total_status / t.total_geral, 2) AS percentual,
                t.percentual_abaixo
            FROM resumo_por_veiculo r
            JOIN total_por_veiculo t ON r.vec_num_id = t.vec_num_id
            WHERE t.percentual_abaixo >= {mediana_viagem}
        """

        df = pd.read_sql(query, self.pgEngine)

        if df.empty:
            return pd.DataFrame(columns=["vec_num_id", "vec_model", "media_consumo_por_km", "total_viagens"])

        # Pivot da tabela
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual"],
            fill_value=0
        )

        # Ajusta nomes de colunas
        df_pivot.columns = [f"{col[0]}_{col[1].lower().replace(' ', '_')}" for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        # Calcula totais
        df_pivot["total_viagens"] = df_pivot.filter(like="total_status").sum(axis=1)
        df_pivot = df_pivot.sort_values(by="total_viagens", ascending=False)
        df_pivot["media_viagens_dia"] = df_pivot["total_viagens"]

        # Filtros por km/L
        df_pivot = df_pivot[
            (df_pivot["media_consumo_por_km"] >= excluir_km_l_menor_que) &
            (df_pivot["media_consumo_por_km"] <= excluir_km_l_maior_que)
        ]

        # Aplicação dos filtros por percentual
        filtros_percentuais = {
            'percentual_erro_telemetria': erro_telemetria,
            'percentual_suspeita_baixa_performance': suspeita_performace,
            'percentual_baixa_performance': indicativo_performace
        }

        for coluna, limite in filtros_percentuais.items():
            if coluna in df_pivot.columns:
                df_pivot = df_pivot[df_pivot[coluna] >= limite]

        # Filtro por número mínimo de viagens
        if quantidade_de_viagens > 0:
            df_pivot = df_pivot[df_pivot['total_viagens'] >= quantidade_de_viagens]

        # Arredonda colunas de percentual
        colunas_para_arredondar = [
            'percentual_erro_telemetria',
            'percentual_suspeita_baixa_performance',
            'percentual_baixa_performance',
            'media_consumo_por_km'
        ]

        for coluna in colunas_para_arredondar:
            if coluna in df_pivot.columns:
                df_pivot[coluna] = df_pivot[coluna].round(2).apply(lambda x: f"{x:.2f}")

        return df_pivot

    

    def get_estatistica_veiculos_analise_performance(
        self,
        data,
        modelos,
        linha,
        quantidade_de_viagens,
        dias_marcados,
        excluir_km_l_menor_que,
        excluir_km_l_maior_que,
        mediana_viagem,
        suspeita_performace,
        indicativo_performace,
        erro_telemetria          
    ):

        # Extrai a data inicial e final
        data_inicio_str, data_fim_str = pd.to_datetime(data[0]).strftime("%Y-%m-%d"), pd.to_datetime(data[1]).strftime("%Y-%m-%d")

        # Converte para tipos esperados
        mediana_viagem = int(mediana_viagem or 0)
        erro_telemetria = float(erro_telemetria or 0)
        suspeita_performace = float(suspeita_performace or 0)
        indicativo_performace = float(indicativo_performace or 0)
        quantidade_de_viagens = int(quantidade_de_viagens or 0)
        excluir_km_l_menor_que = float(excluir_km_l_menor_que or 0)
        excluir_km_l_maior_que = float(excluir_km_l_maior_que or 10)

        # Subqueries auxiliares
        subquery_dias_marcados = self.get_subquery_dias(dias_marcados)
        subquery_modelo = subquery_modelos_combustivel(modelos)
        subquery_linhas = subquery_linha_combustivel(linha)

        # Query principal
        query = f"""
            WITH base AS (
                SELECT *,
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
                FROM rmtc_viagens_analise
                WHERE 
                    encontrou_linha = TRUE
                    AND km_por_litro > 0
                    AND km_por_litro <= 10
                    {subquery_modelo}
                    {subquery_linhas}
            ),
            amostras_validas AS (
                SELECT *
                FROM base
                WHERE {subquery_dias_marcados}
            ),
            amostras_filtradas AS (
                SELECT *
                FROM amostras_validas
                WHERE data_local BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            ),
            estatisticas AS (
                SELECT
                    vec_model_padronizado,
                    encontrou_numero_linha,
                    encontrou_numero_sublinha,
                    encontrou_sentido_linha,
                    slot_horario,
                    AVG(km_por_litro) AS media,
                    STDDEV(km_por_litro) AS desvio_padrao
                FROM amostras_filtradas
                GROUP BY vec_model_padronizado, encontrou_numero_linha, encontrou_numero_sublinha, encontrou_sentido_linha, slot_horario
            ),
            classificados AS (
                SELECT a.*, e.media, e.desvio_padrao,
                    CASE
                        WHEN a.km_por_litro > e.media + e.desvio_padrao THEN 'ERRO TELEMETRIA'
                        WHEN a.km_por_litro < e.media - 2 * e.desvio_padrao THEN 'BAIXA PERFORMANCE'
                        WHEN a.km_por_litro < e.media - 1 * e.desvio_padrao THEN 'SUSPEITA BAIXA PERFORMANCE'
                        ELSE 'REGULAR'
                    END AS status_consumo
                FROM amostras_filtradas a
                JOIN estatisticas e
                    ON a.vec_model_padronizado = e.vec_model_padronizado
                    AND a.encontrou_numero_linha = e.encontrou_numero_linha
                    AND a.encontrou_numero_sublinha = e.encontrou_numero_sublinha
                    AND a.encontrou_sentido_linha = e.encontrou_sentido_linha
                    AND a.slot_horario = e.slot_horario
            ),
            resumo_por_veiculo AS (
                SELECT vec_num_id, vec_model, status_consumo, COUNT(*) AS total_status
                FROM classificados
                GROUP BY vec_num_id, vec_model, status_consumo
            ),
            total_por_veiculo AS (
                SELECT 
                    vec_num_id,
                    AVG(km_por_litro) AS media_consumo_por_km,
                    COUNT(*) AS total_geral,
                    AVG(media) AS media_geral,
                    (100.0 * COUNT(*) FILTER (WHERE km_por_litro < media) / COUNT(*)) AS percentual_abaixo
                FROM classificados
                GROUP BY vec_num_id
            )
            SELECT 
                r.vec_num_id,
                r.vec_model,
                r.status_consumo,
                r.total_status,
                t.media_consumo_por_km,
                ROUND(100.0 * r.total_status / t.total_geral, 2) AS percentual,
                t.percentual_abaixo
            FROM resumo_por_veiculo r
            JOIN total_por_veiculo t ON r.vec_num_id = t.vec_num_id
            WHERE t.percentual_abaixo >= {mediana_viagem}
        """

        df = pd.read_sql(query, self.pgEngine)

        if df.empty:
            return pd.DataFrame(columns=["vec_num_id", "vec_model", "media_consumo_por_km", "total_viagens"])

        # Pivot da tabela
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual"],
            fill_value=0
        )

        # Ajusta nomes de colunas
        df_pivot.columns = [f"{col[0]}_{col[1].lower().replace(' ', '_')}" for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        # Calcula totais
        df_pivot["total_viagens"] = df_pivot.filter(like="total_status").sum(axis=1)
        df_pivot = df_pivot.sort_values(by="total_viagens", ascending=False)
        df_pivot["media_viagens_dia"] = df_pivot["total_viagens"]

        # Filtros por km/L
        df_pivot = df_pivot[
            (df_pivot["media_consumo_por_km"] >= excluir_km_l_menor_que) &
            (df_pivot["media_consumo_por_km"] <= excluir_km_l_maior_que)
        ]

        # Aplicação dos filtros por percentual
        filtros_percentuais = {
            'percentual_erro_telemetria': erro_telemetria,
            'percentual_suspeita_baixa_performance': suspeita_performace,
            'percentual_baixa_performance': indicativo_performace
        }

        for coluna, limite in filtros_percentuais.items():
            if coluna in df_pivot.columns:
                df_pivot = df_pivot[df_pivot[coluna] >= limite]

        # Filtro por número mínimo de viagens
        if quantidade_de_viagens > 0:
            df_pivot = df_pivot[df_pivot['total_viagens'] >= quantidade_de_viagens]

        # Arredonda colunas de percentual
        colunas_para_arredondar = [
            'percentual_erro_telemetria',
            'percentual_suspeita_baixa_performance',
            'percentual_baixa_performance',
            'media_consumo_por_km'
        ]

        for coluna in colunas_para_arredondar:
            if coluna in df_pivot.columns:
                df_pivot[coluna] = df_pivot[coluna].round(2).apply(lambda x: f"{x:.2f}")

        return df_pivot


    def salvar_regra_monitoramento(
        self,
        nome_regra,
        data,
        modelos,
        linha,
        quantidade_de_viagens,
        dias_marcados,
        excluir_km_l_menor_que=0,
        excluir_km_l_maior_que=0,
        mediana_viagem=0,
        suspeita_performace=0,
        indicativo_performace=0,
        erro_telemetria=0
    ):

        usar_km_l_min = excluir_km_l_menor_que is not None
        usar_km_l_max = excluir_km_l_maior_que is not None
        usar_mediana = mediana_viagem is not None
        usar_suspeita = suspeita_performace is not None
        usar_indicativo = indicativo_performace is not None
        usar_erro = erro_telemetria is not None

        try:
            with self.pgEngine.connect() as conn:
                insert_sql = text("""
                    INSERT INTO regras_monitoramento (
                        nome_regra, periodo, modelos, linha, dias_analise, qtd_viagens,
                        km_l_min, usar_km_l_min,
                        km_l_max, usar_km_l_max,
                        mediana_viagem, usar_mediana_viagem,
                        suspeita_performace, usar_suspeita_performace,
                        indicativo_performace, usar_indicativo_performace,
                        erro_telemetria, usar_erro_telemetria,
                        criado_em
                    ) VALUES (
                        :nome_regra, :periodo, :modelos, :linha, :dias_analise, :qtd_viagens,
                        :km_l_min, :usar_km_l_min,
                        :km_l_max, :usar_km_l_max,
                        :mediana_viagem, :usar_mediana_viagem,
                        :suspeita_performace, :usar_suspeita_performace,
                        :indicativo_performace, :usar_indicativo_performace,
                        :erro_telemetria, :usar_erro_telemetria,
                        :criado_em
                    )
                """)

                conn.execute(insert_sql, {
                    "nome_regra": nome_regra,
                    "periodo": data,
                    "modelos": modelos,
                    "linha": linha,
                    "dias_analise": dias_marcados,
                    "qtd_viagens": quantidade_de_viagens,
                    "km_l_min": excluir_km_l_menor_que,
                    "usar_km_l_min": usar_km_l_min,
                    "km_l_max": excluir_km_l_maior_que,
                    "usar_km_l_max": usar_km_l_max,
                    "mediana_viagem": mediana_viagem,
                    "usar_mediana_viagem": usar_mediana,
                    "suspeita_performace": suspeita_performace,
                    "usar_suspeita_performace": usar_suspeita,
                    "indicativo_performace": indicativo_performace,
                    "usar_indicativo_performace": usar_indicativo,
                    "erro_telemetria": erro_telemetria,
                    "usar_erro_telemetria": usar_erro,
                    "criado_em": datetime.now()
                })

                conn.commit()

        except Exception as e:
            print(f"Erro ao salvar a regra: {e}")
