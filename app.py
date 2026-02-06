import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO SISTEMA ---
st.set_page_config(page_title="Jarvis Ultra-Scan", layout="centered")

# Inicialização do Banco de Dados em Cache (Os dados ficam salvos enquanto a aba estiver aberta)
if 'db_vendas' not in st.session_state:
    st.session_state.db_vendas = {}

# --- INTERFACE LATERAL (LOGO E AJUSTES) ---
st.sidebar.title("⚙️ Configurações Jarvis")
logo = st.sidebar.file_uploader("Upload da Logo da Empresa", type=["png", "jpg"])

if logo:
    st.image(logo, width=200)
else:
    st.title("🛡️ Sistema de Garantia")

st.sidebar.divider()
prazo_meses = st.sidebar.number_input("Prazo Padrão (Meses)", value=12)
st.sidebar.info("O sistema registra automaticamente 1 ano (12 meses) de garantia por padrão.")

# --- PAINEL PRINCIPAL ---
st.subheader("🚀 Scanner de Saída e Consulta")

# O campo de texto limpa automaticamente após cada bip (usando o form)
with st.form("scan_form", clear_on_submit=True):
    input_scanner = st.text_input("ESCANEIE O PRODUTO AQUI", placeholder="Aguardando bip...", help="O foco deve estar aqui para o scanner funcionar.")
    # O botão de "Processar" é acionado pelo 'Enter' automático que o scanner envia
    submit_button = st.form_submit_button("Processar Manualmente (ou aperte Enter)")

if input_scanner:
    codigo = input_scanner.strip()
    
    # 1. VERIFICAÇÃO: O produto já existe no banco?
    if codigo in st.session_state.db_vendas:
        item = st.session_state.db_vendas[codigo]
        hoje = datetime.now()
        
        if hoje <= item["validade"]:
            st.success(f"✅ PRODUTO EM GARANTIA")
            st.write(f"**ID:** {codigo}")
            st.info(f"**Data da Venda:** {item['data_saida'].strftime('%d/%m/%Y')}\n\n**Vence em:** {item['validade'].strftime('%d/%m/%Y')}")
        else:
            st.error(f"❌ GARANTIA EXPIRADA")
            st.write(f"**ID:** {codigo}")
            st.warning(f"**Venceu em:** {item['validade'].strftime('%d/%m/%Y')}")
            
    # 2. CADASTRO: Se é a primeira vez que o código aparece
    else:
        data_saida = datetime.now()
        validade = data_saida + timedelta(days=prazo_meses * 30)
        
        # Salva no dicionário
        st.session_state.db_vendas[codigo] = {
            "data_saida": data_saida,
            "validade": validade
        }
        
        st.balloons()
        st.success(f"💾 PRODUTO CADASTRADO COM SUCESSO!")
        st.write(f"**ID Registrado:** {codigo}")
        st.write(f"**Garantia até:** {validade.strftime('%d/%m/%Y')}")

# --- HISTÓRICO RÁPIDO ---
if st.session_state.db_vendas:
    with st.expander("📊 Últimas 5 Atividades"):
        # Transforma o dicionário em tabela para visualização
        df = pd.DataFrame.from_dict(st.session_state.db_vendas, orient='index')
        df.index.name = "Código/Serial"
        # Formata as datas para o padrão brasileiro na exibição
        df['data_saida'] = df['data_saida'].dt.strftime('%d/%m/%Y')
        df['validade'] = df['validade'].dt.strftime('%d/%m/%Y')
        st.table(df.tail(5))
