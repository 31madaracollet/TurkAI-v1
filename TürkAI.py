import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 CANVA TEMASI ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
    .user-msg {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: #ffffff !important; padding: 12px 18px; border-radius: 15px 15px 0px 15px;
        margin-bottom: 20px; width: fit-content; max-width: 70%; margin-left: auto;
    }
    .user-msg * { color: #ffffff !important; }
    .ai-rapor-alani {
        border-left: 6px solid #cc0000; padding: 20px 25px;
        background-color: #fdfdfd; margin-bottom: 10px;
        border-radius: 0px 15px 15px 0px; box-shadow: 2px 2px 8px rgba(0,0,0,0.02);
    }
    .kaynak-atfi { font-size: 0.85rem; color: #888; font-style: italic; margin-bottom: 20px; }
    .mat-not { background-color: #fff3f3; color: #cc0000; padding: 10px; border-radius: 10px; border: 1px dashed #cc0000; margin-top: 10px; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button { background-color: #cc0000 !important; color: white !important; border-radius: 10px !important; font-weight: bold !important; }
    
    /* PDF YAZDIRMA SİHİRBİAZI */
    @media print {
        header, [data-testid="stSidebar"], .stChatInput, .stButton, footer { display: none !important; }
        .stApp { background-color: white !important; }
        .ai-rapor-alani { border: 1px solid #cc0000 !important; box-shadow: none !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 🛠️ KARAKTER FİLTRESİ (GARİP HARFLERİ KOVAR) ---
def harf_filtresi(metin):
    # Sadece Latin harfleri, sayılar, noktalama ve Türkçe karakterleri tutar
    # Arapça, Çince, Yunanca vs. bu süzgece takılır.
    filtreli = re.sub(r'[^\x00-\x7f\u00C0-\u017F\s.,!?():-]', '', metin)
    return filtreli

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 GİRİŞ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "aktif_motor" not in st.session_state: st.session_state.aktif_motor = ""

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u_in, p_in = st.text_input("Kullanıcı Adı", key="l_u"), st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş Yap"):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): st.session_state.user = u_in; st.rerun()
                else: st.error("Hatalı.")
        with t2:
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kaydoldun!")
                except: st.error("Dolu.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("📡 Analiz Modu:", ["V1 (Wikipedia)", "V2 (Global - Canavar)", "V3 (Matematik)"])
    st.session_state.aktif_motor = m_secim
    if m_secim == "V3 (Matematik)":
        st.markdown("<div class='mat-not'>⚠️ <b>NOT:</b> Çarpı yerine yıldız (<b>*</b>) kullan kanka.</div>", unsafe_allow_html=True)
    st.divider()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## TürkAI Araştırma Terminali")
sorgu = st.chat_input("Neyi analiz edelim kanka?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    h = {'User-Agent': 'Mozilla/5.0'}
    
    if m_secim == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=h).json()
            head = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}", headers=h).text, 'html.parser')
            info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:4])
            st.session_state.bilgi, st.session_state.konu = harf_filtresi(info), head
        except: st.session_state.bilgi = "Bulunamadı."

    elif m_secim == "V2 (Global - Canavar)":
        try:
            wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
            r_wiki = requests.get(wiki_api, headers=h).json()
            bilgi = r_wiki.get('extract', "Kaynak bulunamadı.")
            st.session_state.bilgi, st.session_state.konu = harf_filtresi(bilgi), sorgu.title()
        except: st.session_state.bilgi = "Hata."

    elif m_secim == "V3 (Matematik)":
        try:
            res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"Sonuç: {res}", "Matematik"
        except: st.session_state.bilgi = "Hata."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit(); st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    if "V1" in st.session_state.aktif_motor: st.markdown("<div class='kaynak-atfi'>📍 Kaynak: Wikipedia</div>", unsafe_allow_html=True)
    elif "V2" in st.session_state.aktif_motor: st.markdown("<div class='kaynak-atfi'>📍 Kaynak: Global Network</div>", unsafe_allow_html=True)

    # PDF BUTONU (Sistem yazdırma tetikleyici)
    st.button("📄 Analizi PDF Yap", on_click=lambda: st.write('<script>window.print();</script>', unsafe_allow_html=True))
    st.markdown('<script>function printPage(){window.print();}</script>', unsafe_allow_html=True)
