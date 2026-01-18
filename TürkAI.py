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

# --- 🍪 ÇEREZ YÖNETİMİ (HATA DÜZELTİLDİ) ---
# Burada @st.cache_resource kullanmıyoruz, çünkü CookieManager bir bileşendir.
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

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        safe_baslik = baslik.encode('latin-1', 'ignore').decode('latin-1')
        safe_icerik = icerik.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, safe_baslik, ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, safe_icerik)
        return pdf.output()
    except:
        return None

# --- 🔑 OTURUM YÖNETİMİ ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
    st.session_state.user = ""

# Sayfa her yüklendiğinde çerezi kontrol et
val = cookie_manager.get(cookie="turkai_user")
if val and not st.session_state.giris_yapildi:
    st.session_state.user = val
    st.session_state.giris_yapildi = True

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; margin-bottom:10px; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.4rem; font-weight:bold; }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ VE KAYIT EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v80.3</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol", use_container_width=True):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                except: st.error("Bu isim alınmış!")
                conn.close()
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sistemi Başlat", use_container_width=True):
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
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""; st.rerun()
    if st.button("🔴 Çıkış", use_container_width=True):
        cookie_manager.delete("turkai_user")
        st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for konu, icerik, tarih in c.fetchall():
        if st.button(f"📌 {konu[:15]}...", key=f"h_{tarih}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = konu, icerik
            st.rerun()
    conn.close()

# --- 💻 ANA EKRAN ---
st.markdown("<h2 class='header'>TürkAI Bilgi Sistemi</h2>", unsafe_allow_html=True)

if st.session_state.get("analiz_sonucu"):
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        # PDF OLUŞTUR VE İNDİR
        pdf_cikti = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        if pdf_cikti:
            st.download_button(
                label="📥 Bu Bilgiyi PDF Olarak İndir",
                data=pdf_cikti,
                file_name=f"{st.session_state.su_anki_konu}.pdf",
                mime="application/pdf"
            )

# --- 📥 GİRİŞ MOTORU ---
msg = st.chat_input("Bir konu yazın veya hesap yapın...")

if msg:
    math_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
    if math_match:
        try:
            islem = math_match.group(0).replace('x', '*')
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.analiz_sonucu = f"🔢 Matematiksel Sonuç\n\n✅ Cevap: {sonuc}"
            st.session_state.su_anki_konu = "Hesaplama"; st.rerun()
        except: pass

    with st.spinner("🔎 TürkAI Araştırıyor..."):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            s_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
            r = requests.get(s_url, headers=h).json()
            if r.get('query', {}).get('search'):
                baslik = r['query']['search'][0]['title']
                wiki_res = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", headers=h)
                soup = BeautifulSoup(wiki_res.text, 'html.parser')
                for j in soup(["sup", "table", "style", "script"]): j.decompose()
                txt = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if txt:
                    bilgi = "\n\n".join(txt[:6])
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, str(datetime.datetime.now())))
                    conn.commit(); conn.close()
                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                    st.rerun()
        except: st.error("Wikipedia'ya ulaşılamadı!")
