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

# --- 🧹 TEMİZLİK ARACI (Wikipedia İşaretlerini Siler) ---
def metni_temizle(metin):
    # [1], [2], [15] gibi kaynak işaretlerini temizler
    temiz = re.sub(r'\[\d+\]', '', metin)
    # Garip boşlukları ve satır başlarını düzenler
    return temiz.strip()

# --- 📄 PDF OLUŞTURUCU (Türkçe Karakter Destekli) ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    # Standart fontlar Türkçe desteklemediği için latin-1 dönüşümü yapıyoruz
    # Bu fonksiyon metindeki Türkçe karakterleri PDF'in anlayacağı dile çevirir
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="TurkAI Arastirma Raporu", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    # Türkçe karakter hatası almamak için metni güvenli hale getiriyoruz
    def safe_text(s):
        return s.encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(200, 10, txt=safe_text(f"Konu: {baslik}"), ln=True)
    pdf.cell(200, 10, txt=safe_text(f"Arastirmaci: {kullanici}"), ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=safe_text(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 TEMA AYARI ---
def yerel_css():
    st.markdown("""
        <style>
        .stButton>button { background-color: #e63946; color: white; border-radius: 10px; width: 100%; font-weight: bold; }
        h1 { color: #e63946; text-align: center; }
        .stTextInput>div>div>input { border: 2px solid #e63946; }
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    yerel_css()
    st.title("🇹🇷 TürkAI Analiz Merkezi")
    isim = st.text_input("Kanka adın nedir?", placeholder="Örn: Kaptan")
    if st.button("Sisteme Giriş Yap"):
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
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.sidebar.divider()
st.sidebar.write("**Geçmiş Aramalar:**")
for g in st.session_state.gecmis[-5:]:
    st.sidebar.caption(f"• {g}")

# --- ARAŞTIRMA MOTORU ---
st.title(f"🔍 Bilgi Analiz ve Raporlama")

KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"]
def temiz_mi(metin):
    return not any(kelime in metin.lower() for kelime in KARA_LISTE)

konu = st.text_input("Araştırılacak Konu Başlığı:", placeholder="Örn: Galaksi")

if st.button("Analizi Başlat"):
    if konu and temiz_mi(konu):
        with st.spinner("Veriler filtreleniyor ve işaretler temizleniyor..."):
            arama = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        if konu not in st.session_state.gecmis:
                            st.session_state.gecmis.append(konu)
                        
                        # ANA SONUÇ
                        st.success(f"✅ {konu} hakkında temizlenmiş veriler hazır!")
                        st.info(paragraflar[0])
                        
                        # DETAYLI BİLGİ (HEPSİNİ GÖSTER)
                        tam_metin = "\n\n".join(paragraflar[:10]) # İlk 10 paragrafı birleştir
                        if len(paragraflar) > 1:
                            with st.expander("📖 Detaylı Bilgiyi Gör (Kaynaklar Temizlendi)"):
                                st.write(tam_metin)
                        
                        # PDF BUTONU
                        pdf_data = pdf_olustur(konu, tam_metin[:3000], st.session_state.kullanici_adi)
                        st.download_button("📄 Temiz Raporu PDF Olarak İndir", pdf_data, f"{konu}_Rapor.pdf", "application/pdf")
                    else:
                        st.warning("Konu hakkında detaylı veri bulunamadı.")
                else:
                    st.error("Wikipedia'da bu başlık bulunamadı.")
            except:
                st.error("Sunucu bağlantısı kurulamadı.")
    elif konu:
        st.error("⚠️ Lütfen uygun bir dil kullanın.")

st.divider()
st.caption(f"TürkAI v45.0 | Araştırmacı: {st.session_state.kullanici_adi} | Hatasız Raporlama Modu")



