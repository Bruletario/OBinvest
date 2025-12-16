import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from bcb import Expectativas # Mantemos apenas Expectativas da lib bcb
import warnings
import time
import os
import requests # IMPORTANTE: Necessário para burlar o bloqueio

# Configurações de Cache
DATA_FILE = "market_data_cache.csv" # Arquivo para salvar os dados
CACHE_EXPIRATION = 24 * 3600 # 24 horas em segundos (TTL)

# ==============================================================================
# 1. SETUP E ESTILIZACAO
# ==============================================================================
# config basica da pagina, titulo e layout
st.set_page_config(
    page_title="Monitor de Mercado",
    layout="wide",
    initial_sidebar_state="expanded"
)
warnings.filterwarnings("ignore")

# paleta de cores, mantendo aquele tema dark/clean q vc pediu
C_SIDEBAR = "#0F172A"
C_MAIN = "#F8FAFC"
C_ACCENT = "#F97316" # laranjinha padrao
C_TEXT_MAIN = "#1E293B"
C_TEXT_SIDE = "#FFFFFF"
C_INPUT_BG = "#1E293B"

# cores pros graficos
C_SELIC = "#334155"
C_IPCA = "#D97706"
C_REAL = "#059669"

# css pesadão pra sobrescrever o padrao do streamlit
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {C_MAIN};
        color: {C_TEXT_MAIN};
    }}

    /* tira o espaco em branco gigante do topo */
    header {{ background-color: transparent !important; }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100%;
    }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* sidebar azul escura */
    section[data-testid="stSidebar"] {{
        background-color: {C_SIDEBAR};
        border-right: 1px solid #1E293B;
    }}
    
    /* forca texto branco na sidebar pra dar leitura */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] div {{
        color: {C_TEXT_SIDE} !important;
    }}

    /* hack pra transformar radio button em menu estilo link */
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
    
    /* efeito hover bacana */
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: white !important;
    }}
    
    /* item selecionado fica laranja */
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {C_ACCENT} !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    /* estilizacao dos inputs pra nao ficar aquele cinza padrao feio */
    .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {C_INPUT_BG} !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 6px;
    }}
    .stDateInput svg {{ fill: white !important; }}

    /* botao atualizar da sidebar */
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

    /* botoes do carrossel (setinhas) */
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

    /* cards brancos com sombra suave */
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

    /* css especifico pro glossario */
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
# 2. FUNCOES DE DADOS (MANUAL PARA BURLAR BLOQUEIO)
# ==============================================================================

# Função auxiliar para fingir ser um navegador
def fetch_bcb_manual(codigo, nome_serie):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
    # Este header é o segredo para o BC não bloquear
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df[nome_serie] = pd.to_numeric(df['valor'])
            df.set_index('data', inplace=True)
            return df[[nome_serie]]
    except:
        return None
    return None

@st.cache_data(ttl=CACHE_EXPIRATION, show_spinner=False)
def get_data():
    """Tenta buscar a API do BC. Se falhar, carrega a versão mais recente do cache local."""
    df = pd.DataFrame()
    api_failed = True
    
    # 1. Tenta buscar a API (Este bloco só roda a cada 24h)
    for _ in range(2): 
        try:
            # Busca Selic (432) e IPCA (13522) separadamente "na mão"
            df_selic = fetch_bcb_manual(432, "Selic")
            df_ipca = fetch_bcb_manual(13522, "IPCA")
            
            if df_selic is not None and df_ipca is not None:
                # Junta os dois
                df_api = df_selic.join(df_ipca, how='inner').ffill().dropna()
                
                # Filtra os ultimos 10 anos
                hoje = datetime.today()
                start = (hoje - timedelta(days=365*10))
                df_api = df_api[df_api.index >= start]

                if not df_api.empty:
                    df = df_api
                    df.to_csv(DATA_FILE) # SUCESSO: SALVA A VERSÃO NOVA NO DISCO
                    api_failed = False
                    break
        except Exception:
            time.sleep(0.5)
            continue
            
    # 2. Se a API falhou, tenta carregar o último cache salvo
    if api_failed and os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
            st.info(f"ℹ️ Erro de conexão com o BC. Usando dados cacheados. Última atualização: {df.index[-1].strftime('%d/%m/%Y')}.")
        except Exception:
             # Se falhou ler o CSV (arquivo corrompido), retorna DF vazio
            return pd.DataFrame() 

    # 3. Retorna o DF (ou vazio se falhou e não tinha cache)
    return df 

# pega expectativa futura do relatorio focus
@st.cache_data(ttl=CACHE_EXPIRATION, show_spinner=False)
def get_focus():
    """Busca Focus, limitado também ao TTL de 24h."""
    try:
        em = Expectativas()
        ep = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        dt_lim = (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d')
        df = (ep.query().filter(ep.Data >= dt_lim).filter(ep.Suavizada == 'S').filter(ep.baseCalculo == 0).collect())
        # se der vazio, usa 4.5 como fallback de seguranca pra nao quebrar a tela
        return 4.5 if df.empty else float(df.sort_values('Data').iloc[-1]['Mediana'])
    except: return 4.5

# ==============================================================================
# 3. BARRA LATERAL (NAVEGACAO E FILTROS)
# ==============================================================================
df = get_data()
ipca_proj = get_focus()

# --- Fallback de Variáveis para o Simulador (Se df vazio) ---
if not df.empty:
    selic_h = df["Selic"].iloc[-1]
else:
    # Valores de referência se o DF estiver vazio
    selic_h = 11.25 

# Tratamento de erro: Mensagem e Desativação do Dashboard se não houver dados
if df.empty and st.session_state.get('nav') == "Dashboard":
    st.error("Erro de conexão persistente com o Banco Central. O Dashboard está indisponível.")
    st.warning("⚠️ O Simulador e o Glossário ainda estão operacionais com a última taxa conhecida.")

with st.sidebar:
    st.markdown(f"<div style='color:{C_ACCENT}; font-weight:800; font-size:1.2rem; margin-bottom:20px; padding-left:5px;'>MONITOR</div>", unsafe_allow_html=True)
    
    # menu principal
    nav = st.radio("Navegação", ["Dashboard", "Simulador", "Glossário"], label_visibility="collapsed", key='nav')
    st.markdown("<div style='margin-top:20px; border-top:1px solid #1E293B'></div>", unsafe_allow_html=True)
    
    df_filtered = df.copy()
    
    # filtro de data so aparece na dashboard
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
                st.markdown("###")
                
                # Botão de submissão DENTRO do formulário
                if st.form_submit_button("ATUALIZAR GRÁFICO"):
                    mask = (df.index.date >= d_ini) & (df.index.date <= d_fim)
                    df_filtered = df.loc[mask]
            else:
                 # Exibe aviso se não há dados
                 st.markdown("<p style='color: #F97316; font-weight: 600;'>Filtros indisponíveis (Sem dados).</p>", unsafe_allow_html=True)
                 st.form_submit_button("N/A", disabled=True) 

# ==============================================================================
# TELA 1: DASHBOARD
# ==============================================================================
if nav == "Dashboard":
    
    # Novo check de erro: se df estiver vazio, para esta seção
    if df.empty:
        st.stop()
    
    st.markdown("<h1>Monitor de Mercado</h1>", unsafe_allow_html=True)
    st.markdown("###")

    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para o período selecionado.")
        st.stop()

    # pega o ultimo dado DO FILTRO pra mostrar nos cards
    last = df_filtered.iloc[-1]
    v_selic, v_ipca = last["Selic"], last["IPCA"]
    # calculo de juro real (formula de fisher)
    v_real = ((1 + v_selic/100) / (1 + v_ipca/100) - 1) * 100
    ref = df_filtered.index[-1].strftime('%d/%m/%Y')

    # cards principais
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

    # grafico de linha
    st.markdown("### Evolução Histórica")
    with st.container():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["Selic"], name="Selic", line=dict(color=C_SELIC, width=3)))
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered["IPCA"], name="IPCA", line=dict(color=C_ACCENT, width=3)))
        
        fig.update_layout(
            template="plotly_white", 
            height=320,
            margin=dict(t=20, l=10, r=10, b=10),
            legend=dict(orientation="h", y=1.1, x=0),
            hovermode="x unified",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0", ticksuffix="%")
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- logica do carrossel da tabela ---
    if 'table_page' not in st.session_state:
        st.session_state.table_page = 0
    
    # agrupa por mes pra tabela nao ficar gigante (pega o ultimo dia do mes)
    df_monthly = df.resample('M').last()
    df_rev = df_monthly.sort_index(ascending=False).copy()
    df_rev["Juro Real"] = ((1 + df_rev["Selic"]/100) / (1 + df_rev["IPCA"]/100) - 1) * 100
    
    ITENS = 6
    total = len(df_rev)
    start = st.session_state.table_page * ITENS
    end = start + ITENS
    df_view = df_rev.iloc[start:end]

    # texto com as datas que estao aparecendo na tabela
    if not df_view.empty:
        date_rec = df_view.index[0].strftime('%d/%m/%Y')
        date_old = df_view.index[-1].strftime('%d/%m/%Y')
        periodo_str = f"{date_old} - {date_rec}"
    else:
        periodo_str = ""

    st.markdown("---")
    
    # botoes de navegacao da tabela
    col_t_1, col_t_2, col_t_3 = st.columns([8, 1, 1])
    
    with col_t_1:
        st.markdown(f"### Dados Detalhados <span style='font-size:1rem; color:#64748B; font-weight:400; margin-left:10px'>({periodo_str})</span>", unsafe_allow_html=True)
    
    with col_t_2:
        if st.button("<", key="btn_prev", disabled=(st.session_state.table_page == 0)):
            st.session_state.table_page -= 1
            st.rerun()
            
    with col_t_3:
        if st.button(">", key="btn_next", disabled=(end >= total)):
            st.session_state.table_page += 1
            st.rerun()

    # formatacao da data na tabela
    df_view.index = df_view.index.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_view.style.format("{:.2f}%")
        .applymap(lambda x: f"color:{C_SELIC};font-weight:600", subset=["Selic"])
        .applymap(lambda x: f"color:{C_IPCA};font-weight:600", subset=["IPCA"])
        .applymap(lambda x: f"color:{C_REAL};font-weight:600", subset=["Juro Real"]),
        use_container_width=True,
        height=260
    )

# ==============================================================================
# TELA 2: SIMULADOR
# ==============================================================================
elif nav == "Simulador":
    st.markdown("<h1>Simulador de Rentabilidade</h1>", unsafe_allow_html=True)
    st.markdown("###")
    
    col_in, col_out = st.columns([1.2, 2])
    
    with col_in:
        st.markdown("#### Parâmetros")
        
        # inputs financeiros sem travas chatas
        ini = st.number_input("Aporte Inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        mes = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=100.0, step=50.0, format="%.2f")
        anos = st.slider("Tempo (Anos)", 1, 30, 5)
        
        st.markdown("#### Indexador")
        tipo = st.selectbox("Escolha o índice", ["Pós-fixado (CDI)", "IPCA +", "Pré-fixado"], label_visibility="collapsed")
        
        # selic_h vem do fallback se df estiver vazio
        taxa = 0.0
        
        # logica de calculo da taxa anual
        if tipo == "Pós-fixado (CDI)":
            pct = st.number_input("Rentabilidade (% do CDI)", min_value=0.0, value=100.0)
            taxa = selic_h * (pct/100)
            st.caption(f"CDI Atual (Ref. Selic): {selic_h:.2f}% a.a.")
        elif tipo == "IPCA +":
            fx = st.number_input("Taxa Fixa (IPCA + %)", min_value=0.0, value=6.0)
            taxa = ((1+ipca_proj/100)*(1+fx/100)-1)*100
            st.caption(f"IPCA Projetado (Focus): {ipca_proj:.2f}% a.a.")
        else:
            taxa = st.number_input("Taxa Pré-fixada (% a.a.)", min_value=0.0, value=12.0)
    
    # calculo mes a mes
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
        
        # cards de resultado
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
        
        # grafico de area
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(y=evol, x=list(range(len(evol))), fill='tozeroy', line=dict(color=C_ACCENT, width=3), name="Patrimônio"))
        fig_s.update_layout(
            template="plotly_white", 
            height=350, 
            margin=dict(t=20,l=0,r=0,b=0),
            xaxis=dict(showgrid=False, title="Meses"),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0", tickprefix="R$ ")
        )
        st.plotly_chart(fig_s, use_container_width=True)

# ==============================================================================
# TELA 3: GLOSSÁRIO
# ==============================================================================
elif nav == "Glossário":
    st.markdown("<h1>Glossário Financeiro</h1>", unsafe_allow_html=True)
    st.markdown("Entenda os principais termos utilizados no mercado e na calculadora.")
    
    # funcao auxiliar pra criar os cards de texto
    def gloss_card(title, text):
        st.markdown(f"""
        <div class="glossary-card">
            <div class="gloss-title">{title}</div>
            <div class="gloss-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)

    # BLOCO 1: INDICADORES
    st.markdown("### Indicadores de Mercado")
    c1, c2 = st.columns(2)
    
    with c1:
        gloss_card("Taxa Selic", "É a taxa básica de juros da economia brasileira. Ela influencia todas as outras taxas de juros do país, como as de empréstimos, financiamentos e aplicações financeiras. Definida pelo COPOM a cada 45 dias.")
        st.markdown("###")
        gloss_card("IPCA", "Índice Nacional de Preços ao Consumidor Amplo. É o termômetro oficial da inflação no Brasil. Se o IPCA sobe, o seu dinheiro perde poder de compra.")

    with c2:
        gloss_card("CDI (Certificado de Depósito Interbancário)", "É a taxa que os bancos cobram para emprestar dinheiro entre si. Na prática, o CDI anda quase igual à Selic. A maioria dos investimentos de Renda Fixa (CDB, LCI) rende uma % do CDI.")
        st.markdown("###")
        gloss_card("Juro Real", "É o ganho 'de verdade'. Se você ganhou 10% no investimento, mas a inflação foi 4%, seu Juro Real foi de aproximadamente 6%. É o quanto seu patrimônio cresceu acima do aumento dos preços.")

    # divisoria pedida
    st.markdown("---")

    # BLOCO 2: TIPOS DE INVESTIMENTO
    st.markdown("### Tipos de Rentabilidade")
    c3, c4, c5 = st.columns(3)
    
    with c3:
        gloss_card("Pós-fixado", "Você não sabe exatamente quanto vai ganhar em Reais no final. A rentabilidade segue um índice (ex: 100% do CDI). Se o juro subir, você ganha mais. Se cair, ganha menos. Ideal para reserva de emergência.")
    
    with c4:
        gloss_card("Pré-fixado", "A taxa é combinada na hora da compra (ex: 12% ao ano). Não importa se a Selic subir ou cair, ou se a inflação explodir, você receberá exatamente os 12% combinados.")
    
    with c5:
        gloss_card("Híbrido (IPCA+)", "Combina os dois mundos. Ele paga uma parte fixa (ex: 6%) mais a variação da inflação (IPCA). É o investimento mais seguro para manter seu poder de compra no longo prazo.")

    st.markdown("---")
    st.caption("Fonte dos dados: Banco Central do Brasil (SGS e Focus). Atualização automática.")
