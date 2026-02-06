import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hd3VqbHd3aHRoY2trZXBjYmFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDQxNDg1NiwiZXhwIjoyMDg1OTkwODU2fQ.gRDWM7dD2MP5SbqqKbRThTpO3YhjK359RW1HfdMxGao" # Lembre-se de usar a Service Role para permissão total
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Cloud - Gestão", layout="centered")

# --- LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Sistema</h2>", unsafe_allow_html=True)
        u = st.text_input("Usuário ou Email")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
            if res.data:
                st.session_state.user_data = res.data[0]
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else "Scanner"
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE AQUI", key="s")
            st.form_submit_button("PROCESSAR", use_container_width=True)

        if input_scan:
            codigo = input_scan.strip()
            check = supabase.table("registros_garantia").select("*").eq("codigo", codigo).execute()
            if check.data:
                item = check.data[0]
                val = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                if datetime.now().date() <= val:
                    st.success(f"✅ EM GARANTIA: {val.strftime('%d/%m/%Y')}")
                else:
                    st.error(f"❌ VENCIDA EM: {val.strftime('%d/%m/%Y')}")
            else:
                val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": val}).execute()
                st.info(f"💾 CADASTRADO: {codigo} (1 ano de garantia)")

    # --- ABA: ADMIN (GESTÃO DE USUÁRIOS) ---
    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão de Clientes")
        
        tab_list, tab_cad, tab_edit = st.tabs(["Listar", "Cadastrar Novo", "Alterar Dados/Senha"])

        with tab_list:
            res = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura, role").execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)

        with tab_cad:
            with st.form("cad_user"):
                new_login = st.text_input("Login")
                new_email = st.text_input("E-mail")
                new_pass = st.text_input("Senha Inicial")
                new_venc = st.date_input("Vencimento Assinatura", value=datetime.now() + timedelta(days=30))
                if st.form_submit_button("Criar Usuário"):
                    supabase.table("usuarios_sistema").insert({
                        "login": new_login, "email": new_email, 
                        "senha": new_pass, "vencimento_assinatura": new_venc.isoformat()
                    }).execute()
                    st.success("Usuário criado com sucesso!")

        with tab_edit:
            st.subheader("Alterar Dados de Cliente")
            res_u = supabase.table("usuarios_sistema").select("login").execute()
            lista_u = [u['login'] for u in res_u.data]
            target = st.selectbox("Selecione o usuário para editar", lista_u)
            
            with st.form("edit_user"):
                new_e = st.text_input("Novo E-mail (Deixe em branco para não alterar)")
                new_p = st.text_input("Nova Senha (Deixe em branco para não alterar)")
                if st.form_submit_button("Salvar Alterações"):
                    updates = {}
                    if new_e: updates["email"] = new_e
                    if new_p: updates["senha"] = new_p
                    if updates:
                        supabase.table("usuarios_sistema").update(updates).eq("login", target).execute()
                        st.success(f"Dados de {target} atualizados!")
                    else:
                        st.warning("Nenhuma alteração informada.")
