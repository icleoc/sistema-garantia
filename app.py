import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Jarvis Ultra-Scan", layout="centered")

# --- SISTEMA DE LOGIN SIMPLES ---
def login():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Acesso Restrito")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            # Aqui definimos o acesso (depois integraremos com banco de dados)
            if usuario == "admin" and senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        return False
    return True

if login():
    # Inicialização do Banco de Dados em Cache
    if 'db_vendas' not in st.session_state:
        st.session_state.db_vendas = {}

    # --- BARRA LATERAL ---
    st.sidebar.title("⚙️ Painel de Controle")
    logo = st.sidebar.file_uploader("Logo da Empresa", type=["png", "jpg"])
    if logo: st.sidebar.image(logo)
    
    prazo_meses = st.sidebar.number_input("Garantia (Meses)", value=12)
    
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

    # --- TELA PRINCIPAL ---
    st.title("🛡️ Checkpoint de Garantia")

    # Instrução para o usuário
    st.info("O foco está no campo abaixo. Basta escanear.")

    # O segredo para o scanner não precisar de 'Enter':
    # A maioria dos scanners envia um comando 'Enter' após a leitura. 
    # O st.text_input captura esse 'Enter' e processa o código imediatamente.
    with st.form("scan_form", clear_on_submit=True):
        input_scanner = st.text_input("AGUARDANDO SCANNER...", key="scanner_input")
        # Botão oculto apenas para permitir o envio automático pelo Enter do scanner
        submit = st.form_submit_button("Processando...", help="O scanner enviará o comando automaticamente")

    if input_scanner:
        codigo = input_scanner.strip()
        
        # 1. CONSULTA: Produto já existe?
        if codigo in st.session_state.db_vendas:
            item = st.session_state.db_vendas[codigo]
            hoje = datetime.now()
            
            if hoje <= item["validade"]:
                st.success(f"✅ DENTRO DA GARANTIA")
                st.metric("Status", "Válido", delta=f"Vence em {item['validade'].strftime('%d/%m/%Y')}")
            else:
                st.error(f"❌ GARANTIA EXPIRADA")
                st.metric("Status", "Expirado", delta=f"Venceu em {item['validade'].strftime('%d/%m/%Y')}", delta_color="inverse")
        
        # 2. REGISTRO: Produto novo
        else:
            data_saida = datetime.now()
            validade = data_saida + timedelta(days=prazo_meses * 30)
            
            st.session_state.db_vendas[codigo] = {
                "data_saida": data_saida,
                "validade": validade
            }
            
            # Notificação limpa (sem balões)
            st.success(f"💾 REGISTRADO: {codigo}")
            st.caption(f"Saída: {data_saida.strftime('%d/%m/%Y')} | Garantia até: {validade.strftime('%d/%m/%Y')}")

    # --- HISTÓRICO RÁPIDO (Tabela Limpa) ---
    if st.session_state.db_vendas:
        st.divider()
        st.subheader("📋 Últimos Movimentos")
        df = pd.DataFrame.from_dict(st.session_state.db_vendas, orient='index')
        df.index.name = "Código"
        df['data_saida'] = df['data_saida'].dt.strftime('%d/%m/%Y')
        df['validade'] = df['validade'].dt.strftime('%d/%m/%Y')
        st.dataframe(df.tail(5), use_container_width=True)
