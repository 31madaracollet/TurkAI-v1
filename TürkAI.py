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

# --- 🧹 SÜPER TEMİZLİK ARACI (Soru İşareti Düşmanı) ---
def metni_temizle(metin):
    # 1. Wikipedia kaynak numaralarını siler: [1], [22]
    metin = re.sub(r'\[\d+\]', '', metin)
    
    # 2. PDF'in tanımadığı Yunanca ve özel sembolleri ayıklar (Sadece standart karakterleri bırakır)
    # Bu kısım (Yunanca: τέχνη) gibi kısımlardaki yabancı harfleri temizler
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    
    # 3. Gizli boşluk karakterlerini (non-breaking space vb.) normal boşluğa çevirir
    metin = metin.replace('\xa0', ' ').replace('\u200b', '')
    
    return metin.strip()

# --- 📄 PDF OLUŞTURUCU (Hatasız Mod) ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    
    # PDF içinde soru işareti çıkmaması için güvenli karakter dönüşümü
    def güvenli_yazi(s):
        # Latin-1'e uymayan her şeyi temizle veya soru işaretine dönüştürmeden yok et
        return s.encode('latin-1', 'ignore').decode('latin-1')

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="TurkAI Arastirma Raporu", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=güvenli_yazi(f"Konu: {baslik}"), ln=True)
    pdf.cell(200, 10, txt=güvenli_yazi(f"Arastirmaci: {kullanici}"), ln=True)
    pdf.ln(5)
    
    # Metni satırlara bölerek yazdır
    pdf.multi_cell(0, 8, txt=güvenli_yazi(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 TEMA ---
def yerel_css():
    st.markdown("""
        <style>
        .stButton>button { background-color: #e63946; color: white; border-radius: 8px; font-weight: bold; }
        .stTextInput>div>div>input { border: 2px solid #e63946; border-radius: 8px; }
        h1 { color: #e63946; text-align: center; border-bottom: 2px solid #e63946; padding-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    yerel_css()
    st.title("🇹🇷 TürkAI Analiz Sistemi")
    isim = st.text_input("Kullanıcı Adınız:", placeholder="Örn: Kaptan")
    if st.button("Sisteme Giriş"):
        if len(isim) >= 2:
            st.session_state.kullanici_adi = isim
            st.session_state.giris_yapildi = True
            st.rerun()
    st.stop()

# --- 🚀 ANA EKRAN ---
st.set_page_config(page_title="TürkAI v45.0", page_icon="🇹🇷", layout="wide")
yerel_css()

# YAN PANEL
st.sidebar.title("🛡️ TürkAI Kontrol")
st.sidebar.info(f"👤 Araştırmacı: {st.session_state.kullanici_adi}")
if st.sidebar.button("Çıkış"):
    st.session_state.giris_yapildi = False
    st.rerun()

# ARAŞTIRMA BÖLÜMÜ
st.title("🔍 Profesyonel Araştırma Hattı")

KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"]
konu = st.text_input("Hangi konuyu derinlemesine analiz edelim?", placeholder="Örn: Teknoloji")

if st.button("Analizi Başlat"):
    if konu and not any(k in konu.lower() for k in KARA_LISTE):
        with st.spinner("Veriler ayıklanıyor ve yabancı semboller temizleniyor..."):
            arama_linki = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama_linki}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # Tüm paragrafları al ve her birini temizle
                    paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 40]
                    
                    if paragraflar:
                        if konu not in st.session_state.gecmis:
                            st.session_state.gecmis.append(konu)
                        
                        st.success(f"✅ {konu} analizi hazır.")
                        
                        # Özet (İlk Paragraf)
                        st.subheader("📌 Özet Bilgi")
                        st.info(paragraflar[0])
                        
                        # Hepsini Göster (Detaylar)
                        tam_metin = "\n\n".join(paragraflar[:15]) # İlk 15 paragrafı al
                        with st.expander("📖 Tüm Detaylı Analizi Gör"):
                            st.write(tam_metin)
                        
                        # PDF İNDİRME (Temizlenmiş Metinle)
                        pdf_data = pdf_olustur(konu, tam_metin[:4000], st.session_state.kullanici_adi)
                        st.download_button("📄 Temizlenmiş Raporu PDF İndir", pdf_data, f"{konu}_Arastirma.pdf", "application/pdf")
                    else:
                        st.warning("Yeterli veri bulunamadı.")
                else:
                    st.error("Konu başlığı Wikipedia'da bulunamadı.")
            except:
                st.error("Bağlantı hatası oluştu.")
    elif konu:
        st.error("⚠️ Lütfen uygun bir başlık giriniz.")

st.sidebar.divider()
st.sidebar.write("**Arama Geçmişi:**")
for g in st.session_state.gecmis[-5:]:
    st.sidebar.caption(f"• {g}")



