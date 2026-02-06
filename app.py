import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import io

# --- CONFIGURAÇÕES SUPABASE ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
# Certifique-se de usar sua service_role ou anon key correta aqui
KEY = "SUA_SECRET_KEY_AQUI" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Cloud - Admin", layout="centered")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .main-title { text-align: center; }
    .stTextInput > div > div > input { text-align: center; }
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
                        st.error("❌ Assinatura expirada. Contate o administrador.")
                    else:
                        st.session_state.user_data = user
                        st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
            except Exception:
                st.error("Erro de conexão. Verifique o SQL Editor no Supabase.")
        return False
    return True

if verificar_login():
    user_role = st.session_state.user_data['role']
    
    with st.sidebar:
        st.title("🛡️ Jarvis Control")
        aba = st.radio("Navegação", ["Scanner", "Gerenciar Clientes"]) if user_role == "admin" else "Scanner"
        uploaded_logo = st.file_uploader("Upload da Logo", type=["png", "jpg"])
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER ---
    if aba == "Scanner":
        if uploaded_logo: st.image(uploaded_logo, width=220)
        st.markdown("<h2 class='main-title'>Checkpoint de Garantia</h2>", unsafe_allow_html=True)
        prazo_meses = st.number_input("Meses de Garantia (Padrão)", value=12)

        with st.form("scan_form", clear_on_submit=True):
            st.info("Foque aqui e escaneie o produto")
            input_scanner = st.text_input("SCANNER ATIVO", key="scanner_input", label_visibility="collapsed")
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

    # --- ABA: ADMINISTRADOR ---
    elif aba == "Gerenciar Clientes":
        st.title("👥 Painel Administrativo")
        
        # 1. Exportação Excel
        st.subheader("📊 Relatórios")
        if st.button("Gerar Relatório de Garantias (Excel)"):
            try:
                todos = supabase.table("registros_garantia").select("*").execute()
                if todos.data:
                    df_excel = pd.DataFrame(todos.data)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_excel.to_excel(writer, index=False, sheet_name='Garantias')
                    st.download_button(
                        label="📥 Baixar Arquivo Excel",
                        data=output.getvalue(),
                        file_name=f"relatorio_garantias_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error("Erro ao gerar relatório.")

        # 2. Gestão de Usuários
        st.divider()
        with st.expander("➕ Cadastrar Novo Cliente"):
            with st.form("novo_user"):
                n_user = st.text_input("Login")
                n_pass = st.text_input("Senha")
                n_venc = st.date_input("Vencimento Assinatura", value=datetime.now() + timedelta(days=30))
                if st.form_submit_button("Salvar Cliente"):
                    supabase.table("usuarios_sistema").insert({"login": n_user, "senha": n_pass, "vencimento_assinatura": n_venc.isoformat()}).execute()
                    st.success("Cliente criado!")

        st.subheader("Clientes Ativos")
        users = supabase.table("usuarios_sistema").select("*").eq("role", "cliente").execute()
        if users.data:
            st.table(pd.DataFrame(users.data)[['login', 'vencimento_assinatura']])
