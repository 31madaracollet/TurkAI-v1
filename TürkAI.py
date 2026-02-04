# ANA ARAMA KISMI (st.chat_input veya buton tetikleyicisinde)
if sorgu:
    st.session_state.son_sorgu = sorgu
    
    # Eğer yeniden üret butonuna basıldıysa, mevcut site indeksini kullan
    current_index = st.session_state.get('current_site_index', 0)
    
    # Arama yap
    result = smart_search_engine(
        sorgu, 
        current_site_index=current_index,
        mode="fast" if "Hızlı" in motor_choice else "deep"
    )
    
    if result:
        # Sonucu session state'e kaydet
        st.session_state.bilgi = result['content']
        st.session_state.konu = sorgu
        st.session_state.current_site_index = result['next_index']
        st.session_state.result_info = result  # Ek bilgileri sakla
        
        # Veritabanına kaydet
        c.execute("INSERT INTO aramalar VALUES (NULL,?,?,?,?,?)", 
                 (st.session_state.user, sorgu, result['content'], 
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  motor_choice))
        conn.commit()
    else:
        st.error("Hiçbir sitede sonuç bulunamadı.")

# SONUÇLARI GÖSTERME
if st.session_state.bilgi and st.session_state.son_sorgu:
    st.markdown(f"### 🔍 Analiz: {st.session_state.konu}")
    
    # Sonuç kutusu
    with st.container():
        st.markdown(st.session_state.bilgi)
        
        # "Yeniden Üret" butonu - sağ alt köşe
        col1, col2, col3 = st.columns([3, 1, 1])
        with col3:
            if st.button("🔄 Yeniden Üret", key="regenerate_btn"):
                # Mevcut site indeksini koruyarak yeniden ara
                st.rerun()
        
        # PDF indirme butonu
        with col1:
            try:
                pdf_data = create_pdf()
                st.download_button(
                    label="📄 PDF'e Dönüştür",
                    data=pdf_data,
                    file_name=f"turkai_{st.session_state.konu[:15]}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF oluşturulamadı: {str(e)[:50]}")
