import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
import socket
from fpdf import FPDF # PDF oluşturma kütüphanesi

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷")

def get_db(): 
    return sqlite3.connect('turkai_master_v77.db', check_same_thread=False)

# --- 📄 PDF OLUŞTURMA FONKSİYONU ---
def pdf_olustur(baslik, icerik):
    pdf = FPDF()
    pdf.add_page()
    # Türkçe karakter desteği için standart font (Bazı karakterler için latin-1 kullanılır)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, baslik.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, icerik.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- (Giriş ve Veritabanı kodları v67 ile aynı...) ---
# ... (Kodu kısa tutmak için buraları geçiyorum, senin v67 yapını koru) ...

# --- 📟 ÇIKTI ALANI ---
if st.session_state.get("analiz_sonucu"):
    st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    
    # 📥 PDF İNDİRME BUTONU (YENİ ÖZELLİK)
    pdf_dosyasi = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
    st.download_button(
        label="📥 Bu Bilgiyi PDF Olarak İndir",
        data=pdf_dosyasi,
        file_name=f"{st.session_state.su_anki_konu}.pdf",
        mime="application/pdf"
    )

# --- 📥 ARAŞTIRMA MOTORU ---
# (Wikipedia'dan veri çekme kısmı v67 ile aynı kalacak)
