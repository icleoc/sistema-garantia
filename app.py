import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

# --- ENVIO DE EMAIL ---
def enviar_email(destinatario, login, senha):
    remetente = "seu-email@gmail.com"  # <--- SEU EMAIL
    senha_app = "xxxx xxxx xxxx xxxx" # <--- SUA SENHA DE APP DO GOOGLE
    
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = destinatario
    msg['Subject'] = "Acesso Jarvis Pro Ativado"
    
    corpo = f"Seu acesso está pronto!\n\nUsuário: {login}\nSenha: {senha}\n\nSuporte: https://wa.me/5562991772700"
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")

# CookieManager fora de cache para evitar o erro da imagem e1d8f5
cookie_manager = stx.CookieManager()

def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    saved = cookie_manager.get('jarvis_user')
    if saved and st.session_state.user_data is None:
        res = supabase.table("usuarios_sistema").select("*").eq("login", saved).execute()
        if res.data: 
            st.session_state.user_data = res.data[0]
            return True

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
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
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    hoje = date.today()
    
    # --- ALERTA WHATSAPP ---
    whatsapp = "https://wa.me/5562991772700?text=Renovacao"
    if 0 <= (venc - hoje).days <= 5:
        st.warning(f"⚠️ Vence em {(venc-hoje).days} dias. [Suporte]({whatsapp})")
    elif (venc - hoje).days < 0 and user['role'] != 'admin':
        st.error(f"❌ Expirado! [CONTATO]({whatsapp})")
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE AQUI")
            st.form_submit_button("PROCESSAR", use_container_width=True)
        # Lógica de scanner aqui (conforme versões anteriores)

    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão")
        t1, t2, t3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Editar/Renovar"])
        
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']], use_container_width=True)
                u_del = st.selectbox("Excluir cliente:", [None] + [u['login'] for u in res_u.data])
                if u_del and st.button(f"🗑️ Deletar {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success("Excluído!")
                    st.rerun()

        with t2:
            with st.form("cad"):
                nl, ne, ns = st.text_input("Login *"), st.text_input("Email *"), st.text_input("Senha *")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar e Enviar E-mail"):
                    if nl and ne and ns:
                        supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat()}).execute()
                        enviar_email(ne, nl, ns)
                        st.success("Cadastrado!")
                    else: st.error("Campos obrigatórios!")

        with t3:
            res_e = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_e.data:
                u_list = {u['login']: u for u in res_e.data}
                sel = st.selectbox("Editar:", list(u_list.keys()))
                with st.form("edit"):
                    ee = st.text_input("Email", value=u_list[sel]['email'])
                    es = st.text_input("Nova Senha")
                    ev = st.date_input("Vencimento", value=datetime.strptime(u_list[sel]['vencimento_assinatura'], '%Y-%m-%d').date())
                    if st.form_submit_button("Atualizar"):
                        upd = {"email": ee, "vencimento_assinatura": ev.isoformat()}
                        if es: upd["senha"] = es
                        supabase.table("usuarios_sistema").update(upd).eq("login", sel).execute()
                        st.success("Atualizado!")
                        st.rerun()
