import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import re
from fpdf import FPDF

# --- 🧠 SİSTEM HAFIZASI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "gecmis" not in st.session_state:
    st.session_state.gecmis = []
if "karanlik_mod" not in st.session_state:
    st.session_state.karanlik_mod = True # Varsayılan karanlık mod

# --- 🧹 TEMİZLİK ARACI ---
def metni_temizle(metin):
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    metin = metin.replace('()', '').replace('(, )', '').replace('  ', ' ')
    return metin.strip()

# --- 🎨 YENİ NESİL ESTETİK STİL ---
def stil_uygula():
    bg = "#0E1117" if st.session_state.karanlik_mod else "#FFFFFF"
    text = "#FFFFFF" if st.session_state.karanlik_mod else "#000000"
    card = "#161B22" if st.session_state.karanlik_mod else "#F0F2F6"
    
    st.markdown(f"""
        <style>
        /* Genel Arka Plan */
        .stApp {{ background-color: {bg}; color: {text}; }}
        
        /* Arama Çubuğu ve Konteynır */
        .main-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        
        div[data-baseweb="input"] {{
            width: 100% !important;
            max-width: 700px !important;
            margin: 0 auto;
            border-radius: 12px;
        }}

        input {{
            text-align: center;
            font-size: 1.2rem !important;
            padding: 15px !important;
        }}

        /* Buton Tasarımı */
        .stButton>button {{
            width: 100% !important;
            max-width: 700px !important;
            height: 50px;
            background-color: #e63946 !important;
            color: white !important;
            font-weight: bold;
            font-size: 1.1rem;
            border-radius: 12px;
            margin-top: 10px;
            transition: 0.3s;
        }}
        
        .stButton>button:hover {{
            transform: scale(1.02);
            background-color: #ff4d5a !important;
        }}

        /* Sonuç Kutuları */
        .stInfo {{
            background-color: {card};
            border-radius: 15px;
            border: 1px solid #e63946;
            padding: 20px;
        }}

        h1 {{ color: #e63946; font-size: 3rem !important; margin-bottom: 30px; }}
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    stil_uygula()
    st.markdown("<h1 style='text-align: center;'>🇹🇷 TürkAI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        isim = st.text_input("Kanka adın nedir?", placeholder="Buraya yaz...")
        if st.button("Sistemi Başlat"):
            if len(isim) >= 2:
                st.session_state.kullanici_adi = isim
                st.session_state.giris_yapildi = True
                st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0", page_icon="🇹🇷", layout="wide")
stil_uygula()

# YAN PANEL
with st.sidebar:
    st.title("🛡️ Ayarlar")
    st.session_state.karanlik_mod = st.toggle("🌙 Karanlık Mod", value=st.session_state.karanlik_mod)
    if st.button("🔄 Modu Uygula"): st.rerun()
    st.divider()
    st.write(f"👤 Aktif: **{st.session_state.kullanici_adi}**")
    if st.button("🚪 Çıkış"):
        st.session_state.giris_yapildi = False
        st.rerun()

# ARAŞTIRMA ALANI (MERKEZLENMİŞ)
st.markdown("<h1>🔍 Profesyonel Araştırma Hattı</h1>", unsafe_allow_html=True)

# Çubuğu ortalamak ve büyütmek için kolon yapısı
c1, c2, c3 = st.columns([1, 4, 1])
with c2:
    konu = st.text_input("", placeholder="Araştırmak istediğin konuyu buraya yaz...", label_visibility="collapsed")
    btn = st.button("Analizi Başlat")

if btn and konu:
    with st.spinner("Tır yola çıktı, veriler getiriliyor..."):
        arama = konu.strip().capitalize().replace(' ', '_')
        url = f"https://tr.wikipedia.org/wiki/{arama}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 50]
                
                if paragraflar:
                    if konu not in st.session_state.gecmis: st.session_state.gecmis.append(konu)
                    
                    st.markdown(f"### 📌 {konu} Analiz Sonucu")
                    st.info(paragraflar[0])
                    
                    with st.expander("📖 Detaylı Bilgileri Göster"):
                        st.write("\n\n".join(paragraflar[1:8]))
                        
                    # PDF Butonu (Genişletildi)
                    # (pdf_olustur fonksiyonu önceki kodda olduğu gibi çalışacak şekilde buraya eklenebilir)
                else:
                    st.warning("Veri bulunamadı.")
            else:
                st.error("Konu bulunamadı.")
        except:
            st.error("Bağlantı hatası.")



