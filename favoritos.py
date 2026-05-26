import json
import os
import streamlit as st

FILTROS_FILE = "filtros_favoritos.json"


def carregar_favoritos():
    if os.path.exists(FILTROS_FILE):
        with open(FILTROS_FILE, 'r') as f:
            return json.load(f)
    return {}


def salvar_favoritos(favoritos):
    with open(FILTROS_FILE, 'w') as f:
        json.dump(favoritos, f)


def render_favoritos(favoritos, valores_atuais):
    def aplicar_favorito():
        nome = st.session_state.get('fav_select')
        if nome and nome != "—":
            for chave, valor in favoritos[nome].items():
                st.session_state['_load_' + chave] = valor

    if favoritos:
        st.sidebar.selectbox("⭐", ["—"] + list(favoritos.keys()), key='fav_select', on_change=aplicar_favorito)

    c1, c2, c3 = st.sidebar.columns([3, 1, 1])
    nome_novo = c1.text_input("", placeholder="Salvar filtro...", key='nome_favorito', label_visibility='collapsed')
    if c2.button("💾", use_container_width=True):
        if nome_novo.strip():
            favoritos[nome_novo.strip()] = valores_atuais
            salvar_favoritos(favoritos)
            st.rerun()
        else:
            st.sidebar.warning("Digite um nome.")

    fav_deletar = st.sidebar.selectbox("", ["— excluir —"] + list(favoritos.keys()), key='fav_delete', label_visibility='collapsed') if favoritos else "— excluir —"
    if favoritos and fav_deletar != "— excluir —":
        if c3.button("🗑️", use_container_width=True):
            del favoritos[fav_deletar]
            salvar_favoritos(favoritos)
            st.rerun()
