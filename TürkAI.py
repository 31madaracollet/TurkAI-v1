import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re 
from fpdf import FPDF 

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 CANVA MODERN TEMASI ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
    
    .giris-kapsayici {
        background-color: #fffafa;
        border: 2px solid #cc0000; border-radius: 20px;
        padding: 30px; text-align: center;
        box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
    }

    /* GitHub Buton Stilleri */
    .apk-buton-link {
        display: block;
        width: 100%;
        background-color: #cc0000;
        color: white !important;
        text-align: center;
        padding: 15px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: bold;
        margin-bottom: 25px;
        transition: 0.3s;
    }
    .apk-buton-link:hover {
        background-color: #a30000;
        transform: scale(1.02);
    }

    .sidebar-apk-link {
        display: block;
        background-color: #000000;
        color: white !important;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 14px;
        border: 1px solid #cc0000;
        margin-top: 15px;
    }

    .ai-rapor-alani {
        border-left: 6px solid #cc0000; padding: 20px 25px;
        background-color: #fdfdfd; margin-bottom: 25px;
        border-radius: 0px 15px 15px 0px;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 GİRİŞ SİSTEMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        
        # --- GİRİŞ EKRANI APK BUTONU ---
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">📲 TürkAI Uygulamasını Yükle (Android APK)</a>', unsafe_allow_html=True)
        
        st.markdown("<div class='ozel-not'>⚠️ Beta sürümüdür, oturumlar geçicidir.</div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u_in = st.text_input("Kullanıcı Adı", key="l_u")
            p_in = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş Yap"):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): st.session_state.user = u_in; st.rerun()
                else: st.error("Hatalı bilgi.")
        with t2:
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kaydoldun, giriş yap!")
                except: st.error("Bu isim dolu.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("📡 Analiz Modu:", ["V1 (Wikipedia)", "V2 (Global - Canavar)", "V3 (Matematik)"])
    st.divider()
    
    # Geçmiş Aramalar Listesi
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()
    
    # --- YAN PANEL SONUNA APK BUTONU ---
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-apk-link">📥 Uygulamayı İndir</a>', unsafe_allow_html=True)

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
            st.session_state.bilgi, st.session_state.konu = info, head
        except: st.session_state.bilgi = "Sonuç bulunamadı."
    elif m_secim == "V2 (Global - Canavar)":
        try:
            wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
            r_wiki = requests.get(wiki_api, headers=h).json()
            bilgi = r_wiki.get('extract', "Maalesef özet bilgiye ulaşılamadı.")
            st.session_state.bilgi, st.session_state.konu = bilgi, sorgu.title()
        except: st.session_state.bilgi = "Hata oluştu."
    elif m_secim == "V3 (Matematik)":
        try:
            res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"Sonuç: {res}", "Matematik"
        except: st.session_state.bilgi = "Hesap hatası."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit(); st.rerun()

# --- 📊 SONUÇ VE PDF ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    def pdf_yap():
        try:
            pdf = FPDF()
            pdf.add_page()
            def temizle(t):
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): t = t.replace(k,v)
                return re.sub(r'[^\x00-\x7F]+', ' ', t)
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="TurkAI Analiz Raporu", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            metin = f"Konu: {temizle(st.session_state.konu)}\n\nRapor:\n{temizle(st.session_state.bilgi)}\n\nKullanici: {temizle(st.session_state.user)}"
            pdf.multi_cell(0, 10, txt=metin)
            return pdf.output(dest='S').encode('latin-1', 'replace')
        except: return None

    pdf_data = pdf_yap()
    if pdf_data:
        st.download_button(label="📄 Analizi PDF Olarak İndir", data=pdf_data, file_name=f"TurkAI_{st.session_state.konu}.pdf", mime="application/pdf")
