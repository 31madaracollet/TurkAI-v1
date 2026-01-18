import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF
import extra_streamlit_components as stx # Hafıza için yeni kütüphane

# --- ⚙️ AYARLAR ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🍪 ÇEREZ YÖNETİCİSİ (HAFIZA) ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def sifrele(sifre): 
    return hashlib.sha256(str.encode(sifre)).hexdigest()

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_master_v78.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
conn.commit()

# --- 🔑 OTURUM KONTROLÜ (YENİ SİSTEM) ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
    st.session_state.user = ""
    
    # Tarayıcı çerezine bak
    kayitli_user = cookie_manager.get(cookie="turkai_user")
    if kayitli_user:
        st.session_state.user = kayitli_user
        st.session_state.giris_yapildi = True

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v78.0</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol"):
            if y_u and y_p:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt başarılı!")
                except: st.error("Bu isim dolu!")
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sistemi Aç"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                # HAFIZAYA AL (Çerezi 30 günlüğüne kaydet)
                cookie_manager.set("turkai_user", u, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.giris_yapildi, st.session_state.user = True, u
                st.rerun()
            else: st.error("Hatalı!")
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Oturumu Tamamen Kapat", use_container_width=True):
        cookie_manager.delete("turkai_user") # Çerezi sil
        st.session_state.clear()
        st.rerun()
    st.divider()
    # (Buraya eski aramalar kodunu ekleyebilirsin...)

# --- 💻 ANA EKRAN & PDF İŞLEMLERİ ---
# (v77'deki PDF ve Wikipedia kodlarının aynısı burada devam edecek)
st.write("Hoş geldin kanka! Artık sayfa yenilense de buradasın.")

# --- 📄 PDF OLUŞTURUCU (v77 ile aynı) ---
def pdf_hazirla(baslik, icerik):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, baslik.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
    pdf.ln(5); pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, icerik.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output()

# Çıktı ve Giriş Alanı...
# (v77 kodundaki msg = st.chat_input kısmını buraya yapıştırabilirsin)
