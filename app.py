import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")

# --- LOGIN ---
def verificar_login():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if st.session_state.user_data is None:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário ou Email")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = supabase.table("usuarios_sistema").select("*").or_(f"login.eq.{u},email.eq.{u}").eq("senha", s).execute()
                if res.data:
                    st.session_state.user_data = res.data[0]
                    st.rerun()
                else: st.error("Incorreto.")
        return False
    return True

if verificar_login():
    user = st.session_state.user_data
    venc_assinatura = datetime.strptime(user['vencimento_assinatura'], '%Y-%m-%d').date()
    hoje = date.today()
    
    # --- ALERTA E BLOQUEIO COM WHATSAPP ---
    dias_restantes = (venc_assinatura - hoje).days
    whatsapp_link = "https://wa.me/5562991772700?text=Preciso%20renovar%20minha%20licença"

    if 0 <= dias_restantes <= 5:
        st.warning(f"⚠️ Licença vence em {dias_restantes} dias. [Falar com Suporte]({whatsapp_link})")
    elif dias_restantes < 0 and user['role'] != 'admin':
        st.error(f"❌ Licença expirada em {venc_assinatura.strftime('%d/%m/%Y')}.")
        st.markdown(f"### [CLIQUE AQUI PARA FALAR COM SUPORTE]( {whatsapp_link} )", unsafe_allow_html=True)
        st.stop()

    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Navegação", ["Scanner", "Gerenciar Usuários"]) if user['role'] == 'admin' else ["Scanner"]
        if st.button("Sair"):
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER (DADOS SEPARADOS POR DONO) ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        with st.form("scan_form", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO", key="scanner_input")
            st.form_submit_button("PROCESSAR", use_container_width=True)

        if input_scan:
            codigo = input_scan.strip()
            # Busca apenas nos bips que pertencem a este usuário (owner_id)
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            
            if res.data:
                item = res.data[0]
                val = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                if hoje <= val: st.success(f"✅ EM GARANTIA | Vence em: {val.strftime('%d/%m/%Y')}")
                else: st.error(f"❌ EXPIRADO | Venceu em: {val.strftime('%d/%m/%Y')}")
            else:
                nova_val = (datetime.now() + timedelta(days=365)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": nova_val, "owner_id": user['id']}).execute()
                st.info(f"💾 CADASTRADO: {codigo} (Dono: {user['login']})")

    # --- ABA: ADMIN ---
    elif aba == "Gerenciar Usuários":
        st.title("👥 Gestão de Clientes")
        tab1, tab2, tab3 = st.tabs(["Listar/Excluir", "Novo Usuário", "Renovar / Editar"])

        with tab1:
            res_u = supabase.table("usuarios_sistema").select("login, email, vencimento_assinatura").eq("role", "cliente").execute()
            if res_u.data:
                st.dataframe(pd.DataFrame(res_u.data), use_container_width=True)
                st.divider()
                # TRAVA DE SEGURANÇA: Selectbox começa vazia (None)
                lista_logins = [None] + [u['login'] for u in res_u.data]
                u_del = st.selectbox("Selecione um cliente para habilitar a exclusão", lista_logins)
                
                if u_del:
                    st.warning(f"Atenção: Deletar {u_del} apagará TODOS os bips deste cliente permanentemente.")
                    if st.button(f"🗑️ Confirmar Exclusão Definitiva"):
                        supabase.table("usuarios_sistema").delete().eq("login", u_del).execute()
                        st.success(f"Usuário e dados de {u_del} excluídos.")
                        st.rerun()

        # (Mantendo abas de cadastro e edição conforme as versões anteriores...)
