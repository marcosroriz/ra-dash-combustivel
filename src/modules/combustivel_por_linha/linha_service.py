#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página combustível por linha

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel, subquery_lista_dia_marcado


class LinhaService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

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
    
    def get_indicadores_linha(self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior):
        """
        Função para obter os indicadores da linha
        """
        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_dia_marcado = subquery_lista_dia_marcado(lista_dia_semana)
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

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
                FROM rmtc_viagens_analise_mix r
                WHERE 
                    "encontrou_numero_linha" = '{linha}'
                    AND "encontrou_linha" = TRUE
                    AND "dia" >= '{data_inicio_str}'
                    AND "dia" <= '{data_fim_str}'
                    AND "km_por_litro" >= {limite_km_l_menor}
                    AND "km_por_litro" <= {limite_km_l_maior}
                    {subquery_dia_marcado}
                    {subquery_sentido}
                    {subquery_modelos}
            )
            SELECT
                COUNT(*) as total_num_viagens,
                COUNT(DISTINCT vec_model) AS total_num_modelos,
			    COUNT(DISTINCT vec_num_id) AS total_num_veiculos,
				AVG(3600 * (tamanho_linha_km_sobreposicao / encontrou_tempo_viagem_segundos)) AS velocidade_media_kmh,
				AVG(km_por_litro) AS "media_consumo_viagem",
                SUM(
					CASE 
						WHEN analise_status_90_dias = 'BAIXA PERFOMANCE (<= 2 STD)' THEN ABS(total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias))
						ELSE 0
					END
	            ) AS total_litros_excedentes
            FROM
                rmtc_viagens_analise_mix_padronizado r
        """
        df = pd.read_sql(query, self.pgEngine)

        # Arredonda os valores
        df["velocidade_media_kmh"] = df["velocidade_media_kmh"].round(2)
        df["media_consumo_viagem"] = df["media_consumo_viagem"].round(2)
        df["total_litros_excedentes"] = df["total_litros_excedentes"].round(2)

        return df
    
    def get_consumo_por_time_slot_linha(self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior):
        """
        Função para obter os dados do combustível por linha por horário (que será usado para gerar o gráfico)
        """
        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_dia_marcado = subquery_lista_dia_marcado(lista_dia_semana)
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

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
                FROM rmtc_viagens_analise_mix r
                WHERE 
                    "encontrou_numero_linha" = '{linha}'
                    AND "encontrou_linha" = TRUE
                    AND "dia" >= '{data_inicio_str}'
                    AND "dia" <= '{data_fim_str}'
                    AND "km_por_litro" >= {limite_km_l_menor}
                    AND "km_por_litro" <= {limite_km_l_maior}
                    {subquery_dia_marcado}
                    {subquery_sentido}
                    {subquery_modelos}
            )
            SELECT
                r."time_slot",
                r."vec_model",
                AVG("km_por_litro") AS "mean",
                MIN("km_por_litro") AS "min",
                MAX("km_por_litro") AS "max",
                STDDEV_POP("km_por_litro") AS "std"
            FROM
                rmtc_viagens_analise_mix_padronizado r
            GROUP BY r."time_slot", r."vec_model"
            HAVING
			    COUNT("km_por_litro") FILTER (WHERE "km_por_litro" IS NOT NULL) > 0
			    AND r."vec_model" IS NOT NULL
            ORDER BY r."time_slot"
        """
        df = pd.read_sql(query, self.pgEngine)

        # Normaliza os modelos
        df = self.normaliza_modelos(df)

        # Converte para DT
        df["time_slot_dt"] = pd.to_datetime(df["time_slot"].astype(str), format="%H:%M")

        # Arredonda os valores
        df["mean"] = df["mean"].round(2)
        df["std"] = df["std"].round(2)
        df["min"] = df["min"].round(2)
        df["max"] = df["max"].round(2)

        return df
        


    def get_viagens_realizada_na_linha(
        self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior
    ):
        """
        Função para obter os dados do combustível por linha (que será usado para gerar o gráfico)
        """

        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_dia_marcado = subquery_lista_dia_marcado(lista_dia_semana)
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

        query = f"""
        SELECT
            r.*,
            ABS(total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)) AS litros_excedentes,
            3600 * (tamanho_linha_km_sobreposicao / encontrou_tempo_viagem_segundos) AS velocidade_media_kmh,
            m."Name" AS nome_motorista
        FROM
            rmtc_viagens_analise_mix r
        LEFT JOIN 
            motoristas_api m 
            ON r."DriverId" = m."DriverId"
        WHERE
            "encontrou_numero_linha" = '{linha}'
            AND "encontrou_linha"
            AND "dia" >= '{data_inicio_str}'
            AND "dia" <= '{data_fim_str}'
            AND "km_por_litro" >= {limite_km_l_menor}
            AND "km_por_litro" <= {limite_km_l_maior}
            {subquery_dia_marcado}
            {subquery_modelos}
            {subquery_sentido}
        """
        df = pd.read_sql(query, self.pgEngine)

        # Normaliza os modelos
        df = self.normaliza_modelos(df)

        # Força string nos asset_id
        df["vec_asset_id"] = df["vec_asset_id"].astype(str)

        # Ajusta datas
        df["encontrou_tempo_viagem_segundos"] = df["encontrou_tempo_viagem_segundos"].astype(int)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_segundos"] / 60
        df["timestamp_br_inicio"] = pd.to_datetime(df["encontrou_timestamp_inicio"]) - pd.Timedelta(hours=3)
        df["timestamp_br_fim"] = pd.to_datetime(df["encontrou_timestamp_fim"]) - pd.Timedelta(hours=3)
        df["dia_dt"] = pd.to_datetime(df["dia"]).dt.date
        df["dia_label"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        # Formatar alguns dados (arredonda)
        df["encontrou_tempo_viagem_minutos"] = df["encontrou_tempo_viagem_minutos"].round(2)
        df["tamanho_linha_km_sobreposicao"] = df["tamanho_linha_km_sobreposicao"].round(2)
        df["total_comb_l"] = df["total_comb_l"].round(2)
        df["km_por_litro"] = df["km_por_litro"].round(2)
        df["analise_diff_mediana_90_dias"] = df["analise_diff_mediana_90_dias"].round(2)
        df["velocidade_media_kmh"] = df["velocidade_media_kmh"].round(2)

        # Ajusta NaN
        df["nome_motorista"] = df["nome_motorista"].fillna("Não informado")
        return df

