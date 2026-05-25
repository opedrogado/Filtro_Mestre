import streamlit as st
import pandas as pd
import requests
import io
import numpy as np
import yfinance as yf # A nova biblioteca de gráficos!

# 1. Configuração inicial da página
st.set_page_config(page_title="Filtro Mestre", layout="wide")
st.title("Filtro Mestre - Ações B3")
st.write("O terminal definitivo: Filtros Precisos + Valuation + Gráficos Históricos.")

# 2. Função para carregar os dados DIRETO do site
@st.cache_data(ttl="1h")
def carregar_dados():
    url = 'https://www.fundamentus.com.br/resultado.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    r = requests.get(url, headers=headers)
    html_content = io.StringIO(r.text)
    
    df = pd.read_html(html_content, decimal=',', thousands='.', na_values=['-', ' - '])[0]
    
    df.columns = [
        'Ticker', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pativo', 'pcapgiro', 
        'pebit', 'pativcircliq', 'evebit', 'evebitda', 'mrgbruta', 'mrgebit', 
        'mrgliq', 'liqcorr', 'roic', 'roe', 'liq2meses', 'patrimliq', 'divLpatrim', 'cresc_rec5'
    ]
    
    cols_perc = ['dy', 'mrgbruta', 'mrgebit', 'mrgliq', 'roic', 'roe', 'cresc_rec5']
    for col in cols_perc:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce') / 100
        
    cols_numeric = ['pl', 'pvp', 'divLpatrim', 'cotacao', 'evebit', 'liq2meses']
    for col in cols_numeric:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['pl', 'pvp', 'dy', 'roe', 'liq2meses', 'cresc_rec5'])
        
    return df

with st.spinner("A garimpar dados no Fundamentus..."):
    df_acoes = carregar_dados()

# 3. Controlos precisos na barra lateral
st.sidebar.header("Configure os seus Filtros")

st.sidebar.markdown("**P/L (Preço sobre Lucro)**")
col1, col2 = st.sidebar.columns(2)
pl_min = col1.number_input("Mín", value=3.0, step=0.5, key='pl_min')
pl_max = col2.number_input("Máx", value=15.0, step=0.5, key='pl_max') # Aumentei um pouco o padrão para facilitar veres resultados

st.sidebar.markdown("**P/VP (Preço / Valor Patrimonial)**")
col1, col2 = st.sidebar.columns(2)
pvp_min = col1.number_input("Mín", value=0.5, step=0.1, key='pvp_min')
pvp_max = col2.number_input("Máx", value=3.0, step=0.1, key='pvp_max')

st.sidebar.markdown("**Dividend Yield (%)**")
col1, col2 = st.sidebar.columns(2)
dy_min = col1.number_input("Mín", value=5.0, step=0.5, key='dy_min')
dy_max = col2.number_input("Máx", value=14.0, step=0.5, key='dy_max')

st.sidebar.markdown("**ROE (%)**")
col1, col2 = st.sidebar.columns(2)
roe_min = col1.number_input("Mín", value=10.0, step=1.0, key='roe_min')
roe_max = col2.number_input("Máx", value=30.0, step=1.0, key='roe_max')

st.sidebar.markdown("**Crescimento Rec. 5a (%)**")
cresc_min = st.sidebar.number_input("Mínimo", value=5.0, step=1.0, key='cresc_min')

st.sidebar.markdown("**Liquidez 2 Meses (R$)**")
liq_min = st.sidebar.number_input("Mínimo", value=1000000.0, step=100000.0, key='liq_min')

# 4. Lógica de Filtragem
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) & (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] >= pvp_min) & (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) & (df_acoes['dy'] <= (dy_max / 100)) &
    (df_acoes['roe'] >= (roe_min / 100)) & (df_acoes['roe'] <= (roe_max / 100)) &
    (df_acoes['cresc_rec5'] >= (cresc_min / 100)) & 
    (df_acoes['liq2meses'] >= liq_min)
].copy()

# =====================================================================
# 4.5 CÁLCULOS E RANKING
# =====================================================================
df_filtrado['Pontuação'] = 0

if not df_filtrado.empty:
    df_filtrado['lpa'] = df_filtrado['cotacao'] / df_filtrado['pl']
    df_filtrado['vpa'] = df_filtrado['cotacao'] / df_filtrado['pvp']
    df_filtrado['preco_graham'] = np.sqrt(np.maximum(22.5 * df_filtrado['lpa'] * df_filtrado['vpa'], 0))
    df_filtrado['margem_seguranca'] = ((df_filtrado['preco_graham'] - df_filtrado['cotacao']) / df_filtrado['preco_graham']) * 100
    df_filtrado['proventos_por_acao'] = df_filtrado['cotacao'] * df_filtrado['dy']
    df_filtrado['preco_barsi'] = df_filtrado['proventos_por_acao'] / 0.06

    df_filtrado['Status (Graham)'] = [
        "🟢 Descontada" if margem > 15 else ("🟡 Preço Justo" if margem >= 0 else "🔴 Esticada")
        for margem in df_filtrado['margem_seguranca']
    ]

    df_filtrado.loc[df_filtrado.nsmallest(3, 'pl').index, 'Pontuação'] += 1
    df_filtrado.loc[df_filtrado.nsmallest(3, 'pvp').index, 'Pontuação'] += 1
    df_filtrado.loc[df_filtrado.nlargest(3, 'dy').index, 'Pontuação'] += 1
    df_filtrado.loc[df_filtrado.nlargest(3, 'roe').index, 'Pontuação'] += 1
    df_filtrado.loc[df_filtrado.nlargest(3, 'cresc_rec5').index, 'Pontuação'] += 1

    df_filtrado = df_filtrado.sort_values(by=['Pontuação', 'margem_seguranca'], ascending=[False, False])

# =====================================================================

# 5. Exibição da Tabela
st.markdown(f"### 🎯 Ações aprovadas nos filtros: **{len(df_filtrado)}** de {len(df_acoes)}")

colunas_exibicao = ['Ticker', 'Pontuação', 'Status (Graham)', 'cotacao', 'preco_graham', 'margem_seguranca', 'preco_barsi', 'dy', 'roe', 'cresc_rec5']
df_mostrar = df_filtrado[colunas_exibicao].copy()

if not df_mostrar.empty:
    df_mostrar['Pontuação'] = df_mostrar['Pontuação'].astype(str) + " ⭐"
    df_mostrar['margem_seguranca'] = df_mostrar['margem_seguranca'].round(1).astype(str) + "%"
    df_mostrar['dy'] = [f"{(x * 100):.2f}%" for x in df_mostrar['dy']]
    df_mostrar['roe'] = [f"{(x * 100):.2f}%" for x in df_mostrar['roe']]
    df_mostrar['cresc_rec5'] = [f"{(x * 100):.2f}%" for x in df_mostrar['cresc_rec5']]
    
    df_mostrar['cotacao'] = df_mostrar['cotacao'].apply(lambda x: f"R$ {x:.2f}")
    df_mostrar['preco_graham'] = df_mostrar['preco_graham'].apply(lambda x: f"R$ {x:.2f}")
    df_mostrar['preco_barsi'] = df_mostrar['preco_barsi'].apply(lambda x: f"R$ {x:.2f}")

df_mostrar.columns = ['Ticker', 'Pontos', 'Status (Graham)', 'Cotação Atual', 'Preço Justo (Graham)', 'Margem de Segurança', 'Preço Teto (Barsi)', 'Div. Yield', 'ROE', 'Cresc. 5 anos']

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# =====================================================================
# 6. GRÁFICOS HISTÓRICOS (Integração Yahoo Finance)
# =====================================================================
st.markdown("---")
st.markdown("### 📈 Análise Histórica de Preços (5 Anos)")

if not df_filtrado.empty:
    # Cria uma lista com os tickers que passaram no filtro
    tickers_disponiveis = df_filtrado['Ticker'].tolist()
    
    # Caixa de seleção para o utilizador escolher qual a ação a analisar
    acao_escolhida = st.selectbox("Selecione uma ação do seu filtro para ver o histórico:", tickers_disponiveis)
    
    if acao_escolhida:
        with st.spinner(f"A descarregar dados de {acao_escolhida} do Yahoo Finance..."):
            # O Yahoo Finance exige o sufixo ".SA" para ações brasileiras (ex: PETR4.SA)
            ticker_yf = acao_escolhida + ".SA"
            
            # Puxamos os dados dos últimos 5 anos
            dados_historicos = yf.Ticker(ticker_yf).history(period="5y")
            
            if not dados_historicos.empty:
                # O Streamlit tem uma função nativa linda para desenhar gráficos de linha
                st.line_chart(dados_historicos['Close'])
                
                # Bónus: Mostrar um resumo rápido de altos e baixos
                preco_atual = dados_historicos['Close'].iloc[-1]
                preco_maximo = dados_historicos['Close'].max()
                preco_minimo = dados_historicos['Close'].min()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
                col2.metric("Máxima (5 anos)", f"R$ {preco_maximo:.2f}")
                col3.metric("Mínima (5 anos)", f"R$ {preco_minimo:.2f}")
            else:
                st.warning(f"Não foi possível encontrar o histórico para {acao_escolhida} no Yahoo Finance.")
else:
    st.info("Ajuste os filtros na barra lateral para encontrar ações e desbloquear os gráficos.")