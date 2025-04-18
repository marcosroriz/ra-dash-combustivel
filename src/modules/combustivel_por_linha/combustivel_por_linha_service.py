#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página combustível por linha

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel


class CombustivelPorLinhaService:
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

    def get_percentual_encontros_linha(
        self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior
    ):
        """
        Funçao que otem o percentual de encontros por linha que nosso modelo achou
        """

        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

        query = f"""
            SELECT 
                rmtc_linha_prevista,
                COUNT(*) FILTER (WHERE encontrou_linha IS FALSE) AS nao_encontrou,
                COUNT(*) AS total_por_linha,
                ROUND(100.0 * COUNT(*) FILTER (WHERE encontrou_linha IS FALSE) / COUNT(*), 2) AS percentual_nao_encontrou
            FROM 
                rmtc_viagens_analise
            WHERE 
                "encontrou_numero_linha" = '{linha}'
                AND "dia" >= '{data_inicio_str}'
                AND "dia" <= '{data_fim_str}'
                AND "km_por_litro" >= {limite_km_l_menor}
                AND "km_por_litro" <= {limite_km_l_maior}
                {subquery_modelos}
                {subquery_sentido}
            GROUP BY 
                rmtc_linha_prevista
                rmtc_viagens_analise rva 
        """

        df = pd.read_sql(query, self.pgEngine)

        return df

    def get_combustivel_por_linha(
        self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior
    ):
        """
        Função para obter os dados do combustível por linha (que será usado para gerar o gráfico)
        """

        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

        query = f"""
        SELECT
            *
        FROM
            rmtc_viagens_analise
        WHERE
            "encontrou_numero_linha" = '{linha}'
            AND "encontrou_linha"
            AND "dia" >= '{data_inicio_str}'
            AND "dia" <= '{data_fim_str}'
            AND "km_por_litro" >= {limite_km_l_menor}
            AND "km_por_litro" <= {limite_km_l_maior}
            {subquery_modelos}
            {subquery_sentido}
        """

        print(query)
        df_linha = pd.read_sql(query, self.pgEngine)

        # Normaliza os modelos
        df_linha = self.normaliza_modelos(df_linha)

        # Filtra os dados de acordo com os dias da semana
        df_linha_filtrado = self.filtra_combustivel_por_dia_semana(df_linha, lista_dia_semana)

        return df_linha_filtrado

    def filtra_combustivel_por_dia_semana(self, df_linha, lista_dia_semana):
        """
        Função que filtra o dataframe de acordo com os dias da semana escolhido
        """
        df_linha_filtrado = df_linha

        # Converte a coluna "dia" para o tipo datetime
        df_linha_filtrado["dia_dt"] = pd.to_datetime(df_linha_filtrado["dia"])

        # Cria a coluna "DIA_SEMANA" com o nome do dia da semana
        df_linha_filtrado["WEEKDAY_CATEGORY"] = df_linha_filtrado["dia_dt"].dt.dayofweek.apply(
            lambda x: "SATURDAY" if x == 5 else ("SUNDAY" if x == 6 else "WEEKDAY")
        )
        df_linha_filtrado["WEEKDAY_NUMBER"] = df_linha_filtrado["dia_dt"].dt.dayofweek

        # Remove as linhas que não estão na lista de dias da semana
        dias_para_filtrar = set()

        if "SEG_SEX" in lista_dia_semana:
            dias_para_filtrar.update(range(0, 5))  # segunda (0) a sexta (4)

        if "SABADO" in lista_dia_semana:
            dias_para_filtrar.add(5)  # sábado

        if "DOMINGO" in lista_dia_semana:
            dias_para_filtrar.add(6)  # domingo

        df_linha_filtrado = df_linha_filtrado[df_linha_filtrado["WEEKDAY_NUMBER"].isin(dias_para_filtrar)]

        # # Verifica se o filtro de feriados está ativo
        # if "FERIADO" in lista_dia_semana:
        # Cria uma instância do objeto de feriados
        feriados = holidays.Brazil(years=df_linha_filtrado["dia_dt"].dt.year.unique())

        # Filtra os feriados
        df_linha_filtrado = df_linha_filtrado[~df_linha_filtrado["dia_dt"].isin(feriados)]

        return df_linha_filtrado

    # def agrupa_combustivel_por_linha(self, df, periodo_agrupar="30T"):
    #     """
    #     Função para agrupar os dados do combustível por linha e dia da semana
    #     """

    #         # Agrupa por tempo bin
    # df_agg = df.groupby("time_bin_only_time")["km_por_litro"].agg(["mean", "std", "min", "max"]).reset_index()
    # df_agg["time_bin_only_time"] = pd.to_datetime(df_agg["time_bin_only_time"]).dt.time

    def get_todas_linhas_combustivel(self):
        """
        Retorn todas as linhas de ônibus com informações de combustível.
        """
        query = f"""
            SELECT 
                DISTINCT "encontrou_numero_linha" as "LABEL"
            FROM 
                rmtc_viagens_analise rva 
            WHERE 
                "encontrou_numero_linha" IS NOT NULL
            ORDER BY
                "encontrou_numero_linha"
        """

        df = pd.read_sql(query, self.pgEngine)

        return df
