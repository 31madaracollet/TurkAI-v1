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

# --- 🎨 TEMA VE STİL AYARLARI ---
def yerel_css():
    st.markdown("""
        <style>
        .main { background-color: #f5f5f5; }
        .stButton>button { background-color: #e63946; color: white; border-radius: 10px; }
        .stTextInput>div>div>input { border: 2px solid #e63946; }
        h1 { color: #e63946; font-family: 'Trebuchet MS'; }
        </style>
    """, unsafe_allow_html=True)

# --- 📄 PDF OLUŞTURMA FONKSİYONU ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=f"TurkAI Arastirma Raporu", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Konu: {baslik}", ln=True)
    pdf.cell(200, 10, txt=f"Arastirmaci: {kullanici}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=icerik.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    yerel_css()
    st.title("🇹🇷 TürkAI Analiz Sistemi")
    st.write("---")
    isim = st.text_input("Kanka, adın veya lakabın nedir?", placeholder="Örn: Kaptan")
    if st.button("Sistemi Başlat"):
        if len(isim) >= 2:
            st.session_state.kullanici_adi = isim
            st.session_state.giris_yapildi = True
            st.rerun()
        else:
            st.error("Lütfen en az 2 harfli bir isim yaz!")
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0 - Pro", page_icon="🇹🇷", layout="wide")
yerel_css()

# 👈 YAN PANEL
st.sidebar.title("🕒 TürkAI Panel")
st.sidebar.success(f"👤 Aktif: {st.session_state.kullanici_adi}")
if st.sidebar.button("Oturumu Kapat"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.sidebar.divider()
st.sidebar.write("**Son Aramalar:**")
for g in st.session_state.gecmis[-5:]:
    st.sidebar.caption(f"• {g}")

# --- ANALİZ MOTORU ---
st.title(f"🔍 Araştırma Merkezi")

KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt", "meme", "daşşak"] # Liste devam eder...

def temiz_mi(metin):
    metin_kucuk = metin.lower()
    for kelime in KARA_LISTE:
        if kelime in metin_kucuk: return False
    return True

hitap = random.choice(["Değerli Dostum", "Kıymetli Arkadaşım", "Şefim"])

konu = st.text_input("Araştırmak istediğiniz konuyu giriniz:", placeholder="Örn: Nikola Tesla")

if st.button("Analizi Başlat"):
    if konu:
        if not temiz_mi(konu):
            st.error("⚠️ TürkAI: Uygunsuz içerik tespit edildi.")
        else:
            with st.spinner(f"🔎 {hitap}, kaynaklar taranıyor..."):
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
                            
                            sonuc_metni = paragraflar[0]
                            st.success(f"✅ Analiz tamamlandı.")
                            st.info(sonuc_metni)
                            
                            # PDF İNDİRME BUTONU
                            pdf_data = pdf_olustur(konu, sonuc_metni, st.session_state.kullanici_adi)
                            st.download_button(
                                label="📄 Raporu PDF Olarak İndir",
                                data=pdf_data,
                                file_name=f"{konu}_TurkAI_Raporu.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.warning("⚠️ İçerik bulunamadı.")
                    else:
                        st.error("⚠️ Konu bulunamadı.")
                except:
                    st.error("❌ Bağlantı hatası!")
    else:
        st.warning("Lütfen bir konu giriniz.")

st.divider()
st.caption(f"TürkAI v45.0 | Araştırmacı: {st.session_state.kullanici_adi}")


