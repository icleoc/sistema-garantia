import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Jarvis Ultra-Scan", layout="centered")

# CSS para centralizar imagens e ajustar o design
st.markdown("""
    <style>
    .stImage > img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    .main-title {
        text-align: center;
    }
    </style>
    """, unsafe_allow_manager=True)

# --- SISTEMA DE LOGIN ---
def login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h1 class='main-title'>🔒 Acesso Restrito</h1>", unsafe_allow_html=True)
        with st.container():
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == "admin" and senha == "1234":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        return False
    return True

if login():
    # Inicialização do Banco de Dados em Cache
    if 'db_vendas' not in st.session_state:
        st.session_state.db_vendas = {}

    # --- BARRA LATERAL (Configurações Ocultas) ---
    with st.sidebar:
        st.title("⚙️ Configurações")
        uploaded_logo = st.file_uploader("Upload da Logo", type=["png", "jpg", "jpeg"])
        prazo_meses = st.number_input("Garantia (Meses)", value=12)
        if st.button("Sair do Sistema"):
            st.session_state.autenticado = False
            st.rerun()

    # --- EXIBIÇÃO DA LOGO CENTRALIZADA ---
    if uploaded_logo:
        st.image(uploaded_logo, width=250)
    
    st.markdown("<h1 class='main-title'>🛡️ Checkpoint de Garantia</h1>", unsafe_allow_html=True)

    # --- CAMPO DO SCANNER ---
    with st.form("scan_form", clear_on_submit=True):
        st.info("Aguardando bip do scanner...")
        input_scanner = st.text_input("SCANNER ATIVO", key="scanner_input", label_visibility="collapsed")
        submit = st.form_submit_button("PROCESSANDO...", use_container_width=True)

    if input_scanner:
        codigo = input_scanner.strip()
        
        # 1. CONSULTA
        if codigo in st.session_state.db_vendas:
            item = st.session_state.db_vendas[codigo]
            hoje = datetime.now()
            
            if hoje <= item["validade"]:
                st.success(f"✅ DENTRO DA GARANTIA")
                st.metric("ID: " + codigo, "STATUS: VÁLIDO", delta=f"Expira em {item['validade'].strftime('%d/%m/%Y')}")
            else:
                st.error(f"❌ GARANTIA EXPIRADA")
                st.metric("ID: " + codigo, "STATUS: VENCIDO", delta=f"Venceu em {item['validade'].strftime('%d/%m/%Y')}", delta_color="inverse")
        
        # 2. REGISTRO
        else:
            data_saida = datetime.now()
            validade = data_saida + timedelta(days=prazo_meses * 30)
            st.session_state.db_vendas[codigo] = {"data_saida": data_saida, "validade": validade}
            
            st.success(f"💾 CADASTRADO: {codigo}")
            st.info(f"Garantia válida até: {validade.strftime('%d/%m/%Y')}")

    # --- TABELA DE HISTÓRICO ---
    if st.session_state.db_vendas:
        st.divider()
        st.subheader("📋 Últimos Registros")
        df = pd.DataFrame.from_dict(st.session_state.db_vendas, orient='index')
        df.index.name = "Código/Serial"
        df['data_saida'] = df['data_saida'].dt.strftime('%d/%m/%Y')
        df['validade'] = df['validade'].dt.strftime('%d/%m/%Y')
        st.dataframe(df.tail(10), use_container_width=True)
