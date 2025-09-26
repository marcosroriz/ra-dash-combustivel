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