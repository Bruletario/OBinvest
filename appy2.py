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
    page_title="Monitor de Mercado - OBINVEST",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cores e Variáveis
C_SIDEBAR = "#0F172A"
C_MAIN = "#F8FAFC"
C_ACCENT = "#F97316"
C_TEXT_MAIN = "#1E293B"
C_TEXT_SIDE = "#FFFFFF"
C_INPUT_BG = "#1E293B"
C_SELIC = "#334155"
C_IPCA = "#D97706"

# Injeção de CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {C_MAIN};
        color: {C_TEXT_MAIN};
    }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 2rem !important; }}
    header {{ background-color: transparent !important; }}
    
    /* INPUTS & WIDGETS */
    .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important; color: white !important;
        border: 1px solid #334155 !important; border-radius: 6px;
    }}
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: {C_SIDEBAR}; border-right: 1px solid #1E293B; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, label, div {{ color: {C_TEXT_SIDE}; }}
    
    /* METRIC CARDS */
    .metric-card {{
        background-color: #FFFFFF; border-radius: 8px; padding: 15px; border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 100%; display: flex; flex-direction: column; justify-content: space-between;
        transition: transform 0.2s;
    }}
    .metric-card:hover {{ border-color: {C_ACCENT}; transform: translateY(-2px); }}
    .metric-label {{ font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 5px; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 800; color: {C_TEXT_MAIN}; line-height: 1.1; margin-bottom: 5px; }}
    .metric-delta {{ font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 4px; }}
    
    /* BOTÕES DENTRO DOS CARDS (Hack CSS) */
    .stButton button {{
        width: 100%; border-radius: 6px; font-weight: 600; font-size: 0.8rem;
        background-color: #F1F5F9; color: #475569; border: 1px solid #E2E8F0;
        padding: 4px 8px; min-height: 0px; height: 32px; margin-top: 10px;
    }}
    .stButton button:hover {{ background-color: {C_ACCENT}; color: white; border-color: {C_ACCENT}; }}

    h1 {{ font-weight: 800; color: {C_TEXT_MAIN}; margin: 0; font-size: 1.8rem; }}
    .section-caption {{ font-size: 0.9rem; color: #64748B; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DADOS
# ==============================================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_data():
    """Busca dados de séries temporais (SGS)"""
    for attempt in range(3):
        try:
            hoje = datetime.today()
            start = (hoje - timedelta(days=365*10)).strftime("%Y-%m-%d")
            # 432: Selic Meta, 13522: IPCA 12m, 189: IGP-M 12m, 1: Dolar
            codigos = {"Selic": 432, "IPCA": 13522, "IGPM": 189, "Dolar": 1} 
            df = sgs.get(codigos, start=start).ffill().dropna()
            if not df.empty: return df
        except Exception:
            time.sleep(1)
            continue
    return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def get_focus_summary():
    """Busca dados atuais e históricos do Focus para o gráfico de barras"""
    res = {"IPCA_Proj": 4.5, "PIB_Proj": 2.0, "History_IPCA": []}
    try:
        em = Expectativas()
        
        # 1. Projeções Atuais (PIB e IPCA para cards)
        dt_lim = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        ep_ipca = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        df_ipca = (ep_ipca.query().filter(ep_ipca.Data >= dt_lim).filter(ep_ipca.Suavizada == 'S').filter(ep_ipca.baseCalculo == 0).collect())
        if not df_ipca.empty: res["IPCA_Proj"] = float(df_ipca.sort_values('Data').iloc[-1]['Mediana'])

        ep_anual = em.get_endpoint('ExpectativasMercadoAnual')
        ano_atual = datetime.now().year
        df_pib = (ep_anual.query().filter(ep_anual.Data >= dt_lim).filter(ep_anual.Indicador == 'PIB Total').filter(ep_anual.DataReferencia == ano_atual).collect())
        if not df_pib.empty: res["PIB_Proj"] = float(df_pib.sort_values('Data').iloc[-1]['Mediana'])

        # 2. Dados Históricos para o Gráfico de Barras (Últimos 4 anos + Atual)
        anos_hist = range(ano_atual - 4, ano_atual + 1)
        history_data = []
        
        # Busca projeção que o mercado tinha em JANEIRO de cada ano para aquele ano
        for ano in anos_hist:
            dt_ini_ano = f"{ano}-01-01"
            dt_fim_ano = f"{ano}-02-28" # Janela de busca no inicio do ano
            
            try:
                # Busca expectativa do inicio do ano
                df_hist = (ep_anual.query()
                           .filter(ep_anual.Indicador == 'IPCA')
                           .filter(ep_anual.DataReferencia == ano)
                           .filter(ep_anual.Data >= dt_ini_ano)
                           .filter(ep_anual.Data <= dt_fim_ano)
                           .collect())
                
                projecao = df_hist['Mediana'].mean() if not df_hist.empty else None
                history_data.append({"Ano": ano, "Projecao_Focus": projecao})
            except:
                continue
                
        res["History_IPCA"] = pd.DataFrame(history_data)
        return res
    except:
        return res

with st.spinner('Carregando dados do Banco Central...'):
    df = get_data()
    focus_data = get_focus_summary()

if df.empty:
    st.error("Erro ao conectar com API do Banco Central.")
    st.stop()

# ==============================================================================
# 3. BARRA LATERAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    # LOGO SOLICITADO
    try:
        st.image("Logo OBINVEST Branco.png", use_container_width=True)
    except:
        st.warning("Logo não encontrado.")
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # MUDANÇA DE NOME SOLICITADA
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.1rem; margin-bottom:15px; letter-spacing:1px;'>DADOS ECONÔMICOS</div>", unsafe_allow_html=True)
    
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"], label_visibility="collapsed")
    
    st.markdown("<div style='margin-top:auto; border-top:1px solid #334155; margin-top: 30px; padding-top:10px;'></div>", unsafe_allow_html=True)
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m/%Y')}")

# ==============================================================================
# 4. DASHBOARD - LÓGICA PRINCIPAL
# ==============================================================================
if nav == "Dashboard":
    
    # Inicialização do estado para controle dos gráficos
    if 'selected_chart' not in st.session_state:
        st.session_state.selected_chart = 'default' # Padrão: Selic x IPCA

    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-caption'>Visão unificada dos principais indicadores e projeções.</p>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # LAYOUT DOS 5 CARDS (TODOS DE UMA VEZ)
    # ---------------------------------------------------------
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # Colunas para os 5 cards
    c1, c2, c3, c4, c5 = st.columns(5)

    def card_template(col, label, value, delta, key_chart, is_pib=False):
        # Definição de cores e setas
        color_delta = "#94A3B8"
        arrow = ""
        
        if delta != 0 and delta is not None:
            if is_pib:
                # Lógica PIB (Positivo é bom)
                if delta > 0: color_delta = "#10B981"; arrow = "▲"
                else: color_delta = "#EF4444"; arrow = "▼"
            elif "DÓLAR" in label or "IGP-M" in label or "IPCA" in label:
                # Lógica Inflação/Dolar (Subir é ruim geralmente, mas aqui usamos verde p/ queda)
                if delta > 0: color_delta = "#EF4444"; arrow = "▲"
                else: color_delta = "#10B981"; arrow = "▼"
            else:
                # Selic e outros
                if delta > 0: color_delta = "#10B981"; arrow = "▲"
                else: color_delta = "#EF4444"; arrow = "▼"
        
        delta_fmt = f"{arrow} {abs(delta):.2f}%" if delta is not None else "-"
        if "DÓLAR" in label and delta is not None: delta_fmt = f"{arrow} R$ {abs(delta):.4f}"

        with col:
            # HTML do Card
            st.markdown(f"""
            <div class='metric-card'>
                <div>
                    <div class='metric-label'>{label}</div>
                    <div class='metric-value'>{value}</div>
                    <div class='metric-delta' style='color:{color_delta}'>{delta_fmt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão invisível de estilo para acionar a troca de gráfico
            if st.button("Ver Gráfico", key=f"btn_{key_chart}"):
                st.session_state.selected_chart = key_chart

    # 1. SELIC
    card_template(c1, "TAXA SELIC", f"{latest['Selic']:.2f}%", latest['Selic'] - prev['Selic'], 'selic')
    
    # 2. IPCA
    card_template(c2, "IPCA (12M)", f"{latest['IPCA']:.2f}%", latest['IPCA'] - prev['IPCA'], 'ipca')
    
    # 3. DÓLAR
    card_template(c3, "DÓLAR PTAX", f"R$ {latest['Dolar']:.4f}", latest['Dolar'] - prev['Dolar'], 'dolar')
    
    # 4. IGP-M
    card_template(c4, "IGP-M (12M)", f"{latest['IGPM']:.2f}%", latest['IGPM'] - prev['IGPM'], 'igpm')
    
    # 5. PIB (Projeção)
    pib_val = focus_data["PIB_Proj"]
    card_template(c5, f"PIB ({datetime.now().year})", f"{pib_val:.2f}%", pib_val, 'pib', is_pib=True)

    # ---------------------------------------------------------
    # ÁREA GRÁFICA (Dinâmica)
    # ---------------------------------------------------------
    st.markdown("---")
    
    chart_mode = st.session_state.selected_chart
    
    # Título dinâmico do gráfico
    titles = {
        'default': "Panorama: Selic vs IPCA (Histórico)",
        'selic': "Evolução da Taxa Selic",
        'ipca': "Inflação: Realizado vs Projetado (Focus)",
        'dolar': "Cotação do Dólar (PTAX)",
        'igpm': "Índice Geral de Preços - Mercado (IGP-M)",
        'pib': "Evolução Recente (Série Histórica)"
    }
    
    st.subheader(titles.get(chart_mode, "Gráfico"))
    
    # Container do gráfico
    with st.container():
        # Filtro de data (comum a todos, exceto o comparativo de barras)
        if chart_mode != 'ipca':
            d_max = df.index.max().date()
            start_def = d_max - timedelta(days=1095) # 3 anos padrão
            c_filter, _ = st.columns([2, 4])
            with c_filter:
                ini_date = st.date_input("Início do período", start_def, format="DD/MM/YYYY")
            
            mask = df.index.date >= ini_date
            df_g = df.loc[mask]
        else:
            df_g = df # Placeholder
        
        fig = go.Figure()

        # LOGICA DOS GRÁFICOS
        
        # 1. DEFAULT: SELIC x IPCA
        if chart_mode == 'default' or chart_mode == 'selic':
            fig.add_trace(go.Scatter(x=df_g.index, y=df_g['Selic'], name='Selic', line=dict(color=C_SELIC, width=3)))
            if chart_mode == 'default':
                fig.add_trace(go.Scatter(x=df_g.index, y=df_g['IPCA'], name='IPCA', line=dict(color=C_IPCA, width=3, dash='dot')))
            fig.update_yaxes(title="Taxa (%)")

        # 2. GRÁFICO ESPECÍFICO DE INFLAÇÃO (BARRAS: REALIZADO vs PROJETADO)
        elif chart_mode == 'ipca':
            st.caption("Comparativo: Inflação acumulada no ano (SGS) vs. O que o mercado projetava em Janeiro do mesmo ano (Focus).")
            
            # Preparar dados
            df_hist_focus = focus_data["History_IPCA"]
            
            if not df_hist_focus.empty:
                # Pegar inflação realizada anual (aproximada pelo acumulado 12m de Dezembro de cada ano)
                realizado_vals = []
                anos = df_hist_focus['Ano'].tolist()
                
                for ano in anos:
                    # Tenta pegar valor de dezembro, se não tiver (ano corrente), pega ultimo disponivel
                    try:
                        val = df[df.index.year == ano]['IPCA'].iloc[-1]
                        realizado_vals.append(val)
                    except:
                        realizado_vals.append(0)
                
                fig.add_trace(go.Bar(
                    x=anos, 
                    y=realizado_vals, 
                    name='IPCA Realizado',
                    marker_color=C_IPCA,
                    text=[f"{x:.2f}%" for x in realizado_vals],
                    textposition='auto'
                ))
                
                fig.add_trace(go.Bar(
                    x=anos, 
                    y=df_hist_focus['Projecao_Focus'], 
                    name='Projeção Focus (Jan)',
                    marker_color='#94A3B8',
                    text=[f"{x:.2f}%" if pd.notnull(x) else "" for x in df_hist_focus['Projecao_Focus']],
                    textposition='auto'
                ))
                
                fig.update_layout(barmode='group')
            else:
                st.warning("Dados históricos de projeção indisponíveis no momento.")

        # 3. DÓLAR
        elif chart_mode == 'dolar':
            fig.add_trace(go.Scatter(x=df_g.index, y=df_g['Dolar'], name='Dólar', line=dict(color='#10B981', width=2), fill='tozeroy'))
            fig.update_yaxes(tickprefix="R$ ")

        # 4. IGPM
        elif chart_mode == 'igpm':
            fig.add_trace(go.Scatter(x=df_g.index, y=df_g['IGPM'], name='IGP-M', line=dict(color='#8B5CF6', width=3)))
        
        # 5. PIB (Como SGS não traz PIB mensal fácil, usamos gráfico dummy ou mantemos vazio)
        elif chart_mode == 'pib':
             st.info("O PIB é divulgado trimestralmente. Exibindo projeção anual e histórico recente.")
             # Plot simples de evolução apenas ilustrativo
             fig.add_trace(go.Scatter(x=df_g.index, y=[focus_data["PIB_Proj"]]*len(df_g), name=f'Projeção {datetime.now().year}', line=dict(color='#EAB308', dash='dash')))

        # Configuração Geral do Layout do Gráfico
        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=30, b=0, l=0, r=0),
            legend=dict(orientation="h", y=1.1, x=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Botão para resetar
        if chart_mode != 'default':
            if st.button("Voltar ao Padrão (Selic x IPCA)"):
                st.session_state.selected_chart = 'default'
                st.rerun()

# ==============================================================================
# 5. SIMULADOR E GLOSSÁRIO (Mantidos conforme original, apenas recuo de identação)
# ==============================================================================
elif nav == "Simulador":
    st.markdown("<h1>Simulador de Rentabilidade</h1>", unsafe_allow_html=True)
    col_in, col_out = st.columns([1, 2])
    with col_in:
        st.markdown("#### Parâmetros")
        ini = st.number_input("Aporte Inicial (R$)", min_value=0.0, value=1000.0)
        mes = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=100.0)
        anos = st.slider("Tempo (Anos)", 1, 30, 5)
        tipo = st.selectbox("Escolha o índice", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"])
        
        selic_h = df["Selic"].iloc[-1]
        taxa = 0.0
        if "CDI" in tipo:
            pct = st.number_input("% do CDI", value=100.0)
            taxa = selic_h * (pct/100)
        elif "IPCA" in tipo:
            fx = st.number_input("Taxa Fixa (%)", value=6.0)
            taxa = ((1+focus_data["IPCA_Proj"]/100)*(1+fx/100)-1)*100
        else:
            taxa = st.number_input("Taxa Pré (% a.a.)", value=12.0)

    with col_out:
        periods = anos * 12
        r_men = (1+taxa/100)**(1/12)-1
        vals = [ini]
        curr = ini
        for _ in range(periods):
            curr = curr * (1+r_men) + mes
            vals.append(curr)
        
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("Total Acumulado", f"R$ {curr:,.2f}")
        c_res1.metric("Total Investido", f"R$ {ini + (mes*periods):,.2f}")
        
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(y=vals, fill='tozeroy', line=dict(color=C_ACCENT)))
        fig_sim.update_layout(template="plotly_white", title="Evolução Patrimonial", height=350)
        st.plotly_chart(fig_sim, use_container_width=True)

elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    st.info("Dicionário de termos utilizados na aplicação.")
    # (Mantido estrutura simples para brevidade, já que o foco era o dashboard)
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Selic:** Taxa básica de juros da economia.")
        st.markdown("**IPCA:** Índice oficial de inflação.")
    with cols[1]:
        st.markdown("**Focus:** Relatório semanal do BC com projeções de mercado.")
        st.markdown("**IGP-M:** Inflação composta, muito usada em aluguéis.")
