#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de consumo por veículo

# Imports básicos
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_linha_combustivel, subquery_sentido_combustivel


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
	        AND analise_num_amostras_90_dias >= 10
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
            AND analise_num_amostras_90_dias >= 10
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
            AND analise_num_amostras_90_dias >= 10
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
            r.*
        FROM 
            rmtc_viagens_analise_mix_padronizado r
        LEFT JOIN 
            motoristas_api m 
            ON r."DriverId" = m."DriverId"
        WHERE
            encontrou_linha = TRUE
	        AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
	        AND analise_num_amostras_90_dias >= 10
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            AND vec_num_id = '{vec_num_id}'
            {subquery_linha_combustivel_str}
        ORDER BY 
            encontrou_timestamp_inicio;
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

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
        df["analise_diff_mediana_90_dias"] = df["analise_diff_mediana_90_dias"].round(2)

        return df