#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de criação de regras

# Imports básicos
import os
import pandas as pd

# Lib para lidar com feriados
from datetime import datetime

# Imports BD
import sqlalchemy
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import text

# Imports auxiliares
from modules.sql_utils import *

# Constante indica o número mínimo de viagens que devem existir para poder classificar o consumo de uma viagem
# Por exemplo, NUM_MIN_VIAGENS_PARA_CLASSIFICAR = 5 indica que somente as viagens cuja configuração possuam outras 5
# viagens iguais (mesma linha, sentido, dia, etc) será incluída na análise
NUM_MIN_VIAGENS_PARA_CLASSIFICAR = os.getenv("NUM_MIN_VIAGENS_PARA_CLASSIFICAR", 5)


class RegrasService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine
        
    def get_todas_regras(self):
        """Função para obter todas as regras de monitoramento"""

        # Query
        query = """
            SELECT 
                *,
                (
                    SELECT MAX(dia)
                    FROM relatorio_regra_monitoramento_combustivel
                    WHERE id_regra = regra.id
                    GROUP BY id_regra
                ) AS "dia_ultimo_relatorio",
                (
                    SELECT MAX(executed_at)
                    FROM relatorio_regra_monitoramento_combustivel
                    WHERE id_regra = regra.id
                    GROUP BY id_regra
                ) AS "executed_at"
            FROM regra_monitoramento_combustivel regra
            ORDER BY nome_regra
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def apagar_regra(self, id_regra):
        """Função para apagar uma regra de monitoramento"""

        # Query
        query = f"""
            DELETE FROM regra_monitoramento_combustivel WHERE id = {id_regra}
        """

        try:
            # Executa a query
            with self.dbEngine.begin() as conn:
                conn.execute(text(query))

            return True
        except Exception as e:
            print(f"Erro ao apagar regra: {e}")
            return False
        
    def get_regra_by_id(self, id_regra):
        """Função para obter uma regra de monitoramento pelo ID"""

        # Query
        query = f"""
            SELECT * FROM regra_monitoramento_combustivel WHERE id = {id_regra}
            ORDER BY nome_regra
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df


    def get_regras(self, lista_regras):

        subquery_regras = subquery_regras_monitoramento(lista_regras)

        query = f"""
        SELECT * FROM public.regra_monitoramento_combustivel
        """

        if not lista_regras:
            lista_regras = []

        if lista_regras and "TODAS" not in lista_regras:
            query += f" WHERE {subquery_regras}"

        df = pd.read_sql(query, self.dbEngine)
        df = df.sort_values("nome_regra")
        return df
    

    def get_preview_regra(
        self,
        dias_monitoramento,
        lista_modelos,
        qtd_min_motoristas,
        qtd_min_viagens,
        dias_marcados,
        limite_mediana,
        limite_baixa_perfomance,
        limite_erro_telemetria,
    ):
        subquery_dia_marcado_str = subquery_dia_marcado_str(dias_marcados)
        subquery_modelos_str = subquery_modelos_combustivel(lista_modelos, termo_all="TODOS")

        # Ajusta os limites antes de executar a query
        if limite_mediana is None:
            limite_mediana = 0
        
        if limite_baixa_perfomance is None:
            limite_baixa_perfomance = 0

        if limite_erro_telemetria is None:
            limite_erro_telemetria = 0

        query = f"""
        WITH viagens_agg_periodo AS (
            SELECT
                vec_num_id,
                vec_model,
                COUNT(*) AS total_viagens,
                AVG(km_por_litro) AS media_km_por_litro,

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

                -- Total erro de telemetria
                SUM(
                    CASE
                        WHEN analise_status_90_dias = 'ERRO TELEMETRIA (>= 2.0 STD)' THEN 1
                        ELSE 0
                    END
                ) AS total_erro_telemetria,

                -- Percentual de erro de telemetria
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
                AND analise_num_amostras_90_dias >= {NUM_MIN_VIAGENS_PARA_CLASSIFICAR}
                AND CAST("dia" AS date) BETWEEN CURRENT_DATE - INTERVAL '{350} days' AND CURRENT_DATE + INTERVAL '2 days'
                AND km_por_litro >= 1
                AND km_por_litro <= 10
                {subquery_modelos_str}
                {subquery_dia_marcado_str}
            GROUP BY
                vec_num_id,
                vec_model
            HAVING
                COUNT(*) >= {qtd_min_viagens}
                AND COUNT(DISTINCT "DriverId") >= {qtd_min_motoristas}
        )
        SELECT
            *
        FROM
            viagens_agg_periodo
        WHERE
            perc_total_abaixo_mediana >= {limite_mediana}
            AND perc_baixa_perfomance >= {limite_baixa_perfomance}
            AND perc_erro_telemetria >= {limite_erro_telemetria}
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

    def criar_regra_monitoramento(self, payload):
        """Função para criar uma regra de monitoramento"""
        table = sqlalchemy.Table("regra_monitoramento_combustivel", sqlalchemy.MetaData(), autoload_with=self.dbEngine)

        try:
            with self.dbEngine.begin() as conn:
                stmt = insert(table).values(payload)
                conn.execute(stmt)

            return True
        except Exception as e:
            print(f"Erro ao criar regra de monitoramento: {e}")
            return False

    def atualizar_regra_monitoramento(self, id_regra, payload):
        """Função para atualizar uma regra de monitoramento"""
        table = sqlalchemy.Table("regra_monitoramento_combustivel", sqlalchemy.MetaData(), autoload_with=self.dbEngine)

        try:
            with self.dbEngine.begin() as conn:
                stmt = update(table).where(table.c.id == id_regra).values(payload)
                conn.execute(stmt)

            return True
        except Exception as e:
            print(f"Erro ao atualizar regra de monitoramento: {e}")
            return False


    def get_ultima_data_regra(self, id_regra):
        """Função para obter a última data de uma regra de monitoramento"""
        query = f"""
            SELECT id_regra, MAX(dia) AS ultimo_dia
            FROM relatorio_regra_monitoramento_combustivel
            WHERE id_regra = {id_regra}
            GROUP BY id_regra
        """
        df = pd.read_sql(query, self.dbEngine)
        return df
    
    def existe_execucao_regra_no_dia(self, id_regra, dia):
        """Função para verificar se uma regra já foi executada no dia"""
        query = f"""
            SELECT 1 AS "EXISTE" FROM relatorio_regra_monitoramento_combustivel WHERE id_regra = {id_regra} AND dia = '{dia}'
        """
        df = pd.read_sql(query, self.dbEngine)

        if df.empty:
            return False
        else:
            return True

    def get_resultado_regra(self, id_regra, dia_execucao):
        """Função para obter o resultado de uma regra de monitoramento"""
        query = f"""
            SELECT *
            FROM relatorio_regra_monitoramento_combustivel r 
            WHERE r.id_regra = {id_regra} AND r.dia = '{dia_execucao}'
        """
        df = pd.read_sql(query, self.dbEngine)

        return df


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
        numero_de_motoristas,
        quantidade_de_viagens,
        dias_marcados,
        mediana_viagem,
        indicativo_performace,
        erro_telemetria,
    ):

        # Converte para tipos esperados
        mediana_viagem = int(mediana_viagem or 0) / 100
        erro_telemetria = float(erro_telemetria or 0) / 100
        indicativo_performace = float(indicativo_performace or 0) / 100
        quantidade_de_viagens = int(quantidade_de_viagens or 0)
        numero_de_motoristas = int(numero_de_motoristas or 0)

        # Condições para filtros de dias
        if dias_marcados == "SEG_SEX":
            table = "mat_view_viagens_classificadas_dia_semana"

        elif dias_marcados == "SABADO":
            table = "mat_view_viagens_classificadas_sabado"

        elif dias_marcados == "DOMINGO":
            table = "mat_view_viagens_classificadas_domingo"

        elif dias_marcados == "FERIADO":
            table = "mat_view_viagens_classificadas_feriado"

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
            WHERE vc."dia" >= CURRENT_DATE - interval '{data} days' ---- Aqui a gente faz o filtro de data
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

        df = pd.read_sql(query, self.dbEngine)

        if df.empty:
            return pd.DataFrame(columns=["vec_num_id", "vec_model", "media_consumo_por_km", "total_viagens"])

        # Arredonda o consumo médio
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # AGRUPA para obter comb_excedente_L total e proporcao_abaixo_mediana média por veículo
        df_extra = df.groupby(["vec_num_id", "vec_model", "media_consumo_por_km"], as_index=False).agg(
            {"comb_excedente_l": "first", "proporcao_abaixo_mediana": "mean"}
        )

        # Pivot da tabela: cria colunas para cada status de consumo
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual_categoria_status"],
            fill_value=0,
        )

        # Ajusta nomes de colunas (ex: total_status_regular, percentual_baixa_performance)
        df_pivot.columns = [f"{col[0]}_{col[1].lower().replace(' ', '_')}" for col in df_pivot.columns]

        # Converte de volta o índice em colunas
        df_pivot = df_pivot.reset_index()

        # Junta com os dados de comb_excedente_L e proporcao_abaixo_mediana
        df_pivot = df_pivot.merge(df_extra, on=["vec_num_id", "vec_model", "media_consumo_por_km"], how="left")

        # Calcula total de viagens
        df_pivot["total_viagens"] = df_pivot.filter(like="total_status_").sum(axis=1)

        # Ordena por número de viagens
        df_pivot = df_pivot.sort_values(by="total_viagens", ascending=False)

        # Arredonda comb_excedente_l
        df_pivot["comb_excedente_l"] = df_pivot["comb_excedente_l"].round(2)

        # Multiplica proporcao_abaixo_mediana por 100 e arredonda
        df_pivot["proporcao_abaixo_mediana"] = (df_pivot["proporcao_abaixo_mediana"] * 100).round(2)

        # Arredonda colunas de percentual
        colunas_para_arredondar = [
            "percentual_categoria_status_regular",
            "percentual_categoria_status_suspeita_baixa_perfomance",
            "percentual_categoria_status_baixa_performance",
            "comb_excedente_l",
            "media_consumo_por_km",
            "percentual_categoria_status_erro_telemetria",
            "proporcao_abaixo_mediana",
        ]

        for coluna in colunas_para_arredondar:
            if coluna in df_pivot.columns:
                df_pivot[coluna] = df_pivot[coluna].round(2).apply(lambda x: f"{x:.2f}")

        return df_pivot

    def get_estatistica_veiculos_analise_performance(
        self,
        data,
        modelos,
        numero_de_motoristas,
        quantidade_de_viagens,
        dias_marcados,
        mediana_viagem,
        indicativo_performace,
        erro_telemetria,
    ):

        # Extrai a data inicial e final
        data_inicio_str, data_fim_str = pd.to_datetime(data[0]).strftime("%Y-%m-%d"), pd.to_datetime(data[1]).strftime(
            "%Y-%m-%d"
        )

        # Converte para tipos esperados
        mediana_viagem = int(mediana_viagem or 0) / 100
        erro_telemetria = float(erro_telemetria or 0) / 100
        indicativo_performace = float(indicativo_performace or 0) / 100
        quantidade_de_viagens = int(quantidade_de_viagens or 0)
        numero_de_motoristas = int(numero_de_motoristas or 0)

        # Condições para filtros de dias
        if dias_marcados == "SEG_SEX":
            table = "mat_view_viagens_classificadas_dia_semana"

        elif dias_marcados == "SABADO":
            table = "mat_view_viagens_classificadas_sabado"

        elif dias_marcados == "DOMINGO":
            table = "mat_view_viagens_classificadas_domingo"

        elif dias_marcados == "FERIADO":
            table = "mat_view_viagens_classificadas_feriado"

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
            WHERE vc."dia" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
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
        df = pd.read_sql(query, self.dbEngine)

        if df.empty:
            return pd.DataFrame(columns=["vec_num_id", "vec_model", "media_consumo_por_km", "total_viagens"])

        # Arredonda o consumo médio
        df["media_consumo_por_km"] = df["media_consumo_por_km"].round(2)

        # AGRUPA para obter comb_excedente_L total e proporcao_abaixo_mediana média por veículo
        df_extra = df.groupby(["vec_num_id", "vec_model", "media_consumo_por_km"], as_index=False).agg(
            {"comb_excedente_l": "first", "proporcao_abaixo_mediana": "mean"}
        )

        # Pivot da tabela: cria colunas para cada status de consumo
        df_pivot = df.pivot_table(
            index=["vec_num_id", "vec_model", "media_consumo_por_km"],
            columns="status_consumo",
            values=["total_status", "percentual_categoria_status"],
            fill_value=0,
        )

        # Ajusta nomes de colunas (ex: total_status_regular, percentual_baixa_performance)
        df_pivot.columns = [f"{col[0]}_{col[1].lower().replace(' ', '_')}" for col in df_pivot.columns]

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
            "percentual_categoria_status_regular",
            "percentual_categoria_status_suspeita_baixa_perfomance",
            "percentual_categoria_status_baixa_performance",
            "comb_excedente_l",
            "media_consumo_por_km",
            "percentual_categoria_status_erro_telemetria",
            "proporcao_abaixo_mediana",
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
        numero_de_motoristas,
        quantidade_de_viagens,
        dias_marcados,
        mediana_viagem,
        indicativo_performace,
        erro_telemetria,
        criar_os_automatica=False,
        enviar_email=False,
        enviar_whatsapp=False,
        wpp_regra_monitoramento=None,  # lista de até 5 números
        email_regra_monitoramento=None,  # lista de até 5 emails
    ):
        usar_mediana = mediana_viagem is not None
        usar_indicativo = indicativo_performace is not None
        usar_erro = erro_telemetria is not None

        # Garantir que as listas tenham 5 posições
        email_list = (email_regra_monitoramento or []) + [None] * 5
        email_list = email_list[:5]

        wpp_list = (wpp_regra_monitoramento or []) + [None] * 5
        wpp_list = wpp_list[:5]

        try:
            with self.dbEngine.connect() as conn:
                insert_sql = text(
                    """
                    INSERT INTO regras_monitoramento (
                        nome_regra,
                        periodo,
                        modelos,
                        motoristas,
                        dias_analise,
                        qtd_viagens,
                        mediana_viagem,
                        usar_mediana_viagem,
                        indicativo_performace,
                        usar_indicativo_performace,
                        erro_telemetria,
                        usar_erro_telemetria,
                        criado_em,
                        criar_os_automatica,
                        enviar_email,
                        email_usuario1,
                        email_usuario2,
                        email_usuario3,
                        email_usuario4,
                        email_usuario5,
                        enviar_whatsapp,
                        whatsapp_usuario1,
                        whatsapp_usuario2,
                        whatsapp_usuario3,
                        whatsapp_usuario4,
                        whatsapp_usuario5
                    ) VALUES (
                        :nome_regra,
                        :periodo,
                        :modelos,
                        :motoristas,
                        :dias_analise,
                        :qtd_viagens,
                        :mediana_viagem,
                        :usar_mediana_viagem,
                        :indicativo_performace,
                        :usar_indicativo_performace,
                        :erro_telemetria,
                        :usar_erro_telemetria,
                        :criado_em,
                        :criar_os_automatica,
                        :enviar_email,
                        :email1,
                        :email2,
                        :email3,
                        :email4,
                        :email5,
                        :enviar_whatsapp,
                        :wpp1,
                        :wpp2,
                        :wpp3,
                        :wpp4,
                        :wpp5
                    )
                """
                )

                conn.execute(
                    insert_sql,
                    {
                        "nome_regra": nome_regra,
                        "periodo": data,
                        "modelos": modelos,  # lista de strings
                        "motoristas": numero_de_motoristas,
                        "dias_analise": dias_marcados,
                        "qtd_viagens": quantidade_de_viagens,
                        "mediana_viagem": mediana_viagem,
                        "usar_mediana_viagem": usar_mediana,
                        "indicativo_performace": indicativo_performace,
                        "usar_indicativo_performace": usar_indicativo,
                        "erro_telemetria": erro_telemetria,
                        "usar_erro_telemetria": usar_erro,
                        "criado_em": datetime.now(),
                        "criar_os_automatica": criar_os_automatica,
                        "enviar_email": enviar_email,
                        "email1": email_list[0],
                        "email2": email_list[1],
                        "email3": email_list[2],
                        "email4": email_list[3],
                        "email5": email_list[4],
                        "enviar_whatsapp": enviar_whatsapp,
                        "wpp1": wpp_list[0],
                        "wpp2": wpp_list[1],
                        "wpp3": wpp_list[2],
                        "wpp4": wpp_list[3],
                        "wpp5": wpp_list[4],
                    },
                )

                conn.commit()
                print("Regra salva com sucesso")
        except Exception as e:
            print(f"Erro ao salvar a regra: {e}")

    def deletar_regra_monitoramento(self, id_regra):
        try:
            with self.dbEngine.connect() as conn:
                delete_sql = text(
                    """
                    DELETE FROM regras_monitoramento
                    WHERE id = :id_regra
                """
                )

                conn.execute(delete_sql, {"id_regra": id_regra})
                conn.commit()

        except Exception as e:
            print(f"Erro ao deletar a regra: {e}")
