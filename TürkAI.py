import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 AL-YILDIZ TEMASI (DÜZELTİLDİ) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    
    /* Giriş Kutusu Tasarımı */
    .giris-kapsayici {
        background-color: #fffafa;
        border: 2px solid #cc0000;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
    }
    
    /* Kullanıcı Mesaj Balonu */
    .user-msg {
        background-color: #cc0000;
        color: white;
        padding: 12px 18px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 20px;
        width: fit-content;
        max-width: 70%;
        margin-left: auto;
    }
    
    /* AI Rapor Bloğu */
    .ai-rapor-alani {
        border-left: 6px solid #cc0000;
        padding: 15px 25px;
        background-color: #fcfcfc;
        margin-bottom: 25px;
        font-size: 1.1rem;
        line-height: 1.7;
    }

    /* Kırmızı Butonlar */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #990000 !important;
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v150_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 GİRİŞ EKRANI (DÜZELTİLDİ) ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div class='giris-kapsayici'>
                <h1>🇹🇷 TürkAI</h1>
                <p style='color: #666;'>Milli Bilgi ve Analiz Terminali</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        u_in = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınız...")
        p_in = st.text_input("🔑 Şifre", type="password", placeholder="Şifreniz...")
        
        if st.button("Sistemi Başlat 🚀", use_container_width=True):
            if u_in and p_in:
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in; st.rerun()
                else:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (u_in, h_p)); conn.commit()
                        st.session_state.user = u_in; st.rerun()
                    except: st.error("Hatalı giriş yaptın kanka.")
            else: st.warning("Alanları boş bırakma kanka.")
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👤 {st.session_state.user}</h2>", unsafe_allow_html=True)
    if st.button("🔴 Oturumu Kapat", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("📡 Analiz Modu:", ["V1 (Wikipedia)", "V2 (Sözlük/Ansiklopedi)", "V3 (Matematik)"])
    st.divider()
    st.subheader("📂 Analiz Geçmişi")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("<h2 style='border-bottom: 3px solid #cc0000; padding-bottom: 10px;'>TürkAI Araştırma Terminali</h2>", unsafe_allow_html=True)
sorgu = st.chat_input("Neyi analiz edelim kanka?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    if m_secim == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
            head = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}", headers=headers).text, 'html.parser')
            info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:4])
            st.session_state.bilgi, st.session_state.konu = info, head
        except: st.session_state.bilgi = "Bunu Wikipedia'da bulamadım kanka, başka bir kelime dene."

    elif m_secim == "V2 (Sözlük/Ansiklopedi)":
        try:
            r = requests.get(f"https://api.duckduckgo.com/?q={sorgu}&format=json&no_html=1", headers=headers).json()
            if r.get("AbstractText"):
                st.session_state.bilgi, st.session_state.konu = r["AbstractText"], sorgu.title()
            else: st.session_state.bilgi = "Global kaynaklarda buna dair net bir özet bulamadım kanka."
        except: st.session_state.bilgi = "Sözlük servisine şu an ulaşılamıyor."

    elif m_secim == "V3 (Matematik)":
        try:
            res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"İşlem Sonucu: {res}", "Matematik"
        except: st.session_state.bilgi = "Bu hesabı yapamadım kanka, sayıları doğru girdiğine emin misin?"

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit(); st.rerun()

# --- 📊 GÖRÜNÜM (CHAT STİLİ) ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 TürkAI Analizi: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
