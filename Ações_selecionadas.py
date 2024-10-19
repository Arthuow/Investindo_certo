import pandas as pd
import sqlite3 as sql
import yfinance as yf
from Yfinance import dados_financeiros,DY_ULT12M
from datetime import datetime
import time
# Leitura da lista de ações do arquivo TXT
df = pd.read_csv(r'C:\Carteira\Lista.txt')
##################### ATUALIZAÇÃO DO PREÇO DO ATIVO ########################
#aqui devo buscar na tabela preco_atual_intraday os valores da coluna preco_atual_intraday e atualizar a outra tabela dividendos_acoes
def atualizar_preco_ativo():
    try:
        # Conectar ao banco de dados
        conn = sql.connect('carteira.db')
        cursor = conn.cursor()

        # Consulta SQL para atualizar a tabela 'dividendos_acoes' com base na 'preco_atual_intraday'
        update_query = '''
            UPDATE dividendos_acoes
            SET preco_atual = (
                SELECT pi.preco_atual
                FROM preco_atual_intraday pi
                WHERE pi.ativo = dividendos_acoes.ativo
            )
            WHERE EXISTS (
                SELECT 1
                FROM preco_atual_intraday pi
                WHERE pi.ativo = dividendos_acoes.ativo
            )
        '''

        # Executar a consulta de atualização
        cursor.execute(update_query)

        # Confirmar a atualização
        conn.commit()

        print("Tabela 'dividendos_acoes' atualizada com sucesso.")

    except sql.Error as e:
        print(f"Erro ao atualizar os preços dos ativos: {e}")

    finally:
        # Fechar a conexão com o banco de dados
        if conn:
            conn.close()
# Chamar a função para atualizar os preços
atualizar_preco_ativo()
########################################################################################################################
# Função para armazenar os dividendos no banco de dados
def armazenar_no_banco(ativo, df_dividendos, dividendos_soma, dividendos_media):
    # Conectar ao banco de dados
    global media_200, desvio_padrao_1
    conn = sql.connect('carteira.db')
    cursor = conn.cursor()

    #cursor.execute('DROP TABLE IF EXISTS dividendos_acoes')

    # Criar a tabela se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dividendos_acoes (
            ativo TEXT PRIMARY KEY,
            preco_atual INTEGER,
            dividendos_2015 REAL, 
            dividendos_2016 REAL, 
            dividendos_2017 REAL, 
            dividendos_2018 REAL, 
            dividendos_2019 REAL, 
            dividendos_2020 REAL, 
            dividendos_2021 REAL, 
            dividendos_2022 REAL, 
            dividendos_2023 REAL,
            dividendos_2024 REAL,
            dividendos_2025 REAL,
            dividendos_2026 REAL,
            dividendos_2027 REAL,
            dividendos_2028 REAL,
            dividendos_2029 REAL,
            dividendos_2030 REAL,
            dividendos_soma REAL,
            dividendos_media REAL,
            DY REAL,
            DY_ULT_12 REAL,
            PVP REAL,
            VPA REAL,
            LPA REAL,
            VALOR_JUSTO_GRAHAM INTEGER,
            VALOR_LIMITE_DY_ULT_12M REAL,
            VALOR_LIMITE_DY_ULT_10A REAL,
            MEDIA_200 INTEGER,
            DESVIO_PADRAO_1 INTEGER,
            DESVIO_PADRAO_2 INTEGER,
            DESVIO_PADRAO_3 INTEGER,
            DESVIO_PADRAO_NEG_1 INTEGER,
            DESVIO_PADRAO_NEG_2 INTEGER,
            DESVIO_PADRAO_NEG_3 INTEGER,
            data_hora_atualizacao TEXT
        )
    ''')

    # Obter os dados financeiros do ativo
    dados_financeiros_resultado = dados_financeiros(ativo)
    if dados_financeiros_resultado is None:
        print(f"Nenhum dado financeiro encontrado para o ativo {ativo}. Prosseguindo com o próximo.")
        return
    try:
        (DY, PL, PVP, EV_EBIT, ROE, ROA, ROIC, VPA, LPA, preco_atual, _, media_200, desvio_padrao_1, desvio_padrao_2, desvio_padrao_3,desvio_padrao_neg_1,desvio_padrao_neg_2,desvio_padrao_neg_3,valor_justo_GRAHAM) = dados_financeiros_resultado

    except Exception as e:
        print(f"Erro ao armazenar dados para {ativo}: {e}")
    # Obter a data e hora atual para o campo de atualização
    data_hora_atualizacao = datetime.now()

    # Verificação para garantir que os valores de média e desvios são válidos
    if isinstance(media_200, pd.Series):
        media_200 = media_200.iloc[-1]  # Pegar o último valor da média
    if isinstance(desvio_padrao_1, pd.Series):
        desvio_padrao_1 = desvio_padrao_1.iloc[-1]
    if isinstance(desvio_padrao_2, pd.Series):
        desvio_padrao_2 = desvio_padrao_2.iloc[-1]
    if isinstance(desvio_padrao_3, pd.Series):
        desvio_padrao_3 = desvio_padrao_3.iloc[-1]

    print(
        f"Inserindo os valores: {(ativo, preco_atual, dividendos_soma, dividendos_media, DY, PL, PVP, EV_EBIT, ROE, ROA, ROIC, VPA, LPA, data_hora_atualizacao, media_200, desvio_padrao_1, desvio_padrao_2, desvio_padrao_3, valor_justo_GRAHAM)}")

    print("Ativo", ativo)
    Resultado_DY_ULT12M = DY_ULT12M(ativo)
    (DY_12M) = Resultado_DY_ULT12M
    VALOR_LIMITE_DY_ULT_12M = round(DY_12M / 0.06, 4) if preco_atual else 0 #ta errado
    VALOR_LIMITE_DY_ULT_10A = round(dividendos_media/ 0.06,4) if preco_atual else 0
    DY_ULT_12 = round(DY_12M,4)

    # Criar um dicionário para armazenar os dividendos ano a ano
    dividendos_por_ano = {f"dividendos_{ano}": 0 for ano in range(2015, 2031)}

    # Preencher o dicionário com os dividendos dos anos disponíveis
    for _, row in df_dividendos.iterrows():
        ano = row['Ano']
        if 2015 <= ano <= 2030:
            dividendos_por_ano[f"dividendos_{ano}"] = row['Dividendos + JCP'] if row['Dividendos + JCP'] is not None else 0

    # Inserir os valores no banco de dados
    cursor.execute('''
        INSERT OR REPLACE INTO dividendos_acoes (
            ativo, preco_atual, dividendos_2015, dividendos_2016, dividendos_2017, dividendos_2018, dividendos_2019, 
            dividendos_2020, dividendos_2021, dividendos_2022, dividendos_2023, dividendos_2024,
            dividendos_2025, dividendos_2026, dividendos_2027, dividendos_2028, dividendos_2029, 
            dividendos_2030, dividendos_soma, dividendos_media, DY, DY_ULT_12, PVP, VPA, LPA, 
            VALOR_JUSTO_GRAHAM, VALOR_LIMITE_DY_ULT_12M, VALOR_LIMITE_DY_ULT_10A, MEDIA_200, 
            DESVIO_PADRAO_1, DESVIO_PADRAO_2, DESVIO_PADRAO_3, DESVIO_PADRAO_NEG_1, DESVIO_PADRAO_NEG_2, DESVIO_PADRAO_NEG_3, data_hora_atualizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?)
    ''', (
        ativo,
        preco_atual,
        dividendos_por_ano['dividendos_2015'],
        dividendos_por_ano['dividendos_2016'],
        dividendos_por_ano['dividendos_2017'],
        dividendos_por_ano['dividendos_2018'],
        dividendos_por_ano['dividendos_2019'],
        dividendos_por_ano['dividendos_2020'],
        dividendos_por_ano['dividendos_2021'],
        dividendos_por_ano['dividendos_2022'],
        dividendos_por_ano['dividendos_2023'],
        dividendos_por_ano['dividendos_2024'],
        dividendos_por_ano['dividendos_2025'],
        dividendos_por_ano['dividendos_2026'],
        dividendos_por_ano['dividendos_2027'],
        dividendos_por_ano['dividendos_2028'],
        dividendos_por_ano['dividendos_2029'],
        dividendos_por_ano['dividendos_2030'],
        dividendos_soma if dividendos_soma is not None else 0,
        dividendos_media if dividendos_media is not None else 0,
        DY if DY is not None else 0,
        DY_ULT_12 if DY_ULT_12 is not None else 0,
        PVP if PVP is not None else 0,
        VPA if VPA is not None else 0,
        LPA if LPA is not None else 0,
        valor_justo_GRAHAM if valor_justo_GRAHAM is not None else 0,
        VALOR_LIMITE_DY_ULT_12M,
        VALOR_LIMITE_DY_ULT_10A,
        media_200 if media_200 is not None else 0,
        desvio_padrao_1 if desvio_padrao_1 is not None else 0,
        desvio_padrao_2 if desvio_padrao_2 is not None else 0,
        desvio_padrao_3 if desvio_padrao_3 is not None else 0,
        desvio_padrao_neg_1 if desvio_padrao_neg_1 is not None else 0,
        desvio_padrao_neg_2 if desvio_padrao_neg_2 is not None else 0,
        desvio_padrao_neg_3 if desvio_padrao_neg_3 is not None else 0,
        data_hora_atualizacao
    ))

    # Salvar as mudanças e fechar a conexão
    conn.commit()
    conn.close()
# Função para buscar o histórico de dividendos
def dividendos_historico(ativo):
    ano_inicial = 2015
    ativo_1 = yf.Ticker(ativo)
    historico_acoes = ativo_1.actions

    # Verifica se historico_acoes é um DataFrame válido
    if historico_acoes.empty:
        print(f"Nenhum dado encontrado para {ativo}. Pode estar deslistado.")
        return pd.DataFrame(), 0, 0

    # Verifica se o índice é um DatetimeIndex antes de aplicar tz_localize
    if isinstance(historico_acoes.index, pd.DatetimeIndex):
        historico_acoes.index = historico_acoes.index.tz_localize(None)

    # Filtrar os dividendos e JCP a partir do ano_inicial
    historico_ajustado = historico_acoes[historico_acoes.index.year >= ano_inicial]

    # Agrupar os dividendos/JCP por ano e somar os valores de cada ano
    totais_por_ano = historico_ajustado.groupby(historico_ajustado.index.year)['Dividends'].sum()

    # Converter para DataFrame e resetar o índice para transformar o índice em uma coluna
    df_totais_por_ano = pd.DataFrame(totais_por_ano).reset_index()

    # Adicionar a coluna com o nome do ativo para todas as linhas
    df_totais_por_ano['Ativo'] = ativo

    # Renomear as colunas
    df_totais_por_ano.columns = ['Ano', 'Dividendos + JCP', 'Ativo']

    # Arredondar os dividendos para 4 casas decimais
    df_totais_por_ano['Dividendos + JCP'] = df_totais_por_ano['Dividendos + JCP'].round(4)

    # Calcular a soma e a média dos dividendos dos últimos 5 anos, arredondando para 4 casas decimais
    dividendos_soma = round(df_totais_por_ano['Dividendos + JCP'].sum(), 4)
    dividendos_media = round(df_totais_por_ano['Dividendos + JCP'].mean(), 4)

    # Contar quantos anos a ação pagou dividendos (valores maiores que 0)
    anos_com_dividendos = (df_totais_por_ano['Dividendos + JCP'] > 0).sum()

    return df_totais_por_ano, dividendos_soma, dividendos_media
# Função para filtrar as ações que pagaram dividendos nos últimos 10 anos e armazenar no banco
def filtro_acoes(df):

    print(df)
    acoes_com_dividendos = []
    print("ações com dividendos",acoes_com_dividendos)

    for index,row in df.iterrows():
        ativo = row['TICKER']
        if not ativo.endswith(".SA"):
            ativo += ".SA"
        try:
            print('FILTRO AÇÕES:', ativo)
            df_dividendos, dividendos_soma, dividendos_media = dividendos_historico(ativo)

            # Verifica se o DataFrame retornado tem dados e a coluna 'Ano'
            if df_dividendos.empty or 'Ano' not in df_dividendos.columns:
                print(f"Ação {ativo} não possui dados de dividendos ou a coluna 'Ano' está faltando.")
                continue

        except Exception as e:
            print(f"Erro ao buscar dividendos para {ativo}: {e}")
            continue  # Ignora esta ação se houver erro

        # Verificar se a ação pagou dividendos todos os anos nos últimos 10 anos (2015-2024)
        anos_necessarios = list(range(2015, 2024))  # Lista dos últimos 10 anos

        # Verifica se todos os anos de 2015 a 2024 têm dividendos maiores que zero
        pagou_todos_anos = all(
            (df_dividendos[df_dividendos['Ano'] == ano]['Dividendos + JCP'].sum() > 0)
            for ano in anos_necessarios
        )

        if pagou_todos_anos:
            acoes_com_dividendos.append(ativo)
            # Armazenar no banco de dados apenas se passar pelo filtro
            armazenar_no_banco(ativo, df_dividendos, dividendos_soma, dividendos_media)
        else:
            print(f"Ação {ativo} não pagou dividendos todos os anos nos últimos 10 anos.")

    return acoes_com_dividendos
# Executar o filtro
acoes_filtradas = filtro_acoes(df)
print(f"Ações filtradas: {acoes_filtradas}")

