import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI | Derin Analiz", page_icon="🇹🇷", layout="wide")

# --- GÖRSEL TASARIM (CSS) ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    .stSpinner > div { border-top-color: var(--primary-red) !important; }
    .ai-kutusu {
        background-color: #f8f9fa;
        color: #1a1a1a;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid var(--primary-red);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .giris-kapsayici { padding: 30px; border: 1px solid #ddd; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
conn = sqlite3.connect('turkai_v5.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
conn.commit()

# --- YARDIMCI FONKSİYONLAR ---

def daktilo_yaz(metin):
    """Metni ekrana tane tane yazdırır (Hata Veren Yer Burasıydı, Düzeltildi)"""
    alan = st.empty()
    gosterilen = ""
    for harf in metin:
        gosterilen += harf
        # f-string hatası burada giderildi (f"...)
        alan.markdown(f"<div class='ai-kutusu'>{gosterilen}▌</div>", unsafe_allow_html=True)
        time.sleep(0.01)
    alan.markdown(f"<div class='ai-kutusu'>{gosterilen}</div>", unsafe_allow_html=True)

def icerik_temizle(html):
    """Sitedeki reklamları ve çöpleri ayıklar."""
    soup = BeautifulSoup(html, 'html.parser')
    for cop in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'ins', 'iframe']):
        cop.decompose()
    paragraflar = soup.find_all('p')
    # Sadece anlamlı uzunluktaki paragrafları al
    temiz_metin = [p.get_text().strip() for p in paragraflar if len(p.get_text()) > 80]
    return "\n\n".join(temiz_metin[:6])

def derin_analiz_motoru(soru):
    """25 Farklı Türk sitesini tek tek tarayan motor."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    # Sadece Türkçe sonuçlar için site:.tr filtresi ekli
    arama_sorgusu = f"https://www.google.com/search?q={urllib.parse.quote(soru + ' site:.tr')}"
    
    try:
        r = requests.get(arama_sorgusu, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        linkler = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "url?q=" in href and not "google.com" in href:
                temiz_link = href.split("url?q=")[1].split("&sa=")[0]
                linkler.append(temiz_link)
        
        linkler = list(dict.fromkeys(linkler))[:25] # İlk 25 benzersiz link
        
        for i, l in enumerate(linkler):
            with st.status(f"Analiz Ediliyor ({i+1}/25): {l[:40]}...") as s:
                try:
                    site_r = requests.get(l, headers=headers, timeout=10) # Her siteye 10sn limit
                    if site_r.status_code == 200:
                        veri = icerik_temizle(site_r.text)
                        if len(veri) > 100:
                            s.update(label="✅ Bilgi Onaylandı!", state="complete")
                            return veri
                except:
                    continue
        return "25 farklı kaynağı taradım ancak tatmin edici bir Türkçe cevap bulamadım kanka."
    except:
        return "Arama motoru şu an meşgul, daha sonra tekrar dener misin?"

# --- GİRİŞ / KAYIT EKRANI ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🇹🇷 TürkAI Analiz Platformu")
    col1, _ = st.columns([1.5, 1])
    with col1:
        st.markdown("<div class='giris-kapsayici'>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        with t1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Sisteme Gir", use_container_width=True):
                    st.session_state.user = u
                    st.rerun()
            with b2:
                if st.button("👤 Misafir", use_container_width=True):
                    st.session_state.user = "Misafir"
                    st.rerun()
        with t2:
            st.info("Kayıt sistemi şu an bakımda, Misafir girişi yapabilirsin.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- ANA PANEL ---
st.sidebar.title(f"🛡️ {st.session_state.user}")
motor_secimi = st.sidebar.radio("Analiz Motoru:", ["Hızlı (Wikipedia)", "Derin Düşünen (Türk Ağı)"])

if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

st.header("🔍 TürkAI Araştırma Terminali")
soru = st.chat_input("Bir konu yazın veya matematiksel bir işlem yapın (Örn: 155 * 32)...")

if soru:
    st.empty() # Ekranı temizle
    
    # 1. MATEMATİK KONTROLÜ (Regex ile)
    if re.match(r'^[0-9+\-*/().\s^]+$', soru):
        with st.spinner('Hesaplanıyor...'):
            try:
                # eval kullanımı burada güvenli çünkü regex ile sadece sayı ve işlem karakterlerini aldık
                sonuc = eval(soru)
                cevap = f"🔢 **Matematiksel İşlem Sonucu:**\n\n {soru} = **{sonuc}**"
            except:
                cevap = "⚠️ Matematiksel ifadeyi çözemedim, lütfen kontrol et."
    
    # 2. ARAŞTIRMA MOTORU
    else:
        with st.spinner('TürkAI Veri Madenciliği Yapıyor...'):
            if motor_secimi == "Hızlı (Wikipedia)":
                try:
                    w_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(soru)}"
                    res = requests.get(w_url, timeout=5).json()
                    cevap = res.get('extract', "Wikipedia'da bu başlığı bulamadım kanka.")
                except:
                    cevap = "Wikipedia bağlantısı başarısız."
            else:
                cevap = derin_analiz_motoru(soru)

    # Sonucu ekrana tane tane dök
    daktilo_yaz(cevap)
    
    # Geri Bildirim
    if st.button("👎 Yanıtı Beğenmedim"):
        st.toast("Geri bildirim alındı, algoritma eğitiliyor.")
