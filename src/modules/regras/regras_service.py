# Imports básicos
import pandas as pd
import numpy as np

# Lib para lidar com feriados
import holidays

# Imports auxiliares


class RegrasService:

    def __init__(self, pgEngine):
        self.pgEngine = pgEngine

    def get_data_monitoramento(self):
        pass