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

# --- VERİTABANI YÖNETİMİ ---
def get_db(): 
    return sqlite3.connect('turkai_pro_v101.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- DÖKÜMANTASYON SERVİSİ (PDF) ---
def pdf_olustur(baslik, metin, kaynak_tipi):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        # Karakter kodlama temizliği
        b = str(baslik).encode('latin-1', 'ignore').decode('latin-1')
        m = str(metin).encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak: {kaynak_tipi}".encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=10); pdf.cell(0, 10, k, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=11); pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- OTURUM VE GÜVENLİK ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

if not st.session_state.user:
    st.markdown("<h2 style='text-align:center;'>TürkAI Kurumsal Erişim</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u = st.text_input("Kullanıcı Kimliği")
        p = st.text_input("Güvenlik Şifresi", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            data = c.fetchone()
            if data and data[1] == h_p:
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            elif not data:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p)); conn.commit()
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            else: st.error("Hatalı kimlik bilgileri.")
    st.stop()

# --- YAN PANEL ---
with st.sidebar:
    st.subheader(f"👤 Oturum: {st.session_state.user}")
    if st.button("Güvenli Çıkış", use_container_width=True): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    
    st.divider()
    st.subheader("⚙️ Motor Seçimi")
    motor_secimi = st.radio(
        "Veri Kaynağını Belirleyin:",
        ["V1 (Wikipedia)", "V2 (Global Bilgi Arşivi)"],
        index=0
    )
    
    st.divider()
    st.subheader("📂 Sorgu Geçmişi")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"[{m}] {k[:18]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = i, k
            st.rerun()

# --- ANA ARAŞTIRMA MODÜLÜ ---
st.markdown("<h1 style='color: #1e3a8a;'>TürkAI Araştırma Paneli v101</h1>", unsafe_allow_html=True)
st.caption("Matematiksel analizler için sorgu başına 'hesapla' ekleyiniz.")

sorgu = st.chat_input("Araştırma konusu veya matematiksel işlem giriniz...")

if sorgu:
    # Profesyonel User-Agent (Normal Kullanıcı Taklidi)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    if sorgu.lower().startswith("hesapla"):
        try:
            islem = sorgu.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"Analiz Sonucu: {sonuc}"
            st.session_state.konu = "Matematiksel Analiz"
            st.rerun()
        except: st.error("İşlem hatası.")

    elif motor_secimi == "V1 (Wikipedia)":
        with st.spinner("V1 Akademik Veri Tabanı Taranıyor..."):
            try:
                w_api = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json"
                w_res = requests.get(w_api, headers=headers).json()
                if w_res['query']['search']:
                    baslik = w_res['query']['search'][0]['title']
                    link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    p_res = requests.get(link, headers=headers)
                    soup = BeautifulSoup(p_res.text, 'html.parser')
                    icerik = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:6])
                    st.session_state.bilgi, st.session_state.konu = icerik, baslik
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, icerik, str(datetime.datetime.now()), link, "V1"))
                    conn.commit(); st.rerun()
                else: st.warning("V1 motorunda kayıt bulunamadı.")
            except: st.error("V1 Motoru erişim hatası.")

    elif motor_secimi == "V2 (Global Bilgi Arşivi)":
        with st.spinner("V2 Küresel Veri Motoru Hazırlanıyor..."):
            try:
                # DuckDuckGo HTML üzerinden temiz veri çekme (Normal kullanıcı taklidi ile)
                v2_url = f"https://html.duckduckgo.com/html/?q={sorgu}+nedir+bilgi"
                v2_res = requests.get(v2_url, headers=headers)
                soup = BeautifulSoup(v2_res.text, 'html.parser')
                sonuclar = soup.find_all('a', class_='result__a')
                
                if sonuclar:
                    en_iyi_link = sonuclar[0]['href']
                    # İlk sonucun özetini alalım
                    snippet = soup.find('a', class_='result__snippet').get_text() if soup.find('a', class_='result__snippet') else "Detaylı bilgi için kaynağı ziyaret edin."
                    
                    st.session_state.bilgi, st.session_state.konu = snippet, sorgu
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, sorgu, snippet, str(datetime.datetime.now()), en_iyi_link, "V2"))
                    conn.commit(); st.rerun()
                else: st.warning("V2 motoru sonuç döndüremedi.")
            except: st.error("V2 Motoru teknik bir sorunla karşılaştı.")

# --- SONUÇ PANELİ ---
if st.session_state.bilgi:
    st.divider()
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, motor_secimi)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"TurkAI_Rapor_{st.session_state.konu}.pdf",
            mime="application/pdf"
        )
    st.subheader(f"Analiz Çıktısı: {st.session_state.konu}")
    st.write(st.session_state.bilgi)
