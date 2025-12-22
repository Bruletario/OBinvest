import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from bcb import sgs, Expectativas
import time

# ==============================================================================
# 1. SETUP E ESTILIZACAO
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Mercado",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    /* REMOÇÃO DE ESPAÇO EXTRA NO TOPO (PADDING-TOP: 0rem) */
    .block-container {{ 
        padding-top: 0rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 100%; 
    }}
    header {{ background-color: transparent !important; }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* INPUTS & DATE PICKER */
    .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important; color: white !important;
        border: 1px solid #334155 !important; border-radius: 6px;
    }}
    .stDateInput input {{ font-weight: 500; }}
    div[data-baseweb="input"] svg {{ fill: white !important; }}
    div[data-baseweb="calendar"] {{
        background-color: {C_SIDEBAR} !important; color: white !important;
        border: 1px solid #334155 !important;
    }}
    div[data-baseweb="calendar"] button {{ filter: invert(1); }} 

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {{ background-color: {C_SIDEBAR}; border-right: 1px solid #1E293B; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div {{ color: {C_TEXT_SIDE} !important; }}
    
    /* --- RADIO BUTTONS --- */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 12px 16px !important; margin-bottom: 4px !important; border-radius: 6px !important;
        cursor: pointer !important; transition: all 0.2s ease; color: #94A3B8 !important;
        font-weight: 500 !important; background-color: transparent; border: 1px solid transparent;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background-color: rgba(255, 255, 255, 0.08) !important; color: white !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {C_ACCENT} !important; color: white !important; font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    
    section[data-testid="stSidebar"] button {{
        background-color: {C_ACCENT} !important; color: white !important; border: none !important;
        font-weight: 600; margin-top: 10px; transition: 0.2s;
    }}
    section[data-testid="stSidebar"] button:hover {{ background-color: #EA580C !important; }}
    
    /* --- METRIC CARDS --- */
    .metric-card {{
        background-color: #FFFFFF; border-radius: 8px; padding: 24px; border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 100%; display: flex; flex-direction: column; justify-content: center;
        min-height: 160px;
    }}
    .metric-label {{ font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 800; color: {C_TEXT_MAIN}; line-height: 1; margin-bottom: 8px; }}
    .metric-sub {{ font-size: 0.85rem; color: #64748B; font-weight: 500; display: flex; align-items: center; gap: 5px; }}
    
    /* --- SWAP BUTTON --- */
    .swap-btn {{ display: flex; justify-content: center; }}
    .swap-btn button {{
        background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important;
        color: {C_TEXT_MAIN} !important; border-radius: 50% !important;
        width: 50px !important; height: 50px !important; font-size: 1.5rem !important;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 50px;
    }}
    .swap-btn button:hover {{ background-color: {C_ACCENT} !important; color: white !important; border-color: {C_ACCENT} !important; }}
    @media (max-width: 768px) {{ .swap-btn button {{ margin-top: 10px !important; margin-bottom: 20px !important; }} }}

    /* --- EXPANDER --- */
    .streamlit-expanderHeader {{
        background-color: white !important; border-radius: 8px !important; border: 1px solid #E2E8F0 !important;
        font-weight: 600 !important; color: {C_TEXT_MAIN} !important;
    }}
    .streamlit-expanderContent {{
        border: 1px solid #E2E8F0; border-top: none; background-color: white;
        border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; padding-top: 20px !important;
    }}
    
    /* --- BUTTONS --- */
    div[data-testid="stButton"] button {{
        background-color: #FFFFFF !important; color: {C_TEXT_MAIN} !important;
        border: 1px solid #CBD5E1 !important; border-radius: 6px !important;
        height: 42px;
    }}
    div[data-testid="stButton"] button:hover {{ 
        border-color: {C_ACCENT} !important; color: {C_ACCENT} !important; background-color: #FFF7ED !important;
    }}

    /* --- GLOSSARY --- */
    .glossary-card {{
        background-color: #FFFFFF; border-radius: 8px; padding: 20px; border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 100%; transition: transform 0.2s;
    }}
    .glossary-card:hover {{ border-color: {C_ACCENT}; }}
    .gloss-title {{ font-size: 1rem; font-weight: 700; color: {C_TEXT_MAIN}; margin-bottom: 8px; }}
    .gloss-text {{ font-size: 0.9rem; color: #475569; line-height: 1.5; }}
    
    h1 {{ font-weight: 800; color: {C_TEXT_MAIN}; margin: 0; padding: 0; font-size: 2rem; letter-spacing: -0.5px; }}
    h3 {{ color: {C_TEXT_MAIN}; font-weight: 700; margin-top: 20px; margin-bottom: 5px; }}
    .section-caption {{ font-size: 0.9rem; color: #64748B; margin-bottom: 20px; font-weight: 400; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DADOS
# ==============================================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_data():
    for attempt in range(3):
        try:
            hoje = datetime.today()
            start = (hoje - timedelta(days=365*10)).strftime("%Y-%m-%d")
            codigos = {"Selic": 432, "IPCA": 13522, "IGPM": 13521, "Dolar": 1}
            df = sgs.get(codigos, start=start).ffill().dropna()
            if not df.empty: return df
        except Exception as e:
            time.sleep(1); continue
    return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def get_focus_data():
    res = {"IPCA": 4.5, "PIB": 2.0} 
    try:
        em = Expectativas()
        dt_lim = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        ep_ipca = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        df_ipca = (ep_ipca.query().filter(ep_ipca.Data >= dt_lim).filter(ep_ipca.Suavizada == 'S').filter(ep_ipca.baseCalculo == 0).collect())
        if not df_ipca.empty: res["IPCA"] = float(df_ipca.sort_values('Data').iloc[-1]['Mediana'])
        ep_pib = em.get_endpoint('ExpectativasMercadoAnual')
        ano_atual = datetime.now().year
        df_pib = (ep_pib.query().filter(ep_pib.Data >= dt_lim).filter(ep_pib.Indicador == 'PIB Total').filter(ep_pib.DataReferencia == ano_atual).collect())
        if not df_pib.empty: res["PIB"] = float(df_pib.sort_values('Data').iloc[-1]['Mediana'])
        return res
    except: return res

with st.spinner('Conectando ao Banco Central...'):
    df = get_data()
    focus = get_focus_data()
    ipca_proj = focus["IPCA"]
    pib_proj = focus["PIB"]
    ano_pib = datetime.now().year

if df.empty: st.error("Erro conexão Banco Central."); st.stop()

with st.sidebar:
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.2rem; margin-bottom:20px; padding-left:5px;'>MONITOR</div>", unsafe_allow_html=True)
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"], label_visibility="collapsed")
    st.markdown("<div style='margin-top:20px; border-top:1px solid #1E293B'></div>", unsafe_allow_html=True)
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m/%Y')}")

# ==============================================================================
# 3. DASHBOARD
# ==============================================================================

if nav == "Dashboard":
    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Visão geral dos principais indicadores econômicos do Brasil em tempo real.</p>", unsafe_allow_html=True)

    if 'card_page' not in st.session_state: st.session_state.card_page = 0 
    c1, c2, c3, c_nav = st.columns([3, 3, 3, 0.4])

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    ref = latest.name.strftime('%d/%m/%Y')

    def card(col, lbl, val, sub, delta=None, border="#ccc", color_text="#333", is_pib=False):
        delta_html = ""
        if is_pib:
            val_float = float(val.replace("%","").replace(",","."))
            if val_float > 0: color_delta = "#10B981"; sub_text = "Projeção de <b>Crescimento</b>"; arrow = "▲"
            elif val_float < 0: color_delta = "#EF4444"; sub_text = "Projeção de <b>Retração</b>"; arrow = "▼"
            else: color_delta = "#94A3B8"; sub_text = "Estabilidade"; arrow = "="
            delta_html = f"<span style='color:{color_delta}; font-size:0.9rem; font-weight:600; margin-left:8px'>{arrow}</span>"
        elif delta is not None:
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="
            color_delta = "#10B981" if delta > 0 else "#EF4444" if delta < 0 else "#94A3B8"
            if any(x in lbl for x in ["IPCA", "IGP-M", "DÓLAR"]) and delta != 0: color_delta = "#EF4444" if delta > 0 else "#10B981"
            delta_str = f"{arrow} {abs(delta):.3f}" if "DÓLAR" in lbl else f"{arrow} {abs(delta):.2f}%"
            if delta != 0: delta_html = f"<span style='color:{color_delta}; font-size:0.9rem; font-weight:600; margin-left:8px'>{delta_str}</span>"
            sub_text = sub

        col.markdown(f"<div class='metric-card' style='border-left: 5px solid {border};'><div class='metric-label'>{lbl}</div><div style='display:flex; align-items:baseline;'><div class='metric-value' style='color:{color_text}'>{val}</div>{delta_html}</div><div class='metric-sub'>{sub_text}</div></div>", unsafe_allow_html=True)

    show_primary = (st.session_state.card_page == 0)
    if show_primary:
        v_selic, v_ipca = latest["Selic"], latest["IPCA"]
        v_real = ((1 + v_selic/100) / (1 + v_ipca/100) - 1) * 100
        card(c1, "TAXA SELIC", f"{v_selic:.2f}%", f"Ref: {ref}", v_selic - previous["Selic"], C_SELIC, C_TEXT_MAIN)
        card(c2, "IPCA (12M)", f"{v_ipca:.2f}%", "Inflação Oficial", v_ipca - previous["IPCA"], C_IPCA, C_TEXT_MAIN)
        card(c3, "JURO REAL", f"{v_real:.2f}%", "Acima da Inflação", 0, C_REAL, C_TEXT_MAIN)
    else:
        v_dolar, v_igpm = latest["Dolar"], latest["IGPM"]
        igpm_txt = "Inflação (Aluguel)" if v_igpm >= 0 else "Deflação (Aluguel)"
        card(c1, "DÓLAR PTAX", f"R$ {v_dolar:.4f}", "Cotação de Venda", v_dolar - previous["Dolar"], "#0EA5E9", C_TEXT_MAIN)
        card(c2, "IGP-M (12M)", f"{v_igpm:.2f}%", igpm_txt, v_igpm - previous["IGPM"], "#8B5CF6", C_TEXT_MAIN)
        card(c3, f"PIB (PROJEÇÃO {ano_pib})", f"{pib_proj:.2f}%", "", None, "#EAB308", C_TEXT_MAIN, is_pib=True)

    with c_nav:
        st.markdown('<div class="swap-btn">', unsafe_allow_html=True)
        if st.button("▶" if show_primary else "◀", key="swap"):
            st.session_state.card_page = 1 if show_primary else 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---") 

    c_head_1, c_head_2 = st.columns([2, 1])
    with c_head_1:
        g_title = "Evolução: Selic e IPCA" if show_primary else "Correlação: Dólar e IGP-M"
        st.markdown(f"### {g_title}")
        st.markdown("<p class='section-caption'>Acompanhe como os indicadores se comportaram no período selecionado.</p>", unsafe_allow_html=True)
    with c_head_2:
        with st.expander("Filtrar Período", expanded=False):
            st.markdown("<div style='font-size:0.85rem; color:#64748B; margin-bottom:10px;'>Selecione o intervalo de análise:</div>", unsafe_allow_html=True)
            d_max = df.index.max().date(); d_min = df.index.min().date(); start_def = d_max - timedelta(days=730)
            fd1, fd2 = st.columns(2)
            d_ini = fd1.date_input("Início", start_def, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
            d_fim = fd2.date_input("Fim", d_max, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")

    mask = (df.index.date >= d_ini) & (df.index.date <= d_fim)
    df_chart = df.loc[mask]

    if df_chart.empty: st.warning("Nenhum dado encontrado.")
    else:
        with st.container():
            has_secondary = not show_primary
            fig = make_subplots(specs=[[{"secondary_y": has_secondary}]])
            if show_primary:
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Selic"], name="Selic", line=dict(color=C_SELIC, width=3), hovertemplate="Data: %{x|%d/%m/%Y}<br>Selic: <b>%{y:.2f}%</b><extra></extra>"), secondary_y=False)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["IPCA"], name="IPCA", line=dict(color=C_ACCENT, width=3), hovertemplate="Data: %{x|%d/%m/%Y}<br>IPCA: <b>%{y:.2f}%</b><extra></extra>"), secondary_y=False)
                fig.update_yaxes(title_text="Taxa (%)", showgrid=True, gridcolor="#E2E8F0", ticksuffix="%")
            else:
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Dolar"], name="Dólar", line=dict(color="#0EA5E9", width=3), hovertemplate="Data: %{x|%d/%m/%Y}<br>Dólar: <b>R$ %{y:.4f}</b><extra></extra>"), secondary_y=False)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["IGPM"], name="IGP-M", line=dict(color="#8B5CF6", width=3), hovertemplate="Data: %{x|%d/%m/%Y}<br>IGP-M: <b>%{y:.2f}%</b><extra></extra>"), secondary_y=True)
                fig.update_yaxes(title_text="Cotação (R$)", showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ ", secondary_y=False)
                fig.update_yaxes(title_text="Índice (%)", showgrid=False, ticksuffix="%", secondary_y=True)
            fig.update_layout(template="plotly_white", height=350, margin=dict(t=20, l=10, r=10, b=10), legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified", xaxis=dict(showgrid=False))
            st.plotly_chart(fig, use_container_width=True)

    if 'table_page' not in st.session_state: st.session_state.table_page = 0
    df_rev = df.resample('M').last().sort_index(ascending=False)
    for c in ["Selic", "IPCA", "Dolar", "IGPM"]: df_rev[f"{c}_D"] = df_rev[c].diff(-1)
    
    ITENS = 6; total = len(df_rev); start = st.session_state.table_page * ITENS; end = start + ITENS
    if start >= total and total > 0: st.session_state.table_page = 0; start = 0; end = ITENS
    df_view = df_rev.iloc[start:end].copy()

    st.markdown("---")
    col_t_1, col_t_2, col_t_3 = st.columns([6, 1, 1])
    with col_t_1:
        st.markdown(f"### Dados Detalhados")
        st.markdown("<p class='section-caption'>Histórico completo (últimos 10 anos).</p>", unsafe_allow_html=True)
    with col_t_2:
        if st.button("◀", key="btn_prev", disabled=(st.session_state.table_page == 0), use_container_width=True):
            st.session_state.table_page -= 1; st.rerun()
    with col_t_3:
        if st.button("▶", key="btn_next", disabled=(end >= total), use_container_width=True):
            st.session_state.table_page += 1; st.rerun()

    def fmt_arrow(val, delta, is_currency=False):
        arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="
        val_str = f"R$ {val:.4f}" if is_currency else f"{val:.2f}%"
        return f"{val_str} {arrow}"

    for c in ["Selic", "IPCA", "IGPM", "Dolar"]:
        new_col = []
        for idx, row in df_view.iterrows(): new_col.append(fmt_arrow(row[c], row[f"{c}_D"], c=="Dolar"))
        df_view[f"{c}_Show"] = new_col

    df_view.index = df_view.index.strftime('%b/%Y')
    def color_arrows(val):
        if "▲" in val: return "color: #10B981; font-weight:600"
        if "▼" in val: return "color: #EF4444; font-weight:600"
        return "color: #64748B"

    st.dataframe(
        df_view[["Selic_Show", "IPCA_Show", "Dolar_Show", "IGPM_Show"]]
        .rename(columns={"Selic_Show": "Selic", "IPCA_Show": "IPCA", "Dolar_Show": "Dólar", "IGPM_Show": "IGP-M"})
        .style.applymap(color_arrows),
        use_container_width=True, height=280
    )

# ==============================================================================
# 4. SIMULADOR (SEM DOLAR E SEM LIQUIDO)
# ==============================================================================
elif nav == "Simulador":
    st.markdown("<h1>Simulador de Rentabilidade</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Projeção de ganhos baseada em diferentes indexadores do mercado.</p>", unsafe_allow_html=True)
    
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.markdown("#### Parâmetros")
        ini = st.number_input("Aporte Inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f", help="Valor que você tem hoje para investir.")
        mes = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=100.0, step=50.0, format="%.2f", help="Quanto você vai depositar todo mês.")
        anos = st.slider("Tempo (Anos)", 1, 30, 5)
        
        st.markdown("#### Indexador")
        # REMOVIDO "DÓLAR" DA LISTA
        tipo = st.selectbox("Escolha o índice", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"], label_visibility="collapsed")
        
        selic_h = df["Selic"].iloc[-1]; taxa = 0.0
        
        if tipo == "Pós-fixado (CDI)":
            pct = st.number_input("Rentabilidade (% do CDI)", min_value=0.0, value=100.0)
            taxa = selic_h * (pct/100)
            st.caption(f"CDI Atual: {selic_h:.2f}% a.a.")
        elif tipo == "IPCA +":
            fx = st.number_input("Taxa Fixa (IPCA + %)", min_value=0.0, value=6.0)
            taxa = ((1+ipca_proj/100)*(1+fx/100)-1)*100
            st.caption(f"IPCA Proj: {ipca_proj:.2f}% a.a.")
        else:
            taxa = st.number_input("Taxa Pré-fixada (% a.a.)", min_value=0.0, value=12.0)
    
    periods = anos * 12
    r_mensal = (1+taxa/100)**(1/12)-1
    bal = ini; inv = ini; evol = [ini]
    
    for _ in range(periods):
        bal = bal * (1+r_mensal) + mes
        inv += mes
        evol.append(bal)
        
    with col_out:
        st.markdown("#### Resultado Projetado")
        r1, r2, r3 = st.columns(3)
        def result_card(col, label, value, color):
            col.markdown(f"<div style='background-color:white; padding:15px; border-radius:8px; border:1px solid #E2E8F0; text-align:center;'><div style='font-size:0.8rem; color:#64748B; font-weight:bold; margin-bottom:5px;'>{label}</div><div style='font-size:1.4rem; color:{color}; font-weight:800;'>{value}</div></div>", unsafe_allow_html=True)
            
        result_card(r1, "TOTAL INVESTIDO", f"R$ {inv:,.2f}", "#334155")
        result_card(r2, "SALDO BRUTO", f"R$ {bal:,.2f}", C_ACCENT)
        result_card(r3, "RENDIMENTO", f"R$ {bal-inv:,.2f}", C_REAL)
        
        st.markdown("###")
        
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(y=evol, x=list(range(len(evol))), fill='tozeroy', line=dict(color=C_ACCENT, width=3), name="Patrimônio Total"))
        fig_s.update_layout(template="plotly_white", height=350, margin=dict(t=20,l=0,r=0,b=0), xaxis=dict(showgrid=False, title="Meses"), yaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ "))
        st.plotly_chart(fig_s, use_container_width=True)

# ==============================================================================
# 5. GLOSSARIO
# ==============================================================================
elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Entenda os principais termos utilizados no mercado e na calculadora.</p>", unsafe_allow_html=True)
    def gloss_card(title, text):
        st.markdown(f"<div class='glossary-card'><div class='gloss-title'>{title}</div><div class='gloss-text'>{text}</div></div>", unsafe_allow_html=True)

    st.markdown("### Indicadores Principais")
    c1, c2 = st.columns(2)
    with c1:
        gloss_card("Taxa Selic", "É a taxa básica de juros da economia brasileira. Ela influencia todas as outras taxas de juros do país. Definida pelo COPOM.")
        st.markdown("###")
        gloss_card("IPCA", "Índice Nacional de Preços ao Consumidor Amplo. É o termômetro oficial da inflação no Brasil.")
        st.markdown("###")
        gloss_card("PIB", "Produto Interno Bruto. A soma de todos os bens e serviços finais produzidos pelo país.")
    with c2:
        gloss_card("CDI", "Taxa que os bancos cobram para emprestar dinheiro entre si. Acompanha de perto a Selic e baliza a Renda Fixa.")
        st.markdown("###")
        gloss_card("IGP-M", "Índice Geral de Preços - Mercado. Conhecido como 'inflação do aluguel', é muito usado em reajustes de contratos.")
        st.markdown("###")
        gloss_card("Dólar PTAX", "Média das taxas de compra e venda de dólar apurada pelo Banco Central.")
    
    st.markdown("---")
    st.markdown("### Tipos de Rentabilidade")
    c3, c4, c5 = st.columns(3)
    with c3: gloss_card("Pós-fixado", "A rentabilidade segue um índice (ex: 100% do CDI). Se o juro subir, você ganha mais.")
    with c4: gloss_card("Pré-fixado", "A taxa é combinada na hora da compra (ex: 12% ao ano). Não varia com o mercado.")
    with c5: gloss_card("Híbrido (IPCA+)", "Paga uma parte fixa mais a inflação (IPCA). Protege o poder de compra.")
    st.markdown("---"); st.caption("Fonte dos dados: Banco Central do Brasil (SGS e Focus). Atualização automática.")

