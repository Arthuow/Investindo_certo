import yfinance as yf
import datetime
import sqlite3 as sql
import pandas as pd
import time

# Carregar a lista de ativos a partir do arquivo CSV
df = pd.read_csv(r'C:\Carteira\Lista.txt')

def preco_ativo_intraday(ativo):
    try:
        if not ativo.endswith(".SA"):
            ativo += ".SA"

        # Obter as informações do ativo
        info = yf.Ticker(ativo).info
        ticker = yf.Ticker(ativo)
        preco_atual = info.get('currentPrice', 0)



        # Verifica o timestamp no info
        timestamp = info.get('regularMarketTime') or info.get('preMarketTime') or info.get('postMarketTime')

        # Caso o timestamp não esteja disponível, tenta buscar a última data pelo histórico
        if timestamp:
            data_atualizacao = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')
        else:
            # Usar o método 'history' para obter o último preço e data
            history_data = yf.Ticker(ativo).history(period="1d")
            if not history_data.empty:
                data_atualizacao = history_data.index[-1].strftime('%d-%m-%Y %H:%M')
            else:
                data_atualizacao = "Informação de tempo não disponível"

        dados = ticker.history(period="5d")  # Obter os dados dos últimos 2 dias
        if dados.empty or len(dados) < 2:
            print(f"Não há dados suficientes ou o ativo {ativo} foi delistado.")
            return
        preco_fechamento_anterior = dados['Close'].iloc[-2]  # Fechamento do dia anterior
        preco_atual = dados['Close'].iloc[-1]  # Fechamento ou último preço do dia atual
        preco_atual = round(preco_atual,2)
        variacao_percentual = ((preco_atual - preco_fechamento_anterior) / preco_fechamento_anterior) * 100
        variacao_percentual = round(variacao_percentual,2)

        # Conectar ao banco de dados SQLite
        conn = sql.connect('carteira.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO preco_atual_intraday (ativo, preco_atual, variacao_percentual, data_atualização)
            VALUES (?, ?, ?, ?)
        """, (ativo, preco_atual, variacao_percentual, data_atualizacao))
        conn.commit()
        conn.close()

        print(f"Preço do ativo {ativo} atualizado: {preco_atual} com variação de {variacao_percentual} em {data_atualizacao} ")
    except Exception as e:
        print(f"Erro ao atualizar preço da ação {ativo}: {e}")
    return ativo, preco_atual, data_atualizacao, variacao_percentual
# Loop que atualiza as informações de cada ativo a cada 60 minutos
while True:
    for _, row in df.iterrows():
        ativo = row['TICKER']  # Acessar o valor da coluna TICKER corretamente
        preco_ativo_intraday(ativo)

    # Aguardar 60 minutos antes da próxima atualização
    print("Aguardando 60 minutos para próxima atualização...")
    time.sleep(3600)

