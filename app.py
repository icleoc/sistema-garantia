import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIGURAÇÕES E CONEXÕES ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")
cookie_manager = stx.CookieManager()

# --- 2. DEFINIÇÃO DE FUNÇÕES (Devem vir antes do fluxo principal) ---

def enviar_email_boas_vindas(email_destino, usuario, senha):
    remetente = "icleoc@gmail.com" 
    senha_app = "dkmjzfmfwqnfufrx" 
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = email_destino
    msg['Subject'] = "🚀 Seu acesso ao Jarvis Pro Cloud está pronto!"
    corpo = f"Olá!\n\nSeu acesso foi ativado.\n\n👤 Usuário: {usuario}\n🔑 Senha: {senha}\n\nSuporte: https://wa.me/5562991772700"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

def verificar_login():
    if 'user_data' not in st.session_state: 
        st.session_state.user_data = None
    
    saved = cookie_manager.get('jarvis_user')
    if saved and st.session_state.user_data is None:
        try:
            res = supabase.table("usuarios_sistema").select("*").eq("login", saved).execute()
            if res.data: 
                st.session_state.user_data = res.data[0]
                return True
        except: pass

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
                    if manter: cookie_manager.set('jarvis_user', u, expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

# --- 3. FLUXO PRINCIPAL (Inicia aqui) ---

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    
    if 'bips_sessao' not in st.session_state:
        st.session_state.bips_sessao = []

    # --- MENU LATERAL ---
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        opcoes = ["Scanner", "Meu Perfil", "Gerenciar Usuários"] if user['role'] == 'admin' else ["Scanner", "Meu Perfil"]
        aba = st.radio("Menu", opcoes)
        if st.button("Sair"):
            if cookie_manager.get('jarvis_user'): cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO")
            submit = st.form_submit_button("PROCESSAR", use_container_width=True)
        
        if submit and input_scan:
            codigo = input_scan.strip()
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            
            if res.data:
                item = res.data[0]
                val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                status = "✅ GARANTIA OK" if hoje <= val_p else "❌ EXPIRADO"
                msg = f"{status} | Vencimento: {val_p.strftime('%d/%m/%Y')}"
            else:
                v_p = (datetime.now() + timedelta(days=90)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": v_p, "owner_id": user['id']}).execute()
                msg = "💾 NOVO CADASTRO (90 dias)"
            
            st.session_state.bips_sessao.append({"Código": codigo, "Resultado": msg})

        if st.session_state.bips_sessao:
            st.divider()
            df = pd.DataFrame(st.session_state.bips_sessao)
            df_agrupado = df.groupby(['Código', 'Resultado']).size().reset_index(name='Qtd')
            st.subheader(f"📊 Resumo (Total: {len(st.session_state.bips_sessao)})")
            st.table(df_agrupado[['Qtd', 'Código', 'Resultado']])
            if st.button("Limpar Listagem"):
                st.session_state.bips_sessao = []
                st.rerun()

    # --- ABA: MEU PERFIL ---
    elif aba == "Meu Perfil":
        st.title("📝 Meus Dados")
        with st.form("perfil"):
            ne = st.text_input("Novo E-mail", value=user['email'])
            ns = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Atualizar"):
                upd = {"email": ne}
                if ns: upd["senha"] = ns
                supabase.table("usuarios_sistema").update(upd).eq("id", user['id']).execute()
                st.success("Atualizado!")

    # --- ABA: ADMIN ---
    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão")
        t1, t2, t3 = st.tabs(["Listar", "Novo", "Editar"])
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']])
        with t2:
            with st.form("cad"):
                nl, ne, ns = st.text_input("Login"), st.text_input("Email"), st.text_input("Senha")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Cadastrar"):
                    supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat(), "role": "cliente"}).execute()
                    enviar_email_boas_vindas(ne, nl, ns)
                    st.success("Pronto!")
        with t3:
            res_e = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_e.data:
                u_list = {u['login']: u for u in res_e.data}
                sel = st.selectbox("Editar", list(u_list.keys()))
                with st.form("edit"):
                    ee = st.text_input("Email", value=u_list[sel]['email'])
                    ev = st.date_input("Vencimento", value=datetime.strptime(u_list[sel]['vencimento_assinatura'], '%Y-%m-%d').date())
                    if st.form_submit_button("Salvar"):
                        supabase.table("usuarios_sistema").update({"email": ee, "vencimento_assinatura": ev.isoformat()}).eq("login", sel).execute()
                        st.success("OK!")
