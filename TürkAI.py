import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ AYARLAR ---
st.set_page_config(page_title="TürkAI v95 - 2000 Motor", page_icon="🏎️", layout="wide")

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_v95_ultra.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
conn.commit()

# --- 📄 PDF SİSTEMİ ---
def pdf_olustur(baslik, metin, kaynak):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        b = str(baslik).encode('latin-1', 'ignore').decode('latin-1')
        m = str(metin).encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak: {kaynak}".encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=10); pdf.cell(0, 10, k, ln=True); pdf.ln(5)
        pdf.set_font("Helvetica", size=12); pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- 🔑 GİRİŞ VE HAFIZA ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "motor" not in st.session_state: st.session_state.motor = ""

if not st.session_state.user:
    st.markdown("<h1 style='text-align:center;'>🏎️ TürkAI v95 LOGIN</h1>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sistemi Ateşle", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            data = c.fetchone()
            if data and data[1] == h_p:
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            elif not data:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p)); conn.commit()
                st.session_state.user = u; st.query_params["u"] = u; st.rerun()
            else: st.error("Hatalı!")
    st.stop()

# --- 🚀 SIDEBAR ---
with st.sidebar:
    st.title(f"🏎️ {st.session_state.user}")
    if st.button("🔴 Çıkış"): 
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.subheader("🏁 Yarış Geçmişi")
    c.execute("SELECT konu, icerik, link, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, l, m in c.fetchall():
        if st.button(f"{m} | {k[:15]}...", key=f"h_{k}_{l[-5:]}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.motor = i, k, m
            st.rerun()

# --- 🏎️ ANA MOTORLAR ---
st.markdown("<h2 style='color:#b91c1c;'>TürkAI 2000 Motor Bilgi Üssü</h2>", unsafe_allow_html=True)

msg = st.chat_input("Aranacak konu veya 'hesapla ...' yazın")

if msg:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
    
    # 🔢 MOTOR 1: HESAPLAYICI
    if msg.lower().startswith("hesapla"):
        try:
            res = eval(msg.lower().replace("hesapla", "").strip(), {"__builtins__": {}}, {})
            st.session_state.bilgi = f"🔢 Hesaplama Sonucu: {res}"
            st.session_state.konu = "Matematik Motoru"; st.session_state.motor = "HESAP"; st.rerun()
        except: st.error("Hatalı işlem!")

    # 🌍 MOTOR 2 & 3: BİLGİ ARAŞTIRMA
    else:
        col_w, col_e = st.columns(2)
        
        with st.spinner("Motorlar ısınıyor..."):
            # --- WIKIPEDIA ---
            try:
                w_api = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                w_data = requests.get(w_api, headers=headers).json()
                if w_data['query']['search']:
                    w_baslik = w_data['query']['search'][0]['title']
                    w_link = f"https://tr.wikipedia.org/wiki/{w_baslik.replace(' ', '_')}"
                    w_page = requests.get(w_link, headers=headers)
                    w_soup = BeautifulSoup(w_page.text, 'html.parser')
                    w_text = "\n\n".join([p.get_text() for p in w_soup.find_all('p') if len(p.get_text()) > 50][:4])
                else: w_text = None
            except: w_text = None

            # --- EKŞİ SÖZLÜK (Alternatif Motor) ---
            try:
                e_link = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={msg}"
                e_page = requests.get(e_link, headers=headers)
                e_soup = BeautifulSoup(e_page.text, 'html.parser')
                e_entry = e_soup.find('div', class_='content').get_text(separator='\n') if e_soup.find('div', class_='content') else "Sonuç bulunamadı."
                e_text = e_entry[:1000] + "..."
            except: e_text = "Sosyal motor şu an meşgul."

            # OTOMATİK KARAR VER VE KAYDET
            if w_text:
                st.session_state.bilgi, st.session_state.konu, st.session_state.motor = w_text, w_baslik, "WIKI"
                c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, w_baslik, w_text, str(datetime.datetime.now()), w_link, "WIKI"))
                conn.commit(); st.rerun()
            elif e_text:
                st.session_state.bilgi, st.session_state.konu, st.session_state.motor = e_text, msg, "EKŞİ"
                c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?,?)", (st.session_state.user, msg, e_text, str(datetime.datetime.now()), "Ekşi Sözlük", "EKŞİ"))
                conn.commit(); st.rerun()

# --- 🏁 SONUÇ EKRANI ---
if st.session_state.bilgi:
    st.divider()
    
    # PDF Butonu (En üstte)
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.motor)
    if pdf_byt:
        st.download_button("📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)", data=bytes(pdf_byt), file_name="turkai_rapor.pdf")

    # Çift Panel Görünümü
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader(f"[{st.session_state.motor}] {st.session_state.konu}")
        st.write(st.session_state.bilgi)
    with c2:
        st.metric("Motor Gücü", "2000 HP")
        st.metric("Durum", "Aktif")
