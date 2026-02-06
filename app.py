import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURAÇÕES SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
# ATENÇÃO: Use a 'service_role key' para poder gerenciar usuários livremente
KEY = "SUA_SECRET_KEY_AQUI" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Cloud - Admin", layout="centered")

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .main-title { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("<h1 class='main-title'>🔒 Acesso ao Sistema</h1>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            try:
                res = supabase.table("usuarios_sistema").select("*").eq("login", usuario).eq("senha", senha).execute()
                if res.data:
                    user = res.data[0]
                    venc = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
                    if datetime.now().date() > venc and user['role'] != 'admin':
                        st.error("❌ Assinatura expirada.")
                    else:
                        st.session_state.user_data = user
                        st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
            except Exception as e:
                st.error(f"Erro de conexão: Verifique se as tabelas foram criadas no SQL Editor.")
        return False
    return True

if verificar_login():
    user_role = st.session_state.user_data['role']
    
    # Menu Lateral
    with st.sidebar:
        st.title("🛡️ Jarvis Control")
        if user_role == "admin":
            aba = st.radio("Navegação", ["Scanner", "Gerenciar Clientes"])
        else:
            aba = "Scanner"
            
        uploaded_logo = st.file_uploader("Logo da Empresa", type=["png", "jpg"])
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER (USO DIÁRIO) ---
    if aba == "Scanner":
        if uploaded_logo: st.image(uploaded_logo, width=200)
        st.markdown("<h2 class='main-title'>Checkpoint de Garantia</h2>", unsafe_allow_html=True)
        
        prazo_meses = st.number_input("Meses de Garantia", value=12)

        with st.form("scan_form", clear_on_submit=True):
            input_scanner = st.text_input("AGUARDANDO BIP...", key="scanner_input")
            st.form_submit_button("PROCESSAR", use_container_width=True)

        if input_scanner:
            codigo = input_scanner.strip()
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).execute()
            
            if res.data:
                item = res.data[0]
                validade = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                if datetime.now().date() <= validade:
                    st.success(f"✅ EM GARANTIA | Expira: {validade.strftime('%d/%m/%Y')}")
                else:
                    st.error(f"❌ EXPIRADO | Venceu: {validade.strftime('%d/%m/%Y')}")
            else:
                nova_val = datetime.now() + timedelta(days=prazo_meses * 30)
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": nova_val.isoformat()}).execute()
                st.info(f"💾 CADASTRADO: {codigo} | Válido até {nova_val.strftime('%d/%m/%Y')}")

    # --- ABA: ADMINISTRADOR (GESTÃO DE CLIENTES) ---
    elif aba == "Gerenciar Clientes":
        st.title("👥 Gestão de Clientes")
        
        with st.expander("➕ Cadastrar Novo Cliente"):
            with st.form("novo_user"):
                n_user = st.text_input("Login do Cliente")
                n_pass = st.text_input("Senha do Cliente")
                n_venc = st.date_input("Vencimento da Assinatura", value=datetime.now() + timedelta(days=30))
                if st.form_submit_button("Cadastrar Cliente"):
                    try:
                        supabase.table("usuarios_sistema").insert({"login": n_user, "senha": n_pass, "vencimento_assinatura": n_venc.isoformat(), "role": "cliente"}).execute()
                        st.success("Cliente cadastrado!")
                    except: st.error("Erro: Login já existe.")

        st.subheader("Lista de Clientes e Renovações")
        users = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
        if users.data:
            df_users = pd.DataFrame(users.data)
            st.dataframe(df_users[['login', 'vencimento_assinatura', 'ativo']], use_container_width=True)
            
            # Renovação Rápida
            st.divider()
            target_user = st.selectbox("Selecionar Cliente para Renovar", [u['login'] for u in users.data])
            nova_data = st.date_input("Nova Data de Vencimento")
            if st.button(f"Atualizar Assinatura de {target_user}"):
                supabase.table("usuarios_sistema").update({"vencimento_assinatura": nova_data.isoformat()}).eq("login", target_user).execute()
                st.success("Data atualizada!")
