#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página combustível por linha

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel, subquery_dia_marcado_str


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

    def get_combustivel_por_linha(
        self, datas, lista_modelos, linha, lista_sentido, lista_dia_semana, limite_km_l_menor, limite_km_l_maior
    ):
        """
        Função para obter os dados do combustível por linha (que será usado para gerar o gráfico)
        """

        # Extraí a data inicial e final
        data_inicio_str, data_fim_str = datas[0], datas[1]

        # Subqueries
        subquery_dia_marcado = subquery_dia_marcado_str(lista_dia_semana)
        subquery_modelos = subquery_modelos_combustivel(lista_modelos)
        subquery_sentido = subquery_sentido_combustivel(lista_sentido)

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

        print(query)
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
