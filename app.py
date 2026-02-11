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

# --- 2. FUNÇÕES DE SUPORTE ---

def enviar_email_boas_vindas(email_destino, usuario, senha):
    remetente = "icleoc@gmail.com" 
    senha_app = "dkmjzfmfwqnfufrx" 
    msg = MIMEMultipart()
    msg['From'] = f"Jarvis Suporte <{remetente}>"
    msg['To'] = email_destino
    msg['Subject'] = "🚀 Acesso Jarvis Pro"
    corpo = f"👤 Usuário: {usuario}\n🔑 Senha: {senha}\n\nSuporte: https://wa.me/5562991772700"
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

# --- 3. FLUXO PRINCIPAL ---

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    if 'bips_sessao' not in st.session_state: st.session_state.bips_sessao = []
    if 'pedido_key' not in st.session_state: st.session_state.pedido_key = 0

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        opcoes = ["Scanner", "Meu Perfil", "Gerenciar Usuários"] if user['role'] == 'admin' else ["Scanner", "Meu Perfil"]
        aba = st.radio("Menu", opcoes)
        if st.button("Sair"):
            if cookie_manager.get('jarvis_user'): cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None; st.rerun()

    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([2, 1])
        with c1: 
            num_pedido = st.text_input("📦 Número do Pedido", key=f"ped_{st.session_state.pedido_key}")
        with c2: 
            st.write("##")
            if st.button("🗑️ Zerar Tudo"): 
                st.session_state.bips_sessao = []
                st.session_state.pedido_key += 1
                st.rerun()

        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO")
            if st.form_submit_button("PROCESSAR BIPE", use_container_width=True):
                if not num_pedido:
                    st.error("⚠️ Informe o Pedido!")
                elif input_scan:
                    codigo = input_scan.strip()
                    hora_atual = datetime.now().strftime("%H:%M:%S")
                    
                    # Verifica se o código já foi bipado NESTA SESSÃO para manter o status de Saída
                    ja_na_lista = next((item for item in st.session_state.bips_sessao if item["Código"] == codigo), None)
                    
                    if ja_na_lista:
                        msg = "📦 SAÍDA DE PRODUTO"
                    else:
                        # Consulta banco apenas se for a primeira vez que aparece na tela
                        res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).order("validade", desc=True).limit(1).execute()
                        
                        if res.data:
                            item = res.data[0]
                            val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                            status_db = "✅ GARANTIA VÁLIDA" if hoje <= val_p else "❌ GARANTIA VENCIDA"
                            msg = f"{status_db} (Venc: {val_p.strftime('%d/%m/%Y')})"
                        else:
                            v_p = (datetime.now() + timedelta(days=90)).isoformat()
                            supabase.table("registros_garantia").insert({"codigo": codigo, "validade": v_p, "owner_id": user['id'], "numero_pedido": num_pedido}).execute()
                            msg = "📦 SAÍDA DE PRODUTO (Garantia 90 dias)"
                    
                    # Adiciona individualmente à lista (sem agrupar)
                    st.session_state.bips_sessao.insert(0, {
                        "Hora": hora_atual,
                        "Pedido": num_pedido, 
                        "Código": codigo, 
                        "Status": msg
                    })

        if st.session_state.bips_sessao:
            st.divider()
            df = pd.DataFrame(st.session_state.bips_sessao)
            
            # Mostra a lista completa de bipes
            st.subheader(f"📋 Listagem de Itens")
            st.table(df)
            
            # Soma total no final da listagem
            total_itens = len(st.session_state.bips_sessao)
            st.markdown(f"""
                <div style='text-align: right; font-size: 20px; font-weight: bold; padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>
                    TOTAL DE ITENS NO PEDIDO: {total_itens}
                </div>
            """, unsafe_allow_html=True)

    # --- RESTANTE DAS ABAS ---
    elif aba == "Meu Perfil":
        st.title("📝 Meus Dados")
        with st.form("perfil"):
            ne = st.text_input("Novo E-mail", value=user['email'])
            ns = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Atualizar"):
                upd = {"email": ne}
                if ns: upd["senha"] = ns
                supabase.table("usuarios_sistema").update(upd).eq("id", user['id']).execute()
                st.success("Dados salvos!")

    elif aba == "Gerenciar Usuários" and user['role'] == 'admin':
        st.title("👥 Gestão de Clientes")
        t1, t2 = st.tabs(["Listar", "Novo Usuário"])
        with t1:
            res_u = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
            if res_u.data: st.dataframe(pd.DataFrame(res_u.data)[['login', 'email', 'vencimento_assinatura']])
        with t2:
            with st.form("cad"):
                nl, ne, ns = st.text_input("Login"), st.text_input("Email"), st.text_input("Senha")
                nv = st.date_input("Vencimento", value=hoje + timedelta(days=30))
                if st.form_submit_button("Salvar"):
                    supabase.table("usuarios_sistema").insert({"login": nl, "email": ne, "senha": ns, "vencimento_assinatura": nv.isoformat(), "role": "cliente"}).execute()
                    enviar_email_boas_vindas(ne, nl, ns)
                    st.success("Cadastrado!")
