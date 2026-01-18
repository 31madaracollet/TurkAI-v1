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
    /* Tüm Butonlar Kırmızı */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
    }
    /* Giriş Kartı */
    .giris-kutu {
        border: 2px solid #cc0000;
        padding: 25px;
        border-radius: 15px;
        background-color: #fffafa;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_master_final.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- 📄 PDF ---
def pdf_olustur(baslik, metin, motor):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, str(baslik).encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, str(metin).encode('latin-1', 'ignore').decode('latin-1'))
        return pdf.output()
    except: return None

# --- 🔑 GİRİŞ & KAYDOL SİSTEMİ ---
if "u" in st.query_params: st.session_state.user = st.query_params["u"]
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<div class='giris-kutu'><h1>🇹🇷 TürkAI</h1><p>Kurumsal Analiz Terminali</p></div>", unsafe_allow_html=True)
        mod = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        
        if st.button("Sistemi Başlat"):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            if mod == "Giriş Yap":
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h_p))
                if c.fetchone():
                    st.session_state.user = u
                    st.query_params["u"] = u
                    st.rerun()
                else: st.error("Hatalı kullanıcı adı veya şifre!")
            else:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (u, h_p))
                    conn.commit()
                    st.session_state.user = u
                    st.query_params["u"] = u
                    st.success("Kayıt başarılı! Giriş yapılıyor...")
                    st.rerun()
                except: st.error("Bu kullanıcı adı zaten mevcut!")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    if st.button("🔴 Güvenli Çıkış"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    motor = st.radio("Analiz Motoru:", ["V1 (Wikipedia)", "V2 (Sözlük/Teknik)", "V3 (Hesap Makinesi)"])
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"📌 [{m}] {k[:15]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = i, k, m
            st.rerun()

# --- 💻 MOTORLARIN ÇALIŞMASI ---
st.markdown("<h2 style='border-bottom: 2px solid #cc0000;'>TürkAI Analiz Terminali</h2>", unsafe_allow_html=True)
sorgu = st.chat_input("Sorgu giriniz...")

if sorgu:
    h = {'User-Agent': 'Mozilla/5.0'}
    if motor == "V3 (Hesap Makinesi)":
        try:
            res = eval(sorgu.lower().replace("hesapla","").strip(), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = f"Sonuç: {res}", "Matematiksel İşlem", "V3"
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, "Matematiksel İşlem", f"Sonuç: {res}", str(datetime.datetime.now()), "Dahili", "V3"))
            conn.commit(); st.rerun()
        except: st.error("Matematiksel hata!")
    elif motor == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=h).json()
            baslik = r['query']['search'][0]['title']
            link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
            soup = BeautifulSoup(requests.get(link, headers=h).text, 'html.parser')
            txt = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = txt, baslik, "V1"
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), link, "V1"))
            conn.commit(); st.rerun()
        except: st.error("V1 Hatası!")
    elif motor == "V2 (Sözlük/Teknik)":
        try:
            r = requests.get(f"https://tr.wiktionary.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=h).json()
            baslik = r['query']['search'][0]['title']
            soup = BeautifulSoup(requests.get(f"https://tr.wiktionary.org/wiki/{baslik.replace(' ', '_')}", headers=h).text, 'html.parser')
            txt = soup.find('div', class_='mw-parser-output').get_text()[:1200]
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = txt, baslik, "V2"
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), "V2", "V2"))
            conn.commit(); st.rerun()
        except: st.error("V2 Hatası!")

# --- 📊 SONUÇ ---
if st.session_state.bilgi:
    st.divider()
    pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.motor)
    if pdf: st.download_button("📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)", data=bytes(pdf), file_name="TurkAI_Rapor.pdf")
    st.subheader(st.session_state.konu)
    st.write(st.session_state.bilgi)
