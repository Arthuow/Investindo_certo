import sqlite3 as sql
import streamlit as st
import pandas as pd
st.set_page_config(page_title="📈 Carteira de Ações", layout='wide')

# CSS personalizado para alterar o fundo da sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: ##D0E8FF; /* Cor de fundo */
        padding: 20px;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h3 {
        color: #333;  /* Cor do texto da sidebar */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Conectar ao banco de dados
try:
    with sql.connect('carteira.db', timeout=10) as conn:
        cursor = conn.cursor()
        print("Conectado ao banco sqlite")
        cursor.execute("""
                    UPDATE carteira_acoes
                    SET variacao_hoje = (
                        SELECT preco_atual_intraday.variacao_percentual
                        FROM preco_atual_intraday
                        WHERE carteira_acoes.ativo = preco_atual_intraday.ativo
                    )
                    WHERE EXISTS (
                        SELECT 1
                        FROM preco_atual_intraday
                        WHERE carteira_acoes.ativo = preco_atual_intraday.ativo
                    );
                """)

        conn.commit()
        print("Coluna 'variacao_hoje' atualizada com sucesso!")

        # Criar tabela de ações
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS carteira_acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NULL,
            preco_medio REAL NULL,
            preco_atual REAL NULL,
            diferenca REAL NULL,
            patrimonio REAL NULL,
            variacao_hoje REAL NULL,
            variacao_total REAL NULL,
            quantidade INTEGER NULL,
            percentual_carteira REAL NULL,
            variacao_financeira_hoje REAL NULL,
            data_compra TEXT NULL,
            data_venda TEXT NULL,
            patrimonio_inicial
        );
        """)
        conn.commit()

        # Criar tabela de Compras
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS COMPRAS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NOT NULL,
            quantidade_compra INTEGER NOT NULL,
            preco_compra REAL NOT NULL,
            patrimonio_investido REAL NOT NULL,
            data_compra TEXT NOT NULL
        );
        """)
        conn.commit()

        # Criar tabela de Vendas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS VENDAS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NOT NULL,
            quantidade_vendas INTEGER NOT NULL,
            preco_venda REAL NOT NULL,
            patrimonio_vendido REAL NOT NULL,
            data_venda TEXT NOT NULL
        );
        """)
        conn.commit()
except sql.Error as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
# Barra lateral para adicionar compra
st.sidebar.markdown('<h2 style="color: #00cb89; font-size:18px;"><strong>Adicionar Nova Compra</strong></h2>', unsafe_allow_html=True)
ativo_compra = st.sidebar.text_input("Ação:", key=1)
if ativo_compra and not ativo_compra.endswith(".SA"):
    ativo_compra += ".SA"

Qtd_compra = st.sidebar.number_input("Quantidade Comprada:", key=2, step=1)
vlr_compra = st.sidebar.number_input("Valor da Compra", key=3, format="%.2f")
data_compra = st.sidebar.date_input("Data da Compra:", key="data_compra_1").strftime("%d-%m-%Y")
patrimonio_investido = vlr_compra * Qtd_compra
st.sidebar.write(f"Valor Investido em {ativo_compra} de R$ {patrimonio_investido:.2f}")

if st.sidebar.button("Registrar Compra"):
    if ativo_compra and Qtd_compra > 0 and vlr_compra > 0:
        with sql.connect('carteira.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO COMPRAS (ativo, quantidade_compra, preco_compra, data_compra, patrimonio_investido)
                VALUES (?, ?, ?, ?, ?)
            """, (ativo_compra, Qtd_compra, vlr_compra, data_compra, patrimonio_investido))
            conn.commit()
            st.sidebar.success("Compra adicionada com sucesso!")
    else:
        st.sidebar.error("Preencha todos os campos corretamente.")

# Barra lateral para adicionar venda
st.sidebar.markdown('<h1 style="color: #921e43; font-size:18px;"><strong>Informar Venda</strong></h1>', unsafe_allow_html=True)
ativo_venda = st.sidebar.text_input("Ação:", key=5)
if ativo_venda and not ativo_venda.endswith(".SA"):
    ativo_venda += ".SA"

Qtd_venda = st.sidebar.number_input("Quantidade Vendida:", key=6, step=1)
vlr_venda = st.sidebar.number_input("Valor da Venda", key=7, format="%.2f")
data_venda = st.sidebar.date_input("Data de Venda", key="data_venda_1").strftime("%d-%m-%Y")
patrimonio_vendido = vlr_venda * Qtd_venda
st.sidebar.write(f"Valor vendido em {ativo_venda} de R$ {patrimonio_vendido:.2f}")

if st.sidebar.button("Registrar Venda"):
    if ativo_venda and Qtd_venda > 0 and vlr_venda > 0:
        with sql.connect('carteira.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO VENDAS (ativo, quantidade_vendas, preco_venda, data_venda, patrimonio_vendido)
                VALUES (?, ?, ?, ?, ?)
            """, (ativo_venda, Qtd_venda, vlr_venda, data_venda, patrimonio_vendido))
            conn.commit()
            st.sidebar.success("Venda registrada com sucesso!")
    else:
        st.sidebar.error("Preencha todos os campos corretamente.")

########################################################################################################################
def calculo():
    # Conteúdo da página
    st.markdown("""
        <h1 style="color: #11275c; font-size:30px; background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
            Carteira de Ações
        </h1>
        """, unsafe_allow_html=True)
    # Consultar as compras e vendas
    compras_query = """
        SELECT 
            ativo,
            SUM(quantidade_compra) as quantidade_comprada,
            SUM(quantidade_compra * preco_compra) / SUM(quantidade_compra) as preco_medio_compra,
            SUM(quantidade_compra * preco_compra) as patrimonio_investido
        FROM COMPRAS 
        GROUP BY ativo; 
    """
    df_compras = pd.read_sql_query(compras_query, conn)
    vendas_query = """
    SELECT 
        ativo, 
        SUM(quantidade_vendas) as quantidade_vendida, 
        SUM(quantidade_vendas * preco_venda) / SUM(quantidade_vendas) as preco_medio_venda,
        SUM(quantidade_vendas * preco_venda) as patrimonio_vendido 
    FROM VENDAS 
    GROUP BY ativo;
    """
    carteira_query ="SELECT ativo,variacao_hoje FROM carteira_acoes"
    df_carteira = pd.read_sql_query(carteira_query, conn)
    print(df_carteira)

    df_vendas = pd.read_sql_query(vendas_query, conn)
    # Mesclar as compras e vendas por ativo
    df_ativos = pd.merge(df_compras, df_vendas, on='ativo', how='left').fillna(0)
    # Calcular a quantidade atual de ações por ativo
    df_ativos['quantidade_atual'] = round(df_ativos['quantidade_comprada'] - df_ativos['quantidade_vendida'], 0)
    # Calcular o preço médio de compra
    df_ativos['preco_medio'] = df_ativos.apply(lambda row: row['preco_medio_compra'] if row['quantidade_atual'] > 0 else 0, axis=1)


    # Busca o preço atual do ativo na tabela preco_atual_intraday
    precos_atuais_query = """
       SELECT ativo, preco_atual FROM preco_atual_intraday
       """

#######################################################################################################################
    df_preco_atual = pd.read_sql_query(precos_atuais_query, conn)
    # Calcular a diferença entre preço médio de compra e preço atual
    df_ativos = pd.merge(df_ativos, df_preco_atual[['ativo', 'preco_atual']], on='ativo', how='left')

    #calculo da diferença entre preço médio e o preço atual
    df_ativos['diferenca'] = round((df_ativos['preco_atual'] - df_ativos['preco_medio']) / df_ativos['preco_atual'] * 100, 2)
    df_ativos['diferenca'] = df_ativos['diferenca'].apply(lambda x: f"{x:.2f}%")

    # Calculo do Patrimônio
    df_ativos['patrimonio'] = df_ativos['quantidade_atual']*df_ativos['preco_atual']

    df_ativos['patrimonio_inicial'] = df_ativos['preco_medio']*df_ativos['quantidade_atual']

    patrimonio_inicial = df_ativos['patrimonio_inicial'].sum()
    patrimonio_atual = df_ativos['patrimonio'].sum()
    #Variação total do dinheiro investido
    df_ativos['variacao_total'] = (df_ativos['preco_atual']*df_ativos['quantidade_atual'])-(df_ativos['preco_medio']*df_ativos['quantidade_atual'])

    df_ativos['variacao_financeira_hoje'] =df_ativos['patrimonio']*df_carteira['variacao_hoje']/100

    variacao_financeiro_hoje = df_ativos['variacao_financeira_hoje'].sum()
    variacao_financeiro_hoje = round(variacao_financeiro_hoje,2)


    # Percentual da carteira
    df_ativos['percentual_carteira'] = (df_ativos['patrimonio']/patrimonio_atual)*100
    df_ativos['percentual_carteira'] = df_ativos['percentual_carteira'].apply(lambda x: f"{x:.2f}%")
    df_ativos['patrimonio'] = df_ativos['patrimonio'].apply(lambda x:f"R$ {x:.2f}")
    df_ativos['patrimonio_inicial'] = df_ativos['patrimonio_inicial'].apply(lambda x:f"R$ {x:.2f}")

    lucro = df_ativos['variacao_total'].sum()
    lucro_percentual = lucro/patrimonio_inicial*100


    df_ativos['variacao_total'] = df_ativos['variacao_total'].apply(lambda x:f"R$ {x:.2f}")
    # Definir a cor do texto com base no lucro
    cor_lucro = "#00cb89" if lucro >= 0 else "#ff0000"  # Verde se positivo, vermelho se negativo
    cor_variacao_hoje = "#00cb89" if variacao_financeiro_hoje >= 0 else "#ff0000"

    atualizar_carteira_acoes(df_ativos)
    # Exibir os valores atualizados
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding-top: 8px;">
            <h3 style="color: #333;">Investimento: <span style="color: #00cb89;">R$ {patrimonio_inicial:,.2f}</span></h3>
            <h3 style="color: #333;">Lucro: <span style="color:{cor_lucro};">R$ {lucro:,.2f}</span></h3>
            <h3 style="color: #333;">Lucro(%): <span style="color:{cor_lucro};">{lucro_percentual:,.2f} % </span></h3>
            <h3 style="color: #333;">Var. Hoje: <span style="color:{cor_variacao_hoje};">R$ {variacao_financeiro_hoje:,.2f} </span></h3>
            <h3 style="color: #333;">Patrimônio Atual: <span style="color: #00cb89;">R$ {patrimonio_atual:,.2f}</span></h3>
        </div>
    """, unsafe_allow_html=True)
    return df_ativos

########################################################################################################################
def atualizar_carteira_acoes(df_ativos):
    # Conectar ao banco de dados usando 'with'
    with sql.connect('carteira.db') as conn:
        cursor = conn.cursor()
        for index, row in df_ativos.iterrows():
            ativo = row['ativo']
            preco_medio = row['preco_medio']
            preco_atual = row['preco_atual']
            quantidade = row['quantidade_atual']
            diferenca = row['diferenca']
            patrimonio = row['patrimonio']
            variacao_total = row['variacao_total']
            percentual_carteira = row['percentual_carteira']
            patrimonio_inicial = row['patrimonio_inicial']
            variacao_financeira_hoje = row['variacao_financeira_hoje']

            # Verificar se o ativo já existe na tabela
            cursor.execute("SELECT COUNT(1) FROM carteira_acoes WHERE ativo = ?", (ativo,))
            exists = cursor.fetchone()[0]

            if exists:
                # Atualizar o registro existente
                cursor.execute("""
                    UPDATE carteira_acoes
                    SET preco_medio = ?, preco_atual = ?, quantidade = ?, diferenca =?, patrimonio =?, variacao_total =?,
                    percentual_carteira =?, patrimonio_inicial =?, variacao_financeira_hoje =?
                    WHERE ativo = ?
                """, (preco_medio, preco_atual, quantidade, diferenca, patrimonio,variacao_total,percentual_carteira, patrimonio_inicial,variacao_financeira_hoje, ativo))
            else:
                # Inserir um novo registro
                cursor.execute("""
                    INSERT INTO carteira_acoes (ativo, preco_medio, preco_atual, quantidade, diferenca, patrimonio, variacao_total, percentual_carteira, patrimonio_inicial,variacao_financeira_hoje)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ativo, preco_medio, preco_atual, quantidade,diferenca, patrimonio,variacao_total, percentual_carteira, patrimonio_inicial,variacao_financeira_hoje))
########################################################################################################################

########################################################################################################################
df_ativos = calculo()

novos_nomes_colunas = {
    'ativo': 'Ativo',
    'preco_medio': 'Preço médio',
    'preco_atual': 'Preço Atual',
    'diferanca': 'Diferança',
    'patrimonio': 'Patrimônio Atual',
    'variacao': 'Variação Hoje (%)',
    'vartiacao_total': 'Variação Total (%)',
    'quantidade': 'Quantidade',
    'percentual_carteira': '% na Carteira',
    'diferenca': 'Diferença (Preço Médio / Preço Atual)',
    'patrimonio_inicial': 'Patrimônio Incial',
    'variacao_financeira_hoje': 'Variação Financeira Hoje'

}
# Renomear as colunas
df_ativos_renomeado = df_ativos.rename(columns=novos_nomes_colunas)

# Função para formatar números no padrão brasileiro
def formatar_numero_brasileiro(valor):
    return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Aplicar a formatação em colunas numéricas
df_ativos_formatado = df_ativos_renomeado.copy()
for coluna in df_ativos_formatado.select_dtypes(include=['float', 'int']).columns:
    df_ativos_formatado[coluna] = df_ativos_formatado[coluna].map(formatar_numero_brasileiro)

# Converter para HTML com estilo CSS personalizado
html_table = df_ativos_formatado.to_html(classes='styled-table', index=False, escape=False)

# CSS para a tabela
css = """
<style>
.styled-table {
    font-family: Calibri, sans-serif;
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 14px;
    min-width: 400px;
    border-radius: 5px 5px 0 0;
    overflow: hidden;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.styled-table th {
    background-color: #f7f7f7;
    color: #333;
    text-align: center;
    padding: 10px 12px;
}
.styled-table td {
    background-color: #fff;
    color: #000;
    text-align: center;
    padding: 10px 12px;
    border-bottom: 1px solid #dddddd;
}
.styled-table tr:last-of-type td {
    border-bottom: none;
}
</style>
"""

# Renderizar HTML no Streamlit
st.markdown(css, unsafe_allow_html=True)  # Aplicar o CSS
st.markdown(html_table, unsafe_allow_html=True)  # Renderizar a tabela HTML

st.divider()
############################## Tabelas de compras e vendas #############################################################
col1, col2 = st.columns(2)
    # Título com cor e tamanho de fonte personalizados
with col1:
    st.markdown('<h3 style="color: #FF5733; font-size:16px;">Compras Recentes</h3>', unsafe_allow_html=True)
    compras_query = """
    SELECT
        ativo AS 'Ativo',
        quantidade_compra AS 'Qtd.',
        preco_compra AS "Preço de compra",
        data_compra AS 'Data da compra',
        patrimonio_investido AS 'Patrimônio'
    FROM
        COMPRAS;
    """
    df_compras = pd.read_sql_query(compras_query, conn)

    df_compras_styled = df_compras.style.format({
        'Qtd. Comprada': '{:,.0f}',
        'Preço de Compra': 'R$ {:,.2f}',
        'Patrimônio':'R$ {:,.2f}',
        'Data da Compra': '{}'

    })
    st.dataframe(df_compras_styled)
with col2:
    #Exibir os dados das vendas realizadas

    st.markdown('<h2 style="color: #FF5733; font-size:16px;">Vendas Recentes</h2>', unsafe_allow_html=True)
    vendas_query = """
    SELECT
        ativo AS 'Ativo',
        quantidade_vendas AS 'Qtd. Vendida',
        preco_venda AS 'Preço de Venda',
        patrimonio_vendido AS ' Valor da Venda',
        data_venda AS 'Data da Venda'
    FROM
        VENDAS;
    """
    df_vendas = pd.read_sql_query(vendas_query, conn)

    df_vendas_styled = df_vendas.style.format({
        'Qtd. Vendida': '{:,.0f}',
        'Preço de Venda': 'R$ {:,.2f}',
        'Valor da Venda':'R$ {:,.2f}',
        'Data de Venda': '{}'
    })
    st.dataframe(df_vendas_styled)