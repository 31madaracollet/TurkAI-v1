import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF
import extra_streamlit_components as stx

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🍪 ÇEREZ YÖNETİMİ ---
cookie_manager = stx.CookieManager()

def sifrele(sifre): 
    return hashlib.sha256(str.encode(sifre)).hexdigest()

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_v80.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF OLUŞTURUCU (YENİLENMİŞ) ---
def pdf_olustur(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        # Karakter temizliği
        b = baslik.encode('latin-1', 'ignore').decode('latin-1')
        i = icerik.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, i)
        return pdf.output()
    except:
        return None

# --- 🔑 OTURUM KONTROLÜ ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
    st.session_state.user = ""

val = cookie_manager.get(cookie="turkai_user")
if val and not st.session_state.giris_yapildi:
    st.session_state.user = val
    st.session_state.giris_yapildi = True

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; margin-bottom:5px; }
    /* İndirme Butonu Stili */
    div.stDownloadButton > button {
        background-color: #22c55e !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        width: 100% !important;
        height: 50px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v80.5</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol"):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt ok! Giriş yap.")
                except: st.error("İsim dolu!")
                conn.close()
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sistemi Başlat"):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                cookie_manager.set("turkai_user", u, expires_at=datetime.datetime.now() + datetime.timedelta(days=7))
                st.session_state.giris_yapildi, st.session_state.user = True, u
                st.rerun()
            else: st.error("Hatalı!")
            conn.close()
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("➕ Yeni Sohbet"):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""; st.rerun()
    if st.button("🔴 Çıkış"):
        cookie_manager.delete("turkai_user")
        st.session_state.clear(); st.rerun()

# --- 💻 ANA EKRAN ---
st.markdown("<h2 class='header'>TürkAI Bilgi Sistemi</h2>", unsafe_allow_html=True)

# Eğer bir sonuç varsa, PDF butonunu en başa koyalım ki göründüğünden emin olalım
if st.session_state.get("analiz_sonucu"):
    if "🔢" not in st.session_state.analiz_sonucu:
        # PDF Dosyasını hazırla
        pdf_data = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        if pdf_data:
            st.download_button(
                label="📥 BİLGİYİ PDF OLARAK İNDİR (TIKLA)",
                data=bytes(pdf_data),
                file_name=f"{st.session_state.su_anki_konu}.pdf",
                mime="application/pdf",
                key="pdf_button_fixed"
            )
        
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sonuc-karti" style="background:#f0fdf4; border:2px solid #22c55e; text-align:center; font-weight:bold;">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)

# --- 📥 GİRİŞ MOTORU ---
msg = st.chat_input("Bir konu yazın...")

if msg:
    # Matematik
    m_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
    if m_match:
        try:
            res = eval(m_match.group(0).replace('x', '*'), {"__builtins__": {}}, {})
            st.session_state.analiz_sonucu = f"🔢 Sonuç: {res}"
            st.session_state.su_anki_konu = "Hesaplama"; st.rerun()
        except: pass

    # Wiki
    with st.spinner("🔎 TürkAI Araştırıyor..."):
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
        except: st.error("Bağlantı hatası!")
