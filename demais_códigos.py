# lucro buscando na tabela carteira_acoes
cursor.execute("SELECT SUM(variacao_total) FROM carteira_acoes")
lucro = cursor.fetchone()[0]  # Pega o resultado da soma
# Se não houver registros, configurar lucro como 0
if lucro is None:
    lucro = 0
