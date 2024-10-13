import streamlit as st
import sqlite3 as sql
import pandas as pd

# Definir o layout como 'wide' para usar a largura total da página
st.set_page_config(layout="wide")
st.markdown("""
        <h1 style="color: #11275c; font-size:32px; background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
            Ações Selecionadas para Investimentos
        </h1>
        """, unsafe_allow_html=True)


def abrir_banco():
    conn = sql.connect('carteira.db')
    query = "SELECT * FROM dividendos_acoes"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Função principal do app
def app():
    df = abrir_banco()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Slider para filtrar o Dividendos Yield (DY)
        DY_min = 5
        DY_max = 14
        DY_range = st.slider(
            'Filtro por Dividendos Yeld (%)',
            min_value=float(DY_min),
            max_value=float(DY_max),
            value=(float(DY_min), float(DY_max))
        )

    with col2:
        filtro_graham = st.radio('Filtro de Graham:', ["SIM", "NÃO"], index=0)

    with col3:
        menor_media_200 = st.radio('Menor que a Média de 200 períodos:', ["SIM", "NÃO"], index=0)

    with col4:
        menor_desvio_1 = st.radio('Menor que o desvio -1 negativo:', ["SIM", "NÃO"], index=1)

    # Aplicar o filtro de DY
    df_filtrado = df[(df['DY'] >= DY_range[0]) & (df['DY'] <= DY_range[1])]

    # Filtro Graham: Valor Justo Graham maior que 0
    if filtro_graham == "SIM":
        df_filtrado = df_filtrado[df_filtrado['preco_atual'] < df_filtrado['VALOR_JUSTO_GRAHAM']]

    # Filtro de Preço menor que Média 200 períodos
    if menor_media_200 == "SIM":
        if 'MEDIA_200' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['preco_atual'] < df_filtrado['MEDIA_200']]

    # Filtro de Preço menor que o Desvio Padrão Negativo (-1)
    if menor_desvio_1 == "SIM":
        if 'DESVIO_PADRAO_NEG_1' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['preco_atual'] < df_filtrado['DESVIO_PADRAO_NEG_1']]

    # Mostrar o DataFrame filtrado
    colunas_retiradas = ['dividendos_2015','dividendos_2016','dividendos_2017','dividendos_2018','dividendos_2025',
                         'dividendos_2026','dividendos_2027','dividendos_2028','dividendos_2029','dividendos_2030',
                         ]
    df_filtrado = df_filtrado.drop(columns=colunas_retiradas)

    st.dataframe(df_filtrado, width=None, height=800)

    # Exibir estatísticas descritivas dos dados filtrados
    st.write("Estatísticas Descritivas dos Dados Filtrados:")
    st.write(df_filtrado.describe())


# Executar o app no Streamlit
if __name__ == "__main__":
    app()
