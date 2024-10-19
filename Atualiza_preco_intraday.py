import yfinance as yf
import datetime
import sqlite3 as sql
import pandas as pd
import time
import logging

# Configuração do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Caminho para a lista de ativos
LISTA_ATIVOS_PATH = r'C:\Carteira\Lista.txt'
INTERVALO_ATUALIZACAO = 1800  # 9 minutos (540 segundos)

# Função para obter preço intraday e atualizar no banco de dados
def preco_ativo_intraday(ativo):
    try:
        if not ativo.endswith(".SA"):
            ativo += ".SA"

        ticker = yf.Ticker(ativo)
        info = ticker.info

        # Tenta buscar o preço atual e timestamp
        preco_atual = info.get('currentPrice', 0)
        timestamp = info.get('regularMarketTime') or info.get('preMarketTime') or info.get('postMarketTime')

        # Se timestamp não está disponível, usa o histórico
        if not timestamp:
            history_data = ticker.history(period="1d")
            data_atualizacao = history_data.index[-1].strftime('%d-%m-%Y %H:%M') if not history_data.empty else "Indisponível"
        else:
            data_atualizacao = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')

        # Obter dados dos últimos 2 dias
        dados = ticker.history(period="5d")
        if dados.empty or len(dados) < 2:
            logging.warning(f"Não há dados suficientes para o ativo {ativo}.")
            return

        # Cálculo do preço e variação percentual
        preco_fechamento_anterior = dados['Close'].iloc[-2]
        preco_atual = dados['Close'].iloc[-1]
        preco_atual = round(preco_atual, 2)
        variacao_percentual = round(((preco_atual - preco_fechamento_anterior) / preco_fechamento_anterior) * 100, 2)

        # Inserir ou atualizar no banco de dados
        with sql.connect('carteira.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO preco_atual_intraday (ativo, preco_atual, variacao_percentual, data_atualização)
                VALUES (?, ?, ?, ?)
            """, (ativo, preco_atual, variacao_percentual, data_atualizacao))
            conn.commit()

        logging.info(f"Ativo {ativo} atualizado: {preco_atual} ({variacao_percentual}%) em {data_atualizacao}")

    except Exception as e:
        logging.error(f"Erro ao atualizar preço do ativo {ativo}: {e}")

# Função principal para rodar a atualização contínua
def atualizar_precos():
    while True:
        try:
            # Recarregar a lista de ativos em cada ciclo para garantir que está atualizada
            df = pd.read_csv(LISTA_ATIVOS_PATH)

            # Atualizar cada ativo da lista
            for _, row in df.iterrows():
                ativo = row['TICKER']
                preco_ativo_intraday(ativo)

            # Pausar antes do próximo ciclo
            logging.info(f"Aguardando {INTERVALO_ATUALIZACAO} segundos para a próxima atualização.")
            time.sleep(INTERVALO_ATUALIZACAO)  # Pausa de 9 minutos

        except KeyboardInterrupt:
            logging.info("Processo interrompido manualmente.")
            break
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente

# Executa a função de atualização
if __name__ == "__main__":
    atualizar_precos()
