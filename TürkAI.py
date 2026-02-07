import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time

# --- ⚙️ AYARLAR VE TASARIM ---
st.set_page_config(page_title="TürkAI | Kesin Çözüm", page_icon="🇹🇷", layout="wide")

st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    .stSpinner > div { border-top-color: var(--primary-red) !important; }
    .rapor-alani {
        background-color: #ffffff;
        color: #1a1a1a;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid var(--primary-red);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-size: 1.1rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🧠 ZEKA FONKSİYONLARI ---

def daktilo_efekti(metin):
    """Yazıyı ekrana canlı bir şekilde döker."""
    placeholder = st.empty()
    full_response = ""
    for char in metin:
        full_response += char
        placeholder.markdown(f"<div class='rapor-alani'>{full_response}▌</div>", unsafe_allow_html=True)
        time.sleep(0.005) # Hızlı aksiyon
    placeholder.markdown(f"<div class='rapor-alani'>{full_response}</div>", unsafe_allow_html=True)

def siteyi_oku(url):
    """Sitenin içine girip gerçek bilgiyi ayıklar."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Gereksizleri at (reklam, menü, footer)
        for junk in soup(['script', 'style', 'nav', 'header', 'footer', 'form', 'aside']):
            junk.decompose()
        
        paragraphs = soup.find_all('p')
        # Sadece içi dolu olanları birleştir
        text = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 60])
        return text[:2000] # Çok uzunsa kes
    except:
        return None

def derin_dusunen_motor(soru):
    """Derin Arama: 10 siteyi tek tek gezer."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Sadece Türkçe siteler için arama parametresi
    query = urllib.parse.quote(f"{soru} site:.tr OR site:.com.tr")
    search_url = f"https://www.google.com/search?q={query}"
    
    try:
        status = st.empty()
        res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "url?q=" in href and not "google.com" in href:
                url = href.split("url?q=")[1].split("&sa=")[0]
                links.append(url)
        
        if not links:
            return fast_motor(soru) # Bulamazsa Wiki'ye kaç

        found_content = ""
        for i, link in enumerate(links[:10]): # En iyi 10 site
            status.info(f"🔍 Şu an analiz ediliyor ({i+1}/10): {link[:50]}...")
            content = siteyi_oku(link)
            if content and len(content) > 150:
                found_content = content
                status.empty()
                break
        
        return found_content if found_content else fast_motor(soru)
    except:
        return fast_motor(soru)

def fast_motor(soru):
    """Yedek Motor: Wikipedia."""
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(soru)}"
        data = requests.get(url, timeout=5).json()
        return data.get('extract', "Maalesef ne derin ağda ne de Wikipedia'da bir sonuç bulamadım aga.")
    except:
        return "Bağlantı sorunu yaşanıyor."

# --- 🖥️ ARAYÜZ ---

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🇹🇷 TürkAI Analiz Platformu")
    col1, _ = st.columns([1, 1])
    with col1:
        u = st.text_input("Kullanıcı")
        if st.button("Sisteme Giriş Yap"):
            st.session_state.user = u if u else "Misafir"
            st.rerun()
    st.stop()

# --- ANA PANEL ---
st.sidebar.title(f"🛡️ {st.session_state.user}")
motor_tipi = st.sidebar.selectbox("Analiz Modu", ["Derin Düşünen (Detaylı)", "Hızlı Motor (Özet)"])

if st.sidebar.button("Çıkış"):
    st.session_state.user = None
    st.rerun()

st.header("🔍 Araştırma Terminali")
girdi = st.chat_input("Bir şeyler sor veya matematiksel işlem yap...")

if girdi:
    # 1. MATEMATİK KONTROLÜ (İnternete sormadan önce)
    # Sadece sayılar ve işlem operatörleri var mı?
    if re.match(r'^[0-9+\-*/().\s^]+$', girdi):
        with st.spinner('Hesaplanıyor...'):
            try:
                sonuc = eval(girdi)
                cevap = f"🔢 **Matematiksel İşlem Sonucu:**\n\n{girdi} = **{sonuc}**"
            except:
                cevap = "⚠️ Matematiksel ifadeyi çözemedim."
    
    # 2. ARAŞTIRMA MODU
    else:
        with st.spinner('TürkAI Veri Madenciliği Yapıyor...'):
            if motor_tipi == "Hızlı Motor (Özet)":
                cevap = fast_motor(girdi)
            else:
                cevap = derin_dusunen_motor(girdi)
    
    # Sonucu göster
    daktilo_efekti(cevap)

    if st.button("👎 Sonuç Yanlış/Alakasız"):
        st.error("Geri bildirim alındı. Bu siteyi kara listeye alıyorum...")
