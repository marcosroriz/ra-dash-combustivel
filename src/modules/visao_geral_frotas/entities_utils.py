import pandas as pd
from modules.sql_utils import *

def get_regras(dbEngine)-> pd.DataFrame:
    try:
    # Lista de OS
        with dbEngine.begin() as conn: 
            df = pd.read_sql("""
                SELECT *
                FROM regras_monitoramento
            """, conn)
            return df

    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        raise


def get_regra_where(dbEngine, ids: str)-> pd.DataFrame:
    try:
        subquery_regras = subquery_regras_ids(ids)
    # Lista de OS
        with dbEngine.begin() as conn: 
            df = pd.read_sql(f"""
                SELECT 
                     *,
                    TO_CHAR(criado_em, 'DD/MM/YYYY HH24:MI:SS') AS criado_em,
                    TO_CHAR(atualizado_em, 'DD/MM/YYYY HH24:MI:SS') AS atualizado_em
                FROM regras_monitoramento
                WHERE {subquery_regras}
            """, conn)
            return df

    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        raise

def calcular_proporcao_regras_modelos(dbEngine, df_veiculos_regras):
    try:
        query = f"""
            SELECT "Description" AS "vec_num_id",
                "Model" AS "vec_model"
            FROM veiculos_api va
            WHERE "UserState" = 'Available'
            AND "Description" NOT ILIKE '%%DESATIVADO%%';
        """

        # Abrir conexão explícita
        with dbEngine.begin() as conn: 
            df_veiculos_totais = pd.read_sql(query, conn)


            df_veiculos_regras_com_modelo = df_veiculos_regras.merge(
                df_veiculos_totais[["vec_num_id", "vec_model"]],
                on='vec_num_id',
                how='left'
            )
            
            total_por_modelo = df_veiculos_totais.groupby("vec_model").size().reset_index(name="total")

            regras_por_modelo = df_veiculos_regras_com_modelo.groupby("vec_model").size().reset_index(name="com_regra")

            df_merge = total_por_modelo.merge(regras_por_modelo, on="vec_model", how="left")
            
            df_merge["com_regra"] = df_merge["com_regra"].fillna(0).astype(int)
            df_merge["sem_regra"] = df_merge["total"] - df_merge["com_regra"]

            df_merge["perc_com_regra"] = df_merge["com_regra"] / df_merge["total"] * 100
            df_merge["perc_sem_regra"] = df_merge["sem_regra"] / df_merge["total"] * 100

            df_merge["perc_com_regra"] = df_merge["perc_com_regra"].round(2)
            df_merge["perc_sem_regra"] = df_merge["perc_sem_regra"].round(2)

            return df_merge
        
    except Exception as e:
        print(f"Erro ao executar a consulta: {str(e)}")
        raise