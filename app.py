import streamlit as st
import pandas as pd
import requests
import io

# 1. Configuração inicial da página
st.set_page_config(page_title="Filtro Mestre", layout="wide")
st.title("Filtro Mestre - Ações B3")
st.write("Filtre as melhores ações da B3 em tempo real.")

# 2. Função para carregar os dados DIRETO do site
@st.cache_data(ttl="1h")
def carregar_dados():
    url = 'https://www.fundamentus.com.br/resultado.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    r = requests.get(url, headers=headers)
    html_content = io.StringIO(r.text)
    
    # O SEGREDO ESTÁ AQUI: Avisamos o Pandas do padrão brasileiro de números e o que é espaço vazio
    df = pd.read_html(
        html_content, 
        decimal=',', 
        thousands='.', 
        na_values=['-', ' - ']
    )[0]
    
    df.columns = [
        'Ticker', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pativo', 'pcapgiro', 
        'pebit', 'pativcircliq', 'evebit', 'evebitda', 'mrgbruta', 'mrgebit', 
        'mrgliq', 'liqcorr', 'roic', 'roe', 'liq2meses', 'patrimliq', 'divLpatrim', 'cresc_rec5'
    ]
    
    # Limpamos apenas as colunas de porcentagem (As outras o Pandas já resolveu!)
    cols_perc = ['dy', 'mrgbruta', 'mrgebit', 'mrgliq', 'roic', 'roe', 'cresc_rec5']
    for col in cols_perc:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce') / 100

    # Removemos ações que não têm dados suficientes para a nossa análise
    df = df.dropna(subset=['pl', 'pvp', 'dy', 'roic', 'divLpatrim'])
        
    return df

# Carregando a base de dados
with st.spinner("Garimpando dados no Fundamentus..."):
    df_acoes = carregar_dados()

# 3. Criando o menu lateral para os filtros
st.sidebar.header("Configure seus Filtros")

pl_min, pl_max = st.sidebar.slider("P/L (Preço sobre Lucro)", -20.0, 50.0, (5.0, 20.0))
pvp_max = st.sidebar.number_input("P/VP Máximo", value=3.0, step=0.1)
dy_min = st.sidebar.number_input("Dividend Yield Mínimo (%)", value=5.0, step=0.5)
roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0, step=0.5)
div_pl_max = st.sidebar.number_input("Dívida/Patrimônio Máximo", value=2.0, step=0.1)

# 4. Aplicando a lógica de filtragem no Pandas
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) &
    (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] > 0) & 
    (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) &
    (df_acoes['roic'] >= (roic_min / 100)) &
    (df_acoes['divLpatrim'] <= div_pl_max)
]

# 5. Exibindo os resultados na tela
st.markdown(f"### 🎯 Ações aprovadas nos filtros: **{len(df_filtrado)}** de {len(df_acoes)}")

colunas_exibicao = ['Ticker', 'cotacao', 'pl', 'pvp', 'dy', 'roic', 'divLpatrim', 'cresc_rec5']
df_mostrar = df_filtrado[colunas_exibicao].copy()

# Trocamos as colunas inteiras por listas de texto formatadas, assim o Pandas não briga com o tipo do dado
df_mostrar['dy'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['dy']]
df_mostrar['roic'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['roic']]
df_mostrar['cresc_rec5'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['cresc_rec5']]

df_mostrar.columns = ['Ticker', 'Cotação (R$)', 'P/L', 'P/VP', 'Div. Yield', 'ROIC', 'Dív.Líq/PL', 'Cresc. 5 anos']

st.dataframe(df_mostrar, use_container_width=True)