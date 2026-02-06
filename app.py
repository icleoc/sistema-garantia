import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

# --- GERENCIADOR DE COOKIES ---
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def verificar_login():
    # Tenta recuperar o login salvo no Cookie
    cookie_user = cookie_manager.get('jarvis_user')
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    # Se já existe dado no cookie e não na sessão, restaura a sessão
    if cookie_user and st.session_state.user_data is None:
        try:
            res = supabase.table("usuarios_sistema").select("*").eq("login", cookie_user).execute()
            if res.data:
                st.session_state.user_data = res.data[0]
                return True
        except: pass

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            manter_logado = st.checkbox("Permanecer logado por 24h")
            
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    if manter_logado:
                        # Salva o cookie por 1 dia (86400 segundos)
                        cookie_manager.set('jarvis_user', st.session_state.user_data['login'], expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    # (Restante da lógica de Alerta de Vencimento, Scanner e Admin mantida...)
    
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        if st.button("Sair (Logout)"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()
