import yfinance as yf
import datetime
import sqlite3 as sql
import pandas as pd
import logging

# Configuração do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def preco_ativo_intraday(ativo):
    """Atualiza o preço de um ativo específico."""
    try:
        if not ativo.endswith(".SA"):
            ativo += ".SA"

        ticker = yf.Ticker(ativo)
        info = ticker.info

        preco_atual = info.get('currentPrice', 0)
        timestamp = info.get('regularMarketTime') or info.get('preMarketTime') or info.get('postMarketTime')

        if not timestamp:
            history_data = ticker.history(period="1d")
            data_atualizacao = history_data.index[-1].strftime('%d-%m-%Y %H:%M:%S') if not history_data.empty else "Indisponível"
        else:
            data_atualizacao = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M:%S')

        dados = ticker.history(period="5d")
        if dados.empty or len(dados) < 2:
            logging.warning(f"Não há dados suficientes para o ativo {ativo}.")
            return

        preco_fechamento_anterior = dados['Close'].iloc[-2]
        preco_atual = dados['Close'].iloc[-1]
        preco_atual = round(preco_atual, 2)
        variacao_percentual = round(((preco_atual - preco_fechamento_anterior) / preco_fechamento_anterior) * 100, 2)

        with sql.connect(r'C:\Carteira\carteira.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO preco_atual_intraday (ativo, preco_atual, variacao_percentual, data_atualização)
                VALUES (?, ?, ?, ?)
            """, (ativo, preco_atual, variacao_percentual, data_atualizacao))
            conn.commit()

        logging.info(f"Ativo {ativo} atualizado: {preco_atual} ({variacao_percentual}%) em {data_atualizacao}")

    except Exception as e:
        logging.error(f"Erro ao atualizar preço do ativo {ativo}: {e}")

def atualizar_todos_precos():
    """Atualiza o preço de todos os ativos registrados na carteira."""
    try:
        with sql.connect(r'C:\Carteira\carteira.db') as conn:
            # Consulta para obter os ativos registrados em compras
            compras_query = """
                SELECT DISTINCT ativo FROM carteira_acoes
            """
            df_compras = pd.read_sql_query(compras_query, conn)

        if df_compras.empty:
            logging.warning("Nenhum ativo encontrado na tabela 'carteira_acoes'.")
            return

        # Iterar sobre os ativos e atualizar os preços
        for ativo in df_compras['ativo']:
            preco_ativo_intraday(ativo)

    except Exception as e:
        logging.error(f"Erro ao atualizar todos os preços: {e}")

if __name__ == "__main__":
    atualizar_todos_precos()