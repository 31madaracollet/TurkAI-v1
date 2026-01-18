import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ AYARLAR & TEMA ---
st.set_page_config(page_title="TürkAI v90", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_master_v90.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT)')
conn.commit()

# --- 📄 PDF SİSTEMİ ---
def pdf_olustur(baslik, metin, kaynak):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        b = baslik.encode('latin-1', 'ignore').decode('latin-1')
        m = metin.encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak: {kaynak}".encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, k, ln=True) # PDF'e kaynak atfı ekledik
        pdf.ln(5)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- 🔑 HAFIZALI GİRİŞ SİSTEMİ ---
# Linkten kullanıcıyı hatırla (Sayfa yenilense de gitmez)
url_params = st.query_params
if "u" in url_params and "user" not in st.session_state:
    st.session_state.user = url_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "kaynak_link" not in st.session_state: st.session_state.kaynak_link = ""

if not st.session_state.user:
    st.markdown("<h1 style='text-align: center; color: #b91c1c;'>🇹🇷 TürkAI Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            user_data = c.fetchone()
            if user_data:
                if user_data[1] == h_p:
                    st.session_state.user = u
                    st.query_params["u"] = u # URL'ye kaydet
                    st.rerun()
                else: st.error("Hatalı şifre!")
            else:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p))
                conn.commit()
                st.session_state.user = u
                st.query_params["u"] = u # URL'ye kaydet
                st.rerun()
    st.stop()

# --- 🚀 YAN PANEL (GEÇMİŞ) ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, **{st.session_state.user}**")
    if st.button("🔴 Oturumu Kapat", use_container_width=True):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()
    st.divider()
    st.subheader("📂 Son Aramaların")
    c.execute("SELECT konu, icerik, link FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, l in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"hist_{k}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.kaynak_link = i, k, l
            st.rerun()

# --- 💻 ANA EKRAN ---
st.markdown("<h2 style='color: #b91c1c;'>TürkAI Araştırma Paneli</h2>", unsafe_allow_html=True)
st.info("💡 **Hesap Makinesi:** Başına **'hesapla'** yazın (Örn: hesapla 15*4). Çarpma için `*` kullanın.")

msg = st.chat_input("Bir konu yazın veya hesaplama yapın...")

if msg:
    # 1. HESAP MAKİNESİ
    if msg.lower().startswith("hesapla"):
        try:
            islem = msg.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"🔢 İşlem: {islem}\n✅ Sonuç: {sonuc}"
            st.session_state.konu = "Hesaplama"
            st.session_state.kaynak_link = "TürkAI Matematik Motoru"
            st.rerun()
        except: st.error("Geçersiz işlem!")
    
    # 2. WIKIPEDIA (ATIFLI)
    else:
        with st.spinner("Wikipedia taranıyor..."):
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json").json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    wiki_link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    w = requests.get(wiki_link)
                    soup = BeautifulSoup(w.text, 'html.parser')
                    txt = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:5])
                    
                    st.session_state.bilgi, st.session_state.konu = txt, baslik
                    st.session_state.kaynak_link = wiki_link
                    
                    # Kayıt (Bug önleyici)
                    c.execute("SELECT * FROM aramalar WHERE kullanici=? AND konu=?", (st.session_state.user, baslik))
                    if not c.fetchone():
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), wiki_link))
                        conn.commit()
                    st.rerun()
                else: st.warning("Sonuç bulunamadı.")
            except: st.error("Bağlantı hatası!")

# --- 📊 SONUÇ GÖSTERİMİ ---
if st.session_state.bilgi:
    st.markdown("---")
    
    # PDF Butonu
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.kaynak_link)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"{st.session_state.konu}.pdf",
            mime="application/pdf"
        )
    
    # Ekranda Atıflı Gösterim
    st.subheader(f"🔍 {st.session_state.konu}")
    st.write(st.session_state.bilgi)
    if "http" in st.session_state.kaynak_link:
        st.markdown(f"📍 **Atıf:** Bu bilgiler [Wikipedia ({st.session_state.konu})]({st.session_state.kaynak_link}) üzerinden alınmıştır.")
    else:
        st.caption(f"📍 {st.session_state.kaynak_link}")
