import streamlit as st
import pandas as pd
import requests
import io

# 1. Configuração inicial da página
st.set_page_config(page_title="Filtro Mestre", layout="wide")
st.title("Filtro Mestre - Ações B3")
st.write("Filtre as melhores ações da B3 com precisão cirúrgica.")

# 2. Função para carregar os dados DIRETO do site
@st.cache_data(ttl="1h")
def carregar_dados():
    url = 'https://www.fundamentus.com.br/resultado.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    r = requests.get(url, headers=headers)
    html_content = io.StringIO(r.text)
    
    # O Pandas já faz a leitura perfeita dos números aqui!
    df = pd.read_html(html_content, decimal=',', thousands='.', na_values=['-', ' - '])[0]
    
    df.columns = [
        'Ticker', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pativo', 'pcapgiro', 
        'pebit', 'pativcircliq', 'evebit', 'evebitda', 'mrgbruta', 'mrgebit', 
        'mrgliq', 'liqcorr', 'roic', 'roe', 'liq2meses', 'patrimliq', 'divLpatrim', 'cresc_rec5'
    ]
    
    # Limpamos APENAS as percentagens, porque o símbolo '%' faz o Pandas pensar que é texto
    cols_perc = ['dy', 'mrgbruta', 'mrgebit', 'mrgliq', 'roic', 'roe', 'cresc_rec5']
    for col in cols_perc:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce') / 100
        
    # REMOVIDA a secção que estragava os números normais.
    
    # Removemos linhas que não têm as métricas exigidas pelos nossos novos filtros
    df = df.dropna(subset=['pl', 'pvp', 'dy', 'roe', 'liq2meses', 'cresc_rec5'])
        
    return df

with st.spinner("A garimpar dados no Fundamentus..."):
    df_acoes = carregar_dados()

# 3. Controlos precisos (Campos de Mínimo e Máximo lado a lado)
st.sidebar.header("Configure os seus Filtros")

st.sidebar.markdown("**P/L (Preço sobre Lucro)**")
col1, col2 = st.sidebar.columns(2)
pl_min = col1.number_input("Mín", value=3.0, step=0.5, key='pl_min')
pl_max = col2.number_input("Máx", value=10.0, step=0.5, key='pl_max')

st.sidebar.markdown("**P/VP (Preço / Valor Patrimonial)**")
col1, col2 = st.sidebar.columns(2)
pvp_min = col1.number_input("Mín", value=0.5, step=0.1, key='pvp_min')
pvp_max = col2.number_input("Máx", value=2.0, step=0.1, key='pvp_max')

st.sidebar.markdown("**Dividend Yield (%)**")
col1, col2 = st.sidebar.columns(2)
dy_min = col1.number_input("Mín", value=7.0, step=0.5, key='dy_min')
dy_max = col2.number_input("Máx", value=14.0, step=0.5, key='dy_max')

st.sidebar.markdown("**ROE (%)**")
col1, col2 = st.sidebar.columns(2)
roe_min = col1.number_input("Mín", value=15.0, step=1.0, key='roe_min')
roe_max = col2.number_input("Máx", value=30.0, step=1.0, key='roe_max')

st.sidebar.markdown("**Liquidez 2 Meses (R$)**")
liq_min = st.sidebar.number_input("Mínimo", value=1000000.0, step=100000.0, key='liq_min')

st.sidebar.markdown("**Crescimento Rec. 5a (%)**")
cresc_min = st.sidebar.number_input("Mínimo", value=10.0, step=1.0, key='cresc_min')

# 4. Lógica de Filtragem Corrigida
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) & (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] >= pvp_min) & (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) & (df_acoes['dy'] <= (dy_max / 100)) &
    (df_acoes['roe'] >= (roe_min / 100)) & (df_acoes['roe'] <= (roe_max / 100)) &
    (df_acoes['liq2meses'] >= liq_min) &
    (df_acoes['cresc_rec5'] >= (cresc_min / 100))
]

# 5. Exibição da Tabela
st.markdown(f"### 🎯 Ações aprovadas nos filtros: **{len(df_filtrado)}** de {len(df_acoes)}")

colunas_exibicao = ['Ticker', 'cotacao', 'pl', 'pvp', 'dy', 'roe', 'liq2meses', 'cresc_rec5']
df_mostrar = df_filtrado[colunas_exibicao].copy()

# Deixando os dados formatados com estética profissional
df_mostrar['dy'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['dy']]
df_mostrar['roe'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['roe']]
df_mostrar['cresc_rec5'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['cresc_rec5']]

# Formatando a liquidez em Reais com máscara de milhar
df_mostrar['liq2meses'] = df_mostrar['liq2meses'].apply(lambda x: f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "R$ 0")

df_mostrar.columns = ['Ticker', 'Cotação (R$)', 'P/L', 'P/VP', 'Div. Yield', 'ROE', 'Liquidez Diária', 'Cresc. 5 anos']

st.dataframe(df_mostrar, use_container_width=True)