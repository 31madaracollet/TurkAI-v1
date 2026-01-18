import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI v165", page_icon="🇹🇷", layout="wide")

# --- 🎨 CANVA MODERN & KONTRAST EDİT ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    
    h1, h2, h3 { 
        color: #cc0000 !important; 
        font-family: 'Segoe UI', Tahoma, sans-serif !important;
    }

    /* Giriş Paneli */
    .giris-kart {
        background: white;
        border-radius: 25px;
        padding: 40px;
        border: 1px solid #eee;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.05);
        text-align: center;
    }

    /* KULLANICI BALONU - YAZI BEYAZ YAPILDI */
    .user-box {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: #ffffff !important; /* TAM BEYAZ YAZI */
        padding: 15px 22px;
        border-radius: 20px 20px 0px 20px;
        margin: 10px 0px 25px auto;
        width: fit-content;
        max-width: 80%;
        box-shadow: 0px 4px 12px rgba(204, 0, 0, 0.2);
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* Balonun içindeki kalın yazılar da beyaz olsun */
    .user-box b, .user-box strong {
        color: #ffffff !important;
    }

    /* AI Sonuç Bloğu */
    .ai-res-block {
        background: white;
        border-left: 8px solid #cc0000;
        padding: 25px;
        border-radius: 0px 15px 15px 0px;
        margin-bottom: 30px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.02);
        line-height: 1.8;
        color: #333;
    }

    /* Butonlar */
    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_init():
    conn = sqlite3.connect('turkai_v165.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (user TEXT, topic TEXT, content TEXT, date TEXT, engine TEXT)')
    conn.commit()
    return conn, c

conn, c = db_init()

# --- 🔑 GİRİŞ / KAYIT ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "last_query" not in st.session_state: st.session_state.last_query = None

if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div class='giris-kart'><h1>🇹🇷 TürkAI</h1><p>Milli Bilgi Terminali</p></div>", unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with login_tab:
            u = st.text_input("Kullanıcı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sistemi Başlat", use_container_width=True):
                hp = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Bilgiler hatalı kanka.")
        with reg_tab:
            nu = st.text_input("Yeni Kullanıcı", key="r_u")
            np = st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Kaydol", use_container_width=True):
                if nu and np:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                        conn.commit(); st.success("Kaydoldun kanka, giriş yapabilirsin.")
                    except: st.error("Bu kullanıcı adı dolu.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    engine = st.radio("📡 Motor:", ["V1 (Wikipedia)", "V2 (Global)", "V3 (Matematik)"])
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT topic, content FROM history WHERE user=? ORDER BY date DESC LIMIT 8", (st.session_state.user,))
    for t, cont in c.fetchall():
        if st.button(f"📌 {t[:20]}", key=f"h_{t}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = cont, t
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## 🔍 TürkAI Analiz Paneli")
query = st.chat_input("Neyi merak ediyorsun kanka?")

if query:
    st.session_state.last_query = query
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    if engine == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json").json()
            head = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}").text, 'html.parser')
            res = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:4])
            st.session_state.bilgi, st.session_state.konu = res, head
            c.execute("INSERT INTO history VALUES (?,?,?,?,?)", (st.session_state.user, head, res, str(datetime.datetime.now()), engine))
            conn.commit(); st.rerun()
        except: st.session_state.bilgi = "Wikipedia'da bir aksilik oldu kanka."

    elif engine == "V2 (Global)":
        try:
            r = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1").json()
            res = r.get("AbstractText", "Global özet bulunamadı kanka.")
            st.session_state.bilgi, st.session_state.konu = res, query.title()
            c.execute("INSERT INTO history VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, res, str(datetime.datetime.now()), engine))
            conn.commit(); st.rerun()
        except: st.session_state.bilgi = "Global servis meşgul kanka."

# --- 📊 GÖRÜNÜM ---
if st.session_state.last_query:
    st.markdown(f"<div class='user-box'><b>Sorgu:</b><br>{st.session_state.last_query}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 TürkAI Sonuç: {st.session_state.konu}")
    st.markdown(f"<div class='ai-res-block'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
