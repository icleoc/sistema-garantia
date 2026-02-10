# --- ABA: SCANNER ---
    if aba == "Scanner":
        st.markdown("<h2 style='text-align: center;'>🛡️ Checkpoint</h2>", unsafe_allow_html=True)
        
        # Gerenciador de estado para resetar o campo de pedido
        if 'pedido_key' not in st.session_state:
            st.session_state.pedido_key = 0

        c1, c2 = st.columns([2, 1])
        with c1: 
            # O campo limpa automaticamente quando incrementamos o pedido_key
            num_pedido = st.text_input("📦 Número do Pedido", key=f"pedido_{st.session_state.pedido_key}")
        with c2: 
            st.write("##")
            if st.button("🗑️ Zerar Tudo"): 
                st.session_state.bips_sessao = []
                st.session_state.pedido_key += 1 # Força a limpeza do campo de texto
                st.rerun()

        with st.form("scan", clear_on_submit=True):
            input_scan = st.text_input("ESCANEIE O CÓDIGO")
            if st.form_submit_button("PROCESSAR BIPE", use_container_width=True):
                if not num_pedido:
                    st.error("⚠️ Informe o Pedido antes de começar!")
                elif input_scan:
                    codigo = input_scan.strip()
                    
                    # 1. Verifica no banco se o produto já existe para este dono
                    res = supabase.table("registros_garantia").select("*").eq("codigo", codigo).eq("owner_id", user['id']).order("validade", desc=True).limit(1).execute()
                    
                    if res.data:
                        item = res.data[0]
                        val_p = datetime.fromisoformat(item['validade'].split('+')[0]).date()
                        msg = "✅ EM GARANTIA" if hoje <= val_p else "❌ EXPIRADO"
                        msg += f" (Venc: {val_p.strftime('%d/%m/%Y')})"
                    else:
                        # 2. Cadastro novo de 3 meses (90 dias)
                        v_p = (datetime.now() + timedelta(days=90)).isoformat()
                        supabase.table("registros_garantia").insert({
                            "codigo": codigo, 
                            "validade": v_p, 
                            "owner_id": user['id'], 
                            "numero_pedido": num_pedido
                        }).execute()
                        msg = "🆕 NOVO CADASTRO (90 dias)"
                    
                    st.session_state.bips_sessao.append({"Pedido": num_pedido, "Código": codigo, "Status": msg})

        if st.session_state.bips_sessao:
            st.divider()
            df = pd.DataFrame(st.session_state.bips_sessao)
            df_view = df.groupby(['Pedido', 'Código', 'Status']).size().reset_index(name='Qtd')
            st.subheader(f"📊 Resumo (Total: {len(st.session_state.bips_sessao)})")
            st.table(df_view)
