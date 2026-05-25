import streamlit as st
import pandas as pd
import requests
import io
import numpy as np
import yfinance as yf
import json
import os

# 1. Configuração inicial da página e CSS Suave
st.set_page_config(page_title="Filtro Mestre", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] .block-container { padding-top: 2rem !important; }
    [data-testid="stSidebar"] hr { margin: 0.5rem 0px !important; }
</style>
""", unsafe_allow_html=True)

st.title("Filtro Mestre - Ações B3")
st.write("O terminal definitivo: Filtros Precisos + Valuation + Gráficos Históricos + Fórmula Mágica.")

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

    # Garantimos que também temos o EV/EBIT e ROIC preenchidos para a Fórmula Mágica
    df = df.dropna(subset=['pl', 'pvp', 'dy', 'roe', 'liq2meses', 'cresc_rec5', 'evebit', 'roic'])
        
    return df

with st.spinner("Garimpando dados no Fundamentus..."):
    df_acoes = carregar_dados()

# Aplica favorito carregado antes dos widgets
_chaves_filtro = ['pl_min', 'pl_max', 'pvp_min', 'pvp_max', 'dy_min', 'dy_max', 'roe_min', 'roe_max', 'cresc_min', 'liq_min']
for _k in _chaves_filtro:
    if '_load_' + _k in st.session_state:
        st.session_state[_k] = st.session_state.pop('_load_' + _k)

# 3. Controles precisos na barra lateral
st.sidebar.header("Configure seus Filtros")

st.sidebar.markdown("**P/L (Preço sobre Lucro)**")
col1, col2 = st.sidebar.columns(2)
pl_min = col1.number_input("Mín", value=3.0, step=0.5, key='pl_min')
pl_max = col2.number_input("Máx", value=15.0, step=0.5, key='pl_max')

st.sidebar.markdown("**P/VP (Valor Patrimonial)**")
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

# --- FILTROS ANTI-ARMADILHA ---
st.sidebar.markdown("---")
st.sidebar.markdown("**⚙️ Filtros Estruturais**")

tipo_acao = st.sidebar.radio(
    "Tipo de Ação:",
    ["Todas", "Ordinárias (Final 3)", "Preferenciais (Final 4)"]
)
remover_units = st.sidebar.checkbox("Remover Units (11)", value=False)
remover_bdrs = st.sidebar.checkbox("Remover BDRs (32-35)", value=True)

# --- NOVA SELEÇÃO DE ESTRATÉGIA DE RANKING ---
st.sidebar.markdown("---")
estrategia_ranking = st.sidebar.selectbox(
    "🏆 Estratégia de Ranking:",
    ["Fórmula Mágica (Greenblatt)", "Método das Estrelas (Primo Rico)"]
)

# --- FILTROS FAVORITOS ---
FILTROS_FILE = "filtros_favoritos.json"

def carregar_favoritos():
    if os.path.exists(FILTROS_FILE):
        with open(FILTROS_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_favoritos(favoritos):
    with open(FILTROS_FILE, 'w') as f:
        json.dump(favoritos, f)

favoritos = carregar_favoritos()

st.sidebar.markdown("---")
st.sidebar.markdown("**⭐ Filtros Favoritos**")

def aplicar_favorito():
    nome = st.session_state.get('fav_select')
    if nome and nome != "— selecione —":
        for chave, valor in favoritos[nome].items():
            st.session_state['_load_' + chave] = valor

if favoritos:
    st.sidebar.selectbox(
        "Carregar favorito:",
        ["— selecione —"] + list(favoritos.keys()),
        key='fav_select',
        on_change=aplicar_favorito
    )

    fav_deletar = st.sidebar.selectbox("Excluir favorito:", ["— selecione —"] + list(favoritos.keys()), key='fav_delete')
    if fav_deletar != "— selecione —":
        if st.sidebar.button("🗑️ Excluir"):
            del favoritos[fav_deletar]
            salvar_favoritos(favoritos)
            st.rerun()


nome_novo = st.sidebar.text_input("Nome do favorito:", key='nome_favorito')
if st.sidebar.button("💾 Salvar filtro atual"):
    if nome_novo.strip():
        favoritos[nome_novo.strip()] = {
            'pl_min': pl_min, 'pl_max': pl_max,
            'pvp_min': pvp_min, 'pvp_max': pvp_max,
            'dy_min': dy_min, 'dy_max': dy_max,
            'roe_min': roe_min, 'roe_max': roe_max,
            'cresc_min': cresc_min, 'liq_min': liq_min,
        }
        salvar_favoritos(favoritos)
        st.sidebar.success(f"'{nome_novo}' salvo!")
        st.rerun()
    else:
        st.sidebar.warning("Digite um nome para o favorito.")

# 4. Lógica de Filtragem Base
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) & (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] >= pvp_min) & (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) & (df_acoes['dy'] <= (dy_max / 100)) &
    (df_acoes['roe'] >= (roe_min / 100)) & (df_acoes['roe'] <= (roe_max / 100)) &
    (df_acoes['cresc_rec5'] >= (cresc_min / 100)) & 
    (df_acoes['liq2meses'] >= liq_min)
].copy()

if tipo_acao == "Ordinárias (Final 3)":
    df_filtrado = df_filtrado[df_filtrado['Ticker'].str.endswith('3')]
elif tipo_acao == "Preferenciais (Final 4)":
    df_filtrado = df_filtrado[df_filtrado['Ticker'].str.endswith(('4', '5', '6'))]

if remover_units:
    df_filtrado = df_filtrado[~df_filtrado['Ticker'].str.endswith('11')]
if remover_bdrs:
    df_filtrado = df_filtrado[~df_filtrado['Ticker'].str.endswith(('32', '33', '34', '35'))]


# =====================================================================
# 4.5 CÁLCULOS DE VALUATION, ESTRELAS E FÓRMULA MÁGICA
# =====================================================================
if not df_filtrado.empty:
    # Cálculos base de preço justo (Graham e Barsi)
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

    df_filtrado['Dupla Margem'] = df_filtrado.apply(
    lambda r: "🎯 Dupla Margem!" if r['cotacao'] < r['preco_graham'] and r['cotacao'] < r['preco_barsi'] else "",
    axis=1
)

    # SELEÇÃO DO MODO DE RANKING
    if estrategia_ranking == "Método das Estrelas (Primo Rico)":
        df_filtrado['Ranking_Final'] = 0
        df_filtrado.loc[df_filtrado.nsmallest(3, 'pl').index, 'Ranking_Final'] += 1
        df_filtrado.loc[df_filtrado.nsmallest(3, 'pvp').index, 'Ranking_Final'] += 1
        df_filtrado.loc[df_filtrado.nlargest(3, 'dy').index, 'Ranking_Final'] += 1
        df_filtrado.loc[df_filtrado.nlargest(3, 'roe').index, 'Ranking_Final'] += 1
        df_filtrado.loc[df_filtrado.nlargest(3, 'cresc_rec5').index, 'Ranking_Final'] += 1
        
        # Ordenamos do maior número de estrelas para o menor
        df_filtrado = df_filtrado.sort_values(by=['Ranking_Final', 'margem_seguranca'], ascending=[False, False])
        
    else: # MODO: Fórmula Mágica de Greenblatt
        # Greenblatt ignora empresas com EBIT zerado ou negativo
        df_filtrado = df_filtrado[df_filtrado['evebit'] > 0]
        
        # Ranquear de 1 a N (Menor EV/EBIT é melhor, Maior ROIC é melhor)
        df_filtrado['rank_ev_ebit'] = df_filtrado['evebit'].rank(ascending=True)
        df_filtrado['rank_roic'] = df_filtrado['roic'].rank(ascending=False)
        
        # A pontuação final é a soma das posições no ranking
        df_filtrado['Ranking_Final'] = df_filtrado['rank_ev_ebit'] + df_filtrado['rank_roic']
        
        # Ordenamos do MENOR score somado para o MAIOR (na Fórmula Mágica, menos pontos = topo do ranking)
        df_filtrado = df_filtrado.sort_values(by=['Ranking_Final', 'margem_seguranca'], ascending=[True, False])

# =====================================================================

# 5. Exibição da Tabela
st.markdown(f"### 🎯 Ações aprovadas nos filtros: **{len(df_filtrado)}**")

# Ajustamos as colunas de exibição para incluir os motores da Fórmula Mágica (EV/EBIT e ROIC)
colunas_exibicao = ['Ticker', 'Ranking_Final', 'Dupla Margem', 'Status (Graham)', 'cotacao', 'preco_graham', 'margem_seguranca', 'preco_barsi', 'dy', 'roe', 'evebit', 'roic']
df_mostrar = df_filtrado[colunas_exibicao].copy()

if not df_mostrar.empty:
    # Formatação visual dependendo da estratégia ativa
    if estrategia_ranking == "Método das Estrelas (Primo Rico)":
        df_mostrar['Ranking_Final'] = df_mostrar['Ranking_Final'].astype(int).astype(str) + " ⭐"
        df_mostrar.rename(columns={'Ranking_Final': 'Pontos'}, inplace=True)
    else:
        df_mostrar['Ranking_Final'] = "Posição: " + df_mostrar['Ranking_Final'].astype(int).astype(str)
        df_mostrar.rename(columns={'Ranking_Final': 'Score Greenblatt'}, inplace=True)
        
    df_mostrar['margem_seguranca'] = df_mostrar['margem_seguranca'].round(1).astype(str) + "%"
    df_mostrar['dy'] = [f"{(x * 100):.2f}%" for x in df_mostrar['dy']]
    df_mostrar['roe'] = [f"{(x * 100):.2f}%" for x in df_mostrar['roe']]
    df_mostrar['roic'] = [f"{(x * 100):.2f}%" for x in df_mostrar['roic']]
    
    df_mostrar['cotacao'] = df_mostrar['cotacao'].apply(lambda x: f"R$ {x:.2f}")
    df_mostrar['preco_graham'] = df_mostrar['preco_graham'].apply(lambda x: f"R$ {x:.2f}")
    df_mostrar['preco_barsi'] = df_mostrar['preco_barsi'].apply(lambda x: f"R$ {x:.2f}")
    df_mostrar['evebit'] = df_mostrar['evebit'].round(2)

# Traduzindo os cabeçalhos das colunas
df_mostrar.columns = ['Ticker', 'Posição/Pontos', 'Dupla Margem', 'Status (Graham)', 'Cotação Atual', 'Preço Justo (Graham)', 'Margem de Segurança', 'Preço Teto (Barsi)', 'Div. Yield', 'ROE', 'ROIC', 'EV/EBIT']

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# =====================================================================
# 5.5 COMPARADOR LADO A LADO
# =====================================================================
st.markdown("---")
st.markdown("### ⚖️ Comparador de Ações")

if not df_filtrado.empty:
    tickers_comparar = st.multiselect(
        "Selecione até 3 ações para comparar:",
        options=df_filtrado['Ticker'].tolist(),
        max_selections=3
    )

    if len(tickers_comparar) >= 2:
        df_comp = df_filtrado[df_filtrado['Ticker'].isin(tickers_comparar)].set_index('Ticker')

        indicadores = {
            'Cotação Atual':      ('cotacao',         'R$',  False),
            'Preço Justo (Graham)': ('preco_graham',  'R$',  False),
            'Margem de Segurança': ('margem_seguranca','%',  True),
            'Preço Teto (Barsi)': ('preco_barsi',     'R$',  False),
            'P/L':                ('pl',               'x',  False),
            'P/VP':               ('pvp',              'x',  False),
            'Div. Yield':         ('dy',               '%',  True),
            'ROE':                ('roe',              '%',  True),
            'ROIC':               ('roic',             '%',  True),
            'EV/EBIT':            ('evebit',           'x',  False),
            'Cresc. Rec. 5a':     ('cresc_rec5',       '%',  True),
            'Liquidez 2M':        ('liq2meses',        'R$', True),
        }

        linhas = {}
        raw = {}  # valores numéricos para highlight

        for label, (col, unidade, maior_melhor) in indicadores.items():
            valores = df_comp[col]
            raw[label] = (valores, maior_melhor)

            if unidade == 'R$':
                linhas[label] = {t: f"R$ {v:.2f}" for t, v in valores.items()}
            elif unidade == '%':
                mult = 100 if valores.abs().max() <= 1 else 1
                linhas[label] = {t: f"{v * mult:.2f}%" for t, v in valores.items()}
            else:
                linhas[label] = {t: f"{v:.2f}x" for t, v in valores.items()}

        df_tabela = pd.DataFrame(linhas).T
        df_tabela.index.name = "Indicador"

        # Highlight do melhor valor por linha
        def highlight_melhor(row):
            label = row.name
            valores_num, maior_melhor = raw[label]
            melhor_ticker = valores_num.idxmax() if maior_melhor else valores_num.idxmin()
            return ['background-color: #1a472a; color: white; font-weight: bold'
                    if col == melhor_ticker else '' for col in row.index]

        st.dataframe(
            df_tabela.style.apply(highlight_melhor, axis=1),
            use_container_width=True
        )
    elif len(tickers_comparar) == 1:
        st.info("Selecione pelo menos 2 ações para comparar.")
else:
    st.info("Ajuste os filtros para liberar o comparador.")

# =====================================================================
# 5.6 SIMULADOR DE CARTEIRA
# =====================================================================
st.markdown("---")
st.markdown("### 💼 Simulador de Carteira")

if not df_filtrado.empty:
    col_val, col_top = st.columns([2, 1])
    valor_investir = col_val.number_input("💰 Valor a investir (R$)", min_value=100.0, value=1000.0, step=100.0)
    top_n = col_top.number_input("Nº de ações", min_value=1, max_value=min(10, len(df_filtrado)), value=min(5, len(df_filtrado)), step=1)

    tickers_sim = st.multiselect(
        "Ou escolha manualmente as ações (deixe vazio para usar o Top N do ranking):",
        options=df_filtrado['Ticker'].tolist()
    )

    df_sim = df_filtrado[df_filtrado['Ticker'].isin(tickers_sim)] if tickers_sim else df_filtrado.head(int(top_n))
    df_sim = df_sim[['Ticker', 'cotacao', 'dy', 'Ranking_Final']].copy()

    # Peso proporcional ao ranking (invertido: menor rank = maior peso na Fórmula Mágica)
    if estrategia_ranking == "Fórmula Mágica (Greenblatt)":
        rank_max = df_sim['Ranking_Final'].max()
        df_sim['peso'] = (rank_max + 1 - df_sim['Ranking_Final'])
    else:
        df_sim['peso'] = df_sim['Ranking_Final']

    df_sim['peso'] = df_sim['peso'] / df_sim['peso'].sum()
    df_sim['valor_alocado'] = df_sim['peso'] * valor_investir
    df_sim['cotas'] = (df_sim['valor_alocado'] / df_sim['cotacao']).apply(np.floor)
    df_sim['valor_real'] = df_sim['cotas'] * df_sim['cotacao']
    df_sim['dividendos_ano'] = df_sim['valor_real'] * df_sim['dy']

    total_investido = df_sim['valor_real'].sum()
    troco = valor_investir - total_investido
    dy_carteira = df_sim['dividendos_ano'].sum() / total_investido if total_investido > 0 else 0

    # Métricas resumo
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Investido", f"R$ {total_investido:,.2f}")
    m2.metric("Troco (sobra)", f"R$ {troco:,.2f}")
    m3.metric("Dividendos/Ano Est.", f"R$ {df_sim['dividendos_ano'].sum():,.2f}")
    m4.metric("DY Médio Carteira", f"{dy_carteira * 100:.2f}%")

    # Tabela detalhada
    df_exibir = df_sim[['Ticker', 'cotas', 'cotacao', 'valor_real', 'peso', 'dividendos_ano']].copy()
    df_exibir['cotas'] = df_exibir['cotas'].astype(int)
    df_exibir['cotacao'] = df_exibir['cotacao'].apply(lambda x: f"R$ {x:.2f}")
    df_exibir['valor_real'] = df_exibir['valor_real'].apply(lambda x: f"R$ {x:,.2f}")
    df_exibir['peso'] = df_exibir['peso'].apply(lambda x: f"{x * 100:.1f}%")
    df_exibir['dividendos_ano'] = df_exibir['dividendos_ano'].apply(lambda x: f"R$ {x:,.2f}")
    df_exibir.columns = ['Ticker', 'Cotas', 'Cotação', 'Valor Alocado', 'Peso', 'Dividendos/Ano Est.']

    st.dataframe(df_exibir, use_container_width=True, hide_index=True)
else:
    st.info("Ajuste os filtros para liberar o simulador.")


# =====================================================================
# 6. GRÁFICOS HISTÓRICOS (Yahoo Finance)
# =====================================================================
st.markdown("---")
st.markdown("### 📈 Análise Histórica")

if not df_filtrado.empty:
    acao_escolhida = st.selectbox("Selecione uma ação para ver o histórico:", df_filtrado['Ticker'].tolist(), key='selectbox_historico')

    if acao_escolhida:
        ticker_yf = acao_escolhida + ".SA"
        with st.spinner(f"Baixando dados de {acao_escolhida}..."):
            t = yf.Ticker(ticker_yf)
            dados_historicos = t.history(period="5y")
            dividendos = t.dividends

        aba_preco, aba_div, aba_consist = st.tabs(["📈 Preço (5 Anos)", "💰 Histórico de Dividendos", "📊 Consistência"])

        with aba_preco:
            if not dados_historicos.empty:
                df_preco = dados_historicos[['Close']].copy()
                df_preco['MM50'] = df_preco['Close'].rolling(50).mean()
                df_preco['MM200'] = df_preco['Close'].rolling(200).mean()

                st.line_chart(df_preco[['Close', 'MM50', 'MM200']])

                mm50_atual = df_preco['MM50'].iloc[-1]
                mm200_atual = df_preco['MM200'].iloc[-1]

                if mm50_atual > mm200_atual:
                    sinal = "🟢 Golden Cross — MM50 acima da MM200 (tendência de alta)"
                else:
                    sinal = "🔴 Death Cross — MM50 abaixo da MM200 (tendência de baixa)"

                st.info(sinal)

                preco_atual = df_preco['Close'].iloc[-1]
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
                c2.metric("Máxima (5 anos)", f"R$ {df_preco['Close'].max():.2f}")
                c3.metric("Mínima (5 anos)", f"R$ {df_preco['Close'].min():.2f}")
                c4.metric("MM50", f"R$ {mm50_atual:.2f}")
                c5.metric("MM200", f"R$ {mm200_atual:.2f}")
            else:
                st.warning(f"Sem dados de preço para {acao_escolhida}.")

        with aba_div:
            if not dividendos.empty:
                dividendos.index = dividendos.index.tz_localize(None)
                div_anual = dividendos.resample('YE').sum()
                div_anual.index = div_anual.index.year

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Último Ano", f"R$ {div_anual.iloc[-1]:.2f}")
                c2.metric("Média Anual (5a)", f"R$ {div_anual.tail(5).mean():.2f}")
                c3.metric("Pagamentos Históricos", str(len(dividendos)))

                st.bar_chart(div_anual)

                div_tabela = dividendos.reset_index()
                div_tabela.columns = ['Data', 'Valor (R$)']
                div_tabela['Data'] = div_tabela['Data'].dt.strftime('%d/%m/%Y')
                div_tabela['Valor (R$)'] = div_tabela['Valor (R$)'].apply(lambda x: f"R$ {x:.4f}")
                st.dataframe(div_tabela.sort_values('Data', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.warning(f"Sem histórico de dividendos para {acao_escolhida}.")

        with aba_consist:
            with st.spinner("Analisando consistência histórica..."):
                info = t.financials
                div_hist = t.dividends

            pontos = 0
            max_pontos = 0
            linhas_consist = []

            if not info.empty and 'Net Income' in info.index:
                lucros = info.loc['Net Income'].sort_index()
                anos = lucros.index.year.tolist()

                for i, (ano, lucro) in enumerate(zip(anos, lucros)):
                    max_pontos += 3
                    pts_ano = 0

                    if lucro > 0:
                        pts_ano += 2

                    if not div_hist.empty:
                        div_hist_local = div_hist.copy()
                        div_hist_local.index = div_hist_local.index.tz_localize(None)
                        pagou_div = div_hist_local[div_hist_local.index.year == ano].sum() > 0
                        if pagou_div:
                            pts_ano += 1

                    pontos += pts_ano
                    linhas_consist.append({
                        'Ano': str(ano),
                        'Lucro Líquido': f"R$ {lucro/1e6:.1f}M" if abs(lucro) >= 1e6 else f"R$ {lucro:.0f}",
                        'Lucro Positivo': "✅" if lucro > 0 else "❌",
                        'Pagou Dividendo': "✅" if (not div_hist.empty and div_hist_local[div_hist_local.index.year == ano].sum() > 0) else "❌",
                        'Pontos': f"{pts_ano}/3"
                    })

            if max_pontos > 0:
                pct = pontos / max_pontos * 100
                if pct >= 80:
                    conceito = "🟢 Alta Consistência"
                elif pct >= 50:
                    conceito = "🟡 Consistência Moderada"
                else:
                    conceito = "🔴 Baixa Consistência"

                c1, c2 = st.columns(2)
                c1.metric("Score de Consistência", f"{pontos}/{max_pontos} pts")
                c2.metric("Conceito", conceito)

                st.dataframe(pd.DataFrame(linhas_consist), use_container_width=True, hide_index=True)
            else:
                st.warning("Dados históricos insuficientes para calcular o score.")
else:
    st.info("Ajuste os filtros na barra lateral para encontrar ações e desbloquear os gráficos.")
