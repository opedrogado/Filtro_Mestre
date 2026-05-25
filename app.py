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
    
    # Lemos a tabela informando o padrão brasileiro de pontuação
    df = pd.read_html(html_content, decimal=',', thousands='.', na_values=['-', ' - '])[0]
    
    df.columns = [
        'Ticker', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pativo', 'pcapgiro', 
        'pebit', 'pativcircliq', 'evebit', 'evebitda', 'mrgbruta', 'mrgebit', 
        'mrgliq', 'liqcorr', 'roic', 'roe', 'liq2meses', 'patrimliq', 'divLpatrim', 'cresc_rec5'
    ]
    
    # Limpamos as colunas de porcentagem
    cols_perc = ['dy', 'mrgbruta', 'mrgebit', 'mrgliq', 'roic', 'roe', 'cresc_rec5']
    for col in cols_perc:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce') / 100
        
    # Limpamos as colunas numéricas tradicionais
    cols_numeric = ['pl', 'pvp', 'divLpatrim', 'cotacao', 'evebit']
    for col in cols_numeric:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.replace(' ', '', regex=False).replace('-', 'NaN'), errors='coerce')

    df = df.dropna(subset=['pl', 'pvp', 'dy', 'roic', 'divLpatrim', 'cresc_rec5'])
        
    return df

# Carregando a base de dados
with st.spinner("Garimpando dados no Fundamentus..."):
    df_acoes = carregar_dados()

# 3. Criando o menu lateral para os filtros (AGORA TODOS COM MÍNIMO E MÁXIMO)
st.sidebar.header("Configure seus Filtros")

# Filtro de Preço sobre Lucro
pl_min, pl_max = st.sidebar.slider("P/L (Preço sobre Lucro)", -20.0, 50.0, (0.0, 20.0))

# AJUSTE: Filtro de Preço sobre Valor Patrimonial (Mín e Máx)
pvp_min, pvp_max = st.sidebar.slider("P/VP (Preço sobre Valor Patrimonial)", 0.0, 10.0, (0.0, 3.0))

# AJUSTE: Filtro de Dividend Yield (Mín e Máx)
dy_min, dy_max = st.sidebar.slider("Dividend Yield (%)", 0.0, 40.0, (5.0, 20.0))

# AJUSTE: Filtro de ROIC (Mín e Máx)
roic_min, roic_max = st.sidebar.slider("ROIC (%)", -10.0, 50.0, (10.0, 40.0))

# AJUSTE: Filtro de Dívida Líquida sobre Patrimônio Líquido (Mín e Máx)
div_pl_min, div_pl_max = st.sidebar.slider("Dívida Líquida / Patrimônio", -5.0, 10.0, (-1.0, 2.0))

# AJUSTE: Filtro de Crescimento de Receita nos últimos 5 anos (Mín e Máx)
cresc_min, cresc_max = st.sidebar.slider("Crescimento de Receita (5 anos %)", -30.0, 100.0, (5.0, 50.0))


# 4. Aplicando a lógica de filtragem atualizada no Pandas
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) & (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] >= pvp_min) & (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) & (df_acoes['dy'] <= (dy_max / 100)) &
    (df_acoes['roic'] >= (roic_min / 100)) & (df_acoes['roic'] <= (roic_max / 100)) &
    (df_acoes['divLpatrim'] >= div_pl_min) & (df_acoes['divLpatrim'] <= div_pl_max) &
    (df_acoes['cresc_rec5'] >= (cresc_min / 100)) & (df_acoes['cresc_rec5'] <= (cresc_max / 100))
]

# 5. Exibindo os resultados na tela
st.markdown(f"### 🎯 Ações aprovadas nos filtros: **{len(df_filtrado)}** de {len(df_acoes)}")

colunas_exibicao = ['Ticker', 'cotacao', 'pl', 'pvp', 'dy', 'roic', 'divLpatrim', 'cresc_rec5']
df_mostrar = df_filtrado[colunas_exibicao].copy()

# Formatando as colunas estéticas de forma segura
df_mostrar['dy'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['dy']]
df_mostrar['roic'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['roic']]
df_mostrar['cresc_rec5'] = [f"{(x * 100):.2f}%" if pd.notna(x) else "0.00%" for x in df_mostrar['cresc_rec5']]

# Renomeando as colunas de forma profissional
df_mostrar.columns = ['Ticker', 'Cotação (R$)', 'P/L', 'P/VP', 'Div. Yield', 'ROIC', 'Dív.Líq/PL', 'Cresc. 5 anos']

st.dataframe(df_mostrar, use_container_width=True)