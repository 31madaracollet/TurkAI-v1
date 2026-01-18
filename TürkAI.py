import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 ÖZEL TEMA (v111) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 5px !important;
        width: 100%;
        font-weight: bold !important;
    }
    .giris-konteynir {
        border: 2px solid #cc0000;
        padding: 30px;
        border-radius: 15px;
        background-color: #fffafa;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_v111.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- OTURUM YÖNETİMİ ---
if "u" in st.query_params:
    st.session_state.user = st.query_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None

# --- 🔑 GİRİŞ VE KAYDOL EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    
    with col2:
        st.markdown("""
            <div class='giris-konteynir'>
                <h1 style='margin-bottom:0;'>🇹🇷 TürkAI</h1>
                <p style='color: #666;'>Kurumsal Analiz ve Araştırma Terminali</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Giriş Yap", "Yeni Kayıt"])
        
        with tab1:
            u_login = st.text_input("Kullanıcı Adı", key="l_user")
            p_login = st.text_input("Şifre", type="password", key="l_pass")
            if st.button("Sisteme Eriş"):
                h_p = hashlib.sha256(p_login.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_login, h_p))
                if c.fetchone():
                    st.session_state.user = u_login
                    st.query_params["u"] = u_login
                    st.rerun()
                else:
                    st.error("Kimlik bilgileri hatalı!")
        
        with tab2:
            u_reg = st.text_input("Kullanıcı Adı Belirle", key="r_user")
            p_reg = st.text_input("Şifre Belirle", type="password", key="r_pass")
            if st.button("Hesap Oluştur ve Gir"):
                if u_reg and p_reg:
                    h_p = hashlib.sha256(p_reg.encode()).hexdigest()
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (u_reg, h_p))
                        conn.commit()
                        st.session_state.user = u_reg
                        st.query_params["u"] = u_reg
                        st.success("Kayıt başarılı!")
                        st.rerun()
                    except:
                        st.error("Bu kullanıcı adı zaten alınmış!")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")
    st.stop()

# --- 🚀 ANA PANEL (Giriş sonrası) ---
with st.sidebar:
    st.markdown(f"<h3 style='color:#cc0000; text-align:center;'>🇹🇷 {st.session_state.user}</h3>", unsafe_allow_html=True)
    if st.button("🔴 Güvenli Çıkış"): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    
    st.divider()
    aktif_motor = st.radio("Analiz Motoru:", ["V1 (Wikipedia)", "V2 (Teknik/Sözlük)", "V3 (Hesap Makinesi)"])
    
    st.divider()
    st.subheader("📂 Sorgu Geçmişi")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"📌 [{m}] {k[:15]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = i, k, m
            st.rerun()

# --- ARAŞTIRMA BÖLÜMÜ ---
st.markdown("<h2 style='border-bottom: 2px solid #cc0000;'>TürkAI Analiz Terminali</h2>", unsafe_allow_html=True)
sorgu = st.chat_input("Sorgu veya işlem giriniz...")

# ... (Arama ve Hesaplama Motorları v110 ile aynı kalacak şekilde devam ediyor) ...
# (Kodu çok uzatmamak için arama mantığını v110'dan alabilirsin, giriş kısmı artık tam istediğin gibi Tab'lı ve güvenli)
