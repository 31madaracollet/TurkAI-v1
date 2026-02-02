import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
from duckduckgo_search import DDGS
import concurrent.futures

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 SENİN MODERN TEMAN (Bozulmadı, İyileştirildi) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
    .giris-kapsayici {
        background-color: #fffafa; border: 2px solid #cc0000; border-radius: 20px;
        padding: 30px; text-align: center; box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
    }
    .user-msg {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: #ffffff !important; padding: 12px 18px; border-radius: 15px 15px 0px 15px;
        margin-bottom: 20px; width: fit-content; max-width: 70%; margin-left: auto;
    }
    .ai-rapor-alani {
        border-left: 6px solid #cc0000; padding: 20px 25px;
        background-color: #fdfdfd; margin-bottom: 25px; border-radius: 0px 15px 15px 0px;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button {
        background-color: #cc0000 !important; color: white !important;
        border-radius: 10px !important; font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    return conn

conn = get_db()
c = conn.cursor()

# --- 🛡️ AGRESİF FİLTRE MOTORU ---
def temizle_motoru(text):
    if not text: return ""
    # Arapça, Çince, Korece ve garip sembolleri siler. Sadece Latin + Türkçe + Rakam bırakır.
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/%@=]', '', str(text))

# --- 🔍 ARAŞTIRMA ÇEKİRDEKLERİ ---
def wiki_sorgu(sorgu):
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        r = requests.get(url, timeout=5).json()
        return f"📖 **Wikipedia:** {r.get('extract', '')}"
    except: return ""

def web_sorgu(sorgu):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(sorgu, region='tr-tr', max_results=4))
            return "\n".join([f"🌐 **{r['title']}**: {r['body']}" for r in results])
    except: return ""

# --- 🔑 GİRİŞ / KAYIT ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                if c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone():
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı!")
        with t2:
            nu, np = st.text_input("Yeni Ad"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Tamamdır kanka, giriş yap!")
                except: st.error("Bu isim alınmış.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("### 📌 Geçmiş")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,)).fetchall()
    for k, i in gecmis:
        if st.button(f"📄 {k[:15]}", key=f"h_{hash(k)}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k

# --- 💻 AKILLI ANALİZ ---
st.markdown("## TürkAI Araştırma Terminali")
sorgu = st.chat_input("Emret kanka...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    with st.spinner('🚀 TurkAI derin internete daldı...'):
        # 1. Matematik
        if re.match(r"^[\d\+\-\*/\.\(\)\s,x]+$", sorgu.replace("x", "*")):
            try:
                st.session_state.bilgi = f"🧮 **Sonuç:** {eval(sorgu.replace('x', '*').replace(',', '.'), {'__builtins__':{}}, {})}"
                st.session_state.konu = "Matematik"
            except: st.session_state.bilgi = "Hesap hatası."
        
        # 2. Hava Durumu
        elif any(x in sorgu.lower() for x in ["hava", "derece"]):
            try:
                sehir = sorgu.lower().replace("hava","").replace("durumu","").strip() or "Istanbul"
                r = requests.get(f"https://wttr.in/{sehir}?format=j1", timeout=5).json()
                curr = r['current_condition'][0]
                st.session_state.bilgi = f"📍 {sehir.upper()}: {curr['temp_C']}°C, {curr['lang_tr'][0]['value']}"
                st.session_state.konu = f"{sehir.title()} Hava"
            except: st.session_state.bilgi = "Hava bilgisi alınamadı."
            
        # 3. Derin Web Arama (Paralel)
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                w1 = executor.submit(wiki_sorgu, sorgu)
                w2 = executor.submit(web_sorgu, sorgu)
                st.session_state.bilgi = temizle_motoru(f"{w2.result()}\n\n{w1.result()}")
                st.session_state.konu = sorgu.title()
        
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), "AI"))
        conn.commit()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)
if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)

    def pdf_indir():
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=12)
        def p_temiz(t):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): t = t.replace(k,v)
            return re.sub(r'[^\x00-\x7F]+', '', t)
        t_metin = f"KONU: {p_temiz(st.session_state.konu)}\n\n{p_temiz(st.session_state.bilgi)}"
        pdf.multi_cell(0, 10, txt=t_metin.encode('latin-1', 'ignore').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')
    
    st.download_button("📄 PDF İndir", data=pdf_indir(), file_name="Rapor.pdf")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #cc0000;'>🚀 Developed by <a href='https://github.com/31madaracollet' style='color: #cc0000; text-decoration: none;'><b>Madara</b></a></p>", unsafe_allow_html=True)
