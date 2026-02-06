import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
# Use a service_role key para ter permissão de exclusão
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
    
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else "Scanner"
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

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
                else: st.error(f"❌ VENCIDA EM: {val.strftime('%d/%m/%Y')}")
            else:
                val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": val}).execute()
                st.info(f"💾 CADASTRADO: {codigo} (1 ano)")

    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão de Clientes")
        
        tab_list, tab_cad, tab_edit = st.tabs(["Listar/Excluir", "Cadastrar Novo", "Alterar Dados"])

        with tab_list:
            res = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                st.dataframe(df, use_container_width=True)
                
                st.divider()
                u_excluir = st.selectbox("Selecionar Cliente para EXCLUIR", [u['login'] for u in res.data])
                # Correção do erro da imagem: removido parâmetros incompatíveis
                if st.button(f"🗑️ Confirmar Exclusão de {u_excluir}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_excluir).execute()
                    st.success(f"Usuário {u_excluir} removido!")
                    st.rerun()

        with tab_cad:
            with st.form("cad"):
                nl, ne, ns = st.text_input("Login"), st.text_input("Email"), st.text_input("Senha")
                nv = st.date_input("Vencimento", value=datetime.now() + timedelta(days=30))
                if st.form_submit_button("Cadastrar"):
                    supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat()}).execute()
                    st.success("Criado!")

        with tab_edit:
            res_e = supabase.table("usuarios_sistema").select("login").eq("role", "cliente").execute()
            u_edit = st.selectbox("Editar Usuário", [u['login'] for u in res_e.data])
            with st.form("edit"):
                ne2, ns2 = st.text_input("Novo Email"), st.text_input("Nova Senha")
                if st.form_submit_button("Salvar"):
                    upd = {}
                    if ne2: upd["email"] = ne2
                    if ns2: upd["senha"] = ns2
                    if upd:
                        supabase.table("usuarios_sistema").update(upd).eq("login", u_edit).execute()
                        st.success("Atualizado!")
