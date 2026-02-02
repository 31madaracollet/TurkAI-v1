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

# --- 🎨 CANVA MODERN TEMASI ---
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
        white-space: pre-wrap; font-family: sans-serif; line-height: 1.6;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button {
        background-color: #cc0000 !important; color: white !important;
        border-radius: 10px !important; font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI VE HAFIZA ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    return conn

conn = get_db()
c = conn.cursor()

for key in ["user", "bilgi", "konu", "son_sorgu"]:
    if key not in st.session_state: st.session_state[key] = None if key != "konu" else ""

# --- 🛡️ KARAKTER VE İÇERİK FİLTRESİ ---
def analiz_temizle(text):
    if not text: return ""
    # 1. İngilizce reklam ve çöp metinleri temizle
    cop = ["Microsoft", "Sign In", "Yelp", "Starbucks", "Tripadvisor", "Best Espresso", "Restaurants in", "Log in", "Sign up"]
    for c in cop: text = re.sub(c, "", text, flags=re.I)
    # 2. Sadece Türkçe ve Latin karakterler kalsın (O soru işaretlerini siler)
    text = re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/%@=]', '', str(text))
    return text.strip()

# --- 🔍 ARAMA MOTORLARI ---
def wiki_sorgu(sorgu):
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        r = requests.get(url, timeout=5).json()
        return f"📖 **Wikipedia Analizi:**\n{r['extract']}" if 'extract' in r else ""
    except: return ""

def web_sorgu(sorgu):
    try:
        with DDGS() as ddgs:
            # Aramayı Türkçe bilgiye zorluyoruz
            results = list(ddgs.text(f"{sorgu} nedir bilgi", region='tr-tr', max_results=3))
            if not results: return ""
            res_text = "🌐 **İnternet Kaynakları:**\n"
            for r in results:
                res_text += f"\n- {r['title']}: {r['body']}\n"
            return res_text
    except: return ""

# --- 🔑 GİRİŞ SİSTEMİ ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u, p = st.text_input("Kullanıcı Adı", key="l_u"), st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sisteme Gir"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                if c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone():
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı!")
        with t2:
            nu, np = st.text_input("Yeni Ad", key="r_u"), st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kaydoldun!")
                except: st.error("İsim dolu.")
    st.stop()

# --- 🚀 PANEL VE SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("### 📌 Geçmiş")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,)).fetchall()
    for idx, (k, i) in enumerate(gecmis):
        if st.button(f"📄 {k[:15]}", key=f"btn_{idx}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 AKILLI ANALİZ ---
st.markdown("## TürkAI Analiz Terminali")
sorgu = st.chat_input("Neye bakalım kanka?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    with st.spinner('🚀 TürkAI araştırmaya başladı...'):
        # 1. Matematik
        if re.match(r"^[\d\+\-\*/\.\(\)\s,x]+$", sorgu.replace("x", "*")):
            try:
                res = eval(sorgu.replace('x', '*').replace(',', '.'), {'__builtins__':{}}, {})
                st.session_state.bilgi, st.session_state.konu = f"🧮 **Sonuç:** {res}", "Matematik"
            except: st.session_state.bilgi = "Hesap hatası."
        
        # 2. Hava Durumu
        elif any(x in sorgu.lower() for x in ["hava", "sicaklik"]):
            try:
                sehir = sorgu.lower().replace("hava","").replace("durumu","").strip() or "Istanbul"
                r = requests.get(f"https://wttr.in/{sehir}?format=j1", timeout=5).json()
                curr = r['current_condition'][0]
                st.session_state.bilgi = f"📍 {sehir.upper()}\n🌡️ Sıcaklık: {curr['temp_C']}°C\n☁️ Durum: {curr['lang_tr'][0]['value']}"
                st.session_state.konu = f"{sehir.title()} Hava"
            except: st.session_state.bilgi = "Hava bilgisi çekilemedi."
            
        # 3. Genel Bilgi (Derin Araştırma)
        else:
            with concurrent.futures.ThreadPoolExecutor() as ex:
                w1, w2 = ex.submit(wiki_sorgu, sorgu), ex.submit(web_sorgu, sorgu)
                r_wiki, r_web = w1.result(), w2.result()
                st.session_state.bilgi = analiz_temizle(f"{r_wiki}\n\n{r_web}" if r_wiki else r_web)
                st.session_state.konu = sorgu.title()
        
        if st.session_state.konu and st.session_state.user:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                      (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), "TurkAI"))
            conn.commit()
            st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)
if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    def pdf_indir():
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=11)
        def tr(x):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): x = x.replace(k,v)
            return re.sub(r'[^\x00-\x7F]+', '', x)
        pdf.multi_cell(0, 10, txt=tr(f"TURKAI ANALIZ - {st.session_state.konu}\n\n{st.session_state.bilgi}").encode('latin-1','ignore').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')
    
    st.download_button("📄 Analizi PDF Yap", data=pdf_indir(), file_name="Rapor.pdf", key="pdf_d")

st.markdown("<p style='text-align: center; color: #cc0000;'>🚀 Developed by <b>Madara</b></p>", unsafe_allow_html=True)
