import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURAÇÕES SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "SUA_SECRET_KEY_AQUI" # Coloque sua Secret Key aqui
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Jarvis Ultra-Scan Cloud", layout="centered")

st.markdown("""
    <style>
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .main-title { text-align: center; }
    .stTextInput > div > div > input { text-align: center; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN COM VALIDAÇÃO DE ASSINATURA ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("<h1 class='main-title'>🔒 Acesso ao Sistema</h1>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário", placeholder="Digite seu login")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        
        if st.button("Entrar", use_container_width=True):
            res = supabase.table("usuarios_sistema").select("*").eq("login", usuario).eq("senha", senha).execute()
            
            if res.data:
                user = res.data[0]
                data_vencimento = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
                
                if datetime.now().date() > data_vencimento:
                    st.error(f"❌ Assinatura expirada em {data_vencimento.strftime('%d/%m/%Y')}. Regularize seu acesso.")
                elif not user['ativo']:
                    st.error("❌ Usuário desativado pelo administrador.")
                else:
                    st.session_state.user_data = user
                    st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        return False
    return True

if verificar_login():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("⚙️ Configurações")
        uploaded_logo = st.file_uploader("Trocar Logo da Empresa", type=["png", "jpg", "jpeg"])
        prazo_garantia = st.number_input("Meses de Garantia (Saída)", value=12)
        if st.button("Sair do Sistema"):
            st.session_state.user_data = None
            st.rerun()

    # --- LOGO E TÍTULO ---
    if uploaded_logo:
        st.image(uploaded_logo, width=220)
    
    st.markdown(f"<h3 style='text-align: center;'>🛡️ Checkpoint de Garantia</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Bem-vindo, {st.session_state.user_data['login'].capitalize()}</p>", unsafe_allow_html=True)

    # --- CAMPO DO SCANNER (AUTO-ENVIO) ---
    # O foco automático em HTML é difícil no Streamlit, 
    # mas o campo limpa ao dar Enter (enviado pelo scanner).
    with st.form("scan_form", clear_on_submit=True):
        st.markdown("<p style='text-align: center; color: gray;'>Aguardando Bip...</p>", unsafe_allow_html=True)
        input_scanner = st.text_input("SCANNER", key="scanner_input", label_visibility="collapsed")
        # O botão abaixo fica invisível ou discreto, o Enter do scanner ativa ele
        st.form_submit_button("PROCESSANDO...", use_container_width=True)

    if input_scanner:
        codigo = input_scanner.strip()
        
        # 1. CONSULTA NO BANCO
        res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).execute()
        
        if res.data:
            item = res.data[0]
            # Ajuste de timezone para comparação
            data_validade = datetime.fromisoformat(item['validade'].split('+')[0]).date()
            hoje = datetime.now().date()
            
            if hoje <= data_validade:
                st.success(f"✅ DENTRO DA GARANTIA")
                st.info(f"ID: {codigo} | Expira em: {data_validade.strftime('%d/%m/%Y')}")
            else:
                st.error(f"❌ GARANTIA EXPIRADA")
                st.warning(f"ID: {codigo} | Venceu em: {data_validade.strftime('%d/%m/%Y')}")
        
        # 2. REGISTRO (PRODUTO NOVO)
        else:
            validade = datetime.now() + timedelta(days=prazo_garantia * 30)
            novo_registro = {
                "codigo": codigo,
                "validade": validade.isoformat()
            }
            supabase.table("registros_garantia").insert(novo_registro).execute()
            st.success(f"💾 CADASTRADO: {codigo}")
            st.caption(f"Garantia válida até: {validade.strftime('%d/%m/%Y')}")

    # --- HISTÓRICO RECENTE ---
    st.divider()
    historico = supabase.table("registros_garantia").select("codigo, data_saida, validade").order("data_saida", desc=True).limit(5).execute()
    if historico.data:
        st.subheader("📋 Últimas Saídas")
        df_hist = pd.DataFrame(historico.data)
        st.dataframe(df_hist, use_container_width=True)
