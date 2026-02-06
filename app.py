import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hd3VqbHd3aHRoY2trZXBjYmFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDQxNDg1NiwiZXhwIjoyMDg1OTkwODU2fQ.gRDWM7dD2MP5SbqqKbRThTpO3YhjK359RW1HfdMxGao" # <--- USE A SERVICE_ROLE AQUI

try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Falha ao inicializar cliente Supabase.")

st.set_page_config(page_title="Jarvis Cloud", layout="centered")

# --- LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Sistema</h2>", unsafe_allow_html=True)
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            try:
                # Teste de consulta explícita
                res = supabase.table("usuarios_sistema").select("*").eq("login", u).eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            except Exception as e:
                st.error("Erro de API: Verifique se rodou o SQL no Supabase e se a KEY está correta.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    
    with st.sidebar:
        st.title(f"Olá, {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Admin"]) if user['role'] == 'admin' else "Scanner"
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE AQUI", key="s")
            st.form_submit_button("PROCESSAR", use_container_width=True)

        if input_scan:
            # Lógica de Bip Único
            check = supabase.table("registros_garantia").select("*").eq("codigo", input_scan).execute()
            if check.data:
                item = check.data[0]
                st.info(f"Produto já cadastrado. Expira em: {item['validade']}")
            else:
                val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": input_scan, "validade": val}).execute()
                st.success("✅ Cadastrado com 1 ano de garantia!")

    elif aba == "Admin":
        st.title("👥 Gestão de Usuários")
        users = supabase.table("usuarios_sistema").select("login, vencimento_assinatura").execute()
        st.table(pd.DataFrame(users.data))
