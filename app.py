import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURAÇÕES SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "SUA_SECRET_KEY_AQUI" # Substitua pela chave que você me enviou
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Jarvis Ultra-Scan Cloud", layout="centered")

st.markdown("""
    <style>
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .main-title { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
def login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if not st.session_state.autenticado:
        st.markdown("<h1 class='main-title'>🔒 Acesso Restrito</h1>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if usuario == "admin" and senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")
        return False
    return True

if login():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("⚙️ Painel")
        uploaded_logo = st.file_uploader("Logo da Empresa", type=["png", "jpg", "jpeg"])
        prazo_meses = st.number_input("Garantia (Meses)", value=12)
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

    if uploaded_logo:
        st.image(uploaded_logo, width=250)
    
    st.markdown("<h1 class='main-title'>🛡️ Checkpoint de Garantia</h1>", unsafe_allow_html=True)

    # --- CAMPO DO SCANNER ---
    with st.form("scan_form", clear_on_submit=True):
        st.info("Aguardando bip do scanner...")
        input_scanner = st.text_input("SCANNER ATIVO", key="scanner_input", label_visibility="collapsed")
        st.form_submit_button("PROCESSANDO...", use_container_width=True)

    if input_scanner:
        codigo = input_scanner.strip()
        
        # 1. CONSULTA NO SUPABASE
        res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).execute()
        
        if res.data:
            item = res.data[0]
            data_validade = datetime.fromisoformat(item['validade'].replace('Z', '+00:00'))
            hoje = datetime.now(data_validade.tzinfo)
            
            if hoje <= data_validade:
                st.success(f"✅ DENTRO DA GARANTIA")
                st.metric("ID: " + codigo, "VÁLIDO", delta=f"Expira em {data_validade.strftime('%d/%m/%Y')}")
            else:
                st.error(f"❌ GARANTIA EXPIRADA")
                st.metric("ID: " + codigo, "VENCIDO", delta=f"Venceu em {data_validade.strftime('%d/%m/%Y')}", delta_color="inverse")
        
        # 2. REGISTRO NO SUPABASE
        else:
            validade = datetime.now() + timedelta(days=prazo_meses * 30)
            novo_registro = {
                "codigo": codigo,
                "validade": validade.isoformat()
            }
            supabase.table("registros_garantia").insert(novo_registro).execute()
            st.success(f"💾 CADASTRADO COM SUCESSO: {codigo}")
            st.info(f"Garantia válida até: {validade.strftime('%d/%m/%Y')}")

    # --- HISTÓRICO (BUSCANDO DO BANCO) ---
    st.divider()
    st.subheader("📋 Últimos Registros no Banco")
    historico = supabase.table("registros_garantia").select("*").order("data_saida", desc=True).limit(10).execute()
    if historico.data:
        df = pd.DataFrame(historico.data)
        st.dataframe(df, use_container_width=True)
