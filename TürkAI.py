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

def sifrele(sifre): 
    return hashlib.sha256(str.encode(sifre)).hexdigest()

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_master_v81.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        b = baslik.encode('latin-1', 'ignore').decode('latin-1')
        i = icerik.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, i)
        return pdf.output()
    except:
        return None

# --- 🔑 OTURUM YÖNETİMİ (YENİ SİSTEM) ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
    st.session_state.user = ""

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; margin-bottom:10px; }
    /* İndirme Butonunu Parlat */
    .stDownloadButton button {
        background-color: #22c55e !important;
        color: white !important;
        font-size: 20px !important;
        height: 60px !important;
        width: 100% !important;
        border: 2px solid #16a34a !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v81.0</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol ve Başlat"):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt Başarılı!")
                except: st.error("Bu isim dolu!")
                conn.close()
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sistemi Aç"):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                st.session_state.giris_yapildi, st.session_state.user = True, u
                st.rerun()
            else: st.error("Hatalı Giriş!")
            conn.close()
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""; st.rerun()
    
    # PDF Butonu (Yedek - Sidebar'da her zaman gözükür)
    if st.session_state.get("analiz_sonucu") and "🔢" not in st.session_state.analiz_sonucu:
        st.divider()
        st.write("📂 **Dosya İşlemleri**")
        pdf_data_side = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        if pdf_data_side:
            st.download_button("📥 PDF İNDİR", data=bytes(pdf_data_side), file_name="turkai_rapor.pdf", key="side_pdf")

    if st.button("🔴 Çıkış", use_container_width=True):
        st.session_state.clear(); st.rerun()

# --- 💻 ANA EKRAN ---
st.markdown("<h2 class='header'>TürkAI Araştırma Sistemi</h2>", unsafe_allow_html=True)

if st.session_state.get("analiz_sonucu"):
    if "🔢" in st.session_state.analiz_sonucu:
        st.success(st.session_state.analiz_sonucu)
    else:
        # ANA PDF BUTONU (Cevabın hemen üstünde)
        pdf_data_main = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        if pdf_data_main:
            st.download_button(
                label="📥 BİLGİYİ PDF OLARAK TELEFONA İNDİR",
                data=bytes(pdf_data_main),
                file_name=f"{st.session_state.su_anki_konu}.pdf",
                mime="application/pdf",
                key="main_pdf_btn"
            )
        
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

# --- 📥 GİRİŞ MOTORU ---
msg = st.chat_input("Bir konu yazın...")

if msg:
    m_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
    if m_match:
        try:
            res = eval(m_match.group(0).replace('x', '*'), {"__builtins__": {}}, {})
            st.session_state.analiz_sonucu = f"🔢 Sonuç: {res}"
            st.session_state.su_anki_konu = "Hesaplama"; st.rerun()
        except: pass

    with st.spinner("🔎 TürkAI Wikipedia'yı Tarıyor..."):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            api = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
            r = requests.get(api, headers=h).json()
            if r.get('query', {}).get('search'):
                baslik = r['query']['search'][0]['title']
                w_res = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", headers=h)
                soup = BeautifulSoup(w_res.text, 'html.parser')
                for j in soup(["sup", "table", "style", "script"]): j.decompose()
                txt = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if txt:
                    bilgi = "\n\n".join(txt[:6])
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, str(datetime.datetime.now())))
                    conn.commit(); conn.close()
                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                    st.rerun()
        except: st.error("Bağlantı kesildi!")
