import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Araştırma Paneli", page_icon="🏛️", layout="wide")

# --- VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_pro_v102.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- PDF SERVİSİ ---
def pdf_olustur(baslik, metin, kaynak):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        b = str(baslik).encode('latin-1', 'ignore').decode('latin-1')
        m = str(metin).encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak: {kaynak}".encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=10); pdf.cell(0, 10, k, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=11); pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- OTURUM ---
if "u" in st.query_params:
    st.session_state.user = st.query_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

if not st.session_state.user:
    st.markdown("<h2 style='text-align:center;'>TürkAI Kurumsal Erişim</h2>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Kullanıcı Kimliği")
        p = st.text_input("Güvenlik Şifresi", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            data = c.fetchone()
            if data and data[1] == h_p:
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            elif not data:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p)); conn.commit()
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            else: st.error("Hata!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.subheader(f"👤 {st.session_state.user}")
    if st.button("Güvenli Çıkış"): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    motor_secimi = st.radio("Motor Seçimi:", ["V1 (Wikipedia)", "V2 (Ansiklopedik Derinlik)"])
    st.divider()
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"[{m}] {k[:15]}...", key=f"h_{k}_{datetime.datetime.now().microsecond}"):
            st.session_state.bilgi, st.session_state.konu = i, k; st.rerun()

# --- ARAŞTIRMA ---
st.markdown("<h1 style='color: #1e3a8a;'>TürkAI Analiz Paneli</h1>", unsafe_allow_html=True)

msg = st.chat_input("Konu veya 'hesapla [işlem]' giriniz...")

if msg:
    # Kullanıcıyı taklit eden güçlü header
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    if msg.lower().startswith("hesapla"):
        try:
            res = eval(msg.lower().replace("hesapla", "").strip(), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"Sonuç: {res}", "Matematiksel Analiz"; st.rerun()
        except: st.error("Hata!")

    elif motor_secimi == "V1 (Wikipedia)":
        with st.spinner("V1 Taranıyor..."):
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json", headers=h).json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    soup = BeautifulSoup(requests.get(link, headers=h).text, 'html.parser')
                    txt = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:6])
                    st.session_state.bilgi, st.session_state.konu = txt, baslik
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), link, "V1"))
                    conn.commit(); st.rerun()
                else: st.warning("V1 sonuç bulamadı.")
            except: st.error("V1 Hatası.")

    elif motor_secimi == "V2 (Ansiklopedik Derinlik)":
        with st.spinner("V2 Derin Tarama Yapılıyor..."):
            try:
                # Daha kararlı bir API/Arama köprüsü (MediaWiki API üzerinden Vikikaynak/Vikisözlük araması)
                v2_url = f"https://tr.wiktionary.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                r = requests.get(v2_url, headers=h).json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    link = f"https://tr.wiktionary.org/wiki/{baslik.replace(' ', '_')}"
                    soup = BeautifulSoup(requests.get(link, headers=h).text, 'html.parser')
                    txt = soup.find('div', class_='mw-parser-output').get_text()[:1500] + "..."
                    st.session_state.bilgi, st.session_state.konu = txt, baslik
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), link, "V2"))
                    conn.commit(); st.rerun()
                else: st.warning("V2 sonuç bulamadı.")
            except: st.error("V2 Hatası.")

# --- RAPOR ---
if st.session_state.bilgi:
    st.divider()
    pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi, motor_secimi)
    if pdf:
        st.download_button("📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)", data=bytes(pdf), file_name="TurkAI_Rapor.pdf")
    st.subheader(st.session_state.konu)
    st.write(st.session_state.bilgi)
