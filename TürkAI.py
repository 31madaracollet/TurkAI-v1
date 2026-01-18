import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI v180", page_icon="🇹🇷", layout="wide")

# --- 🎨 TEMATİK DETAYLAR (Beyaz Yazılı Kırmızı Balon Stili) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; font-family: 'Segoe UI', Tahoma, sans-serif !important; }

    .giris-kart {
        background: #fffafa;
        border-radius: 20px;
        padding: 35px;
        border: 2px solid #cc0000;
        text-align: center;
        box-shadow: 0px 8px 20px rgba(204,0,0,0.05);
    }

    .user-box {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: #ffffff !important;
        padding: 15px 22px;
        border-radius: 20px 20px 0px 20px;
        margin: 10px 0px 25px auto;
        width: fit-content;
        max-width: 75%;
        box-shadow: 0px 4px 12px rgba(204, 0, 0, 0.2);
        font-weight: 500;
    }
    .user-box b, .user-box strong { color: #ffffff !important; }

    .ai-res-block {
        background: #fdfdfd;
        border-left: 8px solid #cc0000;
        padding: 25px;
        border-radius: 0px 15px 15px 0px;
        margin-bottom: 30px;
        line-height: 1.8;
        color: #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.02);
    }

    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v180.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 GİRİŞ / KAYIT SİSTEMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kart'><h1>🇹🇷 TürkAI</h1><p>Milli Analiz Sistemi</p></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sistemi Başlat", use_container_width=True):
                hp = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Bilgiler hatalı kanka.")
        with t2:
            nu = st.text_input("Yeni Kullanıcı", key="r_u")
            np = st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Kaydol", use_container_width=True):
                if nu and np:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                        conn.commit(); st.success("Kaydoldun kanka, şimdi giriş yap.")
                    except: st.error("Bu kullanıcı adı dolu.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Oturumu Kapat"): st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("📡 Motor Seçimi:", ["V1 (Wikipedia)", "V2 (Global/Sözlük)", "V3 (Hesap Makinesi)"])
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## 🔍 TürkAI Araştırma Terminali")
sorgu = st.chat_input("Neyi analiz edelim kanka?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # --- V1: Wikipedia (Orijinal) ---
    if m_secim == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
            head = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}", headers=headers).text, 'html.parser')
            info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
            st.session_state.bilgi, st.session_state.konu = info, head
        except: st.session_state.bilgi = "Veri bulunamadı kanka."

    # --- V2: Global (Orijinal) ---
    elif m_secim == "V2 (Global/Sözlük)":
        try:
            r = requests.get(f"https://api.duckduckgo.com/?q={sorgu}&format=json&no_html=1", headers=headers).json()
            st.session_state.bilgi, st.session_state.konu = r.get("AbstractText", "Özet bulunamadı."), sorgu.title()
        except: st.session_state.bilgi = "Bağlantı pürüzü çıktı."

    # --- V3: HESAP MAKİNESİ (Yeni) ---
    elif m_secim == "V3 (Hesap Makinesi)":
        try:
            # Sadece güvenli karakterleri eval et
            temiz = "".join(c for c in sorgu if c in "0123456789+-*/(). ")
            res = eval(temiz, {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"Matematiksel Analiz Sonucu: {res}", "Matematik"
        except: st.session_state.bilgi = "Hesaplama hatası! Sayıları ve işlemleri kontrol et kanka."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit(); st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-box'><b>Sorgu:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-res-block'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
