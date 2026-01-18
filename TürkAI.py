import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
from fpdf import FPDF

# --- 🧠 SİSTEM HAFIZASI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "gecmis" not in st.session_state:
    st.session_state.gecmis = []

# --- 🎨 TEMA AYARI ---
def yerel_css():
    st.markdown("""
        <style>
        .stButton>button { background-color: #e63946; color: white; border-radius: 10px; width: 100%; }
        h1 { color: #e63946; }
        .reportview-container { background: #f0f2f6; }
        </style>
    """, unsafe_allow_html=True)

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="TurkAI Arastirma Raporu", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Konu: {baslik}", ln=True)
    pdf.cell(200, 10, txt=f"Arastirmaci: {kullanici}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=icerik.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    yerel_css()
    st.title("🇹🇷 TürkAI Analiz Merkezi")
    isim = st.text_input("Kanka adın nedir?", placeholder="Örn: Kaptan")
    if st.button("Sistemi Başlat"):
        if len(isim) >= 2:
            st.session_state.kullanici_adi = isim
            st.session_state.giris_yapildi = True
            st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0 - Pro", page_icon="🇹🇷", layout="wide")
yerel_css()

# 👈 YAN PANEL
st.sidebar.title("🕒 Kontrol Paneli")
st.sidebar.success(f"👤 {st.session_state.kullanici_adi}")
if st.sidebar.button("Çıkış Yap"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.sidebar.write("**Geçmiş:**")
for g in st.session_state.gecmis[-5:]:
    st.sidebar.caption(f"• {g}")

# --- ARAŞTIRMA MOTORU (Orijinal Mantık) ---
st.title(f"🔍 Bilgi Tarayıcı")

KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"] 
def temiz_mi(metin):
    if not metin: return True
    return not any(kelime in metin.lower() for kelime in KARA_LISTE)

konu = st.text_input("Araştırılacak Konu:", placeholder="Örn: Yapay Zeka")

if st.button("Analizi Başlat"):
    if konu and temiz_mi(konu):
        with st.spinner("Wikipedia taranıyor..."):
            arama = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        if konu not in st.session_state.gecmis:
                            st.session_state.gecmis.append(konu)
                        
                        # ANA SONUÇ
                        st.success("✅ Temel Bilgi Bulundu")
                        st.info(paragraflar[0])
                        
                        # --- 🟢 GERİ GELEN "HEPSİNİ GÖSTER" KISMI ---
                        tam_metin = " ".join(paragraflar) # PDF için tüm metni hazırla
                        if len(paragraflar) > 1:
                            with st.expander("📖 Detaylı Bilgiyi Gör (Hepsini Göster)"):
                                st.write(" ".join(paragraflar[1:6])) # Sonraki 5 paragrafı göster
                        
                        # PDF BUTONU (Tüm içeriği kapsar)
                        pdf_data = pdf_olustur(konu, tam_metin[:2000], st.session_state.kullanici_adi)
                        st.download_button("📄 Tüm Analizi PDF Olarak İndir", pdf_data, f"{konu}.pdf", "application/pdf")
                    else:
                        st.warning("İçerik çok kısa veya bulunamadı.")
                else:
                    st.error("Konu bulunamadı.")
            except:
                st.error("Bağlantı sorunu!")
    elif konu:
        st.error("⚠️ Argo kelime tespit edildi!")

st.divider()
st.caption(f"TürkAI v45.0 | Kullanıcı: {st.session_state.kullanici_adi}")


