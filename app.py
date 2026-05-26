import streamlit as st
import pandas as pd
import numpy as np
from dados import carregar_dados, carregar_historico
from calculos import calcular_valuation, calcular_ranking
from favoritos import carregar_favoritos, render_favoritos

# 1. Configuração inicial da página e CSS Suave
st.set_page_config(page_title="Filtro Mestre", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] .block-container { padding-top: 2rem !important; }
    [data-testid="stSidebar"] hr { margin: 0.5rem 0px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 📊 Filtro Mestre — Ações B3")

# 2. Funções em dados.py, calculos.py e favoritos.py

with st.spinner("Garimpando dados no Fundamentus..."):
    df_acoes, erro = carregar_dados()

if erro:
    st.error(erro)
    st.stop()

st.caption(f"🕐 Dados carregados às {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
    
# Aplica favorito carregado antes dos widgets
_chaves_filtro = ['pl_min', 'pl_max', 'pvp_min', 'pvp_max', 'dy_min', 'dy_max', 'roe_min', 'roe_max', 'cresc_min', 'liq_min']
for _k in _chaves_filtro:
    if '_load_' + _k in st.session_state:
        st.session_state[_k] = st.session_state.pop('_load_' + _k)
# 3. Sidebar compacta
st.sidebar.header("🔍 Filtros")

c1, c2 = st.sidebar.columns(2)
pl_min    = c1.number_input("P/L Mín",    value=3.0,  step=0.5, key='pl_min')
pl_max    = c2.number_input("P/L Máx",    value=15.0, step=0.5, key='pl_max')
pvp_min   = c1.number_input("P/VP Mín",   value=0.5,  step=0.1, key='pvp_min')
pvp_max   = c2.number_input("P/VP Máx",   value=3.0,  step=0.1, key='pvp_max')
dy_min    = c1.number_input("DY% Mín",    value=5.0,  step=0.5, key='dy_min')
dy_max    = c2.number_input("DY% Máx",    value=14.0, step=0.5, key='dy_max')
roe_min   = c1.number_input("ROE% Mín",   value=10.0, step=1.0, key='roe_min')
roe_max   = c2.number_input("ROE% Máx",   value=30.0, step=1.0, key='roe_max')
cresc_min = c1.number_input("Cresc% Mín", value=5.0,  step=1.0, key='cresc_min')
liq_min   = c2.number_input("Liq Mín(M)", value=1.0,  step=0.5, key='liq_min', help="Liquidez 2 meses em milhões de R$")

c1, c2, c3 = st.sidebar.columns(3)
remover_units = c1.checkbox("- Units", value=False)
remover_bdrs  = c2.checkbox("- BDRs",  value=True)

tipo_map = {"Todas": "Todas", "ON": "Ordinárias (Final 3)", "PN": "Preferenciais (Final 4)"}
tipo_acao = tipo_map[c3.selectbox("Tipo", list(tipo_map.keys()), key='tipo_acao', label_visibility='collapsed')]

rank_map = {"🧮 Greenblatt": "Fórmula Mágica (Greenblatt)", "⭐ Estrelas (Rico)": "Método das Estrelas (Primo Rico)"}
estrategia_ranking = rank_map[st.sidebar.selectbox("Método", list(rank_map.keys()), key='ranking')]

# --- FAVORITOS ---
favoritos = carregar_favoritos()
render_favoritos(favoritos, {
    'pl_min': pl_min, 'pl_max': pl_max, 'pvp_min': pvp_min, 'pvp_max': pvp_max,
    'dy_min': dy_min, 'dy_max': dy_max, 'roe_min': roe_min, 'roe_max': roe_max,
    'cresc_min': cresc_min, 'liq_min': liq_min,
})



# 4. Lógica de Filtragem Base
df_filtrado = df_acoes[
    (df_acoes['pl'] >= pl_min) & (df_acoes['pl'] <= pl_max) &
    (df_acoes['pvp'] >= pvp_min) & (df_acoes['pvp'] <= pvp_max) &
    (df_acoes['dy'] >= (dy_min / 100)) & (df_acoes['dy'] <= (dy_max / 100)) &
    (df_acoes['roe'] >= (roe_min / 100)) & (df_acoes['roe'] <= (roe_max / 100)) &
    (df_acoes['cresc_rec5'] >= (cresc_min / 100)) &
    (df_acoes['liq2meses'] >= liq_min * 1_000_000)
].copy()

if tipo_acao == "Ordinárias (Final 3)":
    df_filtrado = df_filtrado[df_filtrado['Ticker'].str.endswith('3')]
elif tipo_acao == "Preferenciais (Final 4)":
    df_filtrado = df_filtrado[df_filtrado['Ticker'].str.endswith(('4', '5', '6'))]
if remover_units:
    df_filtrado = df_filtrado[~df_filtrado['Ticker'].str.endswith('11')]
if remover_bdrs:
    df_filtrado = df_filtrado[~df_filtrado['Ticker'].str.endswith(('32', '33', '34', '35'))]

# 4.5 Cálculos de Valuation e Ranking
if not df_filtrado.empty:
    df_filtrado = calcular_valuation(df_filtrado)
    df_filtrado = calcular_ranking(df_filtrado, estrategia_ranking)

# 5. Abas principais
st.markdown(f"**🎯 {len(df_filtrado)} ações aprovadas nos filtros**")
aba_res, aba_comp, aba_sim, aba_hist = st.tabs(["🎯 Resultados", "⚖️ Comparador", "💼 Simulador", "📈 Análise"])

# ── ABA RESULTADOS ──────────────────────────────────────────────────
with aba_res:
    colunas_exibicao = ['Ticker', 'Ranking_Final', 'Dupla Margem', 'Status (Graham)', 'cotacao', 'preco_graham', 'margem_seguranca', 'preco_barsi', 'dy', 'roe', 'roic', 'evebit']
    df_mostrar = df_filtrado[colunas_exibicao].copy() if not df_filtrado.empty else pd.DataFrame(columns=colunas_exibicao)

    if not df_mostrar.empty:
        if estrategia_ranking == "Método das Estrelas (Primo Rico)":
            df_mostrar['Ranking_Final'] = df_mostrar['Ranking_Final'].astype(int).astype(str) + " ⭐"
            df_mostrar.rename(columns={'Ranking_Final': 'Pontos'}, inplace=True)
        else:
            df_mostrar['Ranking_Final'] = "Posição: " + df_mostrar['Ranking_Final'].astype(int).astype(str)
            df_mostrar.rename(columns={'Ranking_Final': 'Score Greenblatt'}, inplace=True)

        df_mostrar['margem_seguranca'] = df_mostrar['margem_seguranca'].round(1).astype(str) + "%"
        df_mostrar['dy']   = [f"{x*100:.2f}%" for x in df_mostrar['dy']]
        df_mostrar['roe']  = [f"{x*100:.2f}%" for x in df_mostrar['roe']]
        df_mostrar['roic'] = [f"{x*100:.2f}%" for x in df_mostrar['roic']]
        df_mostrar['cotacao']      = df_mostrar['cotacao'].apply(lambda x: f"R$ {x:.2f}")
        df_mostrar['preco_graham'] = df_mostrar['preco_graham'].apply(lambda x: f"R$ {x:.2f}")
        df_mostrar['preco_barsi']  = df_mostrar['preco_barsi'].apply(lambda x: f"R$ {x:.2f}")
        df_mostrar['evebit']       = df_mostrar['evebit'].round(2)
        df_mostrar.columns = ['Ticker', 'Posição/Pontos', 'Dupla Margem', 'Status (Graham)', 'Cotação Atual', 'Preço Justo (Graham)', 'Margem de Segurança', 'Preço Teto (Barsi)', 'Div. Yield', 'ROE', 'ROIC', 'EV/EBIT']
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        csv = df_mostrar.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button("📥 Exportar CSV", data=csv, file_name='Filtro_Mestre_Acoes.csv', mime='text/csv')
    else:
        st.info("Nenhuma ação encontrada com os filtros atuais.")

# ── ABA COMPARADOR ──────────────────────────────────────────────────
with aba_comp:
    if not df_filtrado.empty:
        tickers_comparar = st.multiselect("Selecione até 3 ações:", options=df_filtrado['Ticker'].tolist(), max_selections=3)
        if len(tickers_comparar) >= 2:
            df_comp = df_filtrado[df_filtrado['Ticker'].isin(tickers_comparar)].set_index('Ticker')
            indicadores = {
                'Cotação Atual':        ('cotacao',          'R$', False),
                'Preço Justo (Graham)': ('preco_graham',     'R$', False),
                'Margem de Segurança':  ('margem_seguranca', '%',  True),
                'Preço Teto (Barsi)':   ('preco_barsi',      'R$', False),
                'P/L':                  ('pl',               'x',  False),
                'P/VP':                 ('pvp',              'x',  False),
                'Div. Yield':           ('dy',               '%',  True),
                'ROE':                  ('roe',              '%',  True),
                'ROIC':                 ('roic',             '%',  True),
                'EV/EBIT':              ('evebit',           'x',  False),
                'Cresc. Rec. 5a':       ('cresc_rec5',       '%',  True),
                'Liquidez 2M':          ('liq2meses',        'R$', True),
            }
            linhas, raw = {}, {}
            for label, (col, unidade, maior_melhor) in indicadores.items():
                valores = df_comp[col]
                raw[label] = (valores, maior_melhor)
                if unidade == 'R$':
                    linhas[label] = {t: f"R$ {v:.2f}" for t, v in valores.items()}
                elif unidade == '%':
                    mult = 100 if valores.abs().max() <= 1 else 1
                    linhas[label] = {t: f"{v*mult:.2f}%" for t, v in valores.items()}
                else:
                    linhas[label] = {t: f"{v:.2f}x" for t, v in valores.items()}

            df_tabela = pd.DataFrame(linhas).T
            df_tabela.index.name = "Indicador"

            def highlight_melhor(row):
                valores_num, maior_melhor = raw[row.name]
                melhor = valores_num.idxmax() if maior_melhor else valores_num.idxmin()
                return ['background-color: #1a472a; color: white; font-weight: bold' if c == melhor else '' for c in row.index]

            st.dataframe(df_tabela.style.apply(highlight_melhor, axis=1), use_container_width=True)
        elif len(tickers_comparar) == 1:
            st.info("Selecione pelo menos 2 ações.")
    else:
        st.info("Ajuste os filtros para liberar o comparador.")

# ── ABA SIMULADOR ───────────────────────────────────────────────────
with aba_sim:
    if not df_filtrado.empty:
        col_val, col_top = st.columns([2, 1])
        valor_investir = col_val.number_input("💰 Valor a investir (R$)", min_value=100.0, value=1000.0, step=100.0)
        top_n = col_top.number_input("Nº de ações", min_value=1, max_value=min(10, len(df_filtrado)), value=min(5, len(df_filtrado)), step=1)
        tickers_sim = st.multiselect("Escolha manualmente (vazio = Top N do ranking):", options=df_filtrado['Ticker'].tolist())

        df_sim = df_filtrado[df_filtrado['Ticker'].isin(tickers_sim)].copy() if tickers_sim else df_filtrado.head(int(top_n)).copy()
        df_sim = df_sim[['Ticker', 'cotacao', 'dy', 'Ranking_Final']].copy()

        if estrategia_ranking == "Fórmula Mágica (Greenblatt)":
            rank_max = df_sim['Ranking_Final'].max()
            df_sim['peso'] = rank_max + 1 - df_sim['Ranking_Final']
        else:
            df_sim['peso'] = df_sim['Ranking_Final']

        df_sim['peso']          = df_sim['peso'] / df_sim['peso'].sum()
        df_sim['valor_alocado'] = df_sim['peso'] * valor_investir
        df_sim['cotas']         = (df_sim['valor_alocado'] / df_sim['cotacao']).apply(np.floor)
        df_sim['valor_real']    = df_sim['cotas'] * df_sim['cotacao']
        df_sim['dividendos_ano']= df_sim['valor_real'] * df_sim['dy']

        total_investido = df_sim['valor_real'].sum()
        troco = valor_investir - total_investido
        dy_carteira = df_sim['dividendos_ano'].sum() / total_investido if total_investido > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Investido",     f"R$ {total_investido:,.2f}")
        m2.metric("Troco (sobra)",        f"R$ {troco:,.2f}")
        m3.metric("Dividendos/Ano Est.", f"R$ {df_sim['dividendos_ano'].sum():,.2f}")
        m4.metric("DY Médio Carteira",   f"{dy_carteira*100:.2f}%")

        df_exibir = df_sim[['Ticker', 'cotas', 'cotacao', 'valor_real', 'peso', 'dividendos_ano']].copy()
        df_exibir['cotas']          = df_exibir['cotas'].astype(int)
        df_exibir['cotacao']        = df_exibir['cotacao'].apply(lambda x: f"R$ {x:.2f}")
        df_exibir['valor_real']     = df_exibir['valor_real'].apply(lambda x: f"R$ {x:,.2f}")
        df_exibir['peso']           = df_exibir['peso'].apply(lambda x: f"{x*100:.1f}%")
        df_exibir['dividendos_ano'] = df_exibir['dividendos_ano'].apply(lambda x: f"R$ {x:,.2f}")
        df_exibir.columns = ['Ticker', 'Cotas', 'Cotação', 'Valor Alocado', 'Peso', 'Dividendos/Ano Est.']
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.info("Ajuste os filtros para liberar o simulador.")

# ── ABA ANÁLISE HISTÓRICA ───────────────────────────────────────────
with aba_hist:
    if not df_filtrado.empty:
        acao_escolhida = st.selectbox("Selecione uma ação:", df_filtrado['Ticker'].tolist(), key='selectbox_historico')
        if acao_escolhida:
            with st.spinner(f"Baixando dados de {acao_escolhida}..."):
                dados_historicos, dividendos, financials_cache = carregar_historico(acao_escolhida)

            sub_preco, sub_div, sub_consist = st.tabs(["📈 Preço", "💰 Dividendos", "📊 Consistência"])


            with sub_preco:
                if not dados_historicos.empty:
                    df_preco = dados_historicos[['Close']].copy()
                    df_preco['MM50']  = df_preco['Close'].rolling(50).mean()
                    df_preco['MM200'] = df_preco['Close'].rolling(200).mean()
                    st.line_chart(df_preco[['Close', 'MM50', 'MM200']])
                    mm50, mm200 = df_preco['MM50'].iloc[-1], df_preco['MM200'].iloc[-1]
                    st.info("🟢 Golden Cross — tendência de alta" if mm50 > mm200 else "🔴 Death Cross — tendência de baixa")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Preço Atual",     f"R$ {df_preco['Close'].iloc[-1]:.2f}")
                    c2.metric("Máxima (5a)",     f"R$ {df_preco['Close'].max():.2f}")
                    c3.metric("Mínima (5a)",     f"R$ {df_preco['Close'].min():.2f}")
                    c4.metric("MM50",            f"R$ {mm50:.2f}")
                    c5.metric("MM200",           f"R$ {mm200:.2f}")
                else:
                    st.warning("Sem dados de preço.")

            with sub_div:
                if not dividendos.empty:
                    dividendos.index = dividendos.index.tz_localize(None)
                    div_anual = dividendos.resample('YE').sum()
                    div_anual.index = div_anual.index.year
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Último Ano",      f"R$ {div_anual.iloc[-1]:.2f}")
                    c2.metric("Média Anual (5a)",      f"R$ {div_anual.tail(5).mean():.2f}")
                    c3.metric("Pagamentos Históricos", str(len(dividendos)))
                    st.bar_chart(div_anual)
                    div_tab = dividendos.reset_index()
                    div_tab.columns = ['Data', 'Valor (R$)']
                    div_tab['Data'] = div_tab['Data'].dt.strftime('%d/%m/%Y')
                    div_tab['Valor (R$)'] = div_tab['Valor (R$)'].apply(lambda x: f"R$ {x:.4f}")
                    st.dataframe(div_tab.sort_values('Data', ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.warning("Sem histórico de dividendos.")

            with sub_consist:
                info = financials_cache
                div_hist = dividendos

                pontos, max_pontos, linhas_consist = 0, 0, []

                if not info.empty and 'Net Income' in info.index:
                    lucros = info.loc['Net Income'].sort_index()
                    for ano, lucro in zip(lucros.index.year, lucros):
                        max_pontos += 3
                        pts_ano = 2 if lucro > 0 else 0
                        div_hist_local = div_hist.copy()
                        if not div_hist.empty:
                            div_hist_local.index = div_hist_local.index.tz_localize(None)
                            if div_hist_local[div_hist_local.index.year == ano].sum() > 0:
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
                    conceito = "🟢 Alta Consistência" if pct >= 80 else ("🟡 Consistência Moderada" if pct >= 50 else "🔴 Baixa Consistência")
                    c1, c2 = st.columns(2)
                    c1.metric("Score", f"{pontos}/{max_pontos} pts")
                    c2.metric("Conceito", conceito)
                    st.dataframe(pd.DataFrame(linhas_consist), use_container_width=True, hide_index=True)
                else:
                    st.warning("Dados históricos insuficientes.")
    else:
        st.info("Ajuste os filtros para liberar a análise.")
