import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")

# --- SISTEMA DE LOGIN COM SUPORTE A ENTER ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Sistema</h2>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_login:
                try:
                    res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                    if res.data:
                        st.session_state.user_data = res.data[0]
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas.")
                except Exception:
                    st.error("Erro de conexão. Verifique o Supabase.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    venc_assinatura = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    hoje = date.today()
    
    # --- ALERTA DE VENCIMENTO ---
    dias_restantes = (venc_assinatura - hoje).days
    if 0 <= dias_restantes <= 5:
        st.warning(f"⚠️ Sua licença vence em {dias_restantes} dias ({venc_assinatura.strftime('%d/%m/%Y')}).")
    elif dias_restantes < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada em {venc_assinatura.strftime('%d/%m/%Y')}.")
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        menu_options = ["Scanner", "Gerenciar Usuários"] if user['role'] == 'admin' else ["Scanner"]
        aba = st.radio("Navegação", menu_options)
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
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).execute()
            if res.data:
                item = res.data[0]
                val = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                if hoje <= val:
                    st.success(f"✅ EM GARANTIA | Vence em: {val.strftime('%d/%m/%Y')}")
                else: st.error(f"❌ EXPIRADO | Venceu em: {val.strftime('%d/%m/%Y')}")
            else:
                nova_val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": nova_val}).execute()
                st.info(f"💾 CADASTRADO: {codigo} (1 ano de garantia)")

    # --- ABA: ADMIN (GESTÃO DE CLIENTES) ---
    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão de Clientes")
        tab1, tab2, tab3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Renovar / Editar"])

        with tab1:
            res_u = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_u.data:
                df = pd.DataFrame(res_u.data)
                df.columns = ['Login', 'E-mail', 'Vencimento']
                st.dataframe(df, use_container_width=True)
                st.divider()
                u_del = st.selectbox("Selecione para EXCLUIR", [u['login'] for u in res_u.data])
                if st.button(f"🗑️ Confirmar Exclusão de {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success(f"Usuário {u_del} removido.")
                    st.rerun()

        with tab2:
            with st.form("novo_user_form"):
                nl, ne, ns = st.text_input("Login"), st.text_input("Email"), st.text_input("Senha")
                nv = st.date_input("Vencimento Inicial", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar Cliente"):
                    supabase.table("usuarios_sistema").insert({
                        "login": nl, "email": ne, "senha": ns, 
                        "vencimento_assinatura": nv.isoformat(),
                        "role": "cliente"
                    }).execute()
                    st.success("Cliente cadastrado!")

        with tab3:
            res_e = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_e.data:
                # Criar dicionário para carregar dados atuais ao selecionar
                dict_users = {u['login']: u for u in res_e.data}
                u_edit = st.selectbox("Selecione o Cliente para Alterar", list(dict_users.keys()))
                
                user_atual = dict_users[u_edit]
                data_atual_venc = datetime.strptime(user_atual['vencimento_assinatura'], '%Y-%m-%d').date()

                with st.form("edit_form_avancado"):
                    st.info(f"Editando: {u_edit}")
                    new_e = st.text_input("Novo Email", value=user_atual['email'])
                    new_s = st.text_input("Nova Senha (deixe em branco para manter)")
                    # CAMPO SOLICITADO: Alteração de data de vencimento
                    new_v = st.date_input("Nova Data de Vencimento", value=data_atual_venc)
                    
                    if st.form_submit_button("Salvar Alterações / Renovar"):
                        upd = {
                            "email": new_e,
                            "vencimento_assinatura": new_v.isoformat()
                        }
                        if new_s: 
                            upd["senha"] = new_s
                            
                        supabase.table("usuarios_sistema").update(upd).eq("login", u_edit).execute()
                        st.success(f"Dados de {u_edit} atualizados com sucesso!")
                        st.rerun()
