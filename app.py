import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configurações de Página
st.set_page_config(page_title="Jarvis - Controle de Garantia Web", layout="centered")

# --- ESTILIZAÇÃO E LOGO ---
st.sidebar.title("Configurações")
uploaded_logo = st.sidebar.file_uploader("Upload da Logo da Empresa", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    st.image(uploaded_logo, width=200)
else:
    st.title("🛡️ Sistema de Garantia")

# --- LÓGICA DE NAVEGAÇÃO ---
menu = ["Registrar Saída", "Consultar Garantia", "Gestão de Licença (Adm)"]
choice = st.sidebar.selectbox("Menu", menu)

# Simulação de Banco de Dados (Será substituído pelo Supabase)
if 'db_vendas' not in st.session_state:
    st.session_state.db_vendas = {}

# --- TELA DE REGISTRO ---
if choice == "Registrar Saída":
    st.subheader("📝 Registrar Saída de Produto")
    
    with st.form("form_registro", clear_on_submit=True):
        codigo = st.text_input("Escaneie o Código de Barras")
        descricao = st.text_input("Descrição do Produto")
        meses = st.number_input("Prazo de Garantia (Meses)", min_value=1, max_value=60, value=12)
        btn_registrar = st.form_submit_button("Salvar Registro")

        if btn_registrar:
            if codigo and descricao:
                data_saida = datetime.now()
                st.session_state.db_vendas[codigo] = {
                    "descricao": descricao,
                    "data_saida": data_saida,
                    "validade": data_saida + timedelta(days=meses*30)
                }
                st.success(f"Produto {codigo} registrado com sucesso!")
            else:
                st.error("Preencha todos os campos!")

# --- TELA DE CONSULTA ---
elif choice == "Consultar Garantia":
    st.subheader("🔍 Consulta de Status")
    
    # Campo de busca que limpa o estado anterior ao mudar
    codigo_busca = st.text_input("Escaneie o Código para Consultar", key="input_consulta")

    if codigo_busca:
        if codigo_busca in st.session_state.db_vendas:
            item = st.session_state.db_vendas[codigo_busca]
            hoje = datetime.now()
            
            if hoje <= item["validade"]:
                restante = (item["validade"] - hoje).days
                st.success(f"✅ DENTRO DA GARANTIA")
                st.info(f"**Produto:** {item['descricao']}\n\n**Expira em:** {item['validade'].strftime('%d/%m/%Y')} ({restante} dias restantes)")
            else:
                st.error(f"❌ GARANTIA EXPIRADA")
                st.warning(f"**Produto:** {item['descricao']}\n\n**Venceu em:** {item['validade'].strftime('%d/%m/%Y')}")
        else:
            st.warning("Produto não encontrado no sistema.")
    else:
        st.write("Aguardando escaneamento...")

# --- TELA DE LICENÇA ---
elif choice == "Gestão de Licença (Adm)":
    st.subheader("🔑 Controle de Acesso")
    st.info("Aqui o senhor poderá bloquear ou liberar o acesso dos clientes via banco de dados.")