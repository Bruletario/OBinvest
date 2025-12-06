import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from bcb import Expectativas
import warnings
import time
import requests # Necessário para "enganar" o servidor do BC

# ==============================================================================
# 1. SETUP E ESTILIZACAO
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Mercado",
    layout="wide",
    initial_sidebar_state="expanded"
)
warnings.filterwarnings("ignore")

C_SIDEBAR = "#0F172A"
C_MAIN = "#F8FAFC"
C_ACCENT = "#F97316"
C_TEXT_MAIN = "#1E293B"
C_TEXT_SIDE = "#FFFFFF"
C_INPUT_BG = "#1E293B"
C_SELIC = "#334155"
C_IPCA = "#D97706"
C_REAL = "#059669"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {C_MAIN};
        color: {C_TEXT_MAIN};
    }}
    header {{ background-color: transparent !important; }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100%;
    }}
    #MainMenu, footer {{ visibility: hidden; }}
    section[data-testid="stSidebar"] {{
        background-color: {C_SIDEBAR};
        border-right: 1px solid #1E293B;
    }}
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] div {{
        color: {C_TEXT_SIDE} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 12px 16px !important;
        margin-bottom: 4px !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        transition: all 0.2s ease;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        background-color: transparent;
        border: 1px solid transparent;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: white !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {C_ACCENT} !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 6px;
    }}
    .stDateInput svg {{ fill: white !important; }}
    section[data-testid="stSidebar"] button {{
        background-color: {C_ACCENT} !important;
        color: white !important;
        border: none !important;
        font-weight: 600;
        margin-top: 10px;
        transition: 0.2s;
    }}
    section[data-testid="stSidebar"] button:hover {{
        background-color: #EA580C !important;
    }}
    div[data-testid="stHorizontalBlock"] button {{
        background-color: #FFFFFF !important;
        color: {C_TEXT_MAIN} !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    div[data-testid="stHorizontalBlock"] button:hover {{
        border-color: {C_ACCENT} !important;
        color: {C_ACCENT} !important;
    }}
    .metric-card {{
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .metric-label {{ font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 800; color: {C_TEXT_MAIN}; line-height: 1; margin-bottom: 8px; }}
    .metric-sub {{ font-size: 0.85rem; color: #64748B; font-weight: 500; }}
    .glossary-card {{
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        height: 100%;
        transition: transform 0.2s;
    }}
    .glossary-card:hover {{ border-color: {C_ACCENT}; }}
    .gloss-title {{ font-size: 1rem; font-weight: 700; color: {C_TEXT_MAIN}; margin-bottom: 8px; }}
    .gloss-text {{ font-size: 0.9rem; color: #475569; line-height: 1.5; }}
    h1 {{ font-weight: 800; color: {C_TEXT_MAIN}; margin: 0; padding: 0; font-size: 2rem; letter-spacing: -0.5px; }}
    h3 {{ color: {C_TEXT_MAIN}; font-weight: 700; margin-top: 20px; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNCOES DE DADOS (ROBUSTAS)
# ==============================================================================

# Função auxiliar para pegar JSON do BC com Header de navegador
def fetch_bcb_direct(code, name):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Garante que deu 200 OK
        df = pd.DataFrame(response.json())
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'])
        df = df.set_index('data')
        df.columns = [name]
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    # Tenta conectar via requisição direta com User-Agent
    try:
        hoje = datetime.today()
        start_filter = (hoje - timedelta(days=365*10))
        
        # Busca Selic (432) e IPCA (13522) separadamente
        df_selic = fetch_bcb_direct(432, "Selic")
        df_ipca = fetch_bcb_direct(13522, "IPCA")
        
        if df_selic is not None and df_ipca is not None:
            # Junta os dois
            df = df_selic.join(df_ipca, how='inner')
            # Filtra data
            df = df[df.index >= start_filter]
            return df.ffill().dropna()
    except:
        pass
    
    # Se falhar tudo, retorna vazio (sem dados falsos)
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_focus():
    try:
        em = Expectativas()
        ep = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        dt_lim = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        df = (ep.query().filter(ep.Data >= dt_lim).filter(ep.Suavizada == 'S').filter(ep.baseCalculo == 0).collect())
        return 4.5 if df.empty else float(df.sort_values('Data').iloc[-1]['Mediana'])
    except: return 4.5

# ==============================================================================
# 3. INTERFACE
# ==============================================================================
df = get_data()
ipca_proj = get_focus()

if df.empty:
    st.error("Erro de conexão com o Banco Central. O servidor recusou a conexão.")
    if st.button("Tentar Novamente"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

with st.sidebar:
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.2rem; margin-bottom:20px; padding-left:5px;'>MONITOR</div>", unsafe_allow_html=True)
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"], label_visibility="collapsed")
    st.markdown("<div style='margin-top:20px; border-top:1px solid #1E293B'></div>", unsafe_allow_html=True)
    
    df_filtered = df.copy()
    
    if nav == "Dashboard":
        with st.form("f_filtros"):
            st.markdown("**Período do Gráfico**")
            d_max = df.index.max().date()
            d_min = df.index.min().date()
            start_def = d_max - timedelta(days=730)
            if start_def < d_min: start_def = d_min
            
            d_ini = st.date_input("Início", start_def, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
            d_fim = st.date_input("Fim", d_max, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
            st.markdown("###")
            st.form_submit_button("ATUALIZAR GRÁFICO")
        
        mask = (df.index.date >= d_ini) & (df.index.date <= d_fim)
        df_filtered = df.loc[mask]

# --- DASHBOARD ---
if nav == "Dashboard":
    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("###")

    if df_filtered.empty:
        st.warning("Sem dados para o período.")
        st.stop()

    last = df_filtered.iloc[-1]
    v_selic, v_ipca = last["Selic"], last["IPCA"]
    v_real = ((1 + v_selic/100) / (1 + v_ipca/100) - 1) * 100
    ref = df_filtered.index[-1].strftime('%d/%m/%Y')

    c1, c2, c3 = st.
