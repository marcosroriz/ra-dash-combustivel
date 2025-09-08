# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
from datetime import datetime, timedelta
from modules.sql_utils import *
from sqlalchemy import text

# Imports auxiliares


class RegrasServiceVisaoGeral:

    def __init__(self, pgEngine):

        self.pgEngine = pgEngine
    

    def get_estatistica_veiculos_analise_performance(self, regra):
        subquery_regras = subquery_regras_ids(regra)
        dfregras = pd.read_sql(f"""
                SELECT *
                FROM regras_monitoramento
                where {subquery_regras}
        """, self.pgEngine)

       
        if not dfregras.empty:
            mediana_viagem = dfregras.iloc[0]["mediana_viagem"]
            erro_telemetria = dfregras.iloc[0]["erro_telemetria"]
            indicativo_performace = dfregras.iloc[0]["indicativo_performace"]
            quantidade_de_viagens = dfregras.iloc[0]["qtd_viagens"]
            numero_de_motoristas = dfregras.iloc[0]["motoristas"]
            dias_marcados = dfregras.iloc[0]["dias_analise"]
            modelos = dfregras.iloc[0]["modelos"]
            periodo = int(dfregras.iloc[0]["periodo"])

        else:
            mediana_viagem = 0
            erro_telemetria = 0
            indicativo_performace = 0
            quantidade_de_viagens = 0
            numero_de_motoristas = 0
            dias_marcados = 0
            modelos = 0
            periodo = 0

        if mediana_viagem == None:
            mediana_viagem = 0
        if erro_telemetria == None:
            erro_telemetria = 0
        if indicativo_performace == None:
            indicativo_performace = 0
        if quantidade_de_viagens == None:
            quantidade_de_viagens = 0
        if numero_de_motoristas == None:
            numero_de_motoristas = 0
        if dias_marcados == None:
            dias_marcados = 0
        if modelos == None:
            modelos = 0
        if periodo == None:
            periodo = 0

        # data atual
        data_fim_str = pd.Timestamp.today().strftime("%Y-%m-%d")

        # data inicial (data atual - dias)
        data_inicio_str = (pd.Timestamp.today() - pd.Timedelta(days=periodo)).strftime("%Y-%m-%d")
        
        # Condições para filtros de dias 
        if dias_marcados =='SEG_SEX':
            table = 'mat_view_viagens_classificadas_dia_semana'

        elif dias_marcados == 'SABADO':
            table = 'mat_view_viagens_classificadas_sabado'

        elif dias_marcados == 'DOMINGO':
            table = 'mat_view_viagens_classificadas_domingo'

        elif dias_marcados == 'FERIADO':
            table = 'mat_view_viagens_classificadas_feriado'


        subquery_modelo = subquery_modelos_regras(modelos)

        # Query principal
        query = f"""
        WITH viagens AS (
            SELECT *
            FROM public.{table}
        ),

        viagens_classificadas_no_periodo AS (
            SELECT *
            FROM viagens vc
            WHERE vc."dia"::DATE BETWEEN '{data_inicio_str}'::DATE AND '{data_fim_str}'::DATE
        ),

        viagens_classificadas_do_modelo AS (
            SELECT *
            FROM viagens_classificadas_no_periodo
            {subquery_modelo}
        ),

        viagens_classificadas_nas_linhas AS (
            SELECT *
            FROM viagens_classificadas_do_modelo
            -- WHERE de linhas
        ),

        viagens_filtro AS (
            SELECT 
                vcl.vec_asset_id,
                COUNT(*) FILTER (WHERE diferenca_mediana < 0) AS viagens_abaixo_mediana,
                COUNT(*) FILTER (WHERE diferenca_mediana < 0)::decimal / COUNT(*) AS proporcao_abaixo_mediana,
                COUNT(*) FILTER (
                    WHERE status_consumo IN ('SUSPEITA BAIXA PERFOMANCE', 'BAIXA PERFORMANCE')
                )::decimal / COUNT(*) AS proporcao_suspeita_ou_baixa_perfomance,
                COUNT(*) FILTER (WHERE status_consumo IN ('ERRO TELEMETRIA'))::decimal / COUNT(*) AS proporcao_erro,
                -- vbf.num_motoristas_baixa_perf
                COUNT(DISTINCT "DriverId") FILTER (
                    WHERE status_consumo IN ('SUSPEITA BAIXA PERFOMANCE', 'BAIXA PERFORMANCE')
                ) AS num_motoristas_diferentes
            FROM viagens_classificadas_do_modelo vcl
            GROUP BY vcl.vec_asset_id
            HAVING 
                COUNT(*) >= {quantidade_de_viagens} --- quantidade de viagens por periodo
                AND COUNT(*) FILTER (WHERE diferenca_mediana < 0)::decimal / COUNT(*) >= {mediana_viagem} ---- porcentagem abaixo da mediana
                AND COUNT(*) FILTER (
                    WHERE status_consumo IN ('SUSPEITA BAIXA PERFOMANCE', 'BAIXA PERFORMANCE')
                )::decimal / COUNT(*) >= {indicativo_performace}--- filtro de suspeita ou baixa performance
                AND COUNT(*) FILTER (WHERE status_consumo IN ('ERRO TELEMETRIA'))::decimal / COUNT(*) >= {erro_telemetria} --- porcentagem erro telemetria
                AND COUNT(DISTINCT "DriverId") FILTER (
                    WHERE status_consumo IN ('SUSPEITA BAIXA PERFOMANCE', 'BAIXA PERFORMANCE')
                ) >= {numero_de_motoristas}--- filtro para motoristas diferentes
        ),

        viagens_filtro_final AS (
            SELECT 
                todas_viagens.*,
                viagens_filtro.viagens_abaixo_mediana,
                viagens_filtro.proporcao_abaixo_mediana,
                viagens_filtro.proporcao_suspeita_ou_baixa_perfomance,
                viagens_filtro.proporcao_erro,
                viagens_filtro.num_motoristas_diferentes,
                todas_viagens."tamanho_linha_km_sobreposicao" / todas_viagens."mediana" AS comb_esperado_mediana,
                todas_viagens."total_comb_l" - (todas_viagens."tamanho_linha_km_sobreposicao" / todas_viagens."mediana") AS comb_excedente_L
            FROM viagens_classificadas_nas_linhas todas_viagens
            JOIN viagens_filtro viagens_filtro
                ON todas_viagens.vec_asset_id = viagens_filtro.vec_asset_id
        ),

        resumo_por_veiculo AS (
            SELECT 
                vec_asset_id,
                vec_num_id,
                vec_model,
                status_consumo,
                COUNT(*) AS total_status,
                SUM(comb_excedente_L) AS comb_excedente_L_por_categoria
            FROM viagens_filtro_final
            GROUP BY vec_asset_id, vec_num_id, vec_model, status_consumo
        ),

        total_por_veiculo AS (
            SELECT 
                vec_asset_id,
                vec_num_id,
                AVG(km_por_litro) AS MEDIA_CONSUMO_POR_KM,
                SUM(comb_excedente_L) AS comb_excedente_L,
                COUNT(*) AS total_geral
            FROM viagens_filtro_final
            GROUP BY vec_asset_id, vec_num_id
        ),

        proporcao_por_veiculo AS (
            SELECT 
                vec_asset_id,
                viagens_abaixo_mediana,
                proporcao_abaixo_mediana,
                proporcao_suspeita_ou_baixa_perfomance,
                proporcao_erro,
                num_motoristas_diferentes
            FROM viagens_filtro_final
            GROUP BY 
                vec_asset_id,
                viagens_abaixo_mediana,
                proporcao_abaixo_mediana,
                proporcao_suspeita_ou_baixa_perfomance,
                proporcao_erro,
                num_motoristas_diferentes
        ),

        estatistica_veiculos AS (
            SELECT 
                r.vec_asset_id,
                r.vec_num_id,
                r.vec_model,
                r.status_consumo,
                r.total_status,
                ROUND(100.0 * r.total_status / t.total_geral, 2) AS percentual_categoria_status,
                r.comb_excedente_L_por_categoria,
                t.MEDIA_CONSUMO_POR_KM,
                t.comb_excedente_L
            FROM resumo_por_veiculo r
            JOIN total_por_veiculo t
                ON r.vec_num_id = t.vec_num_id
        )

        SELECT *
        FROM estatistica_veiculos e
        LEFT JOIN proporcao_por_veiculo p
            ON e.vec_asset_id = p.vec_asset_id;

        """

        df = pd.read_sql(query, self.pgEngine)
        

        if df.empty:
            return pd.DataFrame(columns=["vec_num_id", "vec_model", "media_consumo_por_km", "total_viagens"])

        # Arredonda o consumo médio
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # AGRUPA para obter comb_excedente_L total e proporcao_abaixo_mediana média por veículo
        df_extra = df.groupby(["vec_num_id", "vec_model", "media_consumo_por_km"], as_index=False).agg({
            "comb_excedente_l": "first",
            "proporcao_abaixo_mediana": "mean"
        })

        # Pivot da tabela: cria colunas para cada status de consumo
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual_categoria_status"],
            fill_value=0
        )

        # Ajusta nomes de colunas (ex: total_status_regular, percentual_baixa_performance)
        df_pivot.columns = [
            f"{col[0]}_{col[1].lower().replace(' ', '_')}" 
            for col in df_pivot.columns
        ]

        # Converte de volta o índice em colunas
        df_pivot = df_pivot.reset_index()

        # Junta com os dados de comb_excedente_L e proporcao_abaixo_mediana
        df_pivot = df_pivot.merge(df_extra, on=["vec_num_id", "vec_model", "media_consumo_por_km"], how="left")

        # Calcula total de viagens
        df_pivot["total_viagens"] = df_pivot.filter(like="total_status_").sum(axis=1)

        # Ordena por número de viagens
        # df_pivot = df_pivot.sort_values(by="total_viagens", ascending=False)

        # Arredonda comb_excedente_l
        df_pivot["comb_excedente_l"] = df_pivot["comb_excedente_l"].round(2)

        # Multiplica proporcao_abaixo_mediana por 100 e arredonda
        df_pivot["proporcao_abaixo_mediana"] = (df_pivot["proporcao_abaixo_mediana"] * 100).round(2)

        # Arredonda colunas de percentual
        colunas_para_arredondar = [
            'percentual_categoria_status_regular',
            'percentual_categoria_status_suspeita_baixa_perfomance',
            'percentual_categoria_status_baixa_performance',
            'comb_excedente_l', 'media_consumo_por_km', 'percentual_categoria_status_erro_telemetria',
            'proporcao_abaixo_mediana'
        ]

        for coluna in colunas_para_arredondar:
            if coluna in df_pivot.columns:
                df_pivot[coluna] = df_pivot[coluna].round(2).apply(lambda x: f"{x:.2f}")

        return df_pivot

