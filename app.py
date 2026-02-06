import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONEXÃO SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÃO DE ENVIO DE EMAIL (SMTP) ---
def enviar_email_boas_vindas(email_destino, usuario, senha):
    seu_email = "seu-email@gmail.com"  # <--- Coloque seu e-mail aqui
    sua_senha_app = "xxxx xxxx xxxx xxxx" # <--- Coloque sua senha de app aqui
    
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Support <{seu_email}>"
    msg['To'] = email_destino
    msg['Subject'] = "🚀 Seu acesso ao Jarvis Pro Cloud está pronto!"

    corpo = f"""
    Olá!
    
    Sua licença para o sistema Jarvis Pro foi ativada com sucesso.
    Abaixo estão suas credenciais de acesso:
    
    👤 Usuário: {usuario}
    🔑 Senha: {senha}
    
    Acesse agora: https://seu-link-do-streamlit.app
    
    Se precisar de suporte, entre em contato: https://wa.me/5562991772700
    """
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(seu_email, sua_senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# --- INTERFACE E LOGIN ---
st.set_page_config(page_title="Jarvis Pro", layout="centered")
cookie_manager = stx.CookieManager()

def verificar_login():
    cookie_user = cookie_manager.get('jarvis_user')
    if 'user_data' not in st.session_state: st.session_state.user_data = None
    
    if cookie_user and st.session_state.user_data is None:
        res = supabase.table("usuarios_sistema").select("*").eq("login", cookie_user).execute()
        if res.data: st.session_state.user_data = res.data[0]

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso Jarvis</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            manter = st.checkbox("Manter logado")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    if manter: cookie_manager.set('jarvis_user', u, expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()

    # --- MENU LATERAL ---
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Clientes"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ÁREA ADMIN: CADASTRO COM ENVIO DE EMAIL ---
    if aba == "Gerenciar Clientes" and user['role'] == 'admin':
        st.title("👥 Gestão de Clientes")
        t1, t2, t3 = st.tabs(["Listar", "Novo Cliente", "Editar"])

        with t2:
            with st.form("cad_cliente"):
                nl = st.text_input("Login *")
                ne = st.text_input("Email *")
                ns = st.text_input("Senha *")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar e Enviar E-mail"):
                    if nl and ne and ns:
                        # 1. Salva no banco
                        supabase.table("usuarios_sistema").insert({
                            "login": nl, "email": ne, "senha": ns, 
                            "vencimento_assinatura": nv.isoformat(), "role": "cliente"
                        }).execute()
                        
                        # 2. Envia e-mail
                        if enviar_email_boas_vindas(ne, nl, ns):
                            st.success(f"✅ Cliente {nl} cadastrado e e-mail enviado!")
                        else:
                            st.warning(f"✅ Cliente {nl} cadastrado, mas o e-mail falhou. Verifique o SMTP.")
                    else:
                        st.error("Preencha os campos obrigatórios.")
