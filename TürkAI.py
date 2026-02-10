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

# --- 🎨 TASARIM (GÜNCELLENDİ) ---
st.markdown("""
    <style>
    :root {
        --primary-color: #800000;
        --accent-color: #D4AF37;
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
    }
    
    /* UYARI NOTU RENK AYARI (İSTEĞİNE GÖRE) */
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
        .warning-note {
            color: white !important; /* Karanlık modda beyaz */
        }
        .result-card {
            background-color: var(--dark-card) !important;
            color: #E0E0E0 !important;
        }
    }

    .stApp { font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: var(--primary-color) !important; font-weight: 700 !important; }
    
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: 1px solid var(--accent-color) !important;
    }

    .result-card {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI (DOKUNULMADI) ---
def db_baslat():
    conn = sqlite3.connect('turkai_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🛠 YARDIMCI FONKSİYONLAR ---

def tr_karakter_duzelt(text):
    if not text: return ""
    text = str(text).replace("“", '"').replace("”", '"').replace("’", "'")
    mapping = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'}
    for k, v in mapping.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def site_tara_brave(url):
    """Brave Ad-Block mantığı ve Wikipedia temizleyici."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=7)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- WIKIPEDIA ÖZEL TEMİZLİK ---
            if "wikipedia.org" in url:
                # Gereksiz Wikipedia başlıklarını ve yönlendirme linklerini temizle
                for junk in soup.select('.mw-empty-elt, .hatnote, .infobox, .toc, .reflist, .navbox, .mw-editsection'):
                    junk.decompose()

            # Brave Ad-Block Mantığı: Gereksiz elementleri uçur
            blacklist = ["script", "style", "nav", "footer", "aside", "header", ".ads", ".reklam", "iframe"]
            for tag in blacklist:
                for element in soup.select(tag):
                    element.decompose()

            # BOŞLUK DÜZELTME: Metni al ve tüm gereksiz satır boşluklarını temizle
            text_parts = soup.get_text(separator=' ').split()
            clean_text = ' '.join(text_parts)
            
            # Cümle başlarında yeni satır simülasyonu (Okunabilirlik için)
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

# --- 🔐 GİRİŞ EKRANI (DOKUNULMADI) ---
if "user" not in st.session_state: st.session_state.user = None
if not st.session_state.user:
    # (Önceki giriş kodun buraya gelir, değişmediği için kısaltıldı)
    st.title("🇹🇷 TÜRKAI GİRİŞ")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş"): st.session_state.user = u; st.rerun()
    if st.button("Misafir"): st.session_state.user = "Misafir"; st.rerun()
    st.stop()

# --- 🖥️ ANA ARAYÜZ ---
st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")

st.markdown("""
<div class='warning-note'>
    ⚠️ Not: Araştırmak istediğiniz konunun ANAHTAR KELİMESİNİ yazınız. (Örn: Türk kimdir?❌ Türk✅)
</div>
""", unsafe_allow_html=True)

col_sorgu, col_motor = st.columns([3, 1])
with col_sorgu: sorgu = st.text_input("Araştırma Konusu:", placeholder="Konuyu buraya yazın...")
with col_motor: motor_tipi = st.selectbox("Motor Seçimi", ["🚀 Hızlı Motor (V1)", "🧠 Derin Motor (V2)"])

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary", use_container_width=True):
    if not sorgu: st.warning("Lütfen konu girin.")
    else:
        st.session_state.konu = sorgu.strip()
        st.session_state.arama_yapildi = True
        st.session_state.aktif_site_index = 0
        q = urllib.parse.quote(st.session_state.konu)
        
        if "Hızlı" in motor_tipi:
            st.session_state.url_listesi = [
                f"https://tr.wikipedia.org/wiki/{q}",
                f"https://sozluk.gov.tr/gts?ara={q}",
                f"https://www.turkcebilgi.com/{q}"
            ]
        else:
            # DERİN MOTOR: Ansiklopedik ve Biyografi Odaklı Olarak Güncellendi
            st.session_state.url_listesi = [
                f"https://islamansiklopedisi.org.tr/ara?q={q}",
                f"https://www.biyografi.info/kisi/{q}",
                f"https://www.biyografya.com/arama?q={q}",
                f"https://www.turkedebiyati.org/index.php?s={q}",
                f"https://tr.wikipedia.org/wiki/{q}"
            ]
        st.rerun()

if st.session_state.get("arama_yapildi"):
    urls = st.session_state.url_listesi
    idx = st.session_state.aktif_site_index
    
    if idx < len(urls):
        current_url = urls[idx]
        st.info(f"🔎 {motor_tipi} taranıyor... Kaynak: {urllib.parse.urlparse(current_url).netloc}")
        
        with st.spinner('Brave Ad-Block Aktif: Veriler Temizleniyor...'):
            bulunan_veri = site_tara_brave(current_url)
            if bulunan_veri:
                st.markdown(f"<div class='result-card'><h3>✅ Analiz Sonucu</h3><p>{bulunan_veri}</p></div>", unsafe_allow_html=True)
                col_pdf, col_next = st.columns(2)
                with col_pdf:
                    pdf_data = pdf_olustur_pro(st.session_state.konu, bulunan_veri)
                    if pdf_data: st.download_button("📄 PDF İndir", pdf_data, f"Rapor_{st.session_state.konu}.pdf", "application/pdf")
                with col_next:
                    if st.button("🔄 Sonraki Kaynağa Geç"):
                        st.session_state.aktif_site_index += 1
                        st.rerun()
            else:
                st.session_state.aktif_site_index += 1
                st.rerun()
    else:
        st.error("❌ Tüm kaynaklar tarandı.")
        if st.button("Sıfırla"): st.session_state.arama_yapildi = False; st.rerun()
