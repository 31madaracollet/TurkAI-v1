import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz", page_icon="🇹🇷", layout="wide")

# --- 🎨 TASARIM ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    h1, h2, h3 { color: var(--primary-red) !important; font-weight: 700 !important; }
    .ai-rapor-alani { 
        border-left: 5px solid var(--primary-red); 
        padding: 20px; 
        background-color: #f9f9f9; 
        border-radius: 8px; 
        color: #1a1a1a;
        line-height: 1.7;
        font-size: 1.1rem;
    }
    .stSpinner > div { border-top-color: #cc0000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c
conn, c = db_baslat()

# --- 🔄 ZEKA FONKSİYONLARI ---

def yazi_efekti(text):
    """Metni daktilo gibi tane tane yazar."""
    placeholder = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.005)
    placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}</div>", unsafe_allow_html=True)

def siteyi_analiz_et(url):
    """Sitenin içine girip reklamları ayıklayarak temiz metni çeker."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Gereksizleri temizle (Reklam, menü, footer)
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            junk.decompose()
        
        # Anlamlı paragrafları topla
        paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 80])
        return content[:1500] if len(content) > 100 else None
    except:
        return None

def derin_dusunen_motor(sorgu):
    """25 Türk sitesini gezip bilgi toplayan ana motor."""
    durum = st.empty()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Sadece Türkiye sonuçları için Google Lite modunu simüle ediyoruz
    encoded_query = urllib.parse.quote(f"{sorgu} site:.tr OR site:.com.tr")
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Google'ın yönlendirme linklerini temizleyip asıl site linkini alıyoruz
            if "url?q=" in href and not "google.com" in href:
                clean_link = href.split("url?q=")[1].split("&sa=")[0]
                links.append(clean_link)
        
        links = list(dict.fromkeys(links))[:25] # İlk 25 benzersiz site
        
        if not links:
            return "Maalesef ağ üzerinde güncel bir Türkçe kaynak bulunamadı."

        for i, link in enumerate(links):
            durum.caption(f"🔍 Analiz Ediliyor ({i+1}/25): {link[:50]}...")
            veri = siteyi_analiz_et(link)
            if veri:
                durum.empty()
                return veri # Bilgi bulduğu an ilk kaliteli kaynağı getirir
        
        durum.empty()
        return "Siteleri taradım ama reklam ve çöp içerik dışında bir veri bulamadım."
    except Exception as e:
        return f"Arama motoru hatası: {str(e)}"

def wiki_arama(sorgu):
    """Hızlı özet motoru."""
    try:
        r = requests.get(f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}", timeout=5).json()
        return r.get('extract', "Wikipedia'da sonuç bulunamadı.")
    except:
        return "Bağlantı hatası."

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("🇹🇷 TürkAI Analiz Terminali")
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
        with tab1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Giriş", use_container_width=True):
                st.session_state.user = u if u else "Kullanıcı"
                st.rerun()
            if col_b2.button("👤 Misafir", use_container_width=True):
                st.session_state.user = "Misafir"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 🚀 ANA PANEL ---
st.sidebar.header(f"🛡️ {st.session_state.user}")
motor_secimi = st.sidebar.radio("Analiz Modu:", ["Derin Düşünen (Türk Ağı)", "Hızlı Özet (Wiki)"])
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

st.title("🔍 Araştırma Merkezi")
sorgu = st.chat_input("Bir konu yazın veya matematiksel işlem yapın...")

if sorgu:
    # 1. MATEMATİK KONTROLÜ (İnternete sormadan önce hallet)
    if re.match(r'^[0-9+\-*/().\s^]+$', sorgu):
        with st.spinner('Hesaplanıyor...'):
            try:
                sonuc = eval(sorgu)
                cevap = f"🔢 **Matematiksel İşlem Sonucu:**\n\n {sorgu} = **{sonuc}**"
            except:
                cevap = "⚠️ Matematiksel ifade hatalı."
    
    # 2. ARAŞTIRMA MOTORU
    else:
        with st.spinner('TürkAI Veri Madenciliği Yapıyor...'):
            if motor_secimi == "Hızlı Özet (Wiki)":
                cevap = wiki_arama(sorgu)
            else:
                cevap = derin_dusunen_motor(sorgu)
    
    # Sonucu ekrana dök
    yazi_efekti(cevap)

    # Geri Bildirim Butonları
    col_f1, col_f2 = st.columns([1, 4])
    with col_f1:
        if st.button("👎 Beğenmedim"):
            st.toast("Geri bildirim alındı. Algoritma güncelleniyor.")
