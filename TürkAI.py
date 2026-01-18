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
    
    .ai-rapor-alani {
        border-left: 5px solid #cc0000;
        padding: 15px 20px;
        background-color: #f9f9f9;
        margin-top: 10px;
        line-height: 1.6;
        color: #333;
    }

    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v140.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM KONTROLÜ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<h1 style='text-align:center;'>🇹🇷 TürkAI Giriş</h1>", unsafe_allow_html=True)
    u_in = st.text_input("Kullanıcı")
    p_in = st.text_input("Şifre", type="password")
    if st.button("Sistemi Başlat"):
        h_p = hashlib.sha256(p_in.encode()).hexdigest()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
        if c.fetchone(): st.session_state.user = u_in; st.rerun()
        else:
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (u_input, h_p)); conn.commit()
                st.session_state.user = u_in; st.rerun()
            except: st.warning("Hatalı giriş veya kullanıcı mevcut.")
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Analiz Motoru:", ["V1 (Wikipedia)", "V2 (Sözlük/Ansiklopedi)", "V3 (Hesap Makinesi)"])
    if m_secim == "V3 (Hesap Makinesi)": st.info("💡 Not: Çarpma (*) sembolüdür.")
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:18]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## TürkAI Araştırma Paneli")
sorgu = st.chat_input("Mesajınızı yazın...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    # İNSAN GİBİ DAVRANAN HEADERS
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # --- V1: WIKIPEDIA (İnsan Modu) ---
    if m_secim == "V1 (Wikipedia)":
        try:
            search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json"
            r = requests.get(search_url, headers=headers).json()
            if r['query']['search']:
                head = r['query']['search'][0]['title']
                page_url = f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}"
                soup = BeautifulSoup(requests.get(page_url, headers=headers).text, 'html.parser')
                info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:4])
                st.session_state.bilgi, st.session_state.konu = info, head
            else: st.session_state.bilgi = "Aradığın konuyu Wikipedia'da bulamadım kanka."
        except: st.session_state.bilgi = "Wikipedia'ya bağlanırken bir sorun çıktı, tekrar dener misin?"

    # --- V2: SÖZLÜK (İnsan Modu - DuckDuckGo Scraper) ---
    elif m_secim == "V2 (Sözlük/Ansiklopedi)":
        try:
            # Sanki birisi DuckDuckGo'da aratıp ilk özeti okuyormuş gibi
            api_url = f"https://api.duckduckgo.com/?q={sorgu}&format=json&no_html=1&skip_disambig=1"
            r = requests.get(api_url, headers=headers).json()
            if r.get("AbstractText"):
                st.session_state.bilgi, st.session_state.konu = r["AbstractText"], sorgu.title()
            else:
                st.session_state.bilgi = "Bunun sözlük karşılığını veya kısa tanımını bulamadım kanka."
        except: st.session_state.bilgi = "Sözlük servisinde bir aksama oldu."

    # --- V3: HESAP MAKİNESİ ---
    elif m_secim == "V3 (Hesap Makinesi)":
        try:
            temiz = "".join(c for c in sorgu if c in "0123456789+-*/(). ")
            res = eval(temiz, {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"Hesaplama Sonucu: {res}", "Matematik"
        except: st.session_state.bilgi = "Matematik işlemini çözemedim, rakamları kontrol et kanka."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit(); st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 TürkAI: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
