import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF # PDF motoru

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI VE GÜVENLİK ---
def db_baslat():
    conn = sqlite3.connect('turkai_pro_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

# --- 📄 PDF OLUŞTURMA FONKSİYONU ---
def pdf_olustur(baslik, icerik):
    pdf = FPDF()
    pdf.add_page()
    # Not: Standart FPDF Latin-1 destekler, Türkçe karakter hatası almamak için 
    # içerikteki Türkçe karakterleri basitçe dönüştürüyoruz (Web sunucularında font yüklemek karmaşıktır)
    temiz_baslik = baslik.replace('İ','I').replace('ı','i').replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
    # HTML etiketlerini PDF için temizle
    temiz_icerik = re.sub('<[^<]+?>', '', icerik) 
    temiz_icerik = temiz_icerik.replace('İ','I').replace('ı','i').replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"TurkAI - {temiz_baslik}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=temiz_icerik)
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, txt=f"Olusturulma Tarihi: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", align='R')
    
    return pdf.output(dest='S').encode('latin-1')

db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" in st.query_params and "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi, st.session_state.user = True, st.query_params["user"]

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 TASARIM ---
st.markdown("""
    <style>
    .sonuc-karti { background-color: #F9FAFB; padding: 25px; border-radius: 12px; border: 1px solid #E5E7EB; color: #111827; }
    .kaynak-box { background-color: #F3F4F6; padding: 15px; border-radius: 8px; border-left: 5px solid #DC2626; margin-top: 20px; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# --- 🚪 GİRİŞ SİSTEMİ (Özetlenmiş) ---
if not st.session_state.giris_yapildi:
    st.title("TürkAI Giriş")
    # (Buradaki giriş/kayıt kodları öncekiyle aynı...)
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Oturumu Kapat"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    # Geçmiş listeleme...

# --- ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    col_bilgi, col_islem = st.columns([4, 1])
    
    with col_bilgi:
        if "🔢" in st.session_state.analiz_sonucu:
            st.success(st.session_state.analiz_sonucu)
        else:
            st.markdown(f'<div class="sonuc-karti"><h3>📌 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
            
    with col_islem:
        # 📄 PDF İNDİRME BUTONU
        pdf_data = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button(
            label="📄 PDF İndir",
            data=pdf_data,
            file_name=f"{st.session_state.su_anki_konu}_TurkAI.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# --- ARAMA VE HESAPLAMA MOTORU ---
sorgu = st.chat_input("Araştır veya hesapla...")
# (Buradaki Wikipedia ve Matematik kodları v60.0 ile aynı kalacak şekilde devam eder)
