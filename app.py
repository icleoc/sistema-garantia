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

# --- FUNÇÃO DE ENVIO DE EMAIL (SMTP GOOGLE) ---
def enviar_email_boas_vindas(email_destino, usuario, senha):
    remetente = "icleoc@gmail.com" 
    senha_app = "dkmjzfmfwqnfufrx" # Sua senha de app configurada
    
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = email_destino
    msg['Subject'] = "🚀 Seu acesso ao Jarvis Pro Cloud está pronto!"

    corpo = f"""
    Olá!
    
    Sua licença para o sistema Jarvis Pro foi ativada.
    Aqui estão suas credenciais:
    
    👤 Usuário: {usuario}
    🔑 Senha: {senha}
    
    Suporte WhatsApp: https://wa.me/5562991772700
    """
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- INTERFACE ---
st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")
cookie_manager = stx.CookieManager()

def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    # Restaura sessão via Cookie (Refresh)
    saved_user = cookie_manager.get('jarvis_user')
    if saved_user and st.session_state.user_data is None:
        res = supabase.table("usuarios_sistema").select("*").eq("login", saved_user).execute()
        if res.data:
            st.session_state.user_data = res.data[0]
            return True

    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Sistema</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            manter = st.checkbox("Manter logado por 24h")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    if manter:
                        cookie_manager.set('jarvis_user', u, expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Credenciais incorretas.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    
    # --- ALERTA DE VENCIMENTO ---
    whatsapp_link = "https://wa.me/5562991772700?text=Preciso%20renovar%20minha%20licença"
    if 0 <= (venc - hoje).days <= 5:
        st.warning(f"⚠️ Licença vence em {(venc - hoje).days} dias. [Falar com Suporte]({whatsapp_link})")
    elif (venc - hoje).days < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada em {venc.strftime('%d/%m/%Y')}.")
        st.markdown(f"### [CLIQUE AQUI PARA SUPORTE VIA WHATSAPP]({whatsapp_link})", unsafe_allow_html=True)
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Navegação", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
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

    # --- ABA: ADMIN ---
    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão de Clientes")
        t1, t2, t3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Editar/Renovar"])
        
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']], use_container_width=True)
                u_del = st.selectbox("Excluir cliente (Selecione para habilitar):", [None] + [u['login'] for u in res_u.data])
                if u_del and st.button(f"🗑️ Confirmar Exclusão de {u_del}"):
                    supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                    st.success("Excluído!")
                    st.rerun()

        with t2:
            with st.form("cad_form"):
                nl, ne, ns = st.text_input("Login *"), st.text_input("Email *"), st.text_input("Senha *")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar e Enviar E-mail"):
                    if nl and ne and ns:
                        supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat()}).execute()
                        enviar_email_boas_vindas(ne, nl, ns)
                        st.success(f"✅ {nl} cadastrado e avisado por e-mail!")
                    else: st.error("Preencha todos os campos obrigatórios!")

        with t3:
            res_e = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_e.data:
                u_list = {u['login']: u for u in res_e.data}
                sel = st.selectbox("Selecionar Cliente:", list(u_list.keys()))
                u_data = u_list[sel]
                with st.form("edit_form"):
                    ee = st.text_input("Email *", value=u_data['email'])
                    es = st.text_input("Nova Senha (vazio para manter)")
                    ev = st.date_input("Vencimento *", value=datetime.strptime(u_data['vencimento_assinatura'], '%Y-%m-%d').date())
                    if st.form_submit_button("Salvar Alterações"):
                        if ee:
                            upd = {"email": ee, "vencimento_assinatura": ev.isoformat()}
                            if es: upd["senha"] = es
                            supabase.table("usuarios_sistema").update(upd).eq("login", sel).execute()
                            st.success("Dados atualizados!")
                            st.rerun()
                        else: st.error("E-mail é obrigatório.")
