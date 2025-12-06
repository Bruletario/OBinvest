import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from bcb import sgs, Expectativas
import warnings
import time

# ==============================================================================
# 1. SETUP E ESTILIZACAO
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Mercado",
    layout="wide",
    initial_sidebar_state="expanded"
)
warnings.filterwarnings("ignore")

# Cores
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
    .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 6px;
    }}
    .stDateInput svg {{ fill: white !important; }}
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
    }}
    .gloss-title {{ font-size: 1rem; font-weight: 700; color: {C_TEXT_MAIN}; margin-bottom: 8px; }}
    .gloss-text {{ font-size: 0.9rem; color: #475569; line-height: 1.5; }}
    h1 {{ font-weight: 800; color: {C_TEXT_MAIN}; margin: 0; padding: 0; font-size: 2rem; letter-spacing: -0.5px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNCOES OTIMIZADAS (Para evitar travamento)
# ==============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    # Tenta apenas 2 vezes (antes era 3) e espera menos tempo
    for _ in range(2):
        try:
            hoje = datetime.today()
            start = (hoje - timedelta(days=365*10)).strftime("%Y-%m-%d")
            # Tenta pegar dados
            df = sgs.get({"Selic": 432, "IPCA": 13522}, start=start)
            if df is not None and not df.empty:
                return df.ffill().dropna()
        except Exception:
            time.sleep(0.2) # Delay reduzido
            continue
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_focus():
    try:
        em = Expectativas()
        ep = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        dt_lim = (datetime.now()-timedelta(days=45)).strftime('%Y-%m-%d')
        df = (ep.query().filter(ep.Data >= dt_lim).filter(ep.Suavizada == 'S').filter(ep.baseCalculo == 0).collect())
        if df.empty: return 4.5
        return float(df.sort_values('Data').iloc[-1]['Mediana'])
    except:
        return 4.5

# ==============================================================================
# 3. INTERFACE
# ==============================================================================

df = get_data()
ipca_proj = get_focus()

# Valores padrão caso a API falhe (Fallback)
if not df.empty:
    last_selic = df.iloc[-1]["Selic"]
    last_ipca = df.iloc[-1]["IPCA"]
else:
    # Valores de emergência para não quebrar o site
    last_selic = 11.25
    last_ipca = 4.50

with st.sidebar:
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.2rem; margin-bottom:20px; padding-left:5px;'>MONITOR</div>", unsafe_allow_html=True)
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"])
    st.markdown("---")
    
    df_filtered = pd.DataFrame()
    if nav == "Dashboard" and not df.empty:
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

# Verificação se carregou os dados
if df.empty and nav == "Dashboard":
    st.warning("⚠️ Instabilidade no Banco Central: Não foi possível carregar os dados históricos agora. O simulador e o glossário continuam funcionando.")
    st.stop()

# --- TELA 1: DASHBOARD ---
if nav == "Dashboard":
    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("###")
    
    if df_filtered.empty:
        df_filtered = df # Fallback simples
        
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
        fig.update_layout(
            template="plotly_white", height=320, margin=dict(t=20, l=10, r=10, b=10),
            legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tabela simplificada sem paginação complexa para evitar bugs
    st.markdown("---")
    st.markdown("### Dados Recentes")
    df_view = df_filtered.tail(6).sort_index(ascending=False).copy()
    df_view["Juro Real"] = ((1 + df_view["Selic"]/100) / (1 + df_view["IPCA"]/100) - 1) * 100
    df_view.index = df_view.index.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_view.style.format("{:.2f}%")
        .applymap(lambda x: f"color:{C_SELIC};font-weight:600", subset=["Selic"])
        .applymap(lambda x: f"color:{C_IPCA};font-weight:600", subset=["IPCA"])
        .applymap(lambda x: f"color:{C_REAL};font-weight:600", subset=["Juro Real"]),
        use_container_width=True
    )

# --- TELA 2: SIMULADOR ---
elif nav == "Simulador":
    st.markdown("<h1>Simulador de Rentabilidade</h1>", unsafe_allow_html=True)
    if df.empty:
        st.info("ℹ️ Usando taxas padrão pois o Banco Central está instável no momento.")
        
    st.markdown("###")
    col_in, col_out = st.columns([1.2, 2])
    
    with col_in:
        st.markdown("#### Parâmetros")
        ini = st.number_input("Aporte Inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        mes = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=100.0, step=50.0, format="%.2f")
        anos = st.slider("Tempo (Anos)", 1, 30, 5)
        
        st.markdown("#### Indexador")
        tipo = st.selectbox("Escolha o índice", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"])
        
        taxa = 0.0
        if tipo == "Pós-fixado (CDI)":
            pct = st.number_input("Rentabilidade (% do CDI)", min_value=0.0, value=100.0)
            taxa = last_selic * (pct/100)
            st.caption(f"CDI Atual: {last_selic:.2f}% a.a.")
        elif tipo == "IPCA +":
            fx = st.number_input("Taxa Fixa (IPCA + %)", min_value=0.0, value=6.0)
            taxa = ((1+ipca_proj/100)*(1+fx/100)-1)*100
            st.caption(f"IPCA Projetado: {ipca_proj:.2f}% a.a.")
        else:
            taxa = st.number_input("Taxa Pré-fixada (% a.a.)", min_value=0.0, value=12.0)
    
    periods = anos * 12
    r_mensal = (1+taxa/100)**(1/12)-1
    bal = ini
    inv = ini
    evol = [ini]
    
    for _ in range(periods):
        bal = bal * (1+r_mensal) + mes
        inv += mes
        evol.append(bal)
        
    with col_out:
        st.markdown("#### Resultado Projetado")
        r1, r2, r3 = st.columns(3)
        def result_card(col, label, value, color):
            col.markdown(f"""
            <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #E2E8F0; text-align:center;">
                <div style="font-size:0.8rem; color:#64748B; font-weight:bold; margin-bottom:5px;">{label}</div>
                <div style="font-size:1.4rem; color:{color}; font-weight:800;">{value}</div>
            </div>
            """, unsafe_allow_html=True)
            
        result_card(r1, "TOTAL INVESTIDO", f"R$ {inv:,.2f}", "#334155")
        result_card(r2, "SALDO BRUTO", f"R$ {bal:,.2f}", C_ACCENT)
        result_card(r3, "RENDIMENTO", f"R$ {bal-inv:,.2f}", C_REAL)
        
        st.markdown("###")
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(y=evol, x=list(range(len(evol))), fill='tozeroy', line=dict(color=C_ACCENT, width=3), name="Patrimônio"))
        fig_s.update_layout(template="plotly_white", height=350, margin=dict(t=20,l=0,r=0,b=0), xaxis=dict(showgrid=False, title="Meses"), yaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ "))
        st.plotly_chart(fig_s, use_container_width=True)

# --- TELA 3: GLOSSÁRIO ---
elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    def gloss_card(title, text):
        st.markdown(f"""
        <div class="glossary-card">
            <div class="gloss-title">{title}</div>
            <div class="gloss-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Indicadores")
    c1, c2 = st.columns(2)
    with c1: gloss_card("Taxa Selic", "Taxa básica de juros da economia brasileira.")
    with c2: gloss_card("IPCA", "Índice oficial de inflação no Brasil.")
