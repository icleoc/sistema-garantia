import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
import secrets

# --- CONFIGURAÇÕES SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÃO DE EMAIL (SMTP) ---
def enviar_email_recuperacao(email_destino, token):
    # O senhor deve configurar estas variáveis com seu provedor (ex: Gmail)
    remetente = "seu-email@gmail.com"
    senha_email = "sua-senha-app"
    
    link = f"https://sistema-garantia.streamlit.app/?token={token}"
    corpo = f"Olá, clique no link para redefinir sua senha: {link}"
    
    msg = MIMEText(corpo)
    msg['Subject'] = 'Recuperação de Senha - Jarvis Cloud'
    msg['From'] = remetente
    msg['To'] = email_destino

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remetente, senha_email)
            server.sendmail(remetente, email_destino, msg.as_string())
        return True
    except:
        return False

# --- INTERFACE ---
st.set_page_config(page_title="Jarvis Pro - Gestão & Scanner", layout="centered")

def verificar_login():
    # Lógica de Recuperação via Link
    query_params = st.query_params
    if "token" in query_params:
        st.subheader("🔄 Redefinir Senha")
        nova_s = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Nova Senha"):
            supabase.table("usuarios_sistema").update({"senha": nova_s, "recovery_token": None}).eq("recovery_token", query_params["token"]).execute()
            st.success("Senha alterada! Vá para a tela de login.")
            st.stop()

    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        tab_log, tab_esqueci = st.tabs(["Login", "Esqueci a Senha"])
        
        with tab_log:
            u = st.text_input("Usuário / Email")
            s = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    st.rerun()
                else: st.error("Incorreto.")
        
        with tab_esqueci:
            email_rec = st.text_input("Digite seu E-mail cadastrado")
            if st.button("Enviar Link de Recuperação"):
                token = secrets.token_urlsafe(16)
                res = supabase.table("usuarios_sistema").update({"recovery_token": token}).eq("email", email_rec).execute()
                if res.data:
                    if enviar_email_recuperacao(email_rec, token):
                        st.success("Link enviado para o seu e-mail!")
                    else: st.error("Erro ao enviar e-mail. Configure o SMTP.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    hoje = datetime.now().date()
    
    # --- ALERTA DE VENCIMENTO ---
    dias_restantes = (venc - hoje).days
    if 0 <= dias_restantes <= 5:
        st.warning(f"⚠️ Atenção: Sua licença vence em {dias_restantes} dias ({venc.strftime('%d/%m/%Y')}).")
    elif dias_restantes < 0:
        st.error(f"❌ Licença expirada em {venc.strftime('%d/%m/%Y')}. Bloqueando scanner...")
        if user['role'] != 'admin': st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Meu Perfil", "Admin"]) if user['role'] == 'admin' else st.radio("Menu", ["Scanner", "Meu Perfil"])
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("AGUARDANDO SCANNER...", key="s")
            st.form_submit_button("PROCESSAR", use_container_width=True)
        # (Lógica de scanner mantida...)

    # --- ABA: MEU PERFIL (ALTERAR SENHA) ---
    elif aba == "Meu Perfil":
        st.subheader("📝 Meus Dados")
        nova_senha = st.text_input("Alterar Senha", type="password")
        novo_email = st.text_input("Alterar E-mail", value=user['email'])
        if st.button("Salvar Alterações"):
            upd = {"email": novo_email}
            if nova_senha: upd["senha"] = nova_senha
            supabase.table("usuarios_sistema").update(upd).eq("id", user['id']).execute()
            st.success("Dados atualizados!")

    # --- ABA: ADMIN (GESTÃO E EXCLUSÃO) ---
    elif aba == "Admin":
        st.title("👥 Gestão de Clientes")
        res_users = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
        if res_users.data:
            df = pd.DataFrame(res_users.data)
            st.dataframe(df[['login', 'email', 'vencimento_assinatura']])
            
            st.divider()
            u_excluir = st.selectbox("Selecionar Cliente para EXCLUIR", [u['login'] for u in res_users.data])
            if st.button(f"🗑️ EXCLUIR {u_excluir}", fg_color="red"):
                supabase.table("usuarios_sistema").delete().eq("login", u_excluir).execute()
                st.success(f"Cliente {u_excluir} removido!")
                st.rerun()
