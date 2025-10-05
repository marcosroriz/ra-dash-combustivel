#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página principal

# Imports básicos
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_linha_combustivel, subquery_sentido_combustivel


class HomeService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def get_sinteze_status_viagens(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter a classificação das viagens analisadas"""

        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
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
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        GROUP BY
            analise_status_90_dias 
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df
    
    def get_sinteze_consumo_modelos(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter a classificação do consumo dos modelos"""

        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
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
            FROM rmtc_viagens_analise_mix r
        )
        SELECT
            vec_model,
            COUNT(*) AS total_viagens,
            AVG(km_por_litro) AS media_km_litro,
            SUM(total_comb_l) AS total_consumo_litros,
            SUM(
                ABS(
                    total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)
                )
            ) AS total_litros_excedentes,
            100 * (
                SUM(
                    ABS(
                        total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)
                    )
                )::NUMERIC 
                / SUM(total_comb_l)::NUMERIC
            ) AS perc_excedente
        FROM 
            rmtc_viagens_analise_mix_padronizado
        WHERE 
            encontrou_linha = true
	        AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
	        AND analise_num_amostras_90_dias >= 10
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        GROUP BY 
            vec_model
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)


        # Arrendonda as colunas necessárias
        df["media_km_litro"] = df["media_km_litro"].round(2)
        df["total_consumo_litros"] = df["total_consumo_litros"].round(2)
        df["total_litros_excedentes"] = df["total_litros_excedentes"].round(2)
        df["perc_excedente"] = df["perc_excedente"].round(2)

        return df

    def get_indicador_consumo_medio_km_l(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter o indicador de consumo médio de km/L"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
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
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        """
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_consumo_litros_excedente(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter o indicador de consumo excedente em L"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
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
		    AND analise_status_90_dias = 'BAIXA PERFOMANCE (<= 2 STD)'
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_tabela_consumo_veiculos(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter os dados da tabela de consumo dos veículos"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT
            vec_num_id,
            vec_model,
            COUNT(*) AS total_viagens,
            AVG(km_por_litro) as media_km_por_litro,
            -- Total abaixo da mediana
            SUM(
                CASE 
                    WHEN analise_diff_mediana_90_dias < 0 THEN 1 
                    ELSE 0 
                END
            ) AS total_abaixo_mediana,

            -- Percentual abaixo da mediana
            100 * (
                SUM(
                    CASE 
                        WHEN analise_diff_mediana_90_dias < 0 THEN 1 
                        ELSE 0 
                    END
                )::NUMERIC / COUNT(*)::NUMERIC
            ) AS perc_total_abaixo_mediana,

            -- Total baixa performance
            SUM(
                CASE 
                    WHEN analise_status_90_dias = 'BAIXA PERFOMANCE (<= 2 STD)' THEN 1 
                    WHEN analise_status_90_dias = 'BAIXA PERFORMANCE (<= 1.5 STD)' THEN 1 
                    ELSE 0 
                END
            ) AS total_baixa_perfomance,
            
            -- Percentual baixa performance
            100 * (
                SUM(
                    CASE 
                        WHEN analise_status_90_dias = 'BAIXA PERFOMANCE (<= 2 STD)' THEN 1 
                        WHEN analise_status_90_dias = 'BAIXA PERFORMANCE (<= 1.5 STD)' THEN 1 
                        ELSE 0 
                    END
                )::NUMERIC / COUNT(*)::NUMERIC
            ) AS perc_baixa_perfomance,

            -- Total de consumo
            SUM(total_comb_l) AS total_consumo_litros,

            -- Litros excedentes
            SUM(
                ABS(
                    total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)
                )
            ) AS litros_excedentes,
            
            -- Total erro de telemetria,
            SUM(
                CASE 
                    WHEN analise_status_90_dias = 'ERRO TELEMETRIA (>= 2.0 STD)' THEN 1 
                    ELSE 0 
                END
            ) AS total_erro_telemetria,

            -- Perc Erro
            100 * (
                SUM(
                    CASE 
                        WHEN analise_status_90_dias = 'ERRO TELEMETRIA (>= 2.0 STD)' THEN 1 
                        ELSE 0 
                    END
                )::NUMERIC / COUNT(*)::NUMERIC
            ) AS perc_erro_telemetria

        FROM
            rmtc_viagens_analise_mix

        WHERE
            encontrou_linha = true
            AND analise_num_amostras_90_dias > 10
            AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        GROUP BY
            vec_num_id, 
            vec_model
        ORDER BY
            perc_baixa_perfomance DESC;
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Arrendonda as colunas necessárias
        df["media_km_por_litro"] = df["media_km_por_litro"].round(2)
        df["perc_total_abaixo_mediana"] = df["perc_total_abaixo_mediana"].round(2)
        df["perc_baixa_perfomance"] = df["perc_baixa_perfomance"].round(2)
        df["perc_erro_telemetria"] = df["perc_erro_telemetria"].round(2)
        df["litros_excedentes"] = df["litros_excedentes"].round(2)
        df["total_consumo_litros"] = df["total_consumo_litros"].round(2)

        return df
    
    def get_tabela_consumo_linhas(self, datas, lista_modelos, lista_linhas, km_l_min, km_l_max):
        """Função para obter os dados da tabela de consumo dos veículos"""
        # Extraí a data inicial e final
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Subqueries
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")
        subquery_linha_combustivel_str = subquery_linha_combustivel(lista_linhas, termo_all="TODAS")

        query = f"""
        SELECT
            encontrou_numero_linha,
            COUNT(*) AS total_viagens,
            AVG(tamanho_linha_km) as media_tam_linha,
            AVG(km_por_litro) as media_km_por_litro,
			SUM(total_comb_l) as total_combustivel_gasto,
			-- Litros excedentes
            SUM(
                ABS(
                    total_comb_l - (tamanho_linha_km_sobreposicao / analise_valor_mediana_90_dias)
                )
            ) AS litros_excedentes
        FROM
            rmtc_viagens_analise_mix
        WHERE
            encontrou_linha = true
            AND analise_num_amostras_90_dias > 10
            AND CAST("dia" AS date) BETWEEN DATE '{data_inicio_str}' AND DATE '{data_fim_str}'
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        GROUP BY
            encontrou_numero_linha
        ORDER BY
            total_viagens DESC;
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Arrendonda as colunas necessárias
        df["media_tam_linha"] = df["media_tam_linha"].round(3)
        df["media_km_por_litro"] = df["media_km_por_litro"].round(2)
        df["total_combustivel_gasto"] = df["total_combustivel_gasto"].round(2)
        df["litros_excedentes"] = df["litros_excedentes"].round(2)

        return df
    
   