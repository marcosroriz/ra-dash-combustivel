#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para construção das queries SQL


# Subqueries para filtrar as oficinas, seções e ordens de serviço quando TODAS não for selecionado
def subquery_oficinas(lista_oficinas, prefix="", termo_all="TODAS"):
    query = ""
    if termo_all not in lista_oficinas:
        query = f"""AND {prefix}"DESCRICAO DA OFICINA" IN ({', '.join([f"'{x}'" for x in lista_oficinas])})"""

    return query


def subquery_secoes(lista_secaos, prefix="", termo_all="TODAS"):
    query = ""
    if termo_all not in lista_secaos:
        query = f"""AND {prefix}"DESCRICAO DA SECAO" IN ({', '.join([f"'{x}'" for x in lista_secaos])})"""

    return query


def subquery_os(lista_os, prefix="", termo_all="TODAS"):
    query = ""
    if termo_all not in lista_os:
        query = f"""AND {prefix}"DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})"""

    return query


def subquery_modelos(lista_modelos, prefix="", termo_all="TODAS"):
    query = ""
    if termo_all not in lista_modelos:
        query = f"""AND {prefix}"DESCRICAO DO MODELO" IN ({', '.join([f"'{x}'" for x in lista_modelos])})"""

    return query


def subquery_veiculos(lista_veiculos, prefix="", termo_all="TODAS"):
    query = ""
    if termo_all not in lista_veiculos:
        query = f"""AND {prefix}"CODIGO DO VEICULO" IN ({', '.join([f"'{x}'" for x in lista_veiculos])})"""

    return query


def subquery_equipamentos(lista_veiculos, prefix=""):
    query = ""
    if "TODAS" not in lista_veiculos:
        query = f"""AND {prefix}"EQUIPAMENTO" IN ({', '.join([f"'{x}'" for x in lista_veiculos])})"""
    return query


def subquery_modelos_veiculos(lista_modelos, prefix=""):
    # query = ""
    if not lista_modelos or "TODOS" in lista_modelos:
        return ""  # Não adiciona a cláusula IN se a lista estiver vazia ou for "TODOS":
    query = f"""AND {prefix}"DESCRICAO DO MODELO" IN ({', '.join([f"'{x}'" for x in lista_modelos])})"""
    return query


def subquery_modelos_pecas(lista_modelos, prefix=""):
    # query = ""
    if not lista_modelos or "TODOS" in lista_modelos:
        return ""  # Não adiciona a cláusula IN se a lista estiver vazia ou for "TODOS":
    query = f"""AND {prefix}"MODELO" IN ({', '.join([f"'{x}'" for x in lista_modelos])})"""
    return query


def subquery_modelos_combustivel(lista_modelos, prefix="", termo_all="TODOS"):
    query = ""
    # Não adiciona a cláusula IN se a lista tiver "TODOS"
    if termo_all not in lista_modelos:
        query = f"""AND {prefix}"vec_model" IN ({', '.join([f"'{x}'" for x in lista_modelos])})"""

    return query


def subquery_modelos_regras(lista_modelos, prefix="", termo_all="TODOS", usa_where=True):

    if termo_all not in lista_modelos:
        clausula = "WHERE" if usa_where else "AND"
        modelos_sql = ", ".join([f"'{x}'" for x in lista_modelos])
        return f'{clausula} {prefix}"vec_model" IN ({modelos_sql})'

    return ""


def subquery_sentido_combustivel(lista_sentido, prefix="", termo_all="TODOS"):
    query = ""
    # Não adiciona a cláusula IN se a lista tiver "TODOS"
    if termo_all not in lista_sentido:
        query = f"""AND {prefix}"encontrou_sentido_linha" IN ({', '.join([f"'{x}'" for x in lista_sentido])})"""

    return query


def subquery_linha_combustivel(lista_linhas, prefix="", termo_all="TODAS"):
    query = ""
    # Não adiciona a cláusula IN se a lista tiver "TODAS"
    if termo_all not in lista_linhas:
        query = f"""AND {prefix} encontrou_numero_linha IN ({', '.join([f"'{x}'" for x in lista_linhas])})"""

    return query


def subquery_regras_monitoramento(lista_regras, prefix=""):
    if not lista_regras or "TODAS" in lista_regras:
        return ""
    return f"""{prefix} nome_regra IN ({', '.join([f"'{x}'" for x in lista_regras])})"""


def subquery_dia_semana(dia_numerico, prefix=""):
    if not dia_numerico:
        return ""

    query = ""    
    if dia_numerico == 1:
        query = "AND dia_numerico = 1"
    elif dia_numerico == 7:
        query = "AND dia_numerico = 7"
    else:
        query = "AND dia_numerico BETWEEN 2 AND 6"

    return query

