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

# --- 🛡️ GELİŞMİŞ GÜVENLİK FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt", "meme", "daşşak", "ibne", "kahpe"]

def guvenli_mi(metin):
    if not metin: return True
    # Kelime benzerliği ve karakter oyunlarını yakalamak için temizleme
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

# --- 📄 KURUMSAL PDF OLUŞTURUCU ---
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

# --- 🎨 CİDDİ ARAYÜZ TASARIMI (CSS) ---
def stil_uygula():
    st.markdown("""
        <style>
        /* Kurumsal Arka Plan */
        .stApp { background-color: #131314; color: #E3E3E3; }
        
        /* Orta Alan Sınırlama (Ciddi Düzen) */
        .main .block-container {
            max-width: 800px;
            padding-top: 4rem;
            padding-bottom: 10rem;
        }

        /* Analiz Kartı */
        .stInfo {
            background-color: #1e1f20;
            border: 1px solid #333537;
            border-radius: 16px;
            padding: 25px;
            font-size: 1.1rem;
            line-height: 1.7;
        }

        /* Sabit Alt Giriş Barı */
        .stChatInputContainer {
            padding-bottom: 20px;
            background-color: #131314;
        }
        
        /* Başlık Stili */
        h1 { 
            color: #ffffff; 
            font-size: 2.2rem; 
            text-align: center; 
            font-weight: 600;
            letter-spacing: -1px;
            margin-bottom: 2rem;
        }

        /* Sidebar Sadelik */
        section[data-testid="stSidebar"] {
            background-color: #1e1f20;
            border-right: 1px solid #333537;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 🚪 GİRİŞ SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI | Kurumsal Giriş", page_icon="🇹🇷")
    stil_uygula()
    st.markdown("<h1>TürkAI Analiz Sistemi</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        isim = st.text_input("Kullanıcı Kimliği:", placeholder="İsminizi giriniz...")
        if st.button("Sisteme Eriş"):
            if len(isim) >= 2:
                st.session_state.kullanici_adi = isim
                st.session_state.giris_yapildi = True
                st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v45.0", page_icon="🇹🇷", layout="wide")
stil_uygula()

# Yan Panel
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.kullanici_adi}")
    st.divider()
    if st.button("Güvenli Çıkış"):
        st.session_state.giris_yapildi = False
        st.rerun()

# ANA EKRAN
st.markdown("<h1>Profesyonel Bilgi Analizi</h1>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    st.markdown(f"### 📋 {st.session_state.su_anki_konu}")
    st.info(st.session_state.analiz_sonucu)
    
    # PDF İndirme Alanı
    pdf_data = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.kullanici_adi)
    st.download_button(
        label="📄 Analiz Raporunu İndir (PDF)",
        data=pdf_data,
        file_name=f"TurkAI_{st.session_state.su_anki_konu}.pdf",
        mime="application/pdf"
    )
else:
    st.markdown("<p style='text-align: center; color: #9aa0a6;'>Araştırmak istediğiniz konuyu aşağıdaki panele yazarak analizi başlatabilirsiniz.</p>", unsafe_allow_html=True)

# --- 📥 ALT ARAMA BARI (KURUMSAL) ---
konu = st.chat_input("Konu başlığını giriniz...")

if konu:
    if not guvenli_mi(konu):
        st.error("⚠️ Uyarı: Uygunsuz içerik veya kural dışı kelime kullanımı tespit edildi.")
    else:
        with st.spinner("Veri tabanı taranıyor..."):
            arama = konu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metni_temizle(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        st.session_state.analiz_sonucu = "\n\n".join(paragraflar[:8])
                        st.session_state.su_anki_konu = konu
                        st.rerun()
                    else:
                        st.error("Konuyla ilgili yeterli veri derinliğine ulaşılamadı.")
                else:
                    st.error("Belirtilen başlık sistem kayıtlarında bulunamadı.")
            except:
                st.error("Bağlantı protokolü hatası.")



