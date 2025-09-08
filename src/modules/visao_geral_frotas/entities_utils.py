import pandas as pd

def get_regras(dbEngine):
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