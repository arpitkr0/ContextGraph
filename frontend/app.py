import os
import requests
import streamlit as st

from frontend.tabs.source_panel import render_source_panel
from frontend.tabs.chat_tab import render_chat_tab
from frontend.tabs.explore_tab import render_explore_tab


API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def api(method: str, path: str, **kwargs):
    response = requests.request(method, f"{API_BASE}{path}", timeout=20, **kwargs)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="ContextGraph", layout="wide")
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)
st.title("ContextGraph")

with st.sidebar:
    render_source_panel(api)

chat_tab, explore_tab = st.tabs(["Chat + Ask", "Explore Graph"])

with chat_tab:
    render_chat_tab(api)

with explore_tab:
    render_explore_tab(api)
