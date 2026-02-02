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
        white-space: pre-wrap;
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

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

# --- 🛡️ AKILLI FİLTRE MOTORU ---
def analiz_temizle(text):
    if not text: return ""
    # "Microsoft", "Login", "Sign in" gibi çöp bilgileri temizle
    cop_kelimeler = ["Microsoft", "Sign In", "Create Your Account", "Sign up", "Login", "Cookies", "Privacy Policy"]
    for kelime in cop_kelimeler:
        text = re.sub(kelime, "", text, flags=re.I)
    
    # Arapça/Korece vs. temizliği + Türkçe koruma
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/%@=]', '', str(text))

# --- 🔍 DERİN ARAŞTIRMA SİSTEMİ ---
def wiki_sorgu(sorgu):
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        r = requests.get(url, timeout=5).json()
        if 'extract' in r:
            return f"📖 **Özet Bilgi:** {r['extract']}"
        return ""
    except: return ""

def web_sorgu(sorgu):
    try:
        with DDGS() as ddgs:
            # Sorguyu "nedir" veya "hakkında bilgi" diye genişletiyoruz ki Microsoft gelmesin
            results = list(ddgs.text(f"{sorgu} nedir hakkında bilgi", region='tr-tr', max_results=3))
            if not results: return ""
            analiz = "🌐 **Web Araştırma Sonuçları:**\n"
            for r in results:
                analiz += f"\n🔹 {r['title']}\n{r['body']}\n"
            return analiz
    except: return ""

# --- 🔑 GİRİŞ (Hatalardan Arındırılmış) ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı Adı", key="u_log")
            p = st.text_input("Şifre", type="password", key="p_log")
            if st.button("Giriş", key="b_log"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                if c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone():
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı!")
        with t2:
            nu, np = st.text_input("Yeni Ad", key="u_reg"), st.text_input("Yeni Şifre", type="password", key="p_reg")
            if st.button("Kaydol", key="b_reg"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kaydoldun!")
                except: st.error("İsim dolu.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış", key="logout"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("### 📌 Geçmiş")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,)).fetchall()
    for idx, (k, i) in enumerate(gecmis):
        if st.button(f"📄 {k[:15]}", key=f"h_{idx}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 AKILLI ANALİZ ---
st.markdown("## TürkAI Analiz Terminali")
sorgu = st.chat_input("Neyi analiz edelim?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    motor_tipi = "AI"
    with st.spinner('🚀 Derin araştırmaya çıkıldı...'):
        # 1. Matematik
        if re.match(r"^[\d\+\-\*/\.\(\)\s,x]+$", sorgu.replace("x", "*")):
            try:
                res = eval(sorgu.replace('x', '*').replace(',', '.'), {'__builtins__':{}}, {})
                st.session_state.bilgi = f"🧮 **Matematik:** {res}"
                st.session_state.konu = "Matematik"
            except: st.session_state.bilgi = "Hata."
        
        # 2. Hava Durumu
        elif any(x in sorgu.lower() for x in ["hava", "derece", "sicaklik"]):
            try:
                sehir = sorgu.lower().replace("hava","").replace("durumu","").strip() or "Istanbul"
                r = requests.get(f"https://wttr.in/{sehir}?format=j1", timeout=5).json()
                curr = r['current_condition'][0]
                st.session_state.bilgi = f"📍 {sehir.upper()}: {curr['temp_C']}°C, {curr['lang_tr'][0]['value']}"
                st.session_state.konu = f"{sehir.title()} Hava"
            except: st.session_state.bilgi = "Hava verisi yok."
            
        # 3. Derin Analiz
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                w1 = executor.submit(wiki_sorgu, sorgu)
                w2 = executor.submit(web_sorgu, sorgu)
                wiki_res = w1.result()
                web_res = w2.result()
                
                # Eğer Wikipedia'da varsa önce onu koy, yoksa web sonuçlarını koy
                birlesik = f"{wiki_res}\n\n{web_res}" if wiki_res else web_res
                st.session_state.bilgi = analiz_temizle(birlesik)
                st.session_state.konu = sorgu.title()
        
        if st.session_state.konu:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                      (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), "TurkAI"))
            conn.commit()
            st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)
if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    def pdf_yap():
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=12)
        def t(x):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): x = x.replace(k,v)
            return re.sub(r'[^\x00-\x7F]+', '', x)
        pdf.multi_cell(0, 10, txt=t(f"KONU: {st.session_state.konu}\n\n{st.session_state.bilgi}").encode('latin-1','ignore').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')
    
    st.download_button("📄 PDF Yap", data=pdf_yap(), file_name="Rapor.pdf", key="pdf_b")

st.markdown("<p style='text-align: center; color: #cc0000;'>Developed by <b>Madara</b></p>", unsafe_allow_html=True)
