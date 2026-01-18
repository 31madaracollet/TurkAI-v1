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
    return sqlite3.connect('turkai_v100_pro.db', check_same_thread=False)

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
        b = str(baslik).encode('latin-1', 'ignore').decode('latin-1')
        m = str(metin).encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak Tipi: {kaynak_tipi}".encode('latin-1', 'ignore').decode('latin-1')
        
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
if "aktif_motor" not in st.session_state: st.session_state.aktif_motor = "V1 (Wikipedia)"

if not st.session_state.user:
    st.markdown("<h2 style='text-align:center;'>TürkAI Kurumsal Erişim</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
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
            else: st.error("Kimlik doğrulama başarısız.")
    st.stop()

# --- YAN PANEL (KONTROL MERKEZİ) ---
with st.sidebar:
    st.subheader(f"👤 Oturum: {st.session_state.user}")
    if st.button("Güvenli Çıkış", use_container_width=True): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    
    st.divider()
    # MOTOR SEÇİMİ (V1 VE V2)
    st.subheader("⚙️ Motor Seçimi")
    st.session_state.aktif_motor = st.radio(
        "Veri Kaynağını Belirleyin:",
        ["V1 (Wikipedia)", "V2 (Ekşi Sözlük)"],
        help="V1 Akademik, V2 Toplumsal perspektif sunar."
    )
    
    st.divider()
    st.subheader("📂 Sorgu Geçmişi")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"[{m}] {k[:18]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = i, k
            st.rerun()

# --- ANA ARAŞTIRMA MODÜLÜ ---
st.markdown("<h1 style='color: #1e3a8a;'>TürkAI Araştırma Paneli v100</h1>", unsafe_allow_html=True)

# HESAPLAMA NOTU
st.caption("Matematiksel işlemler için sorgu başına 'hesapla' ekleyiniz. Örn: hesapla (250*4)/2")

sorgu = st.chat_input("Araştırmak istediğiniz konuyu giriniz...")

if sorgu:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    # MATEMATİKSEL MOTOR
    if sorgu.lower().startswith("hesapla"):
        try:
            islem = sorgu.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"Matematiksel Analiz Sonucu:\nİşlem: {islem}\nSonuç: {sonuc}"
            st.session_state.konu = "Matematiksel Analiz"
            st.rerun()
        except: st.error("Geçersiz matematiksel ifade.")

    # V1: WIKIPEDIA MOTORU
    elif st.session_state.aktif_motor == "V1 (Wikipedia)":
        with st.spinner("V1 Akademik Motor Taraması Yapılıyor..."):
            try:
                w_api = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json"
                w_res = requests.get(w_api, headers=headers).json()
                if w_res['query']['search']:
                    baslik = w_res['query']['search'][0]['title']
                    link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    p_res = requests.get(link, headers=headers)
                    soup = BeautifulSoup(p_res.text, 'html.parser')
                    paragraflar = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    icerik = "\n\n".join(paragraflar[:6])
                    
                    st.session_state.bilgi, st.session_state.konu = icerik, baslik
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, baslik, icerik, str(datetime.datetime.now()), link, "V1"))
                    conn.commit(); st.rerun()
                else: st.warning("İlgili kayıt bulunamadı.")
            except: st.error("V1 Motoru bağlantı hatası.")

    # V2: EKŞİ SÖZLÜK MOTORU
    elif st.session_state.aktif_motor == "V2 (Ekşi Sözlük)":
        with st.spinner("V2 Toplumsal Bellek Taraması Yapılıyor..."):
            try:
                # Ciddi bir arama yapısı
                search_url = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={sorgu}"
                e_res = requests.get(search_url, headers=headers)
                soup = BeautifulSoup(e_res.text, 'html.parser')
                entry = soup.find('div', class_='content')
                if entry:
                    icerik = entry.get_text(separator='\n').strip()
                    st.session_state.bilgi, st.session_state.konu = icerik, sorgu
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, sorgu, icerik, str(datetime.datetime.now()), search_url, "V2"))
                    conn.commit(); st.rerun()
                else: st.warning("V2 motorunda veri bulunamadı.")
            except: st.error("V2 Motoru erişim hatası.")

# --- SONUÇ VE RAPORLAMA ---
if st.session_state.bilgi:
    st.divider()
    
    # RAPORLAMA BUTONU
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.aktif_motor)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"TurkAI_Rapor_{st.session_state.konu}.pdf",
            mime="application/pdf"
        )

    st.subheader(f"Analiz Konusu: {st.session_state.konu}")
    st.write(st.session_state.bilgi)
    
    # ATIF PANELİ
    if st.session_state.aktif_motor == "V1 (Wikipedia)":
        st.caption(f"Veri Kaynağı: Wikipedia (Resmi/Akademik)")
    elif st.session_state.aktif_motor == "V2 (Ekşi Sözlük)":
        st.caption(f"Veri Kaynağı: Toplumsal Veri Tabanı (V2)")
