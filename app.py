import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")

# --- LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                try:
                    res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                    if res.data:
                        st.session_state.user_data = res.data[0]
                        st.rerun()
                    else: st.error("Credenciais incorretas.")
                except: st.error("Erro de conexão com o banco de dados.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    venc_assinatura = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    hoje = date.today()
    
    # --- ALERTA E BLOQUEIO ---
    whatsapp_link = "https://wa.me/5562991772700?text=Preciso%20renovar%20minha%20licença"
    dias_restantes = (venc_assinatura - hoje).days

    if 0 <= dias_restantes <= 5:
        st.warning(f"⚠️ Sua licença vence em {dias_restantes} dias. [Falar com Suporte]({whatsapp_link})")
    elif dias_restantes < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada em {venc_assinatura.strftime('%d/%m/%Y')}.")
        st.markdown(f"### [CONTATO SUPORTE VIA WHATSAPP]({whatsapp_link})", unsafe_allow_html=True)
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        menu = ["Scanner", "Gerenciar Usuários"] if user['role'] == 'admin' else ["Scanner"]
        aba = st.radio("Navegação", menu)
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan_form", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO", key="scanner_input")
            st.form_submit_button("PROCESSAR", use_container_width=True)

        if input_scan:
            codigo = input_scan.strip()
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            
            if res.data:
                item = res.data[0]
                val = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                if hoje <= val: st.success(f"✅ EM GARANTIA | Vence em: {val.strftime('%d/%m/%Y')}")
                else: st.error(f"❌ EXPIRADO | Venceu em: {val.strftime('%d/%m/%Y')}")
            else:
                nova_val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": nova_val, "owner_id": user['id']}).execute()
                st.info(f"💾 CADASTRADO: {codigo} (1 ano de garantia)")

    # --- ABA: ADMIN ---
    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão de Clientes")
        tab1, tab2, tab3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Renovar / Editar"])

        with tab1:
            res_u = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data), use_container_width=True)
                st.divider()
                lista_logins = [None] + [u['login'] for u in res_u.data]
                u_del = st.selectbox("Selecione um cliente para EXCLUIR", lista_logins)
                if u_del:
                    st.warning(f"Atenção: A exclusão de {u_del} é permanente.")
                    if st.button(f"🗑️ Confirmar Exclusão"):
                        supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                        st.success("Excluído!")
                        st.rerun()

        with tab2:
            st.subheader("Cadastrar Novo Cliente")
            with st.form("novo_user_form"):
                nl = st.text_input("Login *")
                ne = st.text_input("Email *")
                ns = st.text_input("Senha *")
                nv = st.date_input("Vencimento *", value=hoje + timedelta(days=30))
                
                if st.form_submit_button("Salvar Cadastro"):
                    # VALIDAÇÃO DE CAMPOS OBRIGATÓRIOS
                    if not nl or not ne or not ns:
                        st.error("⚠️ Por favor, preencha todos os campos marcados com *")
                    else:
                        supabase.table("usuarios_sistema").insert({
                            "login": nl, "email": ne, "senha": ns, 
                            "vencimento_assinatura": nv.isoformat(), "role": "cliente"
                        }).execute()
                        st.success(f"Cliente {nl} cadastrado com sucesso!")

        with tab3:
            st.subheader("Editar Dados e Renovação")
            res_e = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_e.data:
                dict_users = {u['login']: u for u in res_e.data}
                u_edit = st.selectbox("Selecione o Cliente", list(dict_users.keys()))
                user_atual = dict_users[u_edit]
                
                with st.form("edit_form"):
                    new_e = st.text_input("E-mail *", value=user_atual['email'])
                    new_s = st.text_input("Nova Senha (deixe vazio para manter)")
                    new_v = st.date_input("Data de Vencimento *", value=datetime.strptime(user_atual['vencimento_assinatura'], '%Y-%m-%d').date())
                    
                    if st.form_submit_button("Salvar Alterações"):
                        # VALIDAÇÃO DE CAMPOS OBRIGATÓRIOS NA EDIÇÃO
                        if not new_e:
                            st.error("⚠️ O campo E-mail é obrigatório.")
                        else:
                            upd = {"email": new_e, "vencimento_assinatura": new_v.isoformat()}
                            if new_s: upd["senha"] = new_s
                            supabase.table("usuarios_sistema").update(upd).eq("login", u_edit).execute()
                            st.success("Dados atualizados!")
                            st.rerun()
