import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÕES ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")
cookie_manager = stx.CookieManager()

# --- FUNÇÕES DE SUPORTE ---
def enviar_email_boas_vindas(email_destino, usuario, senha):
    remetente = "icleoc@gmail.com" 
    senha_app = "dkmjzfmfwqnfufrx" 
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = email_destino
    msg['Subject'] = "🚀 Acesso Jarvis Pro"
    corpo = f"Usuário: {usuario}\nSenha: {senha}"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(remetente, senha_app); server.send_message(msg); server.quit()
        return True
    except: return False

def verificar_login():
    if 'user_data' not in st.session_state: st.session_state.user_data = None
    saved = cookie_manager.get('jarvis_user')
    if saved and st.session_state.user_data is None:
        try:
            res = supabase.table("usuarios_sistema").select("*").eq("login", saved).execute()
            if res.data: st.session_state.user_data = res.data[0]; return True
        except: pass
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    cookie_manager.set('jarvis_user', u, expires_at=datetime.now() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

# --- FLUXO PRINCIPAL ---
if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    
    if 'bips_sessao' not in st.session_state: st.session_state.bips_sessao = []

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        opcoes = ["Scanner", "Meu Perfil", "Gerenciar Usuários"] if user['role'] == 'admin' else ["Scanner", "Meu Perfil"]
        aba = st.radio("Menu", opcoes)
        if st.button("Sair"):
            cookie_manager.delete('jarvis_user'); st.session_state.user_data = None; st.rerun()

    # --- ABA: SCANNER (COM SEPARAÇÃO POR PEDIDO) ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint de Garantia</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            num_pedido = st.text_input("📦 Número do Pedido", placeholder="Ex: PED-1001")
        with col2:
            st.write("##")
            if st.button("🗑️ Zerar Listagem"):
                st.session_state.bips_sessao = []; st.rerun()

        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO")
            submit = st.form_submit_button("PROCESSAR BIPE", use_container_width=True)
        
        if submit and input_scan:
            if not num_pedido:
                st.error("⚠️ Informe o Número do Pedido antes de bipar!")
            else:
                codigo = input_scan.strip()
                # FILTRO RIGOROSO: Por código, dono E pedido
                res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).eq("numero_pedido", num_pedido).execute()
                
                if res.data:
                    item = res.data[0]
                    val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                    msg = "✅ GARANTIA OK" if hoje <= val_p else "❌ EXPIRADO"
                else:
                    v_p = (datetime.now() + timedelta(days=90)).isoformat()
                    supabase.table("registros_garantia").insert({
                        "codigo": codigo, "validade": v_p, "owner_id": user['id'], "numero_pedido": num_pedido
                    }).execute()
                    msg = "💾 NOVO CADASTRO"
                
                st.session_state.bips_sessao.append({"Pedido": num_pedido, "Código": codigo, "Status": msg})

        if st.session_state.bips_sessao:
            st.divider()
            df = pd.DataFrame(st.session_state.bips_sessao)
            df_view = df.groupby(['Pedido', 'Código', 'Status']).size().reset_index(name='Qtd')
            st.subheader(f"📊 Resumo Atual (Total: {len(st.session_state.bips_sessao)})")
            st.table(df_view)

    # --- ABA: ADMIN (LISTAGEM SOMENTE DO QUE É DELE) ---
    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão de Clientes")
        t1, t2, t3 = st.tabs(["Listar Usuários", "Novo Usuário", "Ver Meus Bips"])
        
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data: st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']])
        
        with t3:
            st.subheader("Meus Registros Pessoais")
            # Admin agora só vê os bips onde ele é o owner
            meus_bips = supabase.table("registros_garantia").select("*").eq("owner_id", user['id']).execute()
            if meus_bips.data: st.dataframe(pd.DataFrame(meus_bips.data))
            else: st.info("Você ainda não bipou nada na sua conta de admin.")

    # (Aba Meu Perfil mantida...)
