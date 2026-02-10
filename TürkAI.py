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
        --primary-color: #800000; /* Lüks Bordo */
        --accent-color: #D4AF37; /* Altın Sarısı */
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
        --text-light: #E0E0E0;
    }
    
    /* Genel Yapı */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Başlıklar */
    h1, h2, h3 {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
    }
    
    h1 { border-bottom: 2px solid var(--accent-color); padding-bottom: 10px; }

    /* Özel Not Kutusu */
    .warning-note {
        background-color: rgba(255, 193, 7, 0.15);
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        color: var(--text-light);
        font-weight: bold;
        margin-bottom: 20px;
        font-size: 1rem;
    }

    /* Butonlar */
    .stButton > button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: 1px solid var(--accent-color) !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #5a0000 !important;
        border-color: #fff !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* Sonuç Kartı */
    .result-card {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
    }
    
    @media (prefers-color-scheme: dark) {
        .result-card {
            background-color: var(--dark-card);
            border-color: #333;
            color: #E0E0E0;
        }
        .warning-note {
            color: #E0E0E0;
        }
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #333;
        color: #666;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v3.db', check_same_thread=False)
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
    # Tırnak işaretleri ve özel karakterler
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    
    mapping = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 
        'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 
        'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
        'â': 'a', 'î': 'i', 'û': 'u'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    
    return text.encode('latin-1', 'replace').decode('latin-1')

def site_tara_brave(url):
    """Brave Browser gibi davranan gelişmiş tarayıcı."""
    try:
        # Brave Browser Header Taklidi
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- BRAVE AD-BLOCK MANTIĞI ---
            # Reklam, script, tracking, pop-up elementlerini temizle
            blacklist = [
                "script", "style", "nav", "footer", "aside", "form", "iframe",
                "div.ads", "div.reklam", "div.banner", "div.cookie-consent", 
                "div.popup", "div.social-share", "header"
            ]
            for tag in blacklist:
                for element in soup.select(tag):
                    element.decompose()
            
            # Metni al ve temizle
            text = soup.get_text(separator='\n')
            
            # Boş satırları sil
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n\n'.join(lines)
            
            # Eğer içerik çok kısaysa (muhtemelen bloklanmıştır veya boş sayfadır)
            if len(clean_text) < 250:
                return None
                
            # Çok uzun metinleri sınırla (PDF patlamasın diye)
            return clean_text[:3000]
            
    except Exception as e:
        return None
    return None

def pdf_olustur_pro(baslik, icerik):
    """Hatasız PDF Oluşturucu."""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Başlık
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(128, 0, 0) # Bordo
        pdf.cell(0, 10, tr_karakter_duzelt("TURKAI ANALIZ RAPORU"), ln=True, align='C')
        pdf.set_draw_color(212, 175, 55) # Altın
        pdf.line(10, 25, 200, 25)
        pdf.ln(20)
        
        # Bilgiler
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 10, tr_karakter_duzelt(f"Konu: {baslik}"), ln=True)
        pdf.cell(40, 10, tr_karakter_duzelt(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}"), ln=True)
        pdf.ln(10)
        
        # İçerik
        pdf.set_font("Arial", '', 11)
        temiz_icerik = tr_karakter_duzelt(icerik)
        pdf.multi_cell(0, 6, temiz_icerik)
        
        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, tr_karakter_duzelt("TurkAI Profesyonel Arastirma Terminali - 2026"), align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        return None

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; border: 2px solid #800000; padding: 40px; border-radius: 10px; background-color: var(--dark-card);'>
            <h1 style='color: #800000; font-size: 3rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #888; font-size: 1.2rem;'>Profesyonel Araştırma Terminali</p>
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
                    if c.fetchone():
                        st.session_state.user = u
                        st.rerun()
                    else:
                        st.error("Hatalı bilgiler.")
            with c2:
                # MİSAFİR GİRİŞİ BUTONU
                if st.button("Misafir Girişi", use_container_width=True, type="secondary"):
                    st.session_state.user = "Misafir"
                    st.rerun()

        with tab2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kayıt başarılı. Giriş yapabilirsiniz.")
                except:
                    st.error("Kullanıcı adı alınmış.")

        st.markdown(f'<a href="{APK_URL}" style="text-decoration:none;"><button style="width:100%; background-color:#333; color:white; padding:10px; border-radius:5px; margin-top:20px; border:none; cursor:pointer;">📱 Mobil Uygulamayı İndir</button></a>', unsafe_allow_html=True)
        
        # Giriş Ekranı Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #666; font-size: 0.8rem;'>
            <p>2026 © Tüm Hakları Saklıdır.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()

# --- 🖥️ ANA ARAYÜZ ---

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ KONTROL PANELİ")
    st.write(f"👤 **Aktif:** {st.session_state.user}")
    
    if st.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()
        
    st.divider()
    
    st.subheader("🧮 Hesap Makinesi")
    calc_exp = st.text_input("İşlem (Örn: 125*18)", key="calc_input")
    if st.button("Hesapla"):
        try:
            allowed = set("0123456789+-*/.()")
            if set(calc_exp) <= allowed:
                st.session_state.hesap_sonuc = str(eval(calc_exp))
            else:
                st.session_state.hesap_sonuc = "Hata"
        except:
            st.session_state.hesap_sonuc = "Hata"
    
    if st.session_state.hesap_sonuc:
        st.info(f"Sonuç: {st.session_state.hesap_sonuc}")

    st.divider()
    st.markdown(f'<a href="{APK_URL}" style="text-decoration:none;">📱 Android Uygulama</a>', unsafe_allow_html=True)

# Main Content
st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")

# İSTENİLEN UYARI NOTU
st.markdown("""
<div class='warning-note'>
    ⚠️ Not: Araştırmak istediğiniz konunun ANAHTAR KELİMESİNİ yazınız. (Örn: Türk kimdir?❌ Türk✅)
</div>
""", unsafe_allow_html=True)

col_sorgu, col_motor = st.columns([3, 1])

with col_sorgu:
    sorgu = st.text_input("Araştırma Konusu:", placeholder="Konuyu buraya yazın...")

with col_motor:
    motor_tipi = st.selectbox("Motor Seçimi", ["🚀 Hızlı Motor (V1)", "🧠 Derin Motor (V2)"])

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary", use_container_width=True):
    if not sorgu:
        st.warning("Lütfen bir konu giriniz.")
    else:
        st.session_state.konu = sorgu.strip()
        st.session_state.arama_yapildi = True
        st.session_state.aktif_site_index = 0
        st.session_state.bilgi = None
        
        # URL Listesi Oluşturma (İki motor için farklı listeler)
        q = urllib.parse.quote(st.session_state.konu)
        
        if "Hızlı" in motor_tipi:
            # V1: Hızlı, güvenilir, sözlük ve ansiklopedi ağırlıklı
            st.session_state.url_listesi = [
                f"https://tr.wikipedia.org/wiki/{q}",
                f"https://sozluk.gov.tr/gts?ara={q}",
                f"https://www.turkcebilgi.com/{q}",
                f"https://www.nedir.com/{q}",
                f"https://www.etimolojiturkce.com/kelime/{q}"
            ]
        else:
            # V2: Derin, makale, biyografi ve detay ağırlıklı
            st.session_state.url_listesi = [
                f"https://www.biyografi.info/kisi/{q}",
                f"https://tr.wikipedia.org/wiki/{q}",
                f"https://dergipark.org.tr/tr/search?q={q}",
                f"https://islamansiklopedisi.org.tr/ara?q={q}",
                f"https://www.kimkimdir.gen.tr/ara/{q}",
                f"https://1000kitap.com/ara?q={q}"
            ]
        st.rerun()

# --- ARAMA SONUÇLARI VE DÖNGÜSÜ ---
if st.session_state.arama_yapildi:
    urls = st.session_state.url_listesi
    idx = st.session_state.aktif_site_index
    
    if idx < len(urls):
        current_url = urls[idx]
        
        # Kullanıcıya bilgi ver
        st.info(f"🔎 {motor_tipi} ile taranıyor... (Kaynak {idx+1}/{len(urls)})")
        st.write(f"🔗 Adres: {current_url}")
        
        with st.spinner('Veriler analiz ediliyor, reklamlar engelleniyor...'):
            bulunan_veri = site_tara_brave(current_url)
            
            if bulunan_veri:
                # Veri Bulundu
                st.session_state.bilgi = bulunan_veri
                
                # Kart Görünümü
                st.markdown(f"""
                <div class='result-card'>
                    <h3 style='border-bottom:1px solid #ddd; padding-bottom:10px;'>✅ Analiz Sonucu</h3>
                    <div style='max-height: 400px; overflow-y: auto; white-space: pre-wrap;'>{bulunan_veri}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Aksiyon Butonları
                col_pdf, col_next = st.columns(2)
                
                with col_pdf:
                    pdf_data = pdf_olustur_pro(st.session_state.konu, bulunan_veri)
                    if pdf_data:
                        st.download_button(
                            label="📄 Bu Sonucu PDF İndir",
                            data=pdf_data,
                            file_name=f"TurkAI_Rapor_{st.session_state.konu}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                with col_next:
                    if st.button("🔄 Bu Kaynağı Beğenmedim, Sonrakine Geç", use_container_width=True):
                        st.session_state.aktif_site_index += 1
                        st.rerun()
                        
            else:
                # Veri bulunamadıysa otomatik geç
                time.sleep(0.5)
                st.session_state.aktif_site_index += 1
                st.rerun()
    else:
        st.error("❌ Mevcut kaynakların tamamı tarandı. Daha fazla sonuç bulunamadı.")
        if st.button("Aramayı Sıfırla"):
            st.session_state.arama_yapildi = False
            st.session_state.aktif_site_index = 0
            st.rerun()

# --- FOOTER ---
st.markdown("""
    <div class='footer'>
        <p>&copy; 2026 TürkAI Profesyonel Sistemler | Tüm Hakları Saklıdır.</p>
        <p>Gelişmiş Türkçe Araştırma Motoru</p>
    </div>
""", unsafe_allow_html=True)
