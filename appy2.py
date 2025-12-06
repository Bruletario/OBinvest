import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from bcb import sgs, Expectativas # Voltamos a usar o sgs da biblioteca
import warnings
import time
# Remover import requests (simplifica o ambiente)

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
# 2. FUNCOES DE DADOS (AGORA MAIS RÁPIDAS E SIMPLES)
# ==============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    # Tenta conectar apenas 1 vez para ser rápido e não causar TIMEOUT
    try:
        hoje = datetime.today()
        start = (hoje - timedelta(days=365*10)).strftime("%Y-%m-%d")
        df = sgs.get({"Selic": 432, "IPCA": 13522}, start=start)
        if df is not None and not df.empty:
            return df.ffill().dropna()
    except Exception:
        pass # Não usa loop nem sleep para evitar o Timeout
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_focus():
    try:
        em = Expectativas()
        ep = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        dt_lim = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        df = (ep.query().filter(ep.Data >= dt_lim).filter(ep.Suavizada == 'S').filter(ep.baseCalculo == 0).collect())
        # Mantém fallback simples para o Simulador
        return 4.5 if df.empty else float(df.sort_values('Data').iloc[-1]['Mediana'])
    except: return 4.5

# ==============================================================================
# 3. INTERFACE E NAVEGAÇÃO
# ==============================================================================

df = get_data()
ipca_proj = get_focus()

# --- Fallback de Variáveis ---
# Se o DataFrame estiver vazio, usa valores de referência para o Simulador
if not df.empty:
    selic_h = df["Selic"].iloc[-1]
    ipca_h = df["IPCA"].iloc[-1]
else:
    # Valores de referência para o Simulador não quebrar
    selic_h = 11.25 
    ipca_h = 4.50 

with st.sidebar:
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.2rem; margin-bottom:20px; padding-left:5px;'>MONITOR</div>", unsafe_allow_html=True)
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"], label_visibility="collapsed")
    st.markdown("<div style='margin-top:20px; border-top:1px solid #1E293B'></div>", unsafe_allow_html=True)
    
    df_filtered = df.copy()
    
    if nav == "Dashboard":
        with st.form("f_filtros"):
            st.markdown("**Período do Gráfico**")
            
            # Checa se há dados para habilitar o filtro
            if not df.empty:
                d_max = df.index.max().date()
                d_min = df.index.min().date()
                start_def = d_max - timedelta(days=730)
                if start_def < d_min: start_def = d_min
                
                d_ini = st.date_input("Início", start_def, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                d_fim = st.date_input("Fim", d_max, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                
                if st.form_submit_button("ATUALIZAR GRÁFICO"):
                    mask = (df.index.date >= d_ini) & (df.index.date <= d_fim)
                    df_filtered = df.loc[mask]
            else:
                st.warning("Filtros indisponíveis.")
                
# --- DASHBOARD ---
if nav == "Dashboard":
    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("###")

    # Tratamento de erro final do Dashboard (Sem dados, sem Dashboard)
    if df.empty:
        st.error("Erro de conexão com o Banco Central. O Dashboard está indisponível.")
        st.warning("⚠️ O Simulador e o Glossário continuam ativos. Tente recarregar a página.")
        if st.button("Recarregar Dados (Limpar Cache)"):
            st.cache_data.clear()
            st.rerun()
        st.stop()
        
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para o período selecionado.")
        st.stop()

    last = df_filtered.iloc[-1]
    v_selic, v_ipca = last["Selic"], last["IPCA"]
    v_real = ((1 + v_selic/100) / (1 + v_ipca/100) - 1) * 100
    ref = df_filtered.index[-1].strftime('%d/%m/%Y')

    c1, c2, c3 = st.columns(3)
    def card(col, lbl, val, sub, border):
        col.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {border};">
            <div class="metric-label">{lbl}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    card(c1, "TAXA SELIC", f"{v_selic:.2f}%", f"Ref: {ref}", C_SELIC)
    card(c2, "IPCA (12M)", f"{v_ipca:.2f}%", "Inflação Acumulada", C_IPCA)
    card(c3, "JURO REAL", f"{v_real:.2f}%", "Acima da Inflação", C_REAL)

    st.markdown("---") 

    st.markdown("### Evolução Histórica")
    with st.container():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["Selic"], name="Selic", line=dict(color=C_SELIC, width=3)))
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["IPCA"], name="IPCA", line=dict(color=C_ACCENT, width=3)))
        
        fig.update_layout(template="plotly_white", height=320, margin=dict(t=20, l=10, r=10, b=10), legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#E2E8F0", ticksuffix="%"))
        st.plotly_chart(fig, use_container_width=True)

    # Tabela
    if 'table_page' not in st.session_state: st.session_state.table_page = 0
    df_rev = df.resample('M').last().sort_index(ascending=False).copy()
    df_rev["Juro Real"] = ((1 + df_rev["Selic"]/100) / (1 + df_rev["IPCA"]/100) - 1) * 100
    
    ITENS = 6
    total = len(df_rev)
    start = st.session_state.table_page * ITENS
    end = start + ITENS
    df_view = df_rev.iloc[start:end]

    if not df_view.empty:
        per_str = f"{df_view.index[-1].strftime('%d/%m/%Y')} - {df_view.index[0].strftime('%d/%m/%Y')}"
    else: per_str = ""

    st.markdown("---")
    col_t_1, col_t_2, col_t_3 = st.columns([8, 1, 1])
    with col_t_1: st.markdown(f"### Dados Detalhados <span style='font-size:1rem; color:#64748B; font-weight:400; margin-left:10px'>({per_str})</span>", unsafe_allow_html=True)
    with col_t_2:
        if st.button("<", key="btn_prev", disabled=(st.session_state.table_page == 0)):
            st.session_state.table_page -= 1
            st.rerun()
    with col_t_3:
        if st.button(">", key="btn_next", disabled=(end >= total)):
            st.session_state.table_page += 1
            st.rerun()

    df_view.index = df_view.index.strftime('%d/%m/%Y')
    st.dataframe(
        df_view.style.format("{:.2f}%")
        .applymap(lambda x: f"color:{C_SELIC};font-weight:600", subset=["Selic"])
        .applymap(lambda x: f"color:{C_IPCA};font-weight:600", subset=["IPCA"])
        .applymap(lambda x: f"color:{C_REAL};font-weight:600", subset=["Juro Real"]),
        use_container_width=True, height=260
    )

# --- SIMULADOR ---
elif nav == "Simulador":
    st.markdown("<h1>Simulador de Rentabilidade</h1>", unsafe_allow_html=True)
    if df.empty:
        st.info("ℹ️ Usando taxas de referência (últimos valores conhecidos) pois a API do BC está indisponível.")
        
    st.markdown("###")
    col_in, col_out = st.columns([1.2, 2])
    with col_in:
        st.markdown("#### Parâmetros")
        ini = st.number_input("Aporte Inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        mes = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=100.0, step=50.0, format="%.2f")
        anos = st.slider("Tempo (Anos)", 1, 30, 5)
        st.markdown("#### Indexador")
        tipo = st.selectbox("Escolha o índice", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"], label_visibility="collapsed")
        
        if tipo == "Pós-fixado (CDI)":
            pct = st.number_input("Rentabilidade (% do CDI)", min_value=0.0, value=100.0)
            taxa = selic_h * (pct/100)
            st.caption(f"CDI Atual: {selic_h:.2f}% a.a.")
        elif tipo == "IPCA +":
            fx = st.number_input("Taxa Fixa (IPCA + %)", min_value=0.0, value=6.0)
            taxa = ((1+ipca_proj/100)*(1+fx/100)-1)*100
            st.caption(f"IPCA Projetado (Focus): {ipca_proj:.2f}% a.a.")
        else:
            taxa = st.number_input("Taxa Pré-fixada (% a.a.)", min_value=0.0, value=12.0)
    
    periods = anos * 12
    r_mensal = (1+taxa/100)**(1/12)-1
    bal, inv = ini, ini
    evol = [ini]
    for _ in range(periods):
        bal = bal * (1+r_mensal) + mes
        inv += mes
        evol.append(bal)
        
    with col_out:
        st.markdown("#### Resultado Projetado")
        r1, r2, r3 = st.columns(3)
        def result_card(col, label, value, color):
            col.markdown(f"""<div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #E2E8F0; text-align:center;"><div style="font-size:0.8rem; color:#64748B; font-weight:bold; margin-bottom:5px;">{label}</div><div style="font-size:1.4rem; color:{color}; font-weight:800;">{value}</div></div>""", unsafe_allow_html=True)
        result_card(r1, "TOTAL INVESTIDO", f"R$ {inv:,.2f}", "#334155")
        result_card(r2, "SALDO BRUTO", f"R$ {bal:,.2f}", C_ACCENT)
        result_card(r3, "RENDIMENTO", f"R$ {bal-inv:,.2f}", C_REAL)
        st.markdown("###")
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(y=evol, x=list(range(len(evol))), fill='tozeroy', line=dict(color=C_ACCENT, width=3), name="Patrimônio"))
        fig_s.update_layout(template="plotly_white", height=350, margin=dict(t=20,l=0,r=0,b=0), xaxis=dict(showgrid=False, title="Meses"), yaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ "))
        st.plotly_chart(fig_s, use_container_width=True)

# --- GLOSSÁRIO ---
elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    def gloss_card(title, text):
        st.markdown(f"""<div class="glossary-card"><div class="gloss-title">{title}</div><div class="gloss-text">{text}</div></div>""", unsafe_allow_html=True)
    st.markdown("### Indicadores de Mercado")
    c1, c2 = st.columns(2)
    with c1:
        gloss_card("Taxa Selic", "É a taxa básica de juros da economia brasileira.")
        st.markdown("###")
        gloss_card("IPCA", "Índice Nacional de Preços ao Consumidor Amplo.")
    with c2:
        gloss_card("CDI", "Taxa que os bancos cobram para emprestar dinheiro entre si.")
        st.markdown("###")
        gloss_card("Juro Real", "Ganho acima da inflação.")
    st.markdown("---")
    st.markdown("### Tipos de Rentabilidade")
    c3, c4, c5 = st.columns(3)
    with c3: gloss_card("Pós-fixado", "A rentabilidade segue um índice (ex: 100% do CDI).")
    with c4: gloss_card("Pré-fixado", "A taxa é combinada na hora da compra.")
    with c5: gloss_card("Híbrido (IPCA+)", "Paga uma parte fixa mais a inflação.")
