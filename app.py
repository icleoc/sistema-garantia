import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import extra_streamlit_components as stx

# --- CONEXÃO ---
URL = "https://mawujlwwhthckkepcbaj.supabase.co"
KEY = "sb_secret_FoyvSfWQou_YbsMEAfrA2A_5vUPsGqF" 
supabase: Client = create_client(URL, KEY)

# --- INTERFACE ---
st.set_page_config(page_title="Jarvis Pro Cloud", layout="centered")
cookie_manager = stx.CookieManager()

# (Funções de Login e E-mail mantidas conforme versões anteriores...)

if verificar_login():
    user = st.session_state.user_data
    hoje = date.today()
    
    # Inicializa a lista de bips da sessão atual se não existir
    if 'bips_sessao' not in st.session_state:
        st.session_state.bips_sessao = []

    # --- MENU LATERAL ---
    with st.sidebar:
        st.title(f"👤 {user['login']}")
        aba = st.radio("Navegação", ["Scanner", "Meu Perfil", "Gerenciar Usuários"]) if user['role'] == 'admin' else ["Scanner", "Meu Perfil"]
        if st.button("Sair"):
            if cookie_manager.get('jarvis_user'): cookie_manager.delete('jarvis_user')
            st.session_state.user_data = None
            st.rerun()

    # --- ABA: SCANNER (COM AGRUPAMENTO E CONTAGEM) ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        
        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO", key="s")
            submit = st.form_submit_button("PROCESSAR", use_container_width=True)
        
        if submit and input_scan:
            codigo = input_scan.strip()
            # O sistema agora filtra por código E dono
            res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).execute()
            
            if res.data:
                item = res.data[0]
                val_prod = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                status = "✅ GARANTIA OK" if hoje <= val_prod else "❌ EXPIRADO"
                msg = f"{status} | Vencimento: {val_prod.strftime('%d/%m/%Y')}"
            else:
                v_p = (datetime.now() + timedelta(days=90)).isoformat()
                supabase.table("registros_garantia").insert({"codigo": codigo, "validade": v_p, "owner_id": user['id']}).execute()
                msg = f"💾 NOVO CADASTRO (90 dias)"
            
            # Adiciona ao histórico visual da sessão
            st.session_state.bips_sessao.append({"Código": codigo, "Resultado": msg})

        # --- EXIBIÇÃO EM TABELA AGRUPADA ---
        if st.session_state.bips_sessao:
            st.divider()
            df_sessao = pd.DataFrame(st.session_state.bips_sessao)
            
            # Agrupa por Código para mostrar Quantidade
            df_agrupado = df_sessao.groupby(['Código', 'Resultado']).size().reset_index(name='Quantidade')
            
            st.subheader(f"📊 Resumo do Escaneamento (Total: {len(st.session_state.bips_sessao)})")
            st.table(df_agrupado[['Quantidade', 'Código', 'Resultado']])
            
            if st.button("Limpar Listagem Atual"):
                st.session_state.bips_sessao = []
                st.rerun()

    # (Restante das abas Meu Perfil e Admin mantidas...)
