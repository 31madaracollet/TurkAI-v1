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

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# Session State
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "tema" not in st.session_state: st.session_state.tema = "dark"

# --- 🎨 DARK-MOD VE BEYAZLIK GİDERİCİ CSS ---
def css_enjekte_et():
    bg = "#0e1117" if st.session_state.tema == "dark" else "#ffffff"
    txt = "#ffffff" if st.session_state.tema == "dark" else "#000000"
    card = "#1e1e26" if st.session_state.tema == "dark" else "#f8f9fa"
    accent = "#cc0000"

    st.markdown(f"""
        <style>
        /* Tüm Uygulama Arka Planı */
        .stApp, [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stBottom"] {{
            background-color: {bg} !important;
            color: {txt} !important;
        }}
        
        /* Yan Panel */
        [data-testid="stSidebar"] {{ border-right: 2px solid {accent}; }}
        
        /* Chat Giriş Alanı (Beyazlığı Yok Etme) */
        [data-testid="stBottomBlockContainer"] {{ background-color: {bg} !important; }}
        
        /* Analiz Kartları */
        .analiz-kart {{
            background-color: {card};
            border-left: 5px solid {accent};
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: {txt} !important;
        }}
        
        h1, h2, h3 {{ color: {accent} !important; }}
        .stButton>button {{ background-color: {accent} !important; color: white !important; border-radius: 20px; }}
        
        /* Hava Durumu Kutusu */
        .hava-box {{
            padding: 10px; background: {accent}; color: white; border-radius: 10px; text-align: center;
        }}
        </style>
    """, unsafe_allow_html=True)

css_enjekte_et()

# --- 🛡️ TÜRKÇE VE REKLAM FİLTRESİ ---
def sadece_turkce_mi(metin):
    if not metin: return False
    # Türkçe'ye özgü harflerin varlığını kontrol et (Reklamları eler)
    turkce_harfler = re.findall(r'[çğıöşüÇĞİÖŞÜ]', metin)
    # Eğer metinde hiç Türkçe karakter yoksa ve kelime sayısı fazlaysa muhtemelen İngilizce reklamdır
    if len(turkce_harfler) == 0 and len(metin.split()) > 10:
        return False
    return True

# --- 🌦️ HAVA DURUMU SİSTEMİ ---
def hava_durumu_getir(sehir):
    try:
        # wttr.in kullanımı (v2 formatında daha temiz veri)
        url = f"https://wttr.in/{sehir}?format=%C+%t"
        r = requests.get(url, timeout=3)
        return r.text if r.status_code == 200 else "Veri çekilemedi."
    except: return "Bağlantı hatası."

# --- 🔍 DERİN ANALİZ (SADECE TR KAYNAKLAR) ---
def site_icerik_al(url):
    try:
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=h, timeout=4)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece ana metin paragrafları
        p_list = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
        # İlk 2 paragrafı al ve Türkçe kontrolünden geçir
        icerik = " ".join(p_list[:2])
        return icerik if sadece_turkce_mi(icerik) else ""
    except: return ""

def derin_analiz_yap(sorgu):
    havuz = []
    # 1. Wikipedia TR Zorunlu
    try:
        w_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        w_res = requests.get(w_url, timeout=3).json()
        if 'extract' in w_res:
            havuz.append(f"📚 **Wikipedia (TR):**\n{w_res['extract']}")
    except: pass

    # 2. Seçkin Türkçe Kaynaklar (edu.tr, gov.tr ve genel haber/bilgi)
    with DDGS() as ddgs:
        # Aramayı sadece Türkçe ve bilgi odaklı sitelere kısıtla
        arama_sorgusu = f"{sorgu} nedir bilgi site:tr.wikipedia.org OR site:edu.tr OR site:gov.tr OR site:org.tr"
        sonuclar = list(ddgs.text(arama_sorgusu, region='tr-tr', max_results=5))
        linkler = [s['href'] for s in sonuclar]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        site_metinleri = list(executor.map(site_icerik_al, linkler))

    for metin in site_metinleri:
        if metin: havuz.append(f"🌐 **Kurumsal/Akademik Kaynak:**\n{metin}...")

    return "\n\n---\n\n".join(havuz) if havuz else "Sadece Türkçe kaynaklarda temiz bir sonuç bulunamadı."

# --- 🔑 GİRİŞ VE PANEL ---
if not st.session_state.user:
    st.markdown("<h1 style='text-align:center;'>🇹🇷 TürkAI Analiz</h1>", unsafe_allow_html=True)
    if st.button("🚀 Misafir Girişi", use_container_width=True):
        st.session_state.user = "Misafir"; st.rerun()
    st.stop()

with st.sidebar:
    st.write(f"### 👤 {st.session_state.user}")
    if st.button("🌓 Tema Değiştir"):
        st.session_state.tema = "light" if st.session_state.tema == "dark" else "dark"
        st.rerun()
    
    st.divider()
    st.subheader("🌦️ Hava Durumu")
    sehir = st.selectbox("İl:", ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Trabzon", "Erzurum"])
    st.markdown(f"<div class='hava-box'>{hava_durumu_getir(sehir)}</div>", unsafe_allow_html=True)
    
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()

# --- 💬 ANA EKRAN ---
st.markdown("### 🇹🇷 TürkAI Araştırma Terminali v4.0")
sorgu = st.chat_input("Neyi analiz edelim kanka? (Sadece Türkçe Kaynaklar)")

if sorgu:
    st.session_state.konu = sorgu.title()
    with st.spinner("🕵️‍♂️ Reklamlar ayıklanıyor, Türkçe kaynaklar taranıyor..."):
        st.session_state.bilgi = derin_analiz_yap(sorgu)
    st.rerun()

if st.session_state.bilgi:
    st.markdown(f"#### 🔍 Konu: {st.session_state.konu}")
    st.markdown(f"<div class='analiz-kart'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # PDF
    def pdf_olustur():
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=12)
        # Karakter temizliği
        t = re.sub(r'[^\x00-\x7F]+', ' ', st.session_state.bilgi)
        pdf.multi_cell(0, 10, txt=t)
        return pdf.output(dest='S').encode('latin-1')

    st.download_button("📄 PDF Raporu İndir", data=pdf_olustur(), file_name="TurkAI_Rapor.pdf", use_container_width=True)

st.markdown("---")
st.caption("🚀 Powered by Madara | Sadece Güvenilir Türkçe Kaynaklar")
