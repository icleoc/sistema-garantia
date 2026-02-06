import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro", layout="centered")

# --- LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        u = st.text_input("Usuário ou Email")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
            if res.data:
                st.session_state.user_data = res.data[0]
                st.rerun()
            else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    
    # --- LÓGICA DE ALERTA DE VENCIMENTO ---
    # Convertemos a data do banco para o formato de data do Python
    try:
        data_vencimento = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
        hoje = date.today()
        dias_restantes = (data_vencimento - hoje).days

        if 0 <= dias_restantes <= 5:
            st.warning(f"⚠️ **Atenção:** Sua licença expira em {dias_restantes} dias ({data_vencimento.strftime('%d/%m/%Y')}).")
        elif dias_restantes < 0:
            st.error(f"❌ **Licença Expirada:** Seu acesso venceu em {data_vencimento.strftime('%d/%m/%Y')}. Entre em contato com o suporte.")
            if user['role'] != 'admin':
                st.stop() # Bloqueia o uso do sistema para clientes vencidos
    except Exception as e:
        st.error("Erro ao processar data de vencimento.")

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else st.radio("Menu", ["Scanner"])
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        # O restante do seu código do scanner continua aqui...
        st.info("Aguardando leitura do scanner...")

    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão de Clientes")
        # O restante do código de gestão (listar/excluir/cadastrar) continua aqui...
