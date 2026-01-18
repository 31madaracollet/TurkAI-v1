import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF

# --- 🧠 SİSTEM HAFIZASI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "analiz_sonucu" not in st.session_state:
    st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state:
    st.session_state.su_anki_konu = ""

# --- 🛡️ ZIRHLI GÜVENLİK FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt", "meme", "daşşak", "ibne", "kahpe"]

def guvenli_mi(metin):
    if not metin: return True
    # Harf benzerliklerini ve boşluklu yazımları yakalar
    temiz_metin = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    for kelime in KARA_LISTE:
        if kelime in temiz_metin:
            return False
    return True

# --- 🧹 WIKIPEDIA TEMİZLİK ---
def metni_temizle(metin):
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    metin = metin.replace('\xa0', ' ')
    return metin.strip()

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik, kullanici):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="TurkAI Analiz Raporu", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    def safe(s): return s.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe(f"Konu: {baslik}\nArastirmaci: {kullanici}\n\n{icerik}"))
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 HİBRİT ARAYÜZ (GÜNDÜZ/GECE UYUMLU) ---
def stil_uygula():
    st.markdown("""
        <style>
        /* Ana Konteynır Ayarı */
        .main .block-container {
            max-width: 850px;
            padding-top: 3rem;
            padding-bottom: 10rem;
        }

        /* Kurumsal Analiz Kartı - Hem açık hem koyu temada okunabilir */
        .stInfo {
            border-radius: 16px;
            padding: 25px;
            font-size: 1.1rem;
            line-height: 1.7;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        /* Başlıklar */
        h1 { 
            text-align: center; 
            font-weight: 700;
            margin-bottom: 2rem;
        }

        /* Sabit Alt Bar (Gemini Stili) */
        .stChatInputContainer {
            padding-bottom: 25px;
        }
        
        /* PDF Butonu Estetiği */
        .stDownloadButton>button {
            border-radius: 12px;
            padding: 0.5rem 2rem;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI | Giriş", page_icon="🇹🇷")
    stil_uygula()
    st.title("🇹🇷 TürkAI Analiz")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        isim = st.text_input("Kimliğinizi Tanımlayın:", placeholder="İsim...")
        if st.button("Sistemi Aç"):
            if len(isim) >= 2:
                st.session_state.kullanici_adi = isim
                st.session_state.giris_yapildi = True
                st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0", page_icon="🇹🇷", layout="wide")
stil_uygula()

# Yan Panel (Sade ve Ciddi)
with st.sidebar:
    st.markdown(f"### 🛡️ Oturum: {st.session_state.kullanici_adi}")
    st.divider()
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

# ANA EKRAN
st.markdown("<h1>Profesyonel Bilgi Hattı</h1>", unsafe_allow_html=True)

# Eğer bir analiz yapıldıysa ekranda göster
if st.session_state.analiz_sonucu:
    st.markdown(f"### 📋 Analiz: {st.session_state.su_anki_konu}")
    st.info(st.session_state.analiz_sonucu)
    
    # PDF Butonu tam cevabın bittiği yerde
    pdf_data = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.kullanici_adi)
    st.download_button(
        label="📄 Raporu PDF Olarak İndir",
        data=pdf_data,
        file_name=f"TurkAI_{st.session_state.su_anki_konu}.pdf",
        mime="application/pdf"
    )
else:
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Merak ettiğiniz konuyu aşağıya yazarak kurumsal analizi başlatabilirsiniz.</p>", unsafe_allow_html=True)

# --- 📥 SABİT ALT BAR (EN ALTA ÇAKILI) ---
konu = st.chat_input("Analiz edilecek konuyu buraya yazın...")

if konu:
    if not guvenli_mi(konu):
        st.error("⚠️ Uyarı: Sistemsel kural ihlali (Uygunsuz içerik).")
    else:
        with st.spinner("Veri madenciliği yapılıyor..."):
            arama = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        # İlk 8 paragrafı alarak doyurucu bir özet sunuyoruz (Silmedik, güncelledik)
                        st.session_state.analiz_sonucu = "\n\n".join(paragraflar[:8])
                        st.session_state.su_anki_konu = konu
                        st.rerun()
                    else:
                        st.error("Konu hakkında yeterli derinlikte veri bulunamadı.")
                else:
                    st.error("Aranan başlık literatürde bulunamadı.")
            except:
                st.error("Ağ bağlantısı kurulamadı.")


