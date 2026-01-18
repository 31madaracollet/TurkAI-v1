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
    st.session_state.karanlik_mod = False

# --- 🧹 GELİŞMİŞ TEMİZLİK (Görüntüdeki Boşlukları Siler) ---
def metni_temizle(metin):
    metin = re.sub(r'\[\d+\]', '', metin) # Kaynaklar
    # Yunanca vb. karakterleri silerken oluşan çift virgül veya boş parantezleri temizler
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    metin = metin.replace('()', '').replace('(, )', '').replace('  ', ' ')
    return metin.strip()

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="TurkAI Arastirma Raporu", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    def safe(s): return s.encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 10, txt=safe(f"Konu: {baslik}"), ln=True)
    pdf.multi_cell(0, 8, txt=safe(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 DİNAMİK TEMA VE STİL ---
def stil_uygula():
    bg = "#121212" if st.session_state.karanlik_mod else "#FFFFFF"
    text = "#E0E0E0" if st.session_state.karanlik_mod else "#121212"
    input_bg = "#1E1E1E" if st.session_state.karanlik_mod else "#F0F2F6"
    
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        .stButton>button {{ background-color: #e63946; color: white; border-radius: 20px; border:none; padding: 0.5rem 2rem; }}
        /* Arama çubuğunu küçültme ve hizalama */
        .stTextInput>div>div>input {{ 
            background-color: {input_bg}; color: {text}; 
            border: 1px solid #e63946; border-radius: 15px; 
            max-width: 500px; margin: 0 auto;
        }}
        h1 {{ color: #e63946; text-align: center; font-size: 2rem; }}
        .stExpander {{ background-color: {input_bg}; border-radius: 10px; }}
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    stil_uygula()
    st.title("🇹🇷 TürkAI Analiz")
    isim = st.text_input("Kanka adın?", placeholder="Lakabını yaz...")
    if st.button("Sistemi Başlat"):
        if len(isim) >= 2:
            st.session_state.kullanici_adi = isim
            st.session_state.giris_yapildi = True
            st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0", page_icon="🇹🇷", layout="centered")
stil_uygula()

# 👈 YAN PANEL (TEMA VE KONTROL)
st.sidebar.title("🛠️ Ayarlar")
st.session_state.karanlik_mod = st.sidebar.toggle("🌙 Karanlık Mod", value=st.session_state.karanlik_mod)
st.sidebar.divider()
st.sidebar.write(f"👤 Araştırmacı: **{st.session_state.kullanici_adi}**")

if st.sidebar.button("🚪 Oturumu Kapat"):
    st.session_state.giris_yapildi = False
    st.rerun()

# ARAŞTIRMA
st.title("🔍 Profesyonel Araştırma Hattı")

# Arama çubuğunun genişliğini kontrol etmek için kolon kullanıyoruz
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    konu = st.text_input("", placeholder="Arayacağın konuyu yaz...", label_visibility="collapsed")
    btn = st.button("Analizi Başlat")

if btn:
    if konu:
        with st.spinner("İşleniyor..."):
            arama = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 50]
                    
                    if paragraflar:
                        if konu not in st.session_state.gecmis: st.session_state.gecmis.append(konu)
                        
                        st.success(f"✅ {konu} analizi hazır.")
                        st.markdown(f"### 📌 Özet Bilgi")
                        st.info(paragraflar[0])
                        
                        tam_metin = "\n\n".join(paragraflar[:8])
                        with st.expander("📖 Tüm Detaylı Analizi Gör"):
                            st.write(tam_metin)
                        
                        pdf_data = pdf_olustur(konu, tam_metin, st.session_state.kullanici_adi)
                        st.download_button("📄 Raporu PDF İndir", pdf_data, f"{konu}.pdf", "application/pdf")
                    else:
                        st.warning("Veri bulunamadı.")
                else:
                    st.error("Konu bulunamadı.")
            except:
                st.error("Bağlantı hatası.")

st.sidebar.divider()
st.sidebar.write("**Geçmiş:**")
for g in st.session_state.gecmis[-5:]:
    st.sidebar.caption(f"• {g}")



