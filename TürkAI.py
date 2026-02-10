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
st.set_page_config(page_title="TürkAI | Profesyonel Terminal", layout="wide")

# --- 🛠️ GELİŞMİŞ METİN TEMİZLEME MOTORU ---
def profesyonel_temizle(raw_text):
    if not raw_text: return ""
    
    # 1. Wikipedia ve Haber sitesi "çöplerini" ayıkla
    cop_kelimeler = [
        "İçeriğe atla", "Ana menüyü aç", "Ara", "Değiştir", "Kaynağı değiştir", 
        "Giriş yap", "Kayıt ol", "Daha fazla bilgi", "Abone olmak için tıklayın",
        "Ana sayfa", "Manşet haber", "Seçtiklerimiz", "Diğer haberler"
    ]
    for kelime in cop_kelimeler:
        raw_text = raw_text.replace(kelime, "")

    # 2. Köşeli parantezleri [1], [not 1] temizle
    raw_text = re.sub(r'\[.*?\]', '', raw_text)
    
    # 3. Satır başlarındaki ve sonundaki boşlukları buda, boş satırları sil
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    # 4. BOŞLUK DÜZELTME: Çoklu boşlukları ve satırları teke indir
    clean_text = "\n\n".join(lines) # Paragraf arası çift satır
    clean_text = re.sub(r' +', ' ', clean_text) # Kelime arası tek boşluk
    
    return clean_text

def tdk_temizle(json_data):
    try:
        res = []
        for madde in json_data:
            res.append(f"📚 {madde.get('madde', '').upper()}")
            for anl in madde.get('anlamlarListe', []):
                res.append(f"• {anl.get('anlam', '')}")
                if 'orneklerListe' in anl:
                    for o in anl['orneklerListe']:
                        res.append(f"  👉 '{o.get('ornek')}'")
        return "\n".join(res)
    except: return "Sözlük verisi ayrıştırılamadı."

# --- 🌐 VERİ ÇEKME MOTORU ---
def veri_getir(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Brave/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # TDK kontrolü
        if "sozluk.gov.tr" in url:
            return tdk_temizle(response.json())

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Gereksiz HTML etiketlerini tamamen kaldır
        for tag in ["script", "style", "nav", "footer", "header", "aside", "form", "button"]:
            for element in soup.find_all(tag):
                element.decompose()

        # Ana içeriğe odaklan (Makale veya Ana Gövde)
        article = soup.find('article') or soup.find('main') or soup.body
        text = article.get_text(separator=' ')
        
        return profesyonel_temizle(text)
    except:
        return None

# --- 🔑 SESSION & GİRİŞ ---
if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.markdown("<h1 style='text-align:center;'>🇹🇷 TürkAI Giriş</h1>", unsafe_allow_html=True)
    if st.button("Misafir Olarak Başla", use_container_width=True):
        st.session_state.user = "Misafir"
        st.rerun()
    st.stop()

# --- 🖥️ ANA EKRAN ---
st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")
st.markdown("> **Not:** Aramak istediğiniz konunun **ANAHTAR KELİMESİNİ** yazınız. (Örn: Türk✅)")

col_arama, col_motor = st.columns([3, 1])
with col_arama:
    sorgu = st.text_input("Araştırma Konusu:", placeholder="Örn: Sucuk, Fatih Sultan Mehmet...")
with col_motor:
    motor = st.selectbox("Motor", ["🚀 Ansiklopedi (V1)", "🗞️ Gündem/Haber (V2)"])

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary", use_container_width=True):
    if sorgu:
        q = urllib.parse.quote(sorgu)
        st.session_state.sorgu_kelime = sorgu
        if "Ansiklopedi" in motor:
            st.session_state.kaynaklar = [
                f"https://sozluk.gov.tr/gts?ara={q}",
                f"https://tr.wikipedia.org/wiki/{q}",
                f"https://islamansiklopedisi.org.tr/ara?q={q}"
            ]
        else:
            st.session_state.kaynaklar = [
                f"https://www.bbc.com/turkce/search?q={q}",
                f"https://www.trthaber.com/haber/ara/?q={q}",
                f"https://www.ensonhaber.com/arama?q={q}"
            ]
        st.session_state.idx = 0
        st.session_state.arama_aktif = True

if st.session_state.get("arama_aktif"):
    kaynaklar = st.session_state.kaynaklar
    i = st.session_state.idx
    
    if i < len(kaynaklar):
        url = kaynaklar[i]
        st.info(f"🔍 Kaynak taranıyor: {urllib.parse.urlparse(url).netloc}")
        
        sonuc = veri_getir(url)
        if sonuc:
            st.markdown(f"### 📄 {st.session_state.sorgu_kelime.upper()} - Analiz Raporu")
            st.markdown(f"<div style='background:#f0f2f6; color:#111; padding:20px; border-radius:10px; border-left:5px solid #800000; white-space: pre-wrap;'>{sonuc[:5000]}</div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Bu Kaynağı Beğenmedim, Sıradakine Geç", use_container_width=True):
                    st.session_state.idx += 1
                    st.rerun()
            with c2:
                st.success("Veri başarıyla temizlendi ve optimize edildi.")
        else:
            st.session_state.idx += 1
            st.rerun()
    else:
        st.warning("Tüm kaynaklar bitti. Başka bir anahtar kelime deneyebilirsin.")

# --- 📊 FOOTER ---
st.markdown("---")
st.markdown("<center><b>2026 © TürkAI Profesyonel Araştırma Sistemi</b><br>Boşluk Temizleme Modülü: AKTİF</center>", unsafe_allow_html=True)
