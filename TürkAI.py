import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 AL-YILDIZ TEMASI ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
    }
    .giris-kutu { border: 2px solid #cc0000; padding: 25px; border-radius: 15px; background-color: #fffafa; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI TAMİR VE BAĞLANTI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v115_final.db', check_same_thread=False)
    c = conn.cursor()
    # Tabloları oluştur
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    
    # EKSİK SÜTUNLARI KONTROL ET VE EKLE (Hata Önleyici)
    try:
        c.execute('ALTER TABLE aramalar ADD COLUMN link TEXT')
    except: pass
    try:
        c.execute('ALTER TABLE aramalar ADD COLUMN motor TEXT')
    except: pass
    
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 📄 PDF ---
def pdf_olustur(baslik, metin):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, str(baslik).encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, str(metin).encode('latin-1', 'ignore').decode('latin-1'))
        return pdf.output()
    except: return None

# --- 🔑 GİRİŞ SİSTEMİ ---
if "u" in st.query_params: st.session_state.user = st.query_params["u"]
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.markdown("<div class='giris-kutu'><h1>🇹🇷 TürkAI</h1><p>Giriş Paneli</p></div>", unsafe_allow_html=True)
        mod = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
        u_input = st.text_input("Kullanıcı Adı")
        p_input = st.text_input("Şifre", type="password")
        
        if st.button("Sistemi Başlat"):
            h_p = hashlib.sha256(p_input.encode()).hexdigest()
            if mod == "Giriş Yap":
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_input, h_p))
                if c.fetchone():
                    st.session_state.user = u_input
                    st.query_params["u"] = u_input
                    st.rerun()
                else: st.error("Hatalı bilgiler!")
            else:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (u_input, h_p))
                    conn.commit()
                    st.session_state.user = u_input
                    st.query_params["u"] = u_input
                    st.rerun()
                except: st.error("Kullanıcı zaten mevcut!")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    if st.button("🔴 Çıkış"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Analiz Motoru:", ["V1 (Wikipedia)", "V2 (Sözlük/Teknik)", "V3 (Hesap Makinesi)"])
    st.divider()
    st.subheader("📂 Geçmiş")
    # Hata veren sorgu burasıydı, şimdi düzeldi:
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"📌 [{m}] {k[:15]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = i, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("<h2 style='border-bottom: 2px solid #cc0000;'>TürkAI Araştırma Paneli</h2>", unsafe_allow_html=True)
sorgu = st.chat_input("Sorgunuzu buraya yazın...")

if sorgu:
    headers = {'User-Agent': 'Mozilla/5.0'}
    if m_secim == "V3 (Hesap Makinesi)":
        try:
            res = eval(sorgu.lower().replace("hesapla","").strip(), {"__builtins__": {}}, {})
            info, head = f"Sonuç: {res}", "Matematiksel İşlem"
            c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih, motor) VALUES (?,?,?,?,?)", (st.session_state.user, head, info, str(datetime.datetime.now()), "V3"))
            conn.commit(); st.session_state.bilgi, st.session_state.konu = info, head; st.rerun()
        except: st.error("Matematik hatası!")
    
    elif m_secim == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
            head = r['query']['search'][0]['title']
            link = f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}"
            soup = BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser')
            info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
            c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih, motor, link) VALUES (?,?,?,?,?,?)", (st.session_state.user, head, info, str(datetime.datetime.now()), "V1", link))
            conn.commit(); st.session_state.bilgi, st.session_state.konu = info, head; st.rerun()
        except: st.error("V1 verisi alınamadı.")

# --- 📊 ÇIKTI ---
if st.session_state.bilgi:
    st.divider()
    pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
    if pdf: st.download_button("📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)", data=bytes(pdf), file_name="TurkAI_Rapor.pdf")
    st.subheader(st.session_state.konu)
    st.write(st.session_state.bilgi)

