import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro", layout="centered")

# Inicializa o Cookie Manager fora de funções cacheadas para evitar o erro da imagem
cookie_manager = stx.CookieManager()

def verificar_login():
    # 1. Tenta recuperar sessão salva
    cookie_user = cookie_manager.get('jarvis_user')
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if cookie_user and st.session_state.user_data is None:
        res = supabase.table("usuarios_sistema").select("*").eq("login", cookie_user).execute()
        if res.data:
            st.session_state.user_data = res.data[0]
            return True

    # 2. Tela de Login se não houver sessão
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso Jarvis</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            manter = st.checkbox("Manter logado (24h)")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    if manter:
                        cookie_manager.set('jarvis_user', st.session_state.user_data['login'], expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    
    # --- ALERTA DE VENCIMENTO ---
    whatsapp_link = "https://wa.me/5562991772700?text=Renovação"
    if (venc - hoje).days <= 5 and user['role'] != 'admin':
        st.warning(f"⚠️ Licença vence em {(venc-hoje).days} dias. [Suporte]({whatsapp_link})")

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Clientes"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE AQUI", key="scanner_input")
            st.form_submit_button("PROCESSAR", use_container_width=True)
        # (Lógica de processamento mantida conforme versões anteriores)

    # --- ABA: ADMIN (SOLICITADA) ---
    elif aba == "Gerenciar Clientes":
        st.title("👥 Gestão de Clientes")
        tab1, tab2, tab3 = st.tabs(["Listar/Excluir", "Novo Cadastro", "Alterar Dados"])

        with tab1:
            res_u = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data), use_container_width=True)
                st.divider()
                u_del = st.selectbox("Selecione para EXCLUIR", [None] + [u['login'] for u in res_u.data])
                if u_del and st.button(f"🗑️ Deletar {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success("Excluído!")
                    st.rerun()

        with tab2:
            with st.form("novo_user"):
                nl, ne, ns = st.text_input("Login *"), st.text_input("Email *"), st.text_input("Senha *")
                nv = st.date_input("Vencimento *", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar Cliente"):
                    if nl and ne and ns:
                        supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat()}).execute()
                        st.success("Cadastrado!")
                    else: st.error("Preencha tudo.")

        with tab3:
            res_e = supabase.table("usuarios_sistema").select("login, email").eq("role", "cliente").execute()
            u_edit = st.selectbox("Selecione para Editar", [u['login'] for u in res_e.data])
            with st.form("edit"):
                ne2, ns2 = st.text_input("Novo Email"), st.text_input("Nova Senha")
                if st.form_submit_button("Atualizar"):
                    upd = {}
                    if ne2: upd["email"] = ne2
                    if ns2: upd["senha"] = ns2
                    if upd:
                        supabase.table("usuarios_sistema").update(upd).eq("login", u_edit).execute()
                        st.success("Atualizado!")
