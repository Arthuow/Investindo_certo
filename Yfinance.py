import pandas as pd
import datetime
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
import sqlite3 as sql
import math

############### COTAÇÃO EM TEMPO REAL #######################
def cotacao_tempo_real_yfinance(ativo):
    print("Cotação_tempo_real_yfinance",ativo)
    preco_atual = yf.Ticker(ativo)
    data =preco_atual.history(period="1d", interval="1m")
    # Exibindo a última cotação disponível do dia
    preco_atual_yfinance = data['Close'].iloc[-1]
    print("Cotação mais recente:", preco_atual_yfinance)
    return preco_atual_yfinance
########################       DIVIDENDOS DOS ULTIMOS 5 ANOS        ##################################################
def dividendos_medio_5Y(ativo):
    # Obter histórico do ativo
    acao = yf.Ticker(ativo)
    dividendos = acao.dividends
    # Definir a data limite (5 anos atrás)
    data_limite = datetime.now() - timedelta(days=5*365)
    data_limite = pd.Timestamp(data_limite).normalize()  # Normalizar para eliminar a hora e garantir o mesmo formato

    # Garantir que o índice é um DatetimeIndex e sem fuso horário
    if not isinstance(dividendos.index, pd.DatetimeIndex):
        dividendos.index = pd.to_datetime(dividendos.index)

    # Remover qualquer fuso horário do índice para garantir a compatibilidade
    if dividendos.index.tz is not None:
        dividendos.index = dividendos.index.tz_localize(None)

    # Filtrar os dividendos dos últimos 5 anos
    dividendos_5_anos = dividendos[dividendos.index >= data_limite]

    if not dividendos_5_anos.empty:
        media_dividendos = dividendos_5_anos.mean()
        return media_dividendos
    else:
        return 0  # Retorna 0 se não houver dividendos nos últimos 5 anos
########################################################################################################################
############################################# DIVIDENDOS YELDS #########################################################
# Função para calcular o Dividend Yield dos últimos 12 meses
def DY_ULT12M(ativo):
    print('Ativo que chegou no DY_ULT_12M:', ativo)

    # Corrigindo a chamada do yf.Ticker
    ativo_1 = yf.Ticker(ativo)

    # Calculando a data de 12 meses atrás
    ultimo_ano = pd.Timestamp(datetime.today() - timedelta(days=365))

    # Obtendo os dividendos
    dividendos = ativo_1.dividends

    # Verificando se há dividendos
    if dividendos.empty:
        print(f"Sem dividendos registrados no Yahoo Finance para o ativo {ativo}")
        return 0  # Retorna 0 se não houver dividendos

    # Exibindo dividendos para verificação
    print(f"Dividendos obtidos para {ativo}:\n", dividendos)

    # Remover timezone das datas
    dividendos.index = dividendos.index.tz_localize(None)

    # Somando os dividendos dos últimos 12 meses
    DY_12M = dividendos[dividendos.index > ultimo_ano].sum()

    print(f"Dividendos totais dos últimos 12 meses para {ativo}: {DY_12M}")

    # Se não houve dividendos nos últimos 12 meses, retorne 0
    if DY_12M == 0:
        print(f"Sem dividendos nos últimos 12 meses para {ativo}")
        return 0

    return DY_12M
########################################################################################################################
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

    # Calcular a soma e a média dos dividendos dos últimos 10 anos
    dividendos_soma = df_totais_por_ano['Dividendos + JCP'].sum()
    dividendos_media = df_totais_por_ano['Dividendos + JCP'].mean()
    return df_totais_por_ano, dividendos_soma, dividendos_media
#######################################################################################################################
############################################# DADOS DA AÇÃO ###############################################
def dados_financeiros(ativo):
    print("Chegou no dados da ação, ativo: ", ativo)
    try:
        if not ativo.endswith(".SA"):
            ativo += ".SA"
        info = yf.Ticker(ativo).info
        # Obtendo a data e hora da última atualização de mercado

        timestamp = info.get('regularMarketTime', None)
        if timestamp:
            data_hora_atualizacao = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
        else:
            data_hora_atualizacao = "Informação de tempo não disponível"
        print(data_hora_atualizacao)
        DY = round(info.get('dividendYield', 0) *100,4)
        PL = info.get('trailingPE', 0)
        PVP = round(info.get('priceToBook', 0),4)
        EV_EBIT = info.get('enterpriseToEbitda', 0)
        ROE = info.get('returnOnEquity', 0) * 100
        ROA = info.get('returnOnAssets', 0) * 100
        ROIC = 0  # Este indicador não está disponível no yfinance
        VPA = round(info.get('bookValue', 0),2)
        LPA = info.get('trailingEps', 0)
        preco_atual = info.get('currentPrice', 0)
        ############################## CALCULO DOS PARAMETROS #########################################################
        # Obter os dados da ação no YFinance
        acao = yf.Ticker(ativo)
        dia = datetime.now().strftime('%Y-%m-%d')  # Obter a data atual no formato 'YYYY-MM-DD'

        # Histórico de dados de fechamento desde 2022-01-01 até a data atual
        dados = acao.history(period='1d', start="2022-01-01", end=dia)
        if dados.empty:
            print(f"Nenhum dado encontrado para o ativo {ativo}. Prosseguindo com o próximo.")
            return None

        if dados.empty:
            print(f"Não há dados disponíveis para o ativo {ativo}")
            return

        # Calcular a média móvel de 200 dias
        periodo_200 = 200
        media_200 = dados['Close'].rolling(window=periodo_200).mean()
        media_200 = round(media_200,4)

        # Obter o último valor da média móvel
        media_200_ultimo = media_200.dropna().iloc[-1] if not media_200.dropna().empty else None
        media_200_ultimo = round(media_200_ultimo,4)

        if media_200_ultimo is None:
            print(f"Não foi possível calcular a média de 200 dias para o ativo {ativo}")
            return

        print(f"Yfinance - Última média 200 dias para {ativo}: {media_200_ultimo}")

        # Calcular o desvio padrão com janela de 200 dias
        desvio_200 = dados['Close'].rolling(window=periodo_200).std()

        # Obter o último valor do desvio padrão
        desvio_200_ultimo = desvio_200.dropna().iloc[-1] if not desvio_200.dropna().empty else None

        if desvio_200_ultimo is None:
            print(f"Não foi possível calcular o desvio padrão para o ativo {ativo}")
            return

        print(f"Desvio padrão (último valor) para {ativo}: {desvio_200_ultimo}")

        # Cálculo dos desvios padrões (1, 2 e 3)
        desvio_padrao_1 = round(media_200_ultimo + desvio_200_ultimo,4)
        desvio_padrao_2 = round(media_200_ultimo + (2 * desvio_200_ultimo),4)
        desvio_padrao_3 = round(media_200_ultimo + (3 * desvio_200_ultimo),4)
        desvio_padrao_neg_1 = round(media_200_ultimo - desvio_200_ultimo,4)
        desvio_padrao_neg_2 = round(media_200_ultimo - (2 * desvio_200_ultimo),4)
        desvio_padrao_neg_3 = round(media_200_ultimo - (3 * desvio_200_ultimo),4)

        print(f"Desvio padrão 1: {desvio_padrao_1}")
        print(f"Desvio padrão 2: {desvio_padrao_2}")
        print(f"Desvio padrão 3: {desvio_padrao_3}")
        print(f"Desvio padrão neg. 1: {desvio_padrao_neg_1}")
        print(f"Desvio padrão neg. 2: {desvio_padrao_neg_2}")
        print(f"Desvio padrão neg. 3: {desvio_padrao_neg_3}")

        # Cálculo do valor justo de Graham
        valor_justo_GRAHAM = round(math.sqrt(22.5 * VPA * LPA),4)
        print(f"Valor justo de Graham para {ativo}: {valor_justo_GRAHAM}")
        print('Concluido levatamento dos dados')
        return (DY,PL,PVP,EV_EBIT,ROE,ROA,ROIC,VPA,LPA,preco_atual,data_hora_atualizacao,media_200,desvio_padrao_1,
                desvio_padrao_2,desvio_padrao_3,desvio_padrao_neg_1,desvio_padrao_neg_2,desvio_padrao_neg_3,valor_justo_GRAHAM)

    except Exception as e:
        st.error(f"Erro ao buscar dados para o ativo {ativo}: {e}")
        return None
#######################################################################################################################
################################## ARMAZENAR NO BANCO  #############################################################
def armazenar_no_banco(ativo, df_dividendos, dividendos_soma, dividendos_media):
    # Conectar ao banco de dados
    conn = sql.connect('carteira.db')
    cursor = conn.cursor()

    # Criar a tabela se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dividendos_acoes (
            ativo TEXT PRIMARY KEY,
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
            dividendos_media REAL
        )
    ''')

    # Criar um dicionário para armazenar os dividendos ano a ano
    dividendos_por_ano = {f"dividendos_{ano}": None for ano in range(2015, 2031)}

    # Preencher o dicionário com os dividendos dos anos disponíveis
    for _, row in df_dividendos.iterrows():
        ano = row['Ano']
        if 2015 <= ano <= 2030:  # Considerando apenas os anos entre 2015 e 2030
            dividendos_por_ano[f"dividendos_{ano}"] = row['Dividendos + JCP']

    # Inserir os valores no banco de dados
    cursor.execute('''
        INSERT OR REPLACE INTO dividendos_acoes (
            ativo, dividendos_2015, dividendos_2016, dividendos_2017, dividendos_2018, dividendos_2019, 
            dividendos_2020, dividendos_2021, dividendos_2022, dividendos_2023, dividendos_2024,
            dividendos_2025, dividendos_2026, dividendos_2027, dividendos_2028, dividendos_2029, 
            dividendos_2030, dividendos_soma, dividendos_media
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ativo,
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
        dividendos_soma,
        dividendos_media
    ))

    # Salvar as mudanças e fechar a conexão
    conn.commit()
    conn.close()

# Exemplo de uso integrado
ativo = "ITSA4.SA"
df_dividendos, dividendos_soma, dividendos_media = dividendos_historico(ativo)

