#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de consumo por veículo

# Imports básicos
import os
import pandas as pd

# Imports auxiliares
from modules.sql_utils import subquery_linha_combustivel, subquery_dia_semana

# Constante indica o número mínimo de viagens que devem existir para poder classificar o consumo de uma viagem
# Por exemplo, NUM_MIN_VIAGENS_PARA_CLASSIFICAR = 5 indica que somente as viagens cuja configuração possuam outras 5
# viagens iguais (mesma linha, sentido, dia, etc) será incluída na análise
NUM_MIN_VIAGENS_PARA_CLASSIFICAR = os.getenv("NUM_MIN_VIAGENS_PARA_CLASSIFICAR", 5)


class VeiculoService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def get_sinteze_status_viagens(self, datas, vec_num_id, lista_linhas, km_l_min, km_l_max):
        """Função para obter a classificação das viagens analisadas"""

        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT  
            analise_status_90_dias,
            COUNT(*) as total_viagens
        FROM
            rmtc_viagens_analise_mix
        WHERE
	        encontrou_linha = true
	        AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
	        AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        GROUP BY
            analise_status_90_dias 
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_consumo_medio_km_l(self, datas, vec_num_id, lista_linhas, km_l_min, km_l_max):
        """Função para obter o indicador de consumo médio de km/L"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT  
            AVG(km_por_litro) as media_km_por_l
        FROM
            rmtc_viagens_analise_mix
        WHERE
            encontrou_linha = true
            AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
            AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_consumo_litros_excedente(self, datas, vec_num_id, lista_linhas, km_l_min, km_l_max):
        """Função para obter o indicador de consumo excedente em L"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT  
            SUM(ABS(total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias))) AS litros_excedentes
        FROM
            rmtc_viagens_analise_mix
        WHERE
            encontrou_linha = true
            AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
            AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_historico_viagens(self, datas, vec_num_id, lista_linhas, km_l_min, km_l_max):
        """Função para obter o histórico das viagens analisadas"""

        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        WITH rmtc_viagens_analise_mix_padronizado AS (
            SELECT 
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
                r.*
            FROM 
                rmtc_viagens_analise_mix r
        )
        SELECT
            m."Name" AS nome_motorista,
            3600 * (tamanho_linha_km_sobreposicao / encontrou_tempo_viagem_segundos) AS velocidade_media_kmh,
            r.*
        FROM 
            rmtc_viagens_analise_mix_padronizado r
        LEFT JOIN 
            motoristas_api m 
            ON r."DriverId" = m."DriverId"
        WHERE
            encontrou_linha = TRUE
	        AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
	        AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        ORDER BY 
            encontrou_timestamp_inicio;
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Força string nos asset_id
        df["vec_asset_id"] = df["vec_asset_id"].astype(str)

        # Ajusta datas
        df["encontrou_timestamp_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"])
        df["encontrou_timestamp_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"])
        df["timestamp_br_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["timestamp_br_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"]) - pd.Timedelta(hours=3)
        df["encontrou_tempo_viagem_segundos"] = df["encontrou_tempo_viagem_segundos"].astype(int)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_segundos"] / 60
        df["dia_dt"] = pd.to_datetime(df["dia"]).dt.date

        # Ajusta NaN
        df["nome_motorista"] = df["nome_motorista"].fillna("Não informado")

        # Arredonda
        df["km_por_litro"] = df["km_por_litro"].round(2)
        df["analise_valor_mediana_90_dias"] = df["analise_valor_mediana_90_dias"].round(2)
        df["velocidade_media_kmh"] = df["velocidade_media_kmh"].round(2)
        df["analise_diff_mediana_90_dias"] = df["analise_diff_mediana_90_dias"].round(2)

        return df

    def get_histograma_viagens_veiculo(
        self,
        km_l_min,
        km_l_max,
        viagem_data,
        viagem_vec_model,
        viagem_linha,
        viagem_sentido,
        viagem_time_slot,
        viagem_dia_semana,
        viagem_dia_eh_feriado,
    ):
        # Extraí a data inicial e final
        data_fim_str = (pd.to_datetime(viagem_data) + pd.DateOffset(days=1)).strftime("%Y-%m-%d") 
        # Pega 90 dias antes de viagens
        data_inicio_str = (pd.to_datetime(viagem_data) - pd.DateOffset(days=90)).strftime("%Y-%m-%d")

        # Subqueries
        subquery_dia_semana_str = subquery_dia_semana(viagem_dia_semana)
        
        # Query
        query = f"""
        SELECT
            m."Name" AS nome_motorista,
            ABS(
                total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)
            ) AS litros_excedentes,
            3600 * (tamanho_linha_km_sobreposicao / encontrou_tempo_viagem_segundos) AS velocidade_media_kmh,
            r.*
        FROM
            rmtc_viagens_analise_mix AS r
        LEFT JOIN
            motoristas_api AS m
            ON r."DriverId" = m."DriverId"
        WHERE
            encontrou_linha = TRUE
	        AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
	        AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            AND vec_model = '{viagem_vec_model}'
            AND time_slot = '{viagem_time_slot}'
            AND encontrou_numero_sublinha = '{viagem_linha}'
            AND dia_eh_feriado = {viagem_dia_eh_feriado}
            AND encontrou_sentido_linha='{viagem_sentido}'
            {subquery_dia_semana_str}
        ORDER BY
            rmtc_timestamp_inicio DESC;
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Força string nos asset_id
        df["vec_asset_id"] = df["vec_asset_id"].astype(str)

        # Ajusta datas
        df["encontrou_timestamp_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"])
        df["encontrou_timestamp_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"])
        df["timestamp_br_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["timestamp_br_fim"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["encontrou_tempo_viagem_segundos"] = df["encontrou_tempo_viagem_segundos"].astype(int)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_segundos"] / 60
        df["dia_dt"] = pd.to_datetime(df["dia"]).dt.date

        # Ajusta NaN
        df["nome_motorista"] = df["nome_motorista"].fillna("Não informado")

        # Arredonda
        df["km_por_litro"] = df["km_por_litro"].round(2)
        df["analise_valor_mediana_90_dias"] = df["analise_valor_mediana_90_dias"].round(2)
        df["velocidade_media_kmh"] = df["velocidade_media_kmh"].round(2)
        df["analise_diff_mediana_90_dias"] = df["analise_diff_mediana_90_dias"].round(2)

        # Traduz dia da semana para label
        # 1 = Domingo, 2 = Segunda, 3 = Terça, 4 = Quarta, 5 = Quinta, 6 = Sexta, 7 = Sábado
        dia_semana_map = {1: "Domingo", 2: "Segunda", 3: "Terça", 4: "Quarta", 5: "Quinta", 6: "Sexta", 7: "Sábado"}
        df["dia_semana_label"] = df["dia_numerico"].map(dia_semana_map)

        return df

    def get_tabela_lista_viagens_veiculo(self, datas, vec_num_id, lista_linhas, km_l_min, km_l_max):
        """Função para obter os dados da tabela com as viagens realizadsa por um veiculo"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT
            *,
            ABS(total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)) AS litros_excedentes,
            3600 * (tamanho_linha_km_sobreposicao / encontrou_tempo_viagem_segundos) AS velocidade_media_kmh,
            m."Name" AS nome_motorista
        FROM
            rmtc_viagens_analise_mix r
        LEFT JOIN 
            motoristas_api m 
            ON r."DriverId" = m."DriverId"
        WHERE
            encontrou_linha = true
            AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
            AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        ORDER BY
            rmtc_timestamp_inicio DESC;
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Ordena
        df = df.sort_values(by=["dia", "encontrou_timestamp_inicio"], ascending=[False, False])

        # Força string nos asset_id
        df["vec_asset_id"] = df["vec_asset_id"].astype(str)

        # Ajusta datas
        df["encontrou_timestamp_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"])
        df["encontrou_timestamp_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"])
        df["timestamp_br_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["timestamp_br_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"]) - pd.Timedelta(hours=3)
        df["timestamp_br_inicio_str"] = df["timestamp_br_inicio"].dt.strftime("%H:%M:%S")
        df["timestamp_br_fim_str"] = df["timestamp_br_fim"].dt.strftime("%H:%M:%S")
        df["dia_label"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        # Duração
        df["encontrou_tempo_viagem_segundos"] = df["encontrou_tempo_viagem_segundos"].astype(int)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_segundos"] / 60

        # Arrendonda as colunas necessárias
        df["km_por_litro"] = df["km_por_litro"].round(2)
        df["litros_excedentes"] = df["litros_excedentes"].round(2)
        df["velocidade_media_kmh"] = df["velocidade_media_kmh"].round(2)
        df["total_comb_l"] = df["total_comb_l"].round(2)
        df["analise_valor_mediana_90_dias"] = df["analise_valor_mediana_90_dias"].round(2)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_minutos"].round(0)

        # Ajusta NaN
        df["nome_motorista"] = df["nome_motorista"].fillna("Não informado")

        return df

    def get_agg_eventos_ocorreram_viagem(self, data_inicio_str, data_fim_str, vec_asset_id):
        query = f"""
        SELECT
            tea."Description" AS event_label,
            tea."DescriptionCLEAN" AS event_value,
            tea."EventTypeId" AS event_type_id,
            COUNT(*) AS total_eventos
        FROM
            public.trip_possui_evento AS tpe
        LEFT JOIN
            tipos_eventos_api AS tea
            ON tpe.event_type_id = tea."EventTypeId"
        WHERE
            asset_id = '{vec_asset_id}'
            AND dia_evento IS NOT NULL
            AND (
                "dia_evento"::timestamptz AT TIME ZONE 'America/Sao_Paulo'
            ) BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        GROUP BY
            tea."Description", tea."DescriptionCLEAN", tea."EventTypeId"
        ORDER BY
            tea."Description";
        """
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_eventos_ocorreram_viagem(self, data_inicio_str, data_fim_str, vec_asset_id):
        query = f"""
        SELECT
            *
        FROM
            public.trip_possui_evento AS tpe
        LEFT JOIN
            tipos_eventos_api AS tea
            ON tpe.event_type_id = tea."EventTypeId"
        WHERE
            asset_id = '{vec_asset_id}'
            AND dia_evento IS NOT NULL
            AND (
                "dia_evento"::timestamptz AT TIME ZONE 'America/Sao_Paulo'
            ) BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        """
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_detalhamento_evento_mix_veiculo(self, data_inicio_str, data_fim_str, vec_asset_id, event_name):
        query = f"""
            SELECT
            *
            FROM
                public.{event_name} evt
            LEFT JOIN motoristas_api ma 
                on evt."DriverId" = ma."DriverId" 
            WHERE
                "AssetId" = '{vec_asset_id}'
                AND
                "StartDateTime" IS NOT NULL
                AND "StartDateTime"::text NOT ILIKE 'NaN'
                AND ("StartDateTime"::timestamptz AT TIME ZONE 'America/Sao_Paulo')
                    BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        """
        df = pd.read_sql(query, self.dbEngine)

        # Seta nome não conhecido para os motoristas que não tiverem dado
        df["Name"] = df["Name"].fillna("Não informado")
        return df

    def get_posicao_gps_veiculo(self, data_inicio_str, data_fim_str, vec_asset_id):
        query = f"""
            SELECT
            *
            FROM
                public.posicao_gps
            WHERE
                "AssetId" = '{vec_asset_id}'
                AND
                "Timestamp" IS NOT NULL
                AND "Timestamp"::text NOT ILIKE 'NaN'
                AND ("Timestamp"::timestamptz AT TIME ZONE 'America/Sao_Paulo')
                    BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        """
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_shape_linha(self, data_str, viagem_linha, viagem_sentido):
        query = f"""
        SELECT
            id,
            diahorario,
            numero,
            numero_sublinha,
            desc_linha,
            sentido,
            tamanhokm,
            geojsondata
        FROM (
            SELECT DISTINCT ON (numero_sublinha, sentido) *
            FROM rmtc_kml_via_ra kml
            ORDER BY numero_sublinha, sentido, ABS(EXTRACT(EPOCH FROM (kml.diahorario::timestamp - '{data_str}'::timestamp)))
        ) AS via_ra
        WHERE numero_sublinha = '{viagem_linha}' AND sentido = '{viagem_sentido}'
        """
        df = pd.read_sql(query, self.dbEngine)

        return df
