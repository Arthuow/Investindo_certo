import sqlite3 as sql

conn = sql.connect('carteira.db')
cursor = conn.cursor()

# Criar a tabela se ela não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS preco_atual_intraday (
        ativo TEXT PRIMARY KEY,
        preco_atual REAL,
        data_atualização TEXT
    )
''')