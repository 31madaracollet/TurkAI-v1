import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI MOTORU (SOHBETLERİ VE HESAPLARI TUTAR) ---
def db_baslat():
    conn = sqlite3.connect('turkai_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS arsiv (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

def db_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_data.db', check_same_thread=False)
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    c.execute("INSERT INTO arsiv VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def db_gecmis_getir(user):
    conn = sqlite3.connect('turkai_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM arsiv WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

db_baslat()

# --- 📄 PDF OLUŞTURUCU ---
def pdf_yap(baslik, icerik):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=baslik.encode('latin-1', 'ignore').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    # HTML etiketlerini temizle
    temiz_metin = re.sub('<[^<]+?>', '', icerik)
    pdf.multi_cell(0, 10, txt=temiz_metin.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 SESSION STATE BAŞLATMA ---
if "user" in st.query_params: st.session_state.user = st.query_params["user"]
if "user" not in st.session_state: st.session_state.user = None
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🚪 GİRİŞ EKRANI (SADELEŞTİRİLDİ) ---
if not st.session_state.user:
    st.markdown("<h1 style='text-align: center; color: #DC2626;'>TürkAI Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Giriş Yap", use_container_width=True):
                conn = sqlite3.connect('turkai_data.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifre_hashle(p)))
                if c.fetchone():
                    st.session_state.user = u
                    st.query_params["user"] = u
                    st.rerun()
                else: st.error("Hatalı giriş!")
        with c2:
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    conn = sqlite3.connect('turkai_data.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users VALUES (?,?)", (u, sifre_hashle(p)))
                    conn.commit()
                    st.success("Kayıt başarılı! Giriş yapabilirsin.")
                except: st.error("Bu kullanıcı zaten var.")
    st.stop()

# --- 🚀 ANA PANEL (ARŞİV) ---
with st.sidebar:
    st.subheader(f"👤 {st.session_state.user}")
    if st.button("Çıkış Yap"):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş İşlemler**")
    for konu, icerik in db_gecmis_getir(st.session_state.user):
        if st.button(f"{konu[:20]}...", use_container_width=True):
            st.session_state.analiz_sonucu = icerik
            st.session_state.su_anki_konu = konu
            st.rerun()

# --- 🖥️ ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    col_metin, col_pdf = st.columns([4, 1])
    with col_metin:
        st.markdown(f"""<div style="background: #F9FAFB; padding: 20px; border-radius: 10px; border: 1px solid #DDD;">
        <h3 style="color:#DC2626;">{st.session_state.su_anki_konu}</h3>
        {st.session_state.analiz_sonucu.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)
    with col_pdf:
        st.download_button("📄 PDF İndir", data=pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu), file_name="turkai_cikti.pdf")

# --- 📥 AKILLI GİRİŞ ---
sorgu = st.chat_input("İşlem yazın (5*5) veya konu aratın...")

if sorgu:
    # 1. HESAPLAMA KONTROLÜ
    is_math = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", sorgu)
    if is_math:
        try:
            islem = is_math.group(0)
            cevap = eval(islem)
            sonuc = f"🔢 Hesaplama Sonucu\n\nİşlem: {islem}\nCevap: {cevap}"
            db_kaydet(st.session_state.user, f"Hesap: {islem}", sonuc)
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = sonuc, "Hesaplama"
            st.rerun()
        except: pass

    # 2. ARAMA KONTROLÜ
    with st.spinner("Aranıyor..."):
        r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            paragraflar = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50]
            bilgi = "\n\n".join(paragraflar[:5])
            bilgi += f"\n\n📚 Kaynak: Wikipedia - {sorgu}"
            db_kaydet(st.session_state.user, sorgu, bilgi)
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, sorgu
            st.rerun()
        else: st.error("Sonuç bulunamadı.")
