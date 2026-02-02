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
import concurrent.futures # Hızlandırma için lazım

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 CANVA MODERN TEMASI (Korundu & Güçlendirildi) ---
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
    .user-msg {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        color: #ffffff !important; padding: 12px 18px; border-radius: 15px 15px 0px 15px;
        margin-bottom: 20px; width: fit-content; max-width: 70%;
        margin-left: auto; box-shadow: 0px 4px 10px rgba(204, 0, 0, 0.2);
    }
    .ai-rapor-alani {
        border-left: 6px solid #cc0000; padding: 20px 25px;
        background-color: #fdfdfd; margin-bottom: 25px;
        border-radius: 0px 15px 15px 0px; box-shadow: 2px 2px 8px rgba(0,0,0,0.02);
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button {
        background-color: #cc0000 !important; color: white !important;
        border-radius: 10px !important; font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI BAĞLANTISI ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    return conn

conn = get_db_connection()
c = conn.cursor()

# --- 🛠️ YARDIMCI MOTORLAR ---
def agresif_temizle(text):
    """Sadece Latin harfleri ve Türkçe karakterleri tutar."""
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/]', '', str(text))

def wiki_cek(sorgu):
    try:
        r = requests.get(f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}", timeout=5).json()
        return f"📖 **Wikipedia Özeti:**\n{r.get('extract', 'Bilgi bulunamadı.')}"
    except: return ""

def web_ara(sorgu):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(sorgu, region='tr-tr', max_results=3))
            return "🌐 **Güncel Web Analizi:**\n" + "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except: return ""

# --- 🔑 OTURUM VE GİRİŞ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u_in = st.text_input("Kullanıcı Adı")
            p_in = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir"):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                res = c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p)).fetchone()
                if res: st.session_state.user = u_in; st.rerun()
                else: st.error("Hatalı kullanıcı veya şifre!")
        with t2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydı Tamamla"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kayıt başarılı! Giriş yapabilirsin.")
                except: st.error("Bu isimle bir kahraman zaten var.")
    st.stop()

# --- 🚀 ANA PANEL VE SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış Yap"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("### 📌 Geçmiş Aramalar")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,)).fetchall()
    for k, i in gecmis:
        if st.button(f"📄 {k[:20]}", key=f"btn_{hash(k+i)}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = i, k
            st.session_state.son_sorgu = k

# --- 💻 AKILLI ANALİZ DÖNGÜSÜ ---
st.markdown("## TürkAI Araştırma Terminali")

sorgu = st.chat_input("Neyi analiz edelim?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    motor_notu = "Derin Analiz"
    
    with st.spinner('🚀 TurkAI verileri topluyor, lütfen bekle kanka...'):
        # 1. MATEMATİK KONTROLÜ
        if re.match(r"^[\d\+\-\*/\.\(\)\s,x]+$", sorgu.replace("x", "*")):
            try:
                res = eval(sorgu.replace("x", "*").replace(",", "."), {"__builtins__": {}}, {})
                st.session_state.bilgi = f"🧮 **Matematiksel Sonuç:**\n# {res}"
                st.session_state.konu = "Matematik"
                motor_notu = "Matematik"
            except: st.session_state.bilgi = "Hesaplama yapılamadı."
            
        # 2. HAVA DURUMU KONTROLÜ
        elif any(x in sorgu.lower() for x in ["hava", "derece", "sıcaklık"]):
            try:
                sehir = sorgu.lower().replace("hava", "").replace("durumu", "").strip() or "Istanbul"
                r = requests.get(f"https://wttr.in/{sehir}?format=j1", timeout=5).json()
                curr = r['current_condition'][0]
                st.session_state.bilgi = f"📍 **{sehir.title()} Hava Durumu:**\n- Sıcaklık: {curr['temp_C']}°C\n- Nem: %{curr['humidity']}\n- Durum: {curr['lang_tr'][0]['value']}"
                st.session_state.konu = f"{sehir.title()} Hava"
                motor_notu = "Hava"
            except: st.session_state.bilgi = "Hava durumu verisi alınamadı."

        # 3. DERİN ARAŞTIRMA (Threading ile Paralel Çalışma)
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                f1 = executor.submit(wiki_cek, sorgu)
                f2 = executor.submit(web_ara, sorgu)
                res_wiki = f1.result()
                res_web = f2.result()
            
            st.session_state.bilgi = f"{res_web}\n\n{res_wiki}"
            st.session_state.konu = sorgu.title()
            
        # Veritabanına Kaydet
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), motor_notu))
        conn.commit()

# --- 📊 SONUÇ EKRANI ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)

    # PDF MODÜLÜ (Güvenli Filtreli)
    def indirilebilir_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        def temiz(t):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): t = t.replace(k,v)
            return re.sub(r'[^\x00-\x7F]+', '', t)

        icerik = f"KONU: {temiz(st.session_state.konu)}\n\n{temiz(st.session_state.bilgi)}"
        pdf.multi_cell(0, 10, txt=icerik.encode('latin-1', 'ignore').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')

    st.download_button("📄 Analizi PDF Yap", data=indirilebilir_pdf(), file_name="TurkAI_Rapor.pdf")
