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
    remetente = "icleoc@gmail.com" 
    senha_app = "dkmjzfmfwqnfufrx" 
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = destinatario
    msg['Subject'] = "🚀 Seu acesso ao Jarvis Pro está pronto!"
    corpo = f"Olá!\n\nSeu acesso foi ativado.\n\n👤 Usuário: {login}\n🔑 Senha: {senha}\n\nSuporte: https://wa.me/5562991772700"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

st.set_page_config(page_title="Jarvis Pro", layout="centered")
cookie_manager = stx.CookieManager()

def verificar_login():
    if 'user_data' not in st.session_state: st.session_state.user_data = None
    saved = cookie_manager.get('jarvis_user')
    if saved and st.session_state.user_data is None:
        try:
            res = supabase.table("usuarios_sistema").select("*").eq("login", saved).execute()
            if res.data: 
                st.session_state.user_data = res.data[0]
                return True
        except: pass

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            manter = st.checkbox("Manter logado (24h)")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    if manter: cookie_manager.set('jarvis_user', st.session_state.user_data['login'], expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    
    # --- ALERTA E BLOQUEIO ---
    whatsapp = "https://wa.me/5562991772700?text=Renovacao"
    if 0 <= (venc - hoje).days <= 5:
        st.warning(f"⚠️ Vence em {(venc-hoje).days} dias. [Suporte]({whatsapp})")
    elif (venc - hoje).days < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada! [CONTATO SUPORTE]({whatsapp})")
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Menu", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else "Scanner"
        if st.button("Sair"):
            if cookie_manager.get('jarvis_user'): cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER (VISÍVEL PARA TODOS) ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE AQUI", key="scanner_input")
            st.form_submit_button("PROCESSAR", use_container_width=True)
        
        if input_scan:
            codigo = input_scan.strip()
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            if res.data:
                item = res.data[0]
                val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                st.info(f"ID: {codigo} | Validade: {val_p.strftime('%d/%m/%Y')}")
            else:
                v_p = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": v_p, "owner_id": user['id']}).execute()
                st.success("💾 Cadastrado com sucesso!")

    # --- ABA: ADMIN ---
    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão")
        t1, t2, t3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Editar/Renovar"])
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']], use_container_width=True)
                u_del = st.selectbox("Excluir cliente:", [None] + [u['login'] for u in res_u.data])
                if u_del and st.button(f"🗑️ Deletar {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success("Excluído!"); st.rerun()
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
                sel = st.selectbox("Selecione para Editar", list(u_list.keys()))
                with st.form("edit"):
                    ee = st.text_input("Email *", value=u_list[sel]['email'])
                    es = st.text_input("Nova Senha")
                    ev = st.date_input("Vencimento *", value=datetime.strptime(u_list[sel]['vencimento_assinatura'], '%Y-%m-%d').date())
                    if st.form_submit_button("Atualizar"):
                        upd = {"email": ee, "vencimento_assinatura": ev.isoformat()}
                        if es: upd["senha"] = es
                        supabase.table("usuarios_sistema").update(upd).eq("login", sel).execute()
                        st.success("Atualizado!"); st.rerun()
