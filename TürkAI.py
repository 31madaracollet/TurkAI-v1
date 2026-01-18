import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI v160", page_icon="🇹🇷", layout="wide")

# --- 🎨 CANVA MODERN EDİT (Tasarım Güncellemesi) ---
st.markdown("""
    <style>
    /* Genel Arkaplan */
    .stApp { background-color: #fcfcfc; }
    
    /* Başlıklar */
    h1, h2, h3 { 
        color: #cc0000 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        letter-spacing: -1px;
    }

    /* Giriş Paneli - Tam Profesyonel */
    .giris-kart {
        background: white;
        border-radius: 25px;
        padding: 50px;
        border: 1px solid #eee;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.05);
        text-align: center;
    }

    /* Sol Panel Özelleştirme */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #f0f0f0;
    }

    /* Kullanıcı Balonu (Chat Stili) */
    .user-box {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 0px 20px;
        margin: 10px 0px 25px auto;
        width: fit-content;
        max-width: 80%;
        box-shadow: 0px 4px 12px rgba(204, 0, 0, 0.2);
    }

    /* AI Sonuç Bloğu (Rapor Stili) */
    .ai-res-block {
        background: white;
        border-left: 8px solid #cc0000;
        padding: 20px;
        border-radius: 0px 15px 15px 0px;
        margin-bottom: 30px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.02);
        line-height: 1.8;
    }

    /* Butonlar */
    div.stButton > button {
        background-color: #cc0000 !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #ee0000 !important;
        box-shadow: 0px 5px 15px rgba(204, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI SİSTEMİ ---
def db_init():
    conn = sqlite3.connect('turkai_v160.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (user TEXT, topic TEXT, content TEXT, date TEXT, engine TEXT)')
    conn.commit()
    return conn, c

conn, c = db_init()

# --- 🔑 GİRİŞ / KAYIT EKRANI ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div class='giris-kart'><h1>🇹🇷 TürkAI</h1><p>Geleceğin Bilgi Terminali</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["🔑 Giriş", "📝 Yeni Kayıt"])
        
        with login_tab:
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sistemi Aç", use_container_width=True):
                hp = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Bilgiler tutmuyor kanka.")

        with reg_tab:
            nu = st.text_input("Kullanıcı Seç", key="r_u")
            np = st.text_input("Şifre Belirle", type="password", key="r_p")
            if st.button("Kaydı Onayla", use_container_width=True):
                if nu and np:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                        conn.commit(); st.success("Tamamdır kanka, şimdi giriş yap.")
                    except: st.error("Bu isim kapılmış.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkışı Yap"): st.session_state.clear(); st.rerun()
    st.divider()
    engine = st.radio("🛠️ Motor:", ["V1 (Wikipedia)", "V2 (Global)", "V3 (Matematik)"])
    st.divider()
    st.subheader("📂 Geçmiş Analizler")
    c.execute("SELECT topic, content FROM history WHERE user=? ORDER BY date DESC LIMIT 8", (st.session_state.user,))
    for t, cont in c.fetchall():
        if st.button(f"📌 {t[:20]}", key=f"h_{t}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = cont, t
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## 🔍 TürkAI Araştırma Terminali")
query = st.chat_input("Hangi konuda bilgi toplamak istersin?")

if query:
    st.session_state.last_query = query
    # --- MOTOR İŞLEMLERİ (V1, V2, V3) ---
    # (Önceki stabil motor kodlarını buraya entegre edebilirsin kanka)
    # Örnek V1 işlemi:
    try:
        if engine == "V1 (Wikipedia)":
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json").json()
            head = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}").text, 'html.parser')
            res = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:4])
            st.session_state.bilgi, st.session_state.konu = res, head
            c.execute("INSERT INTO history VALUES (?,?,?,?,?)", (st.session_state.user, head, res, str(datetime.datetime.now()), engine))
            conn.commit(); st.rerun()
    except: st.session_state.bilgi = "Bir pürüz çıktı kanka."

# --- 📊 GÖRÜNÜM ---
if "last_query" in st.session_state:
    st.markdown(f"<div class='user-box'><b>Sorgu:</b><br>{st.session_state.last_query}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 TürkAI Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-res-block'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
