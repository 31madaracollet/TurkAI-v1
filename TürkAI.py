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

# --- 🔗 GITHUB DIREKT INDIRME LİNKİ ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 PROFESYONEL TASARIM (LÜKS & CİDDİ) ---
st.markdown("""
    <style>
    :root {
        --primary-color: #800000; /* Lüks Bordo */
        --accent-color: #D4AF37; /* Altın Sarısı */
        --dark-bg: #121212;
        --dark-card: #1E1E1E;
        --text-light: #E0E0E0;
        --text-dark: #212121;
        --border-radius: 8px;
    }
    
    /* Genel Yapı */
    .stApp {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* Başlıklar */
    h1, h2, h3 {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
    }
    
    h1 { border-bottom: 2px solid var(--accent-color); padding-bottom: 10px; }

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

    /* Kartlar ve Kutular */
    .info-box {
        background-color: rgba(212, 175, 55, 0.1);
        border-left: 4px solid var(--accent-color);
        padding: 15px;
        margin: 15px 0;
        border-radius: 4px;
        font-size: 0.95rem;
    }

    .result-card {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: var(--border-radius);
        margin-top: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Karanlık Mod Desteği için Manuel Ayar */
    @media (prefers-color-scheme: dark) {
        .result-card {
            background-color: var(--dark-card);
            border-color: #333;
            color: var(--text-light);
        }
    }

    /* Sidebar Hesap Makinesi */
    .calc-input { margin-bottom: 10px; }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #ccc;
        color: #666;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "aktif_site_index" not in st.session_state: st.session_state.aktif_site_index = 0
if "arama_yapildi" not in st.session_state: st.session_state.arama_yapildi = False
if "mevcut_motor" not in st.session_state: st.session_state.mevcut_motor = "V1"
if "hesap_sonuc" not in st.session_state: st.session_state.hesap_sonuc = ""

# --- 🛠 YARDIMCI FONKSİYONLAR ---

def tr_karakter_duzelt(text):
    """PDF için Türkçe karakterleri Latin karakterlere çevirir."""
    if not text: return ""
    text = str(text)
    mapping = {
        'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 
        'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 
        'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
        'â': 'a', 'î': 'i', 'û': 'u'
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    
    # Desteklenmeyen diğer karakterleri temizle
    return text.encode('latin-1', 'replace').decode('latin-1')

def site_tara(url, sorgu):
    """Basit ve etkili site tarayıcı."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Gereksizleri at
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Basit içerik kontrolü
            if len(text) > 200:
                return text[:1500] # Çok uzun metinleri kes
            return None
    except:
        return None
    return None

def pdf_olustur_pro(baslik, icerik):
    """Hatasız PDF Oluşturucu."""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Başlık
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, tr_karakter_duzelt("TÜRKAI ANALIZ RAPORU"), ln=True, align='C')
        pdf.line(10, 25, 200, 25)
        pdf.ln(20)
        
        # Bilgiler
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
        pdf.cell(0, 10, tr_karakter_duzelt("TurkAI Profesyonel Arastirma Sistemi - 2026"), align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF Hatasi: {str(e)}")
        return None

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; border: 2px solid #800000; padding: 40px; border-radius: 10px; background-color: var(--card-color);'>
            <h1 style='color: #800000; font-size: 3rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #555; font-size: 1.2rem; font-style: italic;'>Profesyonel Araştırma Çözümleri</p>
            <hr style='border-color: #D4AF37;'>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        
        with tab1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                h = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                if c.fetchone():
                    st.session_state.user = u
                    st.rerun()
                else:
                    st.error("Hatalı bilgiler.")

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

        st.markdown(f'<a href="{APK_URL}" style="text-decoration:none;"><button style="width:100%; background-color:#333; color:white; padding:10px; border-radius:5px; margin-top:20px;">📱 Mobil Uygulamayı İndir</button></a>', unsafe_allow_html=True)
        st.stop()

# --- 🖥️ ANA ARAYÜZ (Giriş Yapıldıktan Sonra) ---

# Sidebar
with st.sidebar:
    st.title("🎛️ KONTROL PANELİ")
    st.write(f"👤 **Aktif Kullanıcı:** {st.session_state.user}")
    
    if st.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()
        
    st.divider()
    
    st.subheader("🧮 Hesap Makinesi")
    calc_exp = st.text_input("İşlem (Örn: 125*18)", key="calc_input")
    if st.button("Hesapla"):
        try:
            # Güvenlik için sadece sayı ve işlem karakterlerine izin ver
            allowed = set("0123456789+-*/.()")
            if set(calc_exp) <= allowed:
                st.session_state.hesap_sonuc = str(eval(calc_exp))
            else:
                st.session_state.hesap_sonuc = "Hata: Geçersiz karakter"
        except:
            st.session_state.hesap_sonuc = "Hata"
    
    if st.session_state.hesap_sonuc:
        st.markdown(f"<div style='background-color:#eee; padding:10px; border-radius:5px; color:#000; font-weight:bold; text-align:center;'>Sonuç: {st.session_state.hesap_sonuc}</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown(f'<a href="{APK_URL}" style="text-decoration:none;">📱 Android Uygulama</a>', unsafe_allow_html=True)

# Main Area
st.title("PROFESYONEL ARAŞTIRMA TERMİNALİ")

arama_motoru = st.radio("Araştırma Modu Seçin:", ["🚀 Birleşik Motor (Hızlı)", "🧠 Derin Düşünen (Detaylı Sıralı)"], horizontal=True)

sorgu = st.text_input("Araştırma Konusu:", placeholder="Örn: Yapay Zeka Tarihçesi")

if st.button("ARAŞTIRMAYI BAŞLAT", type="primary"):
    if not sorgu:
        st.warning("Lütfen bir konu giriniz.")
    else:
        st.session_state.konu = sorgu
        st.session_state.arama_yapildi = True
        st.session_state.aktif_site_index = 0 # Aramayı sıfırla
        st.session_state.bilgi = None
        
        if "Derin" in arama_motoru:
            st.session_state.mevcut_motor = "V2"
        else:
            st.session_state.mevcut_motor = "V1"
        st.rerun()

# --- 🧠 DERİN DÜŞÜNEN MANTIĞI ---
if st.session_state.arama_yapildi and st.session_state.mevcut_motor == "V2":
    konu_url = urllib.parse.quote(st.session_state.konu)
    
    # Sıralı Kaynak Listesi
    kaynaklar = [
        f"https://tr.wikipedia.org/wiki/{konu_url}",
        f"https://www.turkcebilgi.com/{konu_url}",
        f"https://www.nedir.com/{konu_url}",
        f"https://www.biyografi.info/kisi/{konu_url}",
        f"https://sozluk.gov.tr/gts?ara={konu_url}",
        f"https://dergipark.org.tr/tr/search?q={konu_url}",
        f"https://www.google.com/search?q={konu_url}" # Fallback
    ]
    
    mevcut_index = st.session_state.aktif_site_index
    
    if mevcut_index < len(kaynaklar):
        url = kaynaklar[mevcut_index]
        st.info(f"Derin Düşünen Analiz Ediyor... (Kaynak {mevcut_index + 1}/{len(kaynaklar)}): {url}")
        
        with st.spinner('Veriler çekiliyor ve işleniyor...'):
            bulunan_veri = site_tara(url, st.session_state.konu)
            
            if bulunan_veri:
                st.session_state.bilgi = bulunan_veri
                
                st.markdown(f"""
                <div class='result-card'>
                    <h3>✅ Sonuç Bulundu (Kaynak: {url})</h3>
                    <p>{bulunan_veri}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    pdf_data = pdf_olustur_pro(st.session_state.konu, bulunan_veri)
                    if pdf_data:
                        st.download_button(
                            label="📄 Raporu PDF Olarak İndir",
                            data=pdf_data,
                            file_name=f"TurkAI_Rapor_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                with col_b:
                    if st.button("🔄 Bu Kaynağı Beğenmedim, Sıradakine Geç"):
                        st.session_state.aktif_site_index += 1
                        st.rerun()
            else:
                # Veri bulamazsa otomatik sonrakine geç
                time.sleep(1)
                st.session_state.aktif_site_index += 1
                st.rerun()
    else:
        st.error("Tüm kaynaklar tarandı ancak anlamlı bir sonuç bulunamadı veya listenin sonuna gelindi.")
        if st.button("Başa Dön"):
            st.session_state.aktif_site_index = 0
            st.rerun()

# --- 🚀 BİRLEŞİK MOTOR MANTIĞI ---
elif st.session_state.arama_yapildi and st.session_state.mevcut_motor == "V1":
    with st.spinner('Hızlı arama yapılıyor...'):
        # Basit Wikipedia API
        try:
            api_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(st.session_state.konu)}"
            res = requests.get(api_url)
            if res.status_code == 200:
                data = res.json()
                icerik = data.get('extract', 'İçerik yok.')
                st.session_state.bilgi = icerik
                
                st.markdown(f"""
                <div class='result-card'>
                    <h3>📚 Vikipedi Özeti</h3>
                    <p>{icerik}</p>
                </div>
                """, unsafe_allow_html=True)
                
                pdf_data = pdf_olustur_pro(st.session_state.konu, icerik)
                if pdf_data:
                    st.download_button(
                        label="📄 PDF İndir",
                        data=pdf_data,
                        file_name="arastirma_ozet.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("Hızlı aramada sonuç bulunamadı. 'Derin Düşünen' modunu deneyin.")
        except:
            st.error("Bağlantı hatası.")

# --- FOOTER ---
st.markdown("""
    <div class='footer'>
        <p>&copy; 2026 TürkAI Profesyonel Sistemler | Lüks & Güvenli Araştırma</p>
        <p>Coded with ❤️ by TürkAI Team</p>
    </div>
""", unsafe_allow_html=True)
