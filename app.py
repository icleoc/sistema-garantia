import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")

# Gerenciador de cookies sem cache para evitar o erro da imagem amarela
cookie_manager = stx.CookieManager()

def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    # Tenta recuperar sessão salva no cookie
    saved_user = cookie_manager.get('jarvis_user')
    if saved_user and st.session_state.user_data is None:
        res = supabase.table("usuarios_sistema").select("*").eq("login", saved_user).execute()
        if res.data:
            st.session_state.user_data = res.data[0]
            return True

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        # st.form permite que o ENTER funcione no teclado
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
                else: st.error("Credenciais incorretas.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    
    # --- ALERTA E BLOQUEIO COM WHATSAPP ---
    whatsapp_link = "https://wa.me/5562991772700?text=Preciso%20renovar%20minha%20licença"
    if 0 <= (venc - hoje).days <= 5:
        st.warning(f"⚠️ Licença vence em {(venc - hoje).days} dias. [Falar com Suporte]({whatsapp_link})")
    elif (venc - hoje).days < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada! [CONTATO SUPORTE]({whatsapp_link})")
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Navegação", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO", key="s")
            st.form_submit_button("PROCESSAR", use_container_width=True)
        if input_scan:
            codigo = input_scan.strip()
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            if res.data:
                item = res.data[0]
                val_prod = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                st.info(f"Produto: {codigo} | Validade: {val_prod.strftime('%d/%m/%Y')}")
            else:
                v_p = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": v_p, "owner_id": user['id']}).execute()
                st.success(f"💾 Cadastrado!")

    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão")
        t1, t2, t3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Editar/Renovar"])
        
        # LISTAR E EXCLUIR
        with t1:
            users_res = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if users_res.data:
                st.dataframe(pd.DataFrame(users_res.data)[['login', 'email', 'vencimento_assinatura']], use_container_width=True)
                u_del = st.selectbox("Excluir cliente:", [None] + [u['login'] for u in users_res.data])
                if u_del and st.button(f"🗑️ Confirmar Exclusão de {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success("Excluído!")
                    st.rerun()
        
        # CADASTRAR (CAMPOS OBRIGATÓRIOS)
        with t2:
            with st.form("cad"):
                nl, ne, ns = st.text_input("Login *"), st.text_input("Email *"), st.text_input("Senha *")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Salvar"):
                    if nl and ne and ns:
                        supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat()}).execute()
                        st.success("Cadastrado!")
                    else: st.error("Preencha todos os campos!")

        # EDITAR E RENOVAR (CORRIGIDO PARA NÃO FICAR EM BRANCO)
        with t3:
            users_res = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if users_res.data:
                u_list = {u['login']: u for u in users_res.data}
                sel = st.selectbox("Selecionar para Editar/Renovar", list(u_list.keys()))
                u_data = u_list[sel]
                with st.form("edit"):
                    ee = st.text_input("Email", value=u_data['email'])
                    es = st.text_input("Nova Senha (vazio para manter)")
                    ev = st.date_input("Novo Vencimento", value=datetime.strptime(u_data['vencimento_assinatura'], '%Y-%m-%d').date())
                    if st.form_submit_button("Atualizar"):
                        upd = {"email": ee, "vencimento_assinatura": ev.isoformat()}
                        if es: upd["senha"] = es
                        supabase.table("usuarios_sistema").update(upd).eq("login", sel).execute()
                        st.success("Dados atualizados!")
                        st.rerun()
