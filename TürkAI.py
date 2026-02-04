import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import re
from fpdf import FPDF
from duckduckgo_search import DDGS
import concurrent.futures
import time

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI v5.0", page_icon="🇹🇷", layout="wide")

# --- 💾 SESION YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "tema" not in st.session_state: st.session_state.tema = "system" # Varsayılan sistem

# --- 🎨 CSS: GİRİŞ VE TEMA TAMİRİ ---
def css_yukle():
    # Tema Belirleme
    accent = "#cc0000"
    if st.session_state.tema == "dark":
        bg, txt, input_bg = "#0e1117", "#ffffff", "#262730"
    elif st.session_state.tema == "light":
        bg, txt, input_bg = "#ffffff", "#000000", "#f0f2f6"
    else: # System default
        bg, txt, input_bg = "transparent", "inherit", "transparent"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg}; color: {txt}; }}
        h1, h2, h3 {{ color: {accent} !important; }}
        
        /* Giriş Formu ve Inputlar */
        .stTextInput input, .stTextArea textarea {{
            color: {txt} !important;
            background-color: {input_bg} !important;
            border: 1px solid {accent} !important;
        }}
        
        /* Sidebar Görünürlüğü */
        [data-testid="stSidebar"] {{
            border-right: 2px solid {accent};
        }}
        
        /* Analiz Kutusu */
        .rapor-kutusu {{
            border-left: 6px solid {accent};
            padding: 20px;
            background-color: rgba(204, 0, 0, 0.05);
            border-radius: 10px;
            margin-top: 15px;
        }}
        
        div.stButton > button {{
            background-color: {accent} !important;
            color: white !important;
            border-radius: 10px;
            width: 100%;
        }}
        </style>
    """, unsafe_allow_html=True)

css_yukle()

# --- 🛡️ TÜRKÇE KARAKTER VE REKLAM FİLTRESİ ---
def metin_temizle(t):
    if not t: return ""
    # Reklam ve Yabancı metin temizliği
    yasakli = ["subscribe", "youtube", "privacy policy", "cookie", "apartment", "rent", "all rights reserved"]
    for y in yasakli:
        if y in t.lower(): return ""
    return t.strip()

def pdf_tr_fix(text):
    # FPDF standart fontları için Türkçe karakter çevirici
    tr_map = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
    for k, v in tr_map.items():
        text = text.replace(k, v)
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

# --- 🔍 ARAMA MOTORLARI ---

def site_oku(url, timeout=7):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            ps = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 80]
            return " ".join(ps[:2])
    except: return ""
    return ""

def hizli_motor(sorgu):
    # Wiki ve Ansiklopedi odaklı
    kaynaklar = [
        f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}",
        f"https://www.bilgiustam.com/?s={urllib.parse.quote(sorgu)}"
    ]
    
    # 1. Wikipedia Kontrol
    try:
        res = requests.get(kaynaklar[0], timeout=7).json()
        if 'extract' in res: return f"📚 **Wikipedia:** {res['extract']}"
    except: pass
    
    # 2. Genel Arama (Hızlı)
    with DDGS() as ddgs:
        results = list(ddgs.text(f"{sorgu} nedir bilgi", region='tr-tr', max_results=2))
        for r in results:
            return f"🔎 **Bilgi Kaynağı:** {r['body']}"
    return "Hızlı motor sonuç bulamadı."

def derin_motor(sorgu):
    havuz = []
    with DDGS() as ddgs:
        # Tam 15 siteyi hedefliyoruz
        linkler = [r['href'] for r in ddgs.text(f"{sorgu} hakkında detaylı bilgi", region='tr-tr', max_results=15)]
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Her site için tam 7 saniye süre
        sonuclar = list(executor.map(lambda u: site_oku(u, timeout=7), linkler))
    
    for s in sonuclar:
        temiz = metin_temizle(s)
        if temiz: havuz.append(f"🔹 {temiz}")
    
    return "\n\n".join(havuz[:10]) if havuz else "Derin analiz sonuç bulamadı."

# --- 🔑 GİRİŞ VE PANEL ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🇹🇷 TürkAI v5.0</h1>", unsafe_allow_html=True)
        st.info("Sistem teması algılandı. Değiştirmek isterseniz yan paneli kullanın.")
        if st.button("🚀 Misafir Olarak Başla"):
            st.session_state.user = "Misafir"; st.rerun()
        
        tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
        with tab1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir"):
                st.session_state.user = u; st.rerun()
    st.stop()

with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    st.divider()
    
    # TEMA SEÇİCİ
    st.subheader("🎨 Görünüm")
    tema_sec = st.radio("Tema Ayarı:", ["Sistem", "Karanlık", "Aydınlık"])
    if tema_sec == "Karanlık": st.session_state.tema = "dark"
    elif tema_sec == "Aydınlık": st.session_state.tema = "light"
    else: st.session_state.tema = "system"
    
    st.divider()
    
    # HAVA DURUMU
    st.subheader("🌦️ Hava Durumu")
    sehir = st.text_input("Şehir:", "Istanbul")
    try:
        w = requests.get(f"https://wttr.in/{sehir}?format=%C+%t", timeout=5).text
        st.warning(f"📍 {sehir}: {w}")
    except: st.error("Hava durumu alınamadı.")
    
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()

# --- 💬 ANA ARAŞTIRMA ---
st.write(f"## {st.session_state.user}, Neyi Araştırıyoruz?")
motor_tipi = st.segmented_control("Analiz Derinliği:", ["🏎️ Hızlı (2 Kaynak)", "🧠 Derin (15 Kaynak)"], default="🏎️ Hızlı (2 Kaynak)")

sorgu = st.chat_input("Konuyu buraya yaz kanka...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.konu = sorgu.title()
    with st.spinner("🚀 TürkAI internetin altını üstüne getiriyor..."):
        if "Hızlı" in motor_tipi:
            st.session_state.bilgi = hizli_motor(sorgu)
        else:
            st.session_state.bilgi = derin_motor(sorgu)
    st.rerun()

# --- 📊 SONUÇLAR VE PDF ---
if st.session_state.bilgi:
    st.markdown(f"### 📌 Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='rapor-kutusu'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # PDF HAZIRLAMA
    def pdf_yap():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt=pdf_tr_fix(f"TurkAI Raporu: {st.session_state.konu}"), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=pdf_tr_fix(st.session_state.bilgi))
        return pdf.output(dest='S').encode('latin-1')

    st.divider()
    st.download_button("📄 PDF Raporunu İndir", data=pdf_yap(), file_name=f"TurkAI_{st.session_state.konu}.pdf", use_container_width=True)
    
    if st.button("🔄 Analizi Beğenmedim, Derine İn"):
        st.session_state.bilgi = derin_motor(st.session_state.son_sorgu)
        st.rerun()
