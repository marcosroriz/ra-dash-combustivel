#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página principal

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

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
	        AND analise_num_amostras_full_dias > 10
 	        AND km_por_litro >= {km_l_min}
	        AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        GROUP BY
            analise_status_90_dias 
        """
        print(query)
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

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
            AND analise_num_amostras_full_dias > 10
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        """
        print(query)

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
            AND analise_num_amostras_full_dias > 10
            AND km_por_litro >= {km_l_min}
            AND km_por_litro <= {km_l_max}
		    AND analise_status_90_dias = 'BAIXA PERFOMANCE (<= 2 STD)'
            {subquery_modelos_str}
            {subquery_linha_combustivel_str}
        """
        print(query)

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_consumo_excedente(self, dia, lista_modelos, linha, km_min, km_max):
        pass
