import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 ÖZEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    
    /* Kullanıcı Mesaj Balonu (Sağda) */
    .user-msg {
        background-color: #cc0000;
        color: white;
        padding: 12px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 20px;
        width: fit-content;
        max-width: 70%;
        margin-left: auto;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* TürkAI Cevap Alanı (Normal Metin) */
    .ai-cevap-alani {
        border-left: 5px solid #cc0000;
        padding: 10px 20px;
        margin-top: 10px;
        background-color: #fdfdfd;
        line-height: 1.6;
    }

    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .giris-kutu { border: 2px solid #cc0000; padding: 25px; border-radius: 15px; text-align: center; background-color: #fffafa; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v127.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM VE HATA KONTROLÜ ---
if "u" in st.query_params: st.session_state.user = st.query_params["u"]
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "konu" not in st.session_state: st.session_state.konu = "" # Hata önleyici

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<div class='giris-kutu'><h1>🇹🇷 TürkAI</h1><p>Giriş ve Kayıt Paneli</p></div>", unsafe_allow_html=True)
        mod = st.radio("Seçim:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
        u_in = st.text_input("Kullanıcı")
        p_in = st.text_input("Şifre", type="password")
        if st.button("Başlat"):
            h_p = hashlib.sha256(p_in.encode()).hexdigest()
            if mod == "Giriş Yap":
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): st.session_state.user = u_in; st.query_params["u"] = u_in; st.rerun()
                else: st.warning("Bilgiler hatalı.")
            else:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (u_in, h_p)); conn.commit()
                    st.session_state.user = u_in; st.query_params["u"] = u_in; st.rerun()
                except: st.warning("Kullanıcı zaten var.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    if st.button("🔴 Çıkış Yap"): st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Motor:", ["Wikipedia", "Sözlük/Teknik", "Hesap Makinesi"])
    if m_secim == "Hesap Makinesi":
        st.info("💡 Not: Çarpma işareti (*) sembolüdür.")
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:18]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.son_sorgu, st.session_state.konu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("<h2 style='border-bottom: 2px solid #cc0000;'>TürkAI Analiz Terminali</h2>", unsafe_allow_html=True)
sorgu = st.chat_input("Mesajınızı yazın...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    if m_secim == "Hesap Makinesi":
        try:
            temiz = "".join(c for c in sorgu if c in "0123456789+-*/(). ")
            res = eval(temiz, {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"İşlem Sonucu: {res}", "Matematik"
            c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih) VALUES (?,?,?,?)", (st.session_state.user, "Matematik", st.session_state.bilgi, str(datetime.datetime.now())))
            conn.commit(); st.rerun()
        except: st.session_state.bilgi = "Matematiksel işlem anlaşılamadı."
    
    elif m_secim == "Wikipedia":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json").json()
            if r['query']['search']:
                head = r['query']['search'][0]['title']
                soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}").text, 'html.parser')
                txt = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:3])
                st.session_state.bilgi, st.session_state.konu = txt, head
                c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih) VALUES (?,?,?,?)", (st.session_state.user, head, txt, str(datetime.datetime.now())))
                conn.commit(); st.rerun()
            else: st.session_state.bilgi = "Sonuç bulunamadı."
        except: st.session_state.bilgi = "Veri çekme hatası."

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 TürkAI: {st.session_state.konu}")
    st.markdown(f"<div class='ai-cevap-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
