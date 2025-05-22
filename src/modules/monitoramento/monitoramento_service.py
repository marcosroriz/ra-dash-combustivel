#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de monitoramento

# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares
from modules.sql_utils import subquery_modelos_combustivel, subquery_sentido_combustivel


class MonitoramentoService:
    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def get_ultimas_viagens(self, n_viagens):
        """
        Função que retorna as últimas viagens de todos os veículos
        """

        # Query
        query = f"""
        SELECT 
            *
        FROM 
        (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY vec_num_id ORDER BY rmtc_timestamp_inicio DESC) AS rn
            FROM 
                public.rmtc_viagens_analise_via_ra
        ) sub
        WHERE 
            rn <= {n_viagens};
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df

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