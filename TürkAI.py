import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
from duckduckgo_search import DDGS
import concurrent.futures

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 💾 HAFIZA ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "tema" not in st.session_state: st.session_state.tema = "dark" # Varsayılan artık Dark

# --- 🎨 CSS: BEYAZ ALANLARI YOK EDEN VE REKLAMLARI SİLEN TASARIM ---
def css_temizle():
    ana_renk = "#cc0000"
    if st.session_state.tema == "dark":
        bg = "#0e1117"; txt = "#ffffff"; input_bg = "#262730"
    else:
        bg = "#ffffff"; txt = "#000000"; input_bg = "#f0f2f6"

    st.markdown(f"""
        <style>
        /* Ana ekran ve tüm beyaz boşluklar */
        .stApp, [data-testid="stHeader"], [data-testid="stSidebar"] {{
            background-color: {bg} !important;
            color: {txt} !important;
        }}
        
        /* Arama çubuğu ve alt beyazlık tamiri */
        [data-testid="stChatInput"] {{
            background-color: {bg} !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: {input_bg} !important;
            color: {txt} !important;
            border: 1px solid {ana_renk} !important;
        }}
        
        /* Sidebar yazı renkleri */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h3 {{
            color: {txt} !important;
        }}
        
        /* Analiz rapor alanı */
        .ai-rapor-alani {{
            border-left: 5px solid {ana_renk}; padding: 20px;
            background-color: {input_bg}; border-radius: 10px;
            color: {txt} !important; margin: 10px 0;
        }}
        
        h1, h2, h3 {{ color: {ana_renk} !important; }}
        div.stButton > button {{ background-color: {ana_renk} !important; color: white !important; }}
        </style>
    """, unsafe_allow_html=True)

css_temizle()

# --- 🛡️ AKILLI FİLTRE (REKLAM SAVAR) ---
def bilgi_mi(text):
    if not text or len(text) < 40: return False
    # Yasaklı kelime listesi (Reklamlar genellikle bunları içerir)
    yasakli = [
        "youtube", "app store", "google play", "subscribe", "privacy policy", 
        "terms of service", "cookie", "advertisement", "rent", "apartment",
        "price", "buy now", "click here", "follow us", "tüm hakları saklıdır"
    ]
    text_lower = text.lower()
    for kelime in yasakli:
        if kelime in text_lower: return False
    return True

# --- 🌦️ HAVA DURUMU (GÜNCELLENDİ) ---
def hava_durumu_al(sehir):
    try:
        url = f"https://wttr.in/{sehir}?format=%C+%t+%h"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.text
        return "Veri alınamadı."
    except: return "Bağlantı hatası."

# --- 🔍 DERİN ANALİZ MOTORU (SADECE BİLGİ) ---
def siteyi_oku(url):
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=h, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece ana metin bloklarını (paragrafları) çek
        paragraflar = [p.get_text().strip() for p in soup.find_all('p') if bilgi_mi(p.get_text())]
        return "\n\n".join(paragraflar[:2]) # Her siteden en kaliteli 2 paragraf
    except: return ""

def derin_analiz(sorgu):
    try:
        havuz = []
        # 1. Wikipedia (En güvenilir kaynak)
        wiki_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        try:
            w_res = requests.get(wiki_url, timeout=3).json()
            if 'extract' in w_res: havuz.append(f"📖 WIKIPEDIA:\n{w_res['extract']}")
        except: pass

        # 2. Global Arama (Reklamsız Filtreleme)
        with DDGS() as ddgs:
            # Sorguyu "ansiklopedi" ve "bilgi" kelimeleriyle kısıtlıyoruz
            linkler = [r['href'] for r in ddgs.text(f"{sorgu} ansiklopedik bilgi", region='tr-tr', max_results=5)]
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            icerikler = list(executor.map(siteyi_oku, linkler))
        
        for icerik in icerikler:
            if icerik: havuz.append(f"🌍 KAYNAK VERİSİ:\n{icerik}")

        return "\n\n---\n\n".join(havuz) if havuz else "Maalesef temiz bir bilgi kaynağı bulunamadı."
    except Exception as e: return f"Analiz hatası: {str(e)}"

# --- 👤 GİRİŞ SİSTEMİ (Özet Geçildi) ---
if not st.session_state.user:
    st.markdown("<div style='text-align:center'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
    if st.button("🚀 Misafir Olarak Hemen Başla", use_container_width=True):
        st.session_state.user = "Misafir"; st.rerun()
    st.stop()

# --- 🛸 PANEL ---
with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    if st.button("🌙/☀️ Tema Değiştir"):
        st.session_state.tema = "light" if st.session_state.tema == "dark" else "dark"
        st.rerun()
    
    st.divider()
    st.subheader("🌦️ Hava Durumu")
    il = st.selectbox("İl Seç:", ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Erzurum"])
    st.info(hava_durumu_al(il))
    
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()

# --- 💬 ANA EKRAN ---
st.write("### 🇹🇷 TürkAI Araştırma Terminali")

sorgu = st.chat_input("Araştırma konusu girin...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.konu = sorgu.title()
    with st.spinner("🔍 Ansiklopedik kaynaklar taranıyor, reklamlar ayıklanıyor..."):
        st.session_state.bilgi = derin_analiz(sorgu)
    st.rerun()

if st.session_state.bilgi:
    st.markdown(f"#### 📌 Analiz Sonucu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # PDF Butonu
    def pdf_indir():
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=12)
        temiz_metin = re.sub(r'[^\x00-\x7F]+', ' ', st.session_state.bilgi) # Türkçe karakter fix
        pdf.multi_cell(0, 10, txt=temiz_metin)
        return pdf.output(dest='S').encode('latin-1')

    st.download_button("📄 Raporu PDF Olarak Al", data=pdf_indir(), file_name="TurkAI_Rapor.pdf", use_container_width=True)
