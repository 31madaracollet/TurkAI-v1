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
import json

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔗 MOBİL UYGULAMA LİNKİ ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 TASARIM (CİDDİ & LÜKS) ---
st.markdown("""
    <style>
    :root {
        --primary-color: #800000;
        --accent-color: #D4AF37;
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
        --text-light: #E0E0E0;
    }
    .stApp { font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: var(--primary-color) !important; font-weight: 700 !important; }
    h1 { border-bottom: 2px solid var(--accent-color); padding-bottom: 10px; }
    
    .warning-note {
        background-color: rgba(255, 193, 7, 0.15);
        border-left: 5px solid #ffc107;
        padding: 15px; border-radius: 5px;
        color: var(--text-light); font-weight: bold; margin-bottom: 20px;
    }
    
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: 1px solid var(--accent-color) !important;
    }
    
    /* Sonuç Kartı Tasarımı */
    .result-card {
        background-color: #f8f9fa; border: 1px solid #ddd; padding: 25px;
        border-radius: 8px; margin-top: 20px; color: #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .source-badge {
        background-color: var(--accent-color); color: #000;
        padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;
        margin-bottom: 10px; display: inline-block;
    }
    
    @media (prefers-color-scheme: dark) {
        .result-card { background-color: var(--dark-card); border-color: #333; color: #E0E0E0; }
        .warning-note { color: #E0E0E0; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "aktif_site_index" not in st.session_state: st.session_state.aktif_site_index = 0
if "arama_yapildi" not in st.session_state: st.session_state.arama_yapildi = False
if "url_listesi" not in st.session_state: st.session_state.url_listesi = []
if "hesap_sonuc" not in st.session_state: st.session_state.hesap_sonuc = ""

# --- 🛠 YARDIMCI FONKSİYONLAR ---

def tr_karakter_duzelt(text):
    """PDF için Türkçe karakter düzeltmesi."""
    if not text: return ""
    text = str(text)
    mapping = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c', 'â': 'a', 'î': 'i', 'û': 'u'}
    for k, v in mapping.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def tdk_parser(json_data):
    """TDK JSON verisini okunaklı hale getirir."""
    try:
        text_output = ""
        if isinstance(json_data, list) and len(json_data) > 0:
            madde = json_data[0]
            baslik = madde.get('madde', '')
            text_output += f"📚 TDK SÖZLÜK: {baslik.upper()}\n\n"
            
            if 'anlamlarListe' in madde:
                for i, anlam in enumerate(madde['anlamlarListe']):
                    tanim = anlam.get('anlam', '')
                    text_output += f"{i+1}. {tanim}\n"
                    if 'orneklerListe' in anlam:
                        ornek = anlam['orneklerListe'][0].get('ornek', '')
                        text_output += f"   ➔ Örnek: '{ornek}'\n"
                    text_output += "\n"
            
            if 'atasozu' in madde:
                text_output += "💡 ATASÖZLERİ & DEYİMLER:\n"
                for ata in madde['atasozu']:
                    text_output += f"- {ata.get('madde')}\n"
        return text_output
    except:
        return "TDK verisi çözümlenemedi."

def site_tara_brave(url):
    """Gelişmiş Tarayıcı ve Temizleyici (HTML & JSON)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=8)
        
        # 1. TDK ÖZEL AYRIŞTIRMA (JSON)
        if "sozluk.gov.tr" in url:
            try:
                return tdk_parser(response.json())
            except:
                pass # JSON değilse devam et

        # 2. STANDART HTML AYRIŞTIRMA
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Gereksiz elementleri sil (Reklam, menü, script)
            blacklist = ["script", "style", "nav", "footer", "form", "iframe", "div.ads", "div.reklam", "header", ".mw-editsection", ".reference"]
            for tag in blacklist:
                for element in soup.select(tag):
                    element.decompose()

            # İÇERİK SEÇİCİLER (Siteye göre odaklan)
            content_text = ""
            
            if "wikipedia.org" in url:
                # Sadece makale içeriğini al
                content_div = soup.find(id="mw-content-text")
                if content_div:
                    content_text = content_div.get_text(separator='\n')
                    # Vikipedi temizliği: [1], [değiştir] vb. sil
                    content_text = re.sub(r'\[\d+\]', '', content_text)
                    content_text = re.sub(r'\[değiştir \| kaynağı değiştir\]', '', content_text)
            
            elif "islamansiklopedisi" in url:
                # TDV Arama sayfası gürültüsü temizliği
                results = soup.find_all(class_="search-result-item")
                if results:
                    content_text = "🔎 İSLAM ANSİKLOPEDİSİ SONUÇLARI:\n\n"
                    for res in results[:3]: # İlk 3 sonucu getir
                        baslik = res.find("h3").get_text(strip=True) if res.find("h3") else ""
                        ozet = res.find("p").get_text(strip=True) if res.find("p") else ""
                        content_text += f"📌 {baslik}\n{ozet}\n\n"
                else:
                     content_text = soup.get_text(separator='\n')
            
            else:
                # Genel Haber Siteleri
                content_text = soup.get_text(separator='\n')

            # Genel Temizlik
            lines = [line.strip() for line in content_text.splitlines() if line.strip()]
            clean_text = '\n\n'.join(lines)
            
            # İslam Ansiklopedisi arama arayüzü çöplerini (Alfabe vb.) temizle
            if "islamansiklopedisi" in url:
                clean_text = re.sub(r'x\s+"[\d\s\w\n]+ABC', '', clean_text)
            
            if len(clean_text) < 150: return None
            return clean_text[:4000] # Çok uzun metinleri kes
            
    except Exception as e:
        return None
    return None

def pdf_olustur_pro(baslik, icerik):
    """Hatasız PDF Oluşturucu."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(128, 0, 0)
        pdf.cell(0, 10, tr_karakter_duzelt("TURKAI ANALIZ RAPORU"), ln=True, align='C')
        pdf.line(10, 25, 200, 25)
        pdf.ln(20)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 10, tr_karakter_duzelt(f"Konu: {baslik}"), ln=True)
        pdf.cell(40, 10, tr_karakter_duzelt(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}"), ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, tr_karakter_duzelt(icerik))
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, tr_karakter_duzelt("TurkAI Profesyonel Arastirma Terminali - 2026"), align='C')
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; border: 2px solid #800000; padding: 40px; border-radius: 10px; background-color: var(--dark-card);'>
            <h1 style='color: #800000; font-size: 3rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #888; font-size: 1.2rem;'>Gelişmiş Biyografi & Haber Terminali</p>
            <hr style='border-color: #D4AF37;'>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        with tab1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sisteme Gir", use_container_width=True):
                    h = hashlib.sha256(p.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                    if c.fetchone(): st.session_state.user = u; st.rerun()
                    else: st.error("Hatalı bilgiler.")
            with c2:
                if st.button("Misafir Girişi", use_container_width=True, type="secondary"):
                    st.session_state.user = "Misafir"; st.rerun()
        with tab2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try: c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest())); conn.commit(); st.success("Kayıt başarılı.");
                except: st.error("Kullanıcı adı alınmış.")
        st.stop()

# --- 🖥️ ANA ARAYÜZ ---
with st.sidebar:
    st.markdown("### 🎛️ KONTROL PANELİ")
    st.write(f"👤 **Aktif:** {st.session_state.user}")
    if st.button("Çıkış Yap"): st.session_state.user = None; st.rerun()
    st.divider()
    st.subheader("🧮 Hesap Makinesi")
    calc_exp = st.text_input("İşlem", key="calc_input")
    if st.button("Hesapla"):
        try: st.session_state.hesap_sonuc = str(eval(calc_exp))
        except: st.session_state.hesap_sonuc = "Hata"
    if st.session_state.hesap_sonuc: st.info(f"Sonuç: {st.session_state.hesap_sonuc}")
    st.divider()
    st.markdown(f'<a href="{APK_URL}"><button style="width:100%;">📱 Android Uygulama</button></a>', unsafe_allow_html=True)

st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")
st.markdown("""<div class='warning-note'>⚠️ Not: Araştırmak istediğiniz konunun ANAHTAR KELİMESİNİ yazınız. (Örn: Türk kimdir?❌ Türk✅)</div>""", unsafe_allow_html=True)

col_sorgu, col_motor = st.columns([3, 1])
with col_sorgu: sorgu = st.text_input("Araştırma Konusu:", placeholder="Örn: Sucuk, Fatih Sultan Mehmet, Enflasyon...")
with col_motor: motor_tipi = st.selectbox("Motor Seçimi", ["🚀 Ansiklopedik (V1)", "🌍 Gündem & Haber (V2)"])

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary", use_container_width=True):
    if not sorgu: st.warning("Lütfen bir konu giriniz.")
    else:
        st.session_state.konu = sorgu.strip()
        st.session_state.arama_yapildi = True
        st.session_state.aktif_site_index = 0
        st.session_state.bilgi = None
        q = urllib.parse.quote(st.session_state.konu)
        
        if "Ansiklopedik" in motor_tipi:
            # V1: TDK, Vikipedi, İslam Ansiklopedisi, Biyografi
            st.session_state.url_listesi = [
                f"https://sozluk.gov.tr/gts?ara={q}", # TDK JSON
                f"https://tr.wikipedia.org/wiki/{q}",
                f"https://islamansiklopedisi.org.tr/ara?q={q}",
                f"https://www.biyografi.info/kisi/{q}",
                f"https://www.turkcebilgi.com/{q}"
            ]
        else:
            # V2: Güncel Haberler ve Gündem
            st.session_state.url_listesi = [
                f"https://www.bbc.com/turkce/search?q={q}",
                f"https://www.trthaber.com/haber/ara/?q={q}",
                f"https://www.ensonhaber.com/arama?q={q}",
                f"https://www.hurriyet.com.tr/arama/?q={q}",
                f"https://tr.wikipedia.org/wiki/{q}" # Yedek olarak ansiklopedi
            ]
        st.rerun()

if st.session_state.arama_yapildi:
    urls = st.session_state.url_listesi
    idx = st.session_state.aktif_site_index
    
    if idx < len(urls):
        current_url = urls[idx]
        domain_name = urllib.parse.urlparse(current_url).netloc.replace("www.", "")
        
        st.info(f"🔎 {motor_tipi} | Kaynak: {domain_name} taranıyor...")
        
        with st.spinner('Veriler temizleniyor ve düzenleniyor...'):
            bulunan_veri = site_tara_brave(current_url)
            
            if bulunan_veri:
                st.session_state.bilgi = bulunan_veri
                st.markdown(f"""
                <div class='result-card'>
                    <div class='source-badge'>📌 Kaynak: {domain_name.upper()}</div>
                    <div style='max-height: 500px; overflow-y: auto; white-space: pre-wrap; font-size: 1.05rem;'>{bulunan_veri}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_pdf, col_next = st.columns(2)
                with col_pdf:
                    pdf_data = pdf_olustur_pro(st.session_state.konu, bulunan_veri)
                    if pdf_data: st.download_button("📄 PDF Olarak İndir", pdf_data, f"TurkAI_{st.session_state.konu}.pdf", "application/pdf", use_container_width=True)
                with col_next:
                    if st.button("🔄 Bu Kaynağı Beğenmedim, Sıradaki", use_container_width=True):
                        st.session_state.aktif_site_index += 1; st.rerun()
            else:
                time.sleep(0.5); st.session_state.aktif_site_index += 1; st.rerun()
    else:
        st.error("❌ Tüm kaynaklar tarandı. Daha fazla sonuç yok.")
        if st.button("Sıfırla"): st.session_state.arama_yapildi = False; st.session_state.aktif_site_index = 0; st.rerun()

st.markdown("<div class='footer'><p>&copy; 2026 TürkAI | Gelişmiş Haber & Araştırma</p></div>", unsafe_allow_html=True)
