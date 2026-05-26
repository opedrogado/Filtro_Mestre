import pandas as pd
import requests
import io
import yfinance as yf
import streamlit as st


@st.cache_data(ttl="4h")
def carregar_dados():
    try:
        url = 'https://www.fundamentus.com.br/resultado.php'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        df = pd.read_html(io.StringIO(r.text), decimal=',', thousands='.', na_values=['-', ' - '])[0]

        df.columns = [
            'Ticker', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pativo', 'pcapgiro',
            'pebit', 'pativcircliq', 'evebit', 'evebitda', 'mrgbruta', 'mrgebit',
            'mrgliq', 'liqcorr', 'roic', 'roe', 'liq2meses', 'patrimliq', 'divLpatrim', 'cresc_rec5'
        ]

        for col in ['dy', 'mrgbruta', 'mrgebit', 'mrgliq', 'roic', 'roe', 'cresc_rec5']:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce') / 100

        for col in ['pl', 'pvp', 'divLpatrim', 'cotacao', 'evebit', 'liq2meses']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=['pl', 'pvp', 'dy', 'roe', 'liq2meses', 'cresc_rec5', 'evebit', 'roic'])
        return df, None

    except requests.exceptions.ConnectionError:
        return None, "❌ Sem conexão com a internet. Verifique sua rede."
    except requests.exceptions.Timeout:
        return None, "⏱️ O site do Fundamentus demorou demais para responder. Tente novamente."
    except requests.exceptions.HTTPError as e:
        return None, f"❌ Erro HTTP ao acessar o Fundamentus: {e}"
    except Exception as e:
        return None, f"❌ Erro inesperado: {e}"


@st.cache_data(ttl="30m")
def carregar_historico(ticker):
    t = yf.Ticker(ticker + ".SA")
    return t.history(period="5y"), t.dividends, t.financials
