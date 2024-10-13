import yfinance as yf
from Meta_Trader import inicializando_MetaTrader, pesquisar_ativo, cotacao_tempo_real
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import time  # Importar para usar o time.sleep()

# Configuração da página do Streamlit
st.set_page_config(page_title="Ações", layout='wide')
st.title("Avaliação das Ações")

# Configuração da barra lateral
st.sidebar.header("Selecione uma Ação")
ativo = "PETR4"
ativo = st.sidebar.text_input("Digite Ação:", ativo)

# Corrigir o formato do ativo para o MetaTrader (sem sufixos como ".SA")
ativo_mt5 = ativo  # Certifique-se de que o formato do MetaTrader esteja correto

# Corrigir o formato do ativo para o Yahoo Finance (com sufixo ".SA")
if not ativo.endswith(".SA"):
    ativo_yfinance = ativo + ".SA"
else:
    ativo_yfinance = ativo
print(ativo_yfinance)

periodo = st.sidebar.selectbox('Escolha o período:', ['1d', '5d', '1mo', '3mo', '6mo', '1y'])
dia = datetime.today()

rendimento_titulo = 2.9  # Rendimento do título do governo em %

# Controle de atualização automática
auto_update = st.sidebar.checkbox("Atualizar a cada 60 segundos", value=False)

# Função para baixar dados de ações
def baixar_dados_acoes(ativo_yfinance, periodo, dia):
    acao = yf.Ticker(ativo_yfinance)
    try:
        dados = acao.history(period=periodo, start="2023-01-01", end=dia)
        if dados.empty:
            st.warning("Não foi possível obter os dados da ação.")
        return acao, dados
    except Exception as e:
        st.error(f"Erro ao baixar os dados: {e}")
        return None, pd.DataFrame()

# Função para calcular a média móvel, desvio padrão e valor justo da ação
def calcular_parametros(dados, acao, rendimento_titulo, dia):
    periodo_200 = 200
    media_200 = dados['Close'].rolling(window=periodo_200).mean()
    desvio_200 = dados['Close'].rolling(window=periodo_200).std()
    desvio_2 = desvio_200 * 2 + media_200
    desvio_2_neg = desvio_200 * -2 + media_200

    # Calcular dividendos dos últimos 12 meses
    ultimo_ano = pd.Timestamp(datetime.today() - timedelta(days=365))
    dividendos = acao.dividends
    dividendos.index = dividendos.index.tz_localize(None)  # Remove timezone
    dados.index = dados.index.tz_localize(None)  # Remove timezone
    dividendos_ult_12_meses = dividendos[dividendos.index > ultimo_ano].sum()

    # Realizar a operação de divisão após alinhar os índices
    DY = (dividendos_ult_12_meses / dados['Close'].iloc[-1]) * 100
    preco_limite = dividendos_ult_12_meses / 0.06

    # Obter o EPS
    eps = acao.info.get('forwardEps', 0)

    # Estimar a taxa de crescimento
    taxa_crescimento = 6  # Pode ser ajustado conforme necessário

    # Calcular o valor justo usando a fórmula de Graham
    valor_justo = (eps * (8.5 + 2 * taxa_crescimento)) / rendimento_titulo

    return media_200, desvio_200, desvio_2, desvio_2_neg, dividendos_ult_12_meses, DY, valor_justo, preco_limite

# Função para exibir as informações e gráficos
def exibir_informacoes(ativo_mt5, dados, acao, rendimento_titulo, dia):
    # Calcular média móvel, desvio padrão e valor justo
    media_200, desvio_200, desvio_2, desvio_2_neg, dividendos_ult_12_meses, DY, valor_justo, preco_limite = calcular_parametros(dados, acao, rendimento_titulo, dia)
    # Exibir métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(label="Dividendos dos Últimos 12 Meses", value=f"R$ {dividendos_ult_12_meses:.2f}")
    col2.metric(label="Dividendos Yield (%)", value=f"{DY:.2f}%")
    col3.metric(label="Valor Justo da Ação", value=f"R$ {valor_justo:.2f}")
    col4.metric(label="Preço Limite de Compra", value=f"R$ {preco_limite:.2f}")
    col5.metric(label="Cotação Atual", value=f"R$ {cotacao_last:.2f}")

    # Criar gráfico de candlestick
    fig = go.Figure(data=[go.Candlestick(
        x=dados.index,
        open=dados['Open'],
        high=dados['High'],
        low=dados['Low'],
        close=dados['Close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])

    # Adicionar a média móvel ao gráfico
    fig.add_trace(go.Scatter(
        x=dados.index,
        y=media_200,
        mode='lines',
        line=dict(color='blue', width=2),
        name='Média Móvel 200'
    ))
    fig.add_trace(go.Scatter(
        x=dados.index,
        y=desvio_2,
        mode='lines',
        line=dict(color='red', width=2,dash = 'dash'),
        name='Desvio Padrão-2'
    ))
    fig.add_trace(go.Scatter(
        x=dados.index,
        y=desvio_2_neg,
        mode='lines',
        line=dict(color='red', width=2,dash='dash'),
        name='Desvio Padrão - 2'
    ))

    # Configurar o layout do gráfico
    fig.update_layout(
        title=f'Gráfico Candlestick de {ativo_mt5}',
        xaxis_title='Data',
        yaxis_title='Preço',
        width=1480,
        height=800,
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )

    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)



# Verificar se o botão "Atualizar" foi clicado ou se a atualização automática está ativada
if st.sidebar.button('Atualizar') or auto_update:
    with st.spinner('Baixando dados...'):
        acao, dados = baixar_dados_acoes(ativo_yfinance, periodo, dia)

    if inicializando_MetaTrader():
        cotacao_last = pesquisar_ativo(ativo_mt5)
        print(f"Cotação ask para {ativo_mt5}: {cotacao_last}")

        if not dados.empty:
            exibir_informacoes(ativo_mt5, dados, acao, rendimento_titulo, dia)
        else:
            st.error(f'Não foram encontrados dados para o símbolo "{ativo_mt5}".')

    # Atualizar a cada 60 segundos
    if auto_update:
        time.sleep(60)
        st.experimental_rerun()

