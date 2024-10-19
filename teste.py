import yfinance as yf

# Defina o ticker da ação
ticker = "BBDC4.SA"  # Exemplo para uma ação brasileira

# Obtenha os dados do ativo usando yfinance
ativo = yf.Ticker(ticker)

# Acesse o EPS projetado (forward EPS)
forward_eps = ativo.info.get('forwardEps')

# Exiba o resultado
print(f'O LPA projetado (Forward EPS) de {ticker} é: {forward_eps}')

# <h3 style="color: #333;">Var. Hoje: <span style="color:{cor_variacao_hoje};">R$ {variacao_financeiro_hoje:,.2f} </span></h3>