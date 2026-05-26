import numpy as np


def calcular_valuation(df):
    df = df.copy()
    df['lpa'] = df['cotacao'] / df['pl']
    df['vpa'] = df['cotacao'] / df['pvp']
    df['preco_graham'] = np.sqrt(np.maximum(22.5 * df['lpa'] * df['vpa'], 0))
    df['margem_seguranca'] = ((df['preco_graham'] - df['cotacao']) / df['preco_graham']) * 100
    df['proventos_por_acao'] = df['cotacao'] * df['dy']
    df['preco_barsi'] = df['proventos_por_acao'] / 0.06

    df['Status (Graham)'] = [
        "🟢 Descontada" if m > 15 else ("🟡 Preço Justo" if m >= 0 else "🔴 Esticada")
        for m in df['margem_seguranca']
    ]
    df['Dupla Margem'] = df.apply(
        lambda r: "🎯 Dupla Margem!" if r['cotacao'] < r['preco_graham'] and r['cotacao'] < r['preco_barsi'] else "", axis=1
    )
    return df


def calcular_ranking(df, estrategia):
    df = df.copy()
    if estrategia == "Método das Estrelas (Primo Rico)":
        df['Ranking_Final'] = 0
        for col, asc in [('pl', True), ('pvp', True), ('dy', False), ('roe', False), ('cresc_rec5', False)]:
            fn = df.nsmallest if asc else df.nlargest
            df.loc[fn(3, col).index, 'Ranking_Final'] += 1
        df = df.sort_values(['Ranking_Final', 'margem_seguranca'], ascending=[False, False])
    else:
        df = df[df['evebit'] > 0]
        df['rank_ev_ebit'] = df['evebit'].rank(ascending=True)
        df['rank_roic'] = df['roic'].rank(ascending=False)
        df['Ranking_Final'] = df['rank_ev_ebit'] + df['rank_roic']
        df = df.sort_values(['Ranking_Final', 'margem_seguranca'], ascending=[True, False])
    return df
