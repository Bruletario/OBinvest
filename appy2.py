import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from bcb import sgs, Expectativas
import time

# ==============================================================================
# 1. SETUP E ESTILIZAÇÃO
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Mercado - OBInvest",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores
C_SIDEBAR = "#0F172A"
C_MAIN = "#F8FAFC"
C_ACCENT = "#F97316"
C_TEXT_MAIN = "#1E293B"
C_TEXT_SIDE = "#FFFFFF"
C_INPUT_BG = "#1E293B"

# Cores dos Indicadores
C_SELIC = "#334155"
C_IPCA = "#D97706"
C_REAL = "#059669"
C_DOLAR = "#0EA5E9"
C_IGPM = "#8B5CF6"
C_PIB = "#EAB308"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {C_MAIN};
        color: {C_TEXT_MAIN};
    }}
    
    .block-container {{ 
        padding-top: 3.5rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 100%; 
    }}
    
    section[data-testid="stSidebar"][aria-expanded="true"] {{ 
        min-width: 305px !important; 
        width: 305px !important;
        background-color: {C_SIDEBAR}; 
        border-right: 1px solid #1E293B; 
    }}
    
    section[data-testid="stSidebar"][aria-expanded="false"] {{
        background-color: {C_SIDEBAR}; 
    }}
    
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div {{ 
        color: {C_TEXT_SIDE} !important; 
    }}
    
    [data-testid="stSidebar"] [data-testid="stImage"] {{
        margin-bottom: 20px;
        margin-top: 20px;
        padding: 0 !important;
        text-align: center;
        display: flex;
        justify-content: center;
    }}
    
    [data-testid="stSidebar"] img {{
        width: 100% !important;
        max-width: 260px !important;
        object-fit: contain;
    }}
    
    /* MENU */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
    
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 12px 16px !important; 
        margin-bottom: 6px !important; 
        border-radius: 8px !important;
        cursor: pointer !important; 
        transition: all 0.2s ease; 
        color: #94A3B8 !important;
        font-weight: 500 !important; 
        font-size: 0.90rem !important;
        background-color: transparent; 
        border: 1px solid transparent;
        line-height: 1.3 !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ 
        background-color: rgba(255, 255, 255, 0.08) !important; color: white !important; 
    }}
    
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {C_ACCENT} !important; 
        color: white !important; 
        font-weight: 600 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }}

    .stDateInput input, div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important; color: white !important;
        border: 1px solid #334155 !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="calendar"] {{
        background-color: white !important; color: #1E293B !important;
    }}
    div[data-baseweb="calendar"] button {{ filter: none !important; color: #1E293B !important; }}

    div[data-testid="column"] div[data-testid="stVerticalBlock"] {{ gap: 0rem !important; }}

    .metric-card-container {{
        background-color: #FFFFFF; 
        border: 1px solid #E2E8F0;
        border-bottom: none !important; 
        border-radius: 8px 8px 0 0; 
        padding: 16px; 
        height: 130px; 
        display: flex; flex-direction: column; justify-content: center;
        position: relative;
    }}

    .glossary-card {{
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }}
    .glossary-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .gloss-title {{ font-weight: 700; font-size: 1.1rem; margin-bottom: 10px; color: {C_TEXT_MAIN}; display: flex; align-items: center; gap: 8px; }}
    .gloss-text {{ font-size: 0.9rem; color: #64748B; line-height: 1.5; }}
    
    .metric-label {{ font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px; }}
    .metric-value-row {{ display: flex; align-items: baseline; gap: 8px; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 800; color: {C_TEXT_MAIN}; line-height: 1; }}
    .metric-sub {{ font-size: 0.75rem; color: #64748B; margin-top: 8px; font-weight: 500; }}

    div[data-testid="column"] .stButton button {{
        width: 100% !important;
        border: 1px solid #E2E8F0 !important; border-top: 1px solid #F1F5F9 !important;
        border-radius: 0px !important; 
        background-color: #FFFFFF !important; color: #64748B !important;
        font-size: 0.75rem !important; font-weight: 600 !important;
        height: 38px !important; margin-top: 0px !important; box-shadow: none !important;
        transition: all 0.2s;
    }}
    div[data-testid="column"] .stButton button:hover {{
        background-color: {C_ACCENT} !important; color: white !important; border-color: {C_ACCENT} !important;
    }}
    
    h1 {{ font-weight: 800; color: {C_TEXT_MAIN}; margin: 0; padding: 0; font-size: 2rem; letter-spacing: -0.5px; }}
    h3 {{ color: {C_TEXT_MAIN}; font-weight: 700; margin-top: 20px; margin-bottom: 5px; }}
    .section-caption {{ font-size: 0.9rem; color: #64748B; margin-bottom: 20px; font-weight: 400; }}
    
    .dynamic-legend {{
        background-color: #F1F5F9;
        border-radius: 6px;
        padding: 15px;
        font-size: 0.85rem;
        color: #475569;
        margin-top: 15px;
        border: 1px solid #E2E8F0;
        line-height: 1.6;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DADOS E FUNÇÕES DE BUSCA
# ==============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    """
    Busca dados históricos do SGS (Série Histórica/Passado).
    """
    for attempt in range(3):
        try:
            hoje = datetime.today()
            start = (hoje - timedelta(days=365*10)).strftime("%Y-%m-%d")
            
            # CÓDIGOS SGS:
            # 4380: PIB Mensal (R$ Milhões) - Série oficial de valores correntes
            codigos = {
                "Selic": 432, 
                "IPCA": 13522, 
                "IGPM": 13521, 
                "Dolar": 1, 
                "PIB_Mensal_Raw": 4380 
            }
            df = sgs.get(codigos, start=start).ffill().dropna()
            
            # Calcula o PIB Acumulado 12 Meses para o GRÁFICO
            if not df.empty and "PIB_Mensal_Raw" in df.columns:
                df["PIB_12M"] = df["PIB_Mensal_Raw"].rolling(window=12).sum()
            
            if not df.empty: return df
        except Exception:
            time.sleep(1)
            continue
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_focus_data():
    """
    Busca a projeção do FOCUS para o PIB Total do ano corrente.
    Filtra direto na API para evitar timeout.
    """
    res = {"IPCA": 0.0, "PIB": 0.0, "Data_PIB": "-", "Ref_Year": datetime.now().year}
    
    try:
        em = Expectativas()
        
        # Datas
        hoje = datetime.now()
        dt_lim = (hoje - timedelta(days=30)).strftime('%Y-%m-%d') # 30 dias é suficiente
        ano_atual = hoje.year 
        
        # 1. IPCA (ExpectativasMercadoInflacao12Meses)
        ep_ipca = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        df_ipca = (ep_ipca.query()
                   .filter(ep_ipca.Data >= dt_lim)
                   .filter(ep_ipca.Suavizada == 'S')
                   .filter(ep_ipca.baseCalculo == 0)
                   .collect())
                   
        if not df_ipca.empty:
            # Pega o último registro disponível ordenado por data
            df_ipca = df_ipca.sort_values('Data', ascending=True)
            res["IPCA"] = float(df_ipca.iloc[-1]['Mediana'])

        # 2. PIB (ExpectativasMercadoAnuais -> PIB Total)
        ep_anual = em.get_endpoint('ExpectativasMercadoAnuais')
        
        # Filtra direto no servidor: Indicador 'PIB Total'
        df_pib = (ep_anual.query()
                  .filter(ep_anual.Indicador == 'PIB Total')
                  .filter(ep_anual.Data >= dt_lim)
                  .collect())

        if not df_pib.empty:
            # Garante que DataReferencia seja inteiro
            df_pib['DataReferencia'] = pd.to_numeric(df_pib['DataReferencia'], errors='coerce')
            df_pib = df_pib.dropna(subset=['DataReferencia'])
            df_pib['DataReferencia'] = df_pib['DataReferencia'].astype(int)
            
            # Tenta pegar o ano atual
            df_foco = df_pib[df_pib['DataReferencia'] == ano_atual]
            
            # Se não tiver dados para o ano atual, tenta o próximo
            if df_foco.empty:
                df_foco = df_pib[df_pib['DataReferencia'] == ano_atual + 1]
                ano_atual = ano_atual + 1 # Atualiza a referência
            
            if not df_foco.empty:
                # Pega a publicação mais recente (Data de publicação)
                ultimo = df_foco.sort_values('Data', ascending=False).iloc[0]
                
                res["PIB"] = float(ultimo['Mediana'])
                res["Data_PIB"] = pd.to_datetime(ultimo['Data']).strftime('%d/%m')
                res["Ref_Year"] = int(ultimo['DataReferencia'])

        return res

    except Exception as e:
        print(f"Erro Focus: {e}")
        return res

with st.spinner('Atualizando Indicadores...'):
    df = get_data() # Dados históricos
    focus = get_focus_data() # Dados de projeção
    
    ipca_proj = focus["IPCA"]
    pib_proj = focus["PIB"] # <--- PROJEÇÃO DO FOCUS
    data_ref_pib = focus["Data_PIB"]
    ref_year_pib = focus["Ref_Year"]
    has_focus_pib = data_ref_pib != "-"

if df.empty: 
    st.error("Erro na conexão com Banco Central (SGS). Tente recarregar.")
    st.stop()

# SIDEBAR
with st.sidebar:
    try:
        st.image("Logo OBINVEST Branco.png", use_container_width=True)
    except:
        st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:2rem; text-align:center;'>OBINVEST</div>", unsafe_allow_html=True)
    nav = st.radio("Navegação", ["Dados Macroeconômicos", "Calculadora de Rentabilidade", "Glossário"], label_visibility="collapsed")
    st.markdown("<div style='margin-top:20px; border-top:1px solid #1E293B'></div>", unsafe_allow_html=True)
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m/%Y')}")

if 'last_nav' not in st.session_state: st.session_state.last_nav = nav
if nav != st.session_state.last_nav:
    st.session_state.last_nav = nav
    if nav == "Dados Macroeconômicos": st.session_state.selected_chart = "Geral"

# ==============================================================================
# 3. CONTEÚDO PRINCIPAL
# ==============================================================================

if nav == "Dados Macroeconômicos":
    st.markdown("<h1>DADOS MACROECONÔMICOS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Visão geral dos principais indicadores econômicos do Brasil em tempo real.</p>", unsafe_allow_html=True)

    if 'selected_chart' not in st.session_state: st.session_state.selected_chart = "Geral"

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    ref_date = latest.name.strftime('%d/%m')
    
    v_selic = latest["Selic"]
    v_ipca = latest["IPCA"]
    v_real = ((1 + v_selic/100) / (1 + v_ipca/100) - 1) * 100
    v_dolar = latest["Dolar"]
    v_igpm = latest["IGPM"]
    
    # CARD PIB: LÓGICA CORRIGIDA
    val_pib_str = f"{pib_proj:.2f}%" if has_focus_pib else "-"
    delta_pib = pib_proj if has_focus_pib else None
    # Mostra o ano de referência explicitamente (ex: Focus 2026)
    sub_pib = f"Focus {ref_year_pib} (Pub: {data_ref_pib})" if has_focus_pib else "Sem dados"
    
    cards_config = [
        {"id": "Selic", "lbl": "TAXA SELIC", "val": f"{v_selic:.2f}%", "delta": v_selic - previous["Selic"], "border": C_SELIC, "sub": f"Atualizado em {ref_date}"},
        {"id": "IPCA", "lbl": "IPCA (12M)", "val": f"{v_ipca:.2f}%", "delta": v_ipca - previous["IPCA"], "border": C_IPCA, "sub": "Inflação Oficial"},
        {"id": "Juro Real", "lbl": "JURO REAL", "val": f"{v_real:.2f}%", "delta": 0, "border": C_REAL, "sub": "Acima da Inflação"},
        {"id": "Dolar", "lbl": "DÓLAR PTAX", "val": f"R$ {v_dolar:.4f}", "delta": v_dolar - previous["Dolar"], "border": C_DOLAR, "sub": "Cotação de Venda"},
        {"id": "IGPM", "lbl": "IGP-M (12M)", "val": f"{v_igpm:.2f}%", "delta": v_igpm - previous["IGPM"], "border": C_IGPM, "sub": "Inflação (Aluguel)"},
        {"id": "PIB", "lbl": f"PIB PROJ. {ref_year_pib}", "val": val_pib_str, "delta": delta_pib, "border": C_PIB, "sub": sub_pib}
    ]

    cols = st.columns(6, gap="small")
    for i, col in enumerate(cols):
        cfg = cards_config[i]
        delta_html = ""
        
        if cfg["id"] == "PIB":
            if has_focus_pib:
                arrow = "▲" if pib_proj > 0 else "▼" if pib_proj < 0 else "="
                color_delta = "#10B981" if pib_proj > 0 else "#EF4444"
                delta_html = f"<span style='color:{color_delta}; font-size:0.8rem; font-weight:600;'>{arrow}</span>"
            else: delta_html = "<span style='color:#94A3B8; font-size:0.8rem;'>-</span>"
        elif cfg["delta"] is not None:
            delta = cfg["delta"]
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="
            is_bad_up = any(x in cfg["lbl"] for x in ["IPCA", "IGP-M", "DÓLAR"])
            color_delta = "#EF4444" if (is_bad_up and delta > 0) else "#10B981" if delta > 0 else "#EF4444" if delta < 0 else "#94A3B8"
            if delta != 0: delta_html = f"<span style='color:{color_delta}; font-size:0.8rem; font-weight:600;'>{arrow} {abs(delta):.2f}{'%' if 'DÓLAR' not in cfg['lbl'] else ''}</span>"

        col.markdown(f"<div class='metric-card-container' style='border-left: 4px solid {cfg['border']};'><div class='metric-label'>{cfg['lbl']}</div><div class='metric-value-row'><div class='metric-value'>{cfg['val']}</div>{delta_html}</div><div class='metric-sub'>{cfg['sub']}</div></div>", unsafe_allow_html=True)
        if col.button("Ver Gráfico", key=f"btn_{cfg['id']}", use_container_width=True): 
            st.session_state.selected_chart = cfg["id"]
            st.rerun()

    st.markdown("---") 
    
    chart_type = st.session_state.selected_chart
    
    # Títulos
    titles = {
        "Geral": "Evolução: Selic x IPCA", 
        "Selic": "Histórico da Taxa Selic", 
        "IPCA": "Histórico da Inflação (IPCA)", 
        "Juro Real": "Histórico de Juro Real (Ex-post)", 
        "Dolar": "Cotação do Dólar", 
        "IGPM": "Histórico do IGP-M", 
        "PIB": "Evolução Histórica do PIB (Valores Correntes Acumulados 12M)"
    }
    
    c_head_1, c_head_2 = st.columns([3, 1])
    with c_head_1:
        st.markdown(f"### {titles.get(chart_type, 'Gráfico')}")
    
    df_chart = pd.DataFrame()
    with c_head_2:
        with st.expander("Filtrar Período", expanded=False):
            d_max = df.index.max().date()
            d_ini = st.date_input("Início", d_max - timedelta(days=730 if chart_type != "PIB" else 365*5), min_value=df.index.min().date(), max_value=d_max, format="DD/MM/YYYY")
            d_fim = st.date_input("Fim", d_max, min_value=df.index.min().date(), max_value=d_max, format="DD/MM/YYYY")
    
    df_chart = df.loc[(df.index.date >= d_ini) & (df.index.date <= d_fim)]

    # RENDERIZAÇÃO
    if df_chart.empty: 
        st.warning("Nenhum dado encontrado para o período.")
    else:
        fig = go.Figure()
        
        if chart_type == "Geral":
            fig = make_subplots(specs=[[{"secondary_y": False}]])
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Selic"], name="Selic", line=dict(color=C_SELIC, width=3)))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["IPCA"], name="IPCA", line=dict(color=C_ACCENT, width=3)))
            fig.update_yaxes(title_text="Taxa (%)", ticksuffix="%")
        elif chart_type == "Selic": 
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Selic"], name="Selic", line=dict(color=C_SELIC, width=4)))
            fig.update_yaxes(ticksuffix="%")
        elif chart_type == "IPCA": 
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["IPCA"], name="IPCA", line=dict(color=C_IPCA, width=4)))
            fig.update_yaxes(ticksuffix="%")
        elif chart_type == "Juro Real": 
            df_chart["Real_Calc"] = ((1 + df_chart["Selic"]/100) / (1 + df_chart["IPCA"]/100) - 1) * 100
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Real_Calc"], name="Juro Real", line=dict(color=C_REAL, width=3)))
            fig.update_yaxes(ticksuffix="%")
        elif chart_type == "Dolar": 
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["Dolar"], name="Dólar", fill='tozeroy', line=dict(color=C_DOLAR, width=2)))
            fig.update_yaxes(tickprefix="R$ ")
        elif chart_type == "IGPM": 
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["IGPM"], name="IGP-M", fill='tozeroy', line=dict(color=C_IGPM, width=2)))
            fig.update_yaxes(ticksuffix="%", autorange=True)
            
        elif chart_type == "PIB":
            # ==========================================
            # GRÁFICO: APENAS HISTÓRICO (ACUMULADO 12M)
            # ==========================================
            try:
                # Usa a coluna calculada PIB_12M (R$ Milhões) e converte para Trilhões
                df_pib = df_chart["PIB_12M"].dropna() / 1_000_000
                
                if not df_pib.empty:
                    fig.add_trace(go.Scatter(
                        x=df_pib.index, 
                        y=df_pib, 
                        name="PIB (12 Meses)", 
                        fill='tozeroy', 
                        line=dict(color=C_PIB, width=3)
                    ))

                    fig.update_layout(
                        showlegend=False, 
                        yaxis=dict(title="PIB Nominal (R$ Trilhões)", tickprefix="R$ ", showgrid=True),
                        xaxis=dict(title="Mês de Referência"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown(f"""
                    <div class="dynamic-legend">
                        <b>Histórico Oficial:</b><br>
                        O gráfico exibe a evolução do PIB Nominal acumulado em 12 meses (valores correntes).<br>
                        Fonte: Banco Central do Brasil (Série SGS 4380 consolidada).
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Período selecionado insuficiente para cálculo do acumulado de 12 meses.")
                    
            except Exception as e:
                st.error(f"Erro ao gerar gráfico do PIB: {e}")
        
        if chart_type != "PIB":
            fig.update_layout(template="plotly_white", height=350, margin=dict(t=30, l=10, r=10, b=10), hovermode="x unified", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#E2E8F0"))
            st.plotly_chart(fig, use_container_width=True)

    # TABLE
    if 'table_page' not in st.session_state: st.session_state.table_page = 0
    df_rev = df.resample('M').last().sort_index(ascending=False)
    for c in ["Selic", "IPCA", "Dolar", "IGPM"]: df_rev[f"{c}_D"] = df_rev[c].diff(-1)
    
    ITENS = 6
    start = st.session_state.table_page * ITENS
    end = start + ITENS
    if start >= len(df_rev) and len(df_rev) > 0: st.session_state.table_page = 0; start = 0; end = ITENS
    df_view = df_rev.iloc[start:end].copy()

    st.markdown("---")
    c1, c2, c3 = st.columns([6, 1, 1])
    with c1: st.markdown(f"### Dados Detalhados")
    with c2: 
        if st.button("◀", key="p", disabled=(st.session_state.table_page == 0), use_container_width=True): st.session_state.table_page -= 1; st.rerun()
    with c3: 
        if st.button("▶", key="n", disabled=(end >= len(df_rev)), use_container_width=True): st.session_state.table_page += 1; st.rerun()

    def color_arrows(val): return "color: #10B981; font-weight:600" if "▲" in val else "color: #EF4444; font-weight:600" if "▼" in val else "color: #64748B"
    for c in ["Selic", "IPCA", "IGPM", "Dolar"]:
        df_view[f"{c}_Show"] = [f"{'R$' if c=='Dolar' else ''} {row[c]:.4f}{'%' if c!='Dolar' else ''} {'▲' if row[f'{c}_D']>0 else '▼' if row[f'{c}_D']<0 else '='}" for _, row in df_view.iterrows()]
    st.dataframe(df_view[[f"{c}_Show" for c in ["Selic", "IPCA", "Dolar", "IGPM"]]].rename(columns={f"{c}_Show":c for c in ["Selic", "IPCA", "Dolar", "IGPM"]}).style.applymap(color_arrows), use_container_width=True, height=280)

elif nav == "Calculadora de Rentabilidade":
    st.markdown("<h1>Calculadora de Rentabilidade</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Projeção baseada na média histórica dos últimos 5 anos.</p>", unsafe_allow_html=True)
    
    data_corte = df.index.max() - timedelta(days=365*5)
    df_5y = df[df.index >= data_corte]
    media_selic_5y = df_5y["Selic"].mean()
    media_ipca_5y = df_5y["IPCA"].mean()

    col_in, col_out = st.columns([1, 2])
    with col_in:
        st.markdown("#### Parâmetros")
        ini = st.number_input("Aporte Inicial (R$)", 0.0, 1000000.0, 1000.0, format="%.2f")
        mes = st.number_input("Aporte Mensal (R$)", 0.0, 100000.0, 500.0, format="%.2f")
        anos = st.slider("Tempo (Anos)", 1, 30, 3)
        st.markdown("#### Indexador")
        tipo = st.selectbox("Escolha", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"], label_visibility="collapsed")
        
        if tipo == "Pós-fixado (CDI)":
            pct = st.number_input("Rentabilidade (% do CDI)", 0.0, 200.0, 100.0)
            taxa = media_selic_5y * (pct/100)
            msg = f"Base: Selic média 5 anos ({media_selic_5y:.2f}%)."
        elif tipo == "IPCA +":
            fx = st.number_input("Taxa Fixa (IPCA + %)", 0.0, 20.0, 6.0)
            taxa = ((1 + media_ipca_5y/100) * (1 + fx/100) - 1) * 100
            msg = f"Base: IPCA médio 5 anos ({media_ipca_5y:.2f}%) + Taxa fixa."
        else:
            taxa = st.number_input("Taxa Pré-fixada (% a.a.)", 0.0, 30.0, 12.0)
            msg = "Taxa fixa contratada."
        st.markdown(f"<div style='margin-top:10px; font-size:0.85rem; color:#64748B; border-top:1px solid #E2E8F0; padding-top:10px;'>ℹ️ Taxa Efetiva: <b>{taxa:.2f}% a.a.</b><br>{msg}</div>", unsafe_allow_html=True)

    periods = anos * 12
    r_mensal = (1 + taxa/100)**(1/12) - 1
    bal = ini; inv = ini; evol = [ini]
    for _ in range(periods): 
        bal = bal * (1 + r_mensal) + mes
        inv += mes
        evol.append(bal)
        
    with col_out:
        st.markdown("#### Resultado Projetado")
        r1, r2, r3 = st.columns(3)
        def r_card(c, l, v, cl): c.markdown(f"<div style='background-color:white; padding:15px; border-radius:8px; border:1px solid #E2E8F0; text-align:center;'><div style='font-size:0.8rem; color:#64748B; font-weight:bold; margin-bottom:5px;'>{l}</div><div style='font-size:1.4rem; color:{cl}; font-weight:800;'>{v}</div></div>", unsafe_allow_html=True)
        r_card(r1, "TOTAL INVESTIDO", f"R$ {inv:,.2f}", "#334155")
        r_card(r2, "SALDO BRUTO", f"R$ {bal:,.2f}", C_ACCENT)
        r_card(r3, "RENDIMENTO", f"R$ {bal-inv:,.2f}", C_REAL)
        st.markdown("###")
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(y=evol, x=list(range(len(evol))), fill='tozeroy', line=dict(color=C_ACCENT, width=3), name="Patrimônio Total"))
        fig_s.add_trace(go.Scatter(y=[ini + (mes * i) for i in range(len(evol))], x=list(range(len(evol))), line=dict(color="#94A3B8", width=2, dash='dash'), name="Aporte Acumulado"))
        fig_s.update_layout(template="plotly_white", height=350, margin=dict(t=20,l=0,r=0,b=0), xaxis=dict(showgrid=False, title="Meses"), yaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ "), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_s, use_container_width=True)

elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Entenda os principais termos utilizados no mercado e na calculadora.</p>", unsafe_allow_html=True)
    def gloss_card(t, tx, c="#CBD5E1"): st.markdown(f"<div class='glossary-card' style='border-left: 4px solid {c};'><div class='gloss-title' style='color:{c};'>{t}</div><div class='gloss-text'>{tx}</div></div><br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1: 
        gloss_card("Taxa Selic", "Taxa básica de juros da economia. Define o custo do dinheiro no Brasil.", C_SELIC)
        gloss_card("IPCA", "Inflação oficial do país. Mede a perda do poder de compra.", C_IPCA)
        gloss_card("PIB", "Soma de todas as riquezas produzidas no país.", C_PIB)
    with c2: 
        gloss_card("CDI", "Referência da Renda Fixa. Quase idêntico à Selic, usado por bancos.", "#64748B")
        gloss_card("IGP-M", "Inflação do aluguel. Varia mais que o IPCA.", C_IGPM)
        gloss_card("Dólar PTAX", "Média oficial do dólar calculada pelo Banco Central.", C_DOLAR)
    
    st.markdown("---")
    c3, c4, c5 = st.columns(3, gap="medium")
    with c3: gloss_card("Pós-fixado", "Rende um % de um índice (ex: 100% do CDI). Acompanha os juros.", C_SELIC)
    with c4: gloss_card("Pré-fixado", "Taxa fixa combinada na compra. Você sabe exatamente quanto vai receber.", C_ACCENT)
    with c5: gloss_card("Híbrido (IPCA+)", "Parte fixa + Inflação. Garante ganho real acima da inflação.", C_IPCA)
    st.markdown("---"); st.caption("Fonte: Banco Central do Brasil.")
