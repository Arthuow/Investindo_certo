import sqlite3 as sql

conn = sql.connect('carteira.db')
cursor = conn.cursor()
cursor.execute("""
    ALTER TABLE carteira_acoes ADD COLUMN variacao_financeira_hoje REAL;
""")
conn.commit()
conn.close()
print("Coluna 'variacao_financeira_hoje' adicionada com sucesso!")

# Execute esta função apenas uma vez
# adicionar_coluna_dividendos()

