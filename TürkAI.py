import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🏛️", layout="wide")

# --- VERİTABANI YÖNETİMİ ---
def get_db(): 
    return sqlite3.connect('turkai_pro_v105.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- PDF RAPORLAMA ---
def pdf_olustur(baslik, metin, motor_adi):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        b = str(baslik).encode('latin-1', 'ignore').decode('latin-1')
        m = str(metin).encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak Motor: {motor_adi}".encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.cell(0, 10, b, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=10); pdf.cell(0, 10, k, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=11); pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- OTURUM VE GİRİŞ ---
if "u" in st.query_params:
    st.session_state.user = st.query_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "motor" not in st.session_state: st.session_state.motor = ""

if not st.session_state.user:
    st.markdown("<h2 style='text-align:center;'>TürkAI Kurumsal Erişim</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Kullanıcı Kimliği")
        p = st.text_input("Şifre", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            data = c.fetchone()
            if data and data[1] == h_p:
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            elif not data:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p)); conn.commit()
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            else: st.error("Erişim reddedildi.")
    st.stop()

# --- YAN PANEL (KONTROL & GEÇMİŞ) ---
with st.sidebar:
    st.subheader(f"👤 Kimlik: {st.session_state.user}")
    if st.button("Güvenli Çıkış", use_container_width=True): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    
    st.divider()
    st.subheader("⚙️ Motor Seçimi")
    aktif_motor = st.radio(
        "Aktif Analiz Motoru:",
        ["V1 (Wikipedia)", "V2 (Sözlük/Teknik)", "V3 (Hesap Makinesi)"],
        index=0
    )
    
    st.divider()
    st.subheader("📂 Sorgu Geçmişi")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"[{m}] {k[:18]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = i, k, m
            st.rerun()

# --- ANA ARAŞTIRMA VE ANALİZ MODÜLÜ ---
st.markdown("<h1 style='color: #1e3a8a;'>TürkAI Profesyonel Terminal</h1>", unsafe_allow_html=True)

sorgu = st.chat_input("Veri girişi yapın...")

if sorgu:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    
    # --- V3: HESAP MAKİNESİ MOTORU ---
    if aktif_motor == "V3 (Hesap Makinesi)":
        try:
            # Sadece matematiksel ifadeyi temizle ve hesapla
            islem = sorgu.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            cikti = f"Matematiksel Analiz Sonucu:\nİşlem: {islem}\nSonuç: {sonuc}"
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = cikti, "Matematiksel İşlem", "V3"
            
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, "Matematiksel İşlem", cikti, str(datetime.datetime.now()), "Dahili Modül", "V3"))
            conn.commit(); st.rerun()
        except: st.error("V3: Hatalı matematiksel sözdizimi.")

    # --- V1: WIKIPEDIA MOTORU ---
    elif aktif_motor == "V1 (Wikipedia)":
        with st.spinner("V1 Veri Çekiliyor..."):
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    soup = BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser')
                    icerik = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:6])
                    st.session_state.bilgi, st.session_state.konu, st.session_state.motor = icerik, baslik, "V1"
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, icerik, str(datetime.datetime.now()), link, "V1"))
                    conn.commit(); st.rerun()
                else: st.warning("V1: Kayıt bulunamadı.")
            except: st.error("V1 Bağlantı Hatası.")

    # --- V2: SÖZLÜK / TEKNİK MOTOR ---
    elif aktif_motor == "V2 (Sözlük/Teknik)":
        with st.spinner("V2 Teknik Analiz Yapılıyor..."):
            try:
                v2_url = f"https://tr.wiktionary.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json"
                r = requests.get(v2_url, headers=headers).json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    link = f"https://tr.wiktionary.org/wiki/{baslik.replace(' ', '_')}"
                    soup = BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser')
                    icerik = soup.find('div', class_='mw-parser-output').get_text()[:1500] + "..."
                    st.session_state.bilgi, st.session_state.konu, st.session_state.motor = icerik, baslik, "V2"
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, icerik, str(datetime.datetime.now()), link, "V2"))
                    conn.commit(); st.rerun()
                else: st.warning("V2: Teknik veri bulunamadı.")
            except: st.error("V2 Bağlantı Hatası.")

# --- RAPORLAMA VE ÇIKTI ---
if st.session_state.bilgi:
    st.divider()
    
    # PDF RAPOR BUTONU
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.motor)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"TurkAI_{st.session_state.motor}_Rapor.pdf",
            mime="application/pdf"
        )
    
    st.subheader(f"🔍 [{st.session_state.motor}] {st.session_state.konu}")
    st.write(st.session_state.bilgi)
