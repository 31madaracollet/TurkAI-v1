import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
import time

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔗 MOBİL UYGULAMA LİNKİ ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 TASARIM (CİDDİ & LÜKS - BOZULMADI) ---
st.markdown("""
    <style>
    :root {
        --primary-color: #800000;
        --accent-color: #D4AF37;
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
        --text-light: #E0E0E0;
    }
    
    .stApp { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: var(--primary-color) !important; font-weight: 700 !important; }
    h1 { border-bottom: 2px solid var(--accent-color); padding-bottom: 10px; }

    /* NOT RENGİ DÜZELTMESİ */
    .warning-note {
        background-color: rgba(255, 193, 7, 0.15);
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 20px;
        font-size: 1rem;
        color: black; /* Aydınlık modda siyah */
    }

    @media (prefers-color-scheme: dark) {
        .warning-note { color: white !important; } /* Karanlık modda beyaz */
    }

    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: 1px solid var(--accent-color) !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }

    .result-card {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
    }
    
    @media (prefers-color-scheme: dark) {
        .result-card { background-color: var(--dark-card); border-color: #333; color: #E0E0E0; }
    }

    .footer { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #333; color: #666; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "aktif_site_index" not in st.session_state: st.session_state.aktif_site_index = 0
if "arama_yapildi" not in st.session_state: st.session_state.arama_yapildi = False
if "url_listesi" not in st.session_state: st.session_state.url_listesi = []
if "hesap_sonuc" not in st.session_state: st.session_state.hesap_sonuc = ""

# --- 🛠 YARDIMCI FONKSİYONLAR (GELİŞTİRİLDİ) ---

def tr_karakter_duzelt(text):
    if not text: return ""
    text = str(text).replace("“", '"').replace("”", '"').replace("’", "'")
    mapping = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'}
    for k, v in mapping.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def site_tara_brave(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Brave/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # WIKIPEDIA ÖZEL TEMİZLİK (Bozuk kısımları uçurur)
            if "wikipedia.org" in url:
                for junk in soup.select('.mw-empty-elt, .hatnote, .infobox, .toc, .navbox, .mw-editsection'):
                    junk.decompose()

            # BRAVE AD-BLOCK: Gereksiz her şeyi temizle
            blacklist = ["script", "style", "nav", "footer", "aside", "form", "header", ".ads", "iframe"]
            for tag in blacklist:
                for element in soup.select(tag):
                    element.decompose()
            
            # BOŞLUK DÜZELTME: Kelime aralarındaki tüm gereksiz boşlukları ve satırları siler
            raw_text = soup.get_text(separator=' ')
            words = raw_text.split()
            clean_text = ' '.join(words)
            
            # Okunabilirlik için nokta sonrası yeni satır
            clean_text = clean_text.replace(". ", ".\n\n")
            
            if len(clean_text) < 150: return None
            return clean_text[:4000]
    except: return None

def pdf_olustur_pro(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, tr_karakter_duzelt("TURKAI ANALIZ RAPORU"), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, tr_karakter_duzelt(icerik))
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# --- 🔐 GİRİŞ EKRANI (TAMAMEN GERİ GELDİ) ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; border: 2px solid #800000; padding: 40px; border-radius: 10px; background-color: var(--dark-card);'><h1 style='color: #800000; font-size: 3rem;'>🇹🇷 TÜRKAI</h1><p style='color: #888; font-size: 1.2rem;'>Profesyonel Araştırma Terminali</p><hr style='border-color: #D4AF37;'></div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        with tab1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sisteme Gir", use_container_width=True):
                    h = hashlib.sha256(p.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                    if c.fetchone(): st.session_state.user = u; st.rerun()
                    else: st.error("Hatalı bilgiler.")
            with c2:
                if st.button("Misafir Girişi", use_container_width=True): st.session_state.user = "Misafir"; st.rerun()
        with tab2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kayıt başarılı.")
                except: st.error("Alınmış kullanıcı adı.")
        st.markdown(f'<a href="{APK_URL}"><button style="width:100%; background-color:#333; color:white; padding:10px; border-radius:5px; margin-top:20px; border:none; cursor:pointer;">📱 Mobil Uygulamayı İndir</button></a>', unsafe_allow_html=True)
        st.stop()

# --- 🖥️ ANA ARAYÜZ (KORUNDU) ---
with st.sidebar:
    st.markdown("### 🎛️ KONTROL PANELİ")
    st.write(f"👤 **Aktif:** {st.session_state.user}")
    if st.button("Çıkış Yap"): st.session_state.user = None; st.rerun()
    st.divider()
    st.subheader("🧮 Hesap Makinesi")
    calc_exp = st.text_input("İşlem (Örn: 125*18)", key="calc_input")
    if st.button("Hesapla"):
        try:
            if set(calc_exp) <= set("0123456789+-*/.()"): st.session_state.hesap_sonuc = str(eval(calc_exp))
            else: st.session_state.hesap_sonuc = "Hata"
        except: st.session_state.hesap_sonuc = "Hata"
    if st.session_state.hesap_sonuc: st.info(f"Sonuç: {st.session_state.hesap_sonuc}")
    st.divider()
    st.markdown(f'<a href="{APK_URL}">📱 Android Uygulama</a>', unsafe_allow_html=True)

st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")
st.markdown("<div class='warning-note'>⚠️ Not: Araştırmak istediğiniz konunun ANAHTAR KELİMESİNİ yazınız. (Örn: Türk✅)</div>", unsafe_allow_html=True)

col_sorgu, col_motor = st.columns([3, 1])
with col_sorgu: sorgu = st.text_input("Araştırma Konusu:")
with col_motor: motor_tipi = st.selectbox("Motor Seçimi", ["🚀 Hızlı Motor (V1)", "🧠 Derin Motor (V2)"])

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary", use_container_width=True):
    if sorgu:
        st.session_state.konu = sorgu.strip()
        st.session_state.arama_yapildi = True
        st.session_state.aktif_site_index = 0
        q = urllib.parse.quote(st.session_state.konu)
        if "Hızlı" in motor_tipi:
            st.session_state.url_listesi = [f"https://tr.wikipedia.org/wiki/{q}", f"https://sozluk.gov.tr/gts?ara={q}", f"https://www.turkcebilgi.com/{q}"]
        else:
            # DERİN MOTOR: Ansiklopedik ve Biyografi Odaklı Güncelleme
            st.session_state.url_listesi = [
                f"https://islamansiklopedisi.org.tr/ara?q={q}",
                f"https://www.biyografi.info/kisi/{q}",
                f"https://www.biyografya.com/arama?q={q}",
                f"https://tr.wikipedia.org/wiki/{q}"
            ]
        st.rerun()

if st.session_state.arama_yapildi:
    urls = st.session_state.url_listesi
    idx = st.session_state.aktif_site_index
    if idx < len(urls):
        url = urls[idx]
        st.info(f"🔎 {motor_tipi} taranıyor... Kaynak: {urllib.parse.urlparse(url).netloc}")
        with st.spinner('Brave Filtresi Aktif...'):
            veri = site_tara_brave(url)
            if veri:
                st.markdown(f"<div class='result-card'><h3>✅ Analiz Sonucu</h3><div style='white-space: pre-wrap;'>{veri}</div></div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    pdf = pdf_olustur_pro(st.session_state.konu, veri)
                    if pdf: st.download_button("📄 PDF İndir", pdf, f"TurkAI_{st.session_state.konu}.pdf", use_container_width=True)
                with c2:
                    if st.button("🔄 Sonraki Kaynağa Geç", use_container_width=True):
                        st.session_state.aktif_site_index += 1; st.rerun()
            else:
                st.session_state.aktif_site_index += 1; st.rerun()
    else:
        st.error("Kaynaklar bitti."); st.button("Sıfırla", on_click=lambda: st.session_state.update({"arama_yapildi": False}))

st.markdown("<div class='footer'><p>&copy; 2026 TürkAI Profesyonel Sistemler | Tüm Hakları Saklıdır.</p></div>", unsafe_allow_html=True)
