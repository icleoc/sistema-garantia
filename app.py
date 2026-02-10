# --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint de Garantia</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            num_pedido = st.text_input("📦 Número do Pedido", placeholder="Ex: PED-1001")
        with col2:
            st.write("##")
            if st.button("🗑️ Zerar Sessão"):
                st.session_state.bips_sessao = []
                st.rerun()

        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO")
            submit = st.form_submit_button("PROCESSAR BIPE", use_container_width=True)
        
        if submit and input_scan:
            if not num_pedido:
                st.error("⚠️ Informe o Número do Pedido!")
            else:
                codigo = input_scan.strip()
                
                # 1. VERIFICAÇÃO NA LISTAGEM ATUAL (Sessão)
                # Se já bipou agora, apenas somamos visualmente (o DataFrame cuida disso)
                ja_na_lista = any(d['Código'] == codigo for d in st.session_state.bips_sessao)
                
                if ja_na_lista:
                    # Apenas adicionamos para aumentar a contagem no groupby abaixo
                    st.session_state.bips_sessao.append({
                        "Pedido": num_pedido, "Código": codigo, "Status": "CONTAGEM (Sessão)"
                    })
                else:
                    # 2. VERIFICAÇÃO DE GARANTIA RETROATIVA (Banco de Dados)
                    # Busca o registro mais recente deste código para este dono
                    res = supabase.table("registros_garantia")\
                        .select("*")\
                        .eq("codigo", codigo)\
                        .eq("owner_id", user['id'])\
                        .order("validade", desc=True)\
                        .limit(1).execute()
                    
                    if res.data:
                        # PRODUTO JÁ EXISTE: Checar se ainda vale a garantia
                        item = res.data[0]
                        val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                        
                        if hoje <= val_p:
                            msg = f"✅ EM GARANTIA (Vence: {val_p.strftime('%d/%m/%Y')})"
                        else:
                            msg = f"❌ EXPIRADO (Venceu: {val_p.strftime('%d/%m/%Y')})"
                    else:
                        # PRODUTO NOVO: Criar cadastro de 90 dias
                        v_p = (datetime.now() + timedelta(days=90)).isoformat()
                        supabase.table("registros_garantia").insert({
                            "codigo": codigo, 
                            "validade": v_p, 
                            "owner_id": user['id'], 
                            "numero_pedido": num_pedido
                        }).execute()
                        msg = "🆕 NOVO CADASTRO (90 dias)"
                    
                    st.session_state.bips_sessao.append({
                        "Pedido": num_pedido, "Código": codigo, "Status": msg
                    })

        # --- EXIBIÇÃO AGRUPADA ---
        if st.session_state.bips_sessao:
            st.divider()
            df = pd.DataFrame(st.session_state.bips_sessao)
            # Agrupa para somar quantidades de itens iguais
            df_view = df.groupby(['Pedido', 'Código', 'Status']).size().reset_index(name='Quantidade')
            
            st.subheader(f"📊 Resumo do Lote (Total: {len(st.session_state.bips_sessao)} itens)")
            st.table(df_view)
