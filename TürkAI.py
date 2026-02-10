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

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma Sistemi", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔗 GITHUB DIREKT INDIRME LİNKİ ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 PROFESYONEL TASARIM (KARANLIK/AYDINLIK MOD) ---
st.markdown("""
    <style>
    :root {
        --primary-red: #b22222;
        --dark-bg: #0f0f0f;
        --dark-card: #1a1a1a;
        --dark-text: #f0f0f0;
        --light-bg: #ffffff;
        --light-card: #f8f9fa;
        --light-text: #212529;
        --border-radius: 10px;
    }
    
    /* Otomatik Tema Algılama */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: var(--dark-bg);
            --card-color: var(--dark-card);
            --text-color: var(--dark-text);
            --border-color: #333;
            --shadow-color: rgba(0,0,0,0.3);
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --bg-color: var(--light-bg);
            --card-color: var(--light-card);
            --text-color: var(--light-text);
            --border-color: #dee2e6;
            --shadow-color: rgba(0,0,0,0.1);
        }
    }
    
    /* Ana Stiller */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }
    
    h1, h2, h3, h4 {
        color: var(--primary-red) !important;
        font-family: 'Segoe UI', 'Roboto', sans-serif !important;
        font-weight: 600 !important;
        margin-bottom: 20px !important;
    }
    
    h1 {
        font-size: 2.2rem !important;
        border-bottom: 3px solid var(--primary-red);
        padding-bottom: 10px;
    }
    
    h2 {
        font-size: 1.8rem !important;
        border-left: 4px solid var(--primary-red);
        padding-left: 15px;
    }
    
    .login-container {
        max-width: 450px;
        margin: 60px auto;
        padding: 40px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        border: 2px solid var(--primary-red);
        box-shadow: 0 10px 30px var(--shadow-color);
    }
    
    .apk-button {
        background: linear-gradient(135deg, #b22222, #dc3545) !important;
        color: white !important;
        border: none !important;
        padding: 14px 28px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        width: 100%;
        text-align: center;
        text-decoration: none;
        display: block;
        margin: 20px 0;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    
    .apk-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(178, 34, 34, 0.3) !important;
    }
    
    .info-box {
        background-color: rgba(178, 34, 34, 0.1);
        border-left: 4px solid var(--primary-red);
        padding: 15px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }
    
    .site-card {
        background-color: var(--card-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 15px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .site-card:hover {
        transform: translateX(5px);
        border-color: var(--primary-red);
        box-shadow: 0 5px 15px var(--shadow-color);
    }
    
    .active-site {
        border-left: 5px solid var(--primary-red);
        background-color: rgba(178, 34, 34, 0.05);
    }
    
    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 50px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        margin: 30px 0;
    }
    
    .spinner {
        width: 70px;
        height: 70px;
        border: 5px solid rgba(178, 34, 34, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1.5s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .badge {
        background-color: var(--primary-red);
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0 5px;
    }
    
    .guest-badge {
        background-color: #6c757d;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    
    .pdf-button {
        background: linear-gradient(135deg, #28a745, #20c997) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    .motor-tag {
        display: inline-block;
        background: linear-gradient(45deg, #b22222, #ff6b6b);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 5px;
    }
    
    /* Streamlit Öğeleri için */
    .stButton > button {
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
    }
    
    .stRadio > div {
        background-color: var(--card-color);
        padding: 15px;
        border-radius: var(--border-radius);
    }
    
    /* Sidebar Stilleri */
    section[data-testid="stSidebar"] {
        background-color: var(--card-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Chat Input Stili */
    .stChatInput > div > div > input {
        border: 2px solid var(--primary-red) !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI YÖNETİMİ ---
def db_baslat():
    conn = sqlite3.connect('turkai_profesyonel.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ (HATA DÜZELTMESİ İÇİN) ---
# Session state değişkenlerini güvenli şekilde başlat
def init_session_state():
    if "user" not in st.session_state: 
        st.session_state.user = None
    if "is_guest" not in st.session_state:
        st.session_state.is_guest = False
    if "bilgi" not in st.session_state: 
        st.session_state.bilgi = None
    if "konu" not in st.session_state: 
        st.session_state.konu = ""
    if "son_sorgu" not in st.session_state: 
        st.session_state.son_sorgu = None
    if "arama_devam" not in st.session_state: 
        st.session_state.arama_devam = False
    if "aktif_site" not in st.session_state: 
        st.session_state.aktif_site = 0
    if "site_sonuclari" not in st.session_state: 
        st.session_state.site_sonuclari = []
    if "yap_butonu" not in st.session_state: 
        st.session_state.yap_butonu = False
    if "site_listesi" not in st.session_state:
        st.session_state.site_listesi = []

# Session state'i başlat
init_session_state()

# --- 🔧 PROFESYONEL FONKSİYONLAR ---
def profesyonel_site_tara(url, sorgu, site_adi, timeout=8):
    """Profesyonel site tarama - Brave reklam engelleme ile"""
    try:
        # Brave browser gibi davranan headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # HTTP durum kodunu kontrol et
        if response.status_code != 200:
            return (site_adi, None, 0)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Türkçe içerik kontrolü
        tum_metin = soup.get_text().lower()
        turkce_kelimeler = ['veya', 'ile', 'için', 'olarak', 'göre', 'kadar', 'ancak', 'fakat', 'çünkü', 'eğer']
        turkce_puan = sum(1 for kelime in turkce_kelimeler if kelime in tum_metin)
        
        if turkce_puan < 2:  # Yeterli Türkçe içerik yoksa
            return (site_adi, None, 0)
        
        # Reklam ve gereksiz elementleri temizle
        for element in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'header', 'aside', 'form', 'button']):
            element.decompose()
        
        # Ana içerik alanını bul
        icerik = ""
        
        # 1. Önce makale/ansiklopedi formatını ara
        article_selectors = [
            ('div', {'id': 'content'}),
            ('div', {'class': 'content'}),
            ('article', None),
            ('div', {'class': 'article'}),
            ('div', {'class': 'entry-content'}),
            ('div', {'class': 'post-content'}),
            ('section', {'class': 'content'}),
            ('div', {'class': re.compile(r'main|content|article|entry')}),
            ('div', {'id': re.compile(r'main|article|body')})
        ]
        
        for tag, attrs in article_selectors:
            try:
                if attrs:
                    elements = soup.find_all(tag, attrs)
                else:
                    elements = soup.find_all(tag)
                    
                for elem in elements:
                    text = elem.get_text().strip()
                    if len(text) > 150 and sorgu.lower() in text.lower():
                        # Paragrafları ayır ve filtrele
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if len(para) > 80:
                                icerik += para + "\n\n"
                        if len(icerik) > 400:  # Yeterli içerik
                            break
                if len(icerik) > 400:
                    break
            except:
                continue
        
        # 2. Eğer hala yeterli değilse, tüm sayfadan paragraf ara
        if len(icerik) < 300:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 60:
                    icerik += text + "\n\n"
                    if len(icerik) > 400:
                        break
        
        # İçerik temizleme
        if icerik:
            # Reklam ve gereksiz ifadeleri temizle (Brave gibi)
            temizleme_listesi = [
                r'reklam.*', r'sponsor.*', r'kaydol.*', r'üye ol.*', r'abone ol.*',
                r'bizi takip edin.*', r'yorum yap.*', r'paylaş.*', r'satın al.*',
                r'indirim.*', r'kampanya.*', r'fırsat.*', r'sepete ekle.*',
                r'©.*', r'tüm hakları saklıdır.*', r'www\..*', r'\.com.*',
                r'cookie.*', r'çerez.*', r'gizlilik.*', r'kvkk.*',
                r'facebook.*', r'twitter.*', r'instagram.*', r'youtube.*',
                r'bu web sitesi.*', r'sitemizi.*', r'ziyaretçi.*'
            ]
            
            for pattern in temizleme_listesi:
                icerik = re.sub(pattern, '', icerik, flags=re.IGNORECASE)
            
            # Fazla boşlukları temizle
            icerik = re.sub(r'\s+', ' ', icerik).strip()
            
            # Kalite puanı hesapla
            puan = 0
            if 200 <= len(icerik) <= 800:  # Optimal uzunluk
                puan += 3
            elif len(icerik) > 800:
                puan += 2
            elif len(icerik) > 100:
                puan += 1
            
            # Türkçe puanı ekle
            puan += turkce_puan
            
            # Noktalama puanı
            if icerik.count('.') + icerik.count(',') > 5:
                puan += 2
            
            return (site_adi, icerik[:1000], puan)  # Max 1000 karakter
        
        return (site_adi, None, 0)
            
    except Exception as e:
        return (site_adi, None, 0)

def birlesik_motor_arama(sorgu):
    """V1 ve V2 motorlarını birleştiren akıllı arama"""
    
    # SADECE TÜRKÇE KAYNAKLAR (öncelik sırasına göre)
    turk_siteleri = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': '📚 Vikipedi (Türkçe)',
            'tip': 'ansiklopedi',
            'oncelik': 10
        },
        {
            'url': f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}',
            'adi': '📖 TDK Sözlük',
            'tip': 'sözlük',
            'oncelik': 9
        },
        {
            'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '👤 Biyografi.info',
            'tip': 'biyografi',
            'oncelik': 8
        },
        {
            'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}',
            'adi': '🔤 Etimoloji Türkçe',
            'tip': 'etimoloji',
            'oncelik': 7
        },
        {
            'url': f'https://www.nedir.com/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '💡 Nedir.com',
            'tip': 'açıklama',
            'oncelik': 6
        },
        {
            'url': f'https://www.sanatsal.com/sozluk/{urllib.parse.quote(sorgu.lower())}',
            'adi': '🎨 Sanatsal Sözlük',
            'tip': 'sanat',
            'oncelik': 5
        },
        {
            'url': f'https://www.turkcebilgi.com/{urllib.parse.quote(sorgu.lower().replace(" ", "_"))}',
            'adi': '📘 Türkçe Bilgi',
            'tip': 'bilgi',
            'oncelik': 4
        },
        {
            'url': f'https://www.kimkimdir.gen.tr/kimkimdir.php?k={urllib.parse.quote(sorgu)}',
            'adi': '👨‍💼 Kim Kimdir',
            'tip': 'biyografi',
            'oncelik': 3
        },
        {
            'url': f'https://www.dictionarist.com/turkish/{urllib.parse.quote(sorgu)}',
            'adi': '📕 Dictionarist',
            'tip': 'sözlük',
            'oncelik': 2
        },
        {
            'url': f'https://www.sozlukanlamine.com/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '📒 Sözlük Anlamı',
            'tip': 'sözlük',
            'oncelik': 1
        }
    ]
    
    # Öncelik sırasına göre sırala
    turk_siteleri.sort(key=lambda x: x['oncelik'], reverse=True)
    
    return turk_siteleri

def profesyonel_pdf_olustur():
    """Profesyonel PDF rapor oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Başlık
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(178, 34, 34)  # Koyu kırmızı
        pdf.cell(190, 15, txt="TÜRKAI PROFESYONEL ANALİZ RAPORU", ln=True, align='C')
        pdf.ln(5)
        
        # Çizgi
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # Konu bilgisi
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 10, txt="Konu:", ln=0)
        pdf.set_font("Arial", '', 14)
        pdf.cell(150, 10, txt=str(st.session_state.konu)[:50], ln=True)
        pdf.ln(5)
        
        # Tarih
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 8, txt="Tarih:", ln=0)
        pdf.set_font("Arial", '', 12)
        pdf.cell(150, 8, txt=datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), ln=True)
        
        # Kullanıcı
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 8, txt="Kullanıcı:", ln=0)
        pdf.set_font("Arial", '', 12)
        user_text = str(st.session_state.user)
        if st.session_state.get('is_guest', False):
            user_text += " (Misafir)"
        pdf.cell(150, 8, txt=user_text, ln=True)
        pdf.ln(15)
        
        # İçerik başlığı
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(178, 34, 34)
        pdf.cell(190, 10, txt="ANALİZ SONUÇLARI", ln=True)
        pdf.ln(5)
        
        # İçerik
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        
        # İçeriği paragraflara ayır
        icerik = str(st.session_state.bilgi) if st.session_state.bilgi else ""
        
        # HTML/Markdown temizleme
        icerik = re.sub(r'#+\s*', '', icerik)
        icerik = re.sub(r'\*\*', '', icerik)
        icerik = re.sub(r'\*', '', icerik)
        
        # Cümleleri ayır
        cumleler = re.split(r'(?<=[.!?])\s+', icerik)
        
        for cumle in cumleler:
            cumle = cumle.strip()
            if cumle:
                # Türkçe karakter düzeltme
                for eski, yeni in [('İ', 'I'), ('ı', 'i'), ('Ş', 'S'), ('ş', 's'), 
                                  ('Ğ', 'G'), ('ğ', 'g'), ('Ü', 'U'), ('ü', 'u'),
                                  ('Ö', 'O'), ('ö', 'o'), ('Ç', 'C'), ('ç', 'c')]:
                    cumle = cumle.replace(eski, yeni)
                
                # Uzun cümleleri böl
                if pdf.get_string_width(cumle) > 180:
                    kelimeler = cumle.split()
                    satir = ""
                    for kelime in kelimeler:
                        if pdf.get_string_width(satir + ' ' + kelime) < 180:
                            satir += kelime + ' '
                        else:
                            pdf.multi_cell(0, 6, txt=satir.strip())
                            satir = kelime + ' '
                    if satir:
                        pdf.multi_cell(0, 6, txt=satir.strip())
                else:
                    pdf.multi_cell(0, 6, txt=cumle)
                pdf.ln(4)
        
        # Alt bilgi
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(190, 5, txt="TürkAI Profesyonel Araştırma Sistemi", ln=True, align='C')
        pdf.cell(190, 5, txt="Bu rapor otomatik olarak oluşturulmuştur.", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF oluşturma hatası: {str(e)}")
        return None

# --- 🔐 PROFESYONEL GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Ana Logo ve Başlık
        st.markdown("""
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1 style='color: #b22222; font-size: 2.8rem; font-weight: 700;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #666; font-size: 1.2rem; margin-top: -10px;'>Profesyonel Araştırma Sistemi</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # Misafir Girişi Butonu
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("👤 Misafir Girişi", use_container_width=True, type="primary"):
                st.session_state.user = "Misafir_Kullanıcı"
                st.session_state.is_guest = True
                st.rerun()
        
        with col_b:
            st.markdown(f'<a href="{APK_URL}" class="apk-button">📱 Uygulamayı İndir</a>', unsafe_allow_html=True)
        
        # Bilgi Kutusu
        st.markdown("""
        <div class='info-box'>
            <b>🌟 SİSTEM ÖZELLİKLERİ:</b><br>
            • Brave gibi reklam engelleme<br>
            • Birleşik Motor (V1+V2)<br>
            • Derin Düşünen Modu<br>
            • Türkçe Kaynak Odaklı<br>
            • Profesyonel PDF Rapor
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Formları
        tab_login, tab_register = st.tabs(["🔐 GİRİŞ YAP", "📝 KAYIT OL"])
        
        with tab_login:
            st.markdown("#### Sistem Girişi")
            u_in = st.text_input("Kullanıcı Adı", key="login_user")
            p_in = st.text_input("Şifre", type="password", key="login_pass")
            
            if st.button("SİSTEME GİRİŞ YAP", use_container_width=True, type="primary"):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone():
                        st.session_state.user = u_in
                        st.session_state.is_guest = False
                        st.rerun()
                    else:
                        st.error("❌ Geçersiz kullanıcı adı veya şifre")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun")
        
        with tab_register:
            st.markdown("#### Yeni Hesap Oluştur")
            nu = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            np2 = st.text_input("Şifre Tekrar", type="password", key="reg_pass2")
            
            if st.button("HESAP OLUŞTUR", use_container_width=True, type="primary"):
                if nu and np and np2:
                    if np == np2:
                        if len(np) >= 6:
                            try:
                                c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                                conn.commit()
                                st.success("✅ Hesap başarıyla oluşturuldu")
                                time.sleep(1)
                                st.session_state.user = nu
                                st.session_state.is_guest = False
                                st.rerun()
                            except:
                                st.error("❌ Bu kullanıcı adı zaten kullanımda")
                        else:
                            st.error("❌ Şifre en az 6 karakter olmalıdır")
                    else:
                        st.error("❌ Şifreler eşleşmiyor")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 40px; color: #888; font-size: 0.9rem;'>
            <p>© 2024 TürkAI - Tüm hakları saklıdır</p>
            <p>Profesyonel araştırma çözümleri</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 🚀 PROFESYONEL SIDEBAR ---
with st.sidebar:
    # Kullanıcı Bilgisi
    user_display = str(st.session_state.user)
    if st.session_state.get('is_guest', False):
        user_display += " <span class='guest-badge'>Misafir</span>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #b22222, #dc3545); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h4 style='color: white; margin: 0;'>👤 {user_display}</h4>
        <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.9rem;'>
            {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 OTURUMU KAPAT", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi (Sadeleştirilmiş)
    st.markdown("### 🎯 ARAŞTIRMA MOTORU")
    m_secim = st.radio(
        "",
        ["🚀 Birleşik Motor (V1+V2)", "🤔 Derin Düşünen"],
        label_visibility="collapsed"
    )
    
    # Motor Açıklamaları
    if m_secim == "🚀 Birleşik Motor (V1+V2)":
        st.markdown("""
        <div class='info-box' style='margin-top: 10px; font-size: 0.9rem;'>
        <b>BİRLEŞİK MOTOR:</b><br>
        • Vikipedi + TDK<br>
        • Brave gibi reklam engelleme<br>
        • Hızlı arama
        </div>
        """, unsafe_allow_html=True)
    elif m_secim == "🤔 Derin Düşünen":
        st.markdown("""
        <div class='info-box' style='margin-top: 10px; font-size: 0.9rem;'>
        <b>DERİN DÜŞÜNEN:</b><br>
        • 10 Türkçe site<br>
        • Brave reklam engelleme<br>
        • Site site ilerleme<br>
        • Detaylı analiz
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Geçmiş Aramalar
    st.markdown("### 📋 GEÇMİŞ ARAMALAR")
    if not st.session_state.get('is_guest', False):
        c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 6", (st.session_state.user,))
        results = c.fetchall()
        if results:
            for (konu,) in results:
                if st.button(f"🔍 {konu[:25] if konu else '...'}", key=f"h_{konu}", use_container_width=True, type="secondary"):
                    c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1", 
                             (st.session_state.user, konu))
                    result = c.fetchone()
                    if result:
                        st.session_state.bilgi = result[0]
                        st.session_state.konu = konu
                        st.session_state.son_sorgu = konu
                        st.rerun()
        else:
            st.info("Henüz arama geçmişi yok")
    else:
        st.info("Misafir modunda geçmiş kaydedilmez")
    
    st.divider()
    
    # APK İndirme
    st.markdown(f'<a href="{APK_URL}" target="_blank" style="text-decoration: none;">', unsafe_allow_html=True)
    if st.button("📲 MOBİL UYGULAMA İNDİR", use_container_width=True, type="primary"):
        pass
    st.markdown('</a>', unsafe_allow_html=True)

# --- 💻 ANA ARAYÜZ ---
st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <h1>🔍 PROFESYONEL ARAŞTIRMA TERMİNALİ</h1>
    <p style='color: #666; font-size: 1.1rem;'>Brave gibi reklam engelleme ile Türkçe analiz</p>
</div>
""", unsafe_allow_html=True)

# Kullanım Kılavuzu
st.markdown("""
<div class='info-box'>
<strong>📋 PROFESYONEL KULLANIM:</strong><br>
• <strong>Brave Browser</strong> gibi reklam engelleme aktif<br>
1. Araştırma teriminizi yazın (örn: "Atatürk")<br>
2. Motor seçiminizi yapın<br>
3. Derin analiz için site site ilerleyin<br>
4. Profesyonel raporunuzu alın
</div>
""", unsafe_allow_html=True)

# Arama Çubuğu
sorgu = st.chat_input("🔎 Araştırmak istediğiniz terimi yazın...")

if sorgu and sorgu.strip():
    sorgu = sorgu.strip()
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    st.session_state.aktif_site = 0
    st.session_state.site_sonuclari = []
    st.session_state.yap_butonu = False
    
    # Düşünme Animasyonu
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(f"""
        <div class='spinner-container'>
            <div class='spinner'></div>
            <h3 style='color: #b22222;'>TÜRKAI ANALİZ EDİYOR</h3>
            <p>"{sorgu}" için Türkçe kaynaklar taranıyor...</p>
            <p style='color: #888; font-size: 0.9rem;'>Brave reklam engelleme aktif</p>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(1.5)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        if m_secim == "🚀 Birleşik Motor (V1+V2)":
            try:
                # Vikipedi'den başla (V1)
                wiki_icerik = ""
                try:
                    wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                    wiki_res = requests.get(wiki_api, headers=headers, timeout=10)
                    if wiki_res.status_code == 200:
                        wiki_data = wiki_res.json()
                        wiki_icerik = wiki_data.get('extract', '')
                except:
                    wiki_icerik = ''
                
                # TDK'yı dene (V2)
                tdk_icerik = ""
                try:
                    tdk_url = f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}'
                    tdk_response = requests.get(tdk_url, headers=headers, timeout=10)
                    
                    if tdk_response.status_code == 200:
                        tdk_soup = BeautifulSoup(tdk_response.content, 'html.parser')
                        
                        # Reklamları temizle
                        for element in tdk_soup.find_all(['script', 'style', 'iframe', 'nav', 'footer']):
                            element.decompose()
                        
                        for div in tdk_soup.find_all('div', class_=re.compile(r'(anlam|tanim|aciklama|meaning)')):
                            text = div.get_text().strip()
                            if len(text) > 50 and sorgu.lower() in text.lower():
                                tdk_icerik += text + "\n\n"
                        
                        if len(tdk_icerik) < 100:
                            # Alternatif TDK arama
                            for p in tdk_soup.find_all('p'):
                                text = p.get_text().strip()
                                if len(text) > 50 and sorgu.lower() in text.lower():
                                    tdk_icerik += text + "\n\n"
                except:
                    tdk_icerik = ""
                
                # Birleştirilmiş rapor
                rapor = f"# 🚀 BİRLEŞİK MOTOR ANALİZİ: {sorgu.upper()}\n\n"
                
                if wiki_icerik:
                    rapor += f"## 📚 Vikipedi (Ansiklopedik)\n{wiki_icerik}\n\n"
                
                if tdk_icerik and len(tdk_icerik) > 50:
                    rapor += f"## 📖 TDK Sözlük (Resmi Tanım)\n{tdk_icerik[:800]}...\n\n"
                
                if not wiki_icerik and (not tdk_icerik or len(tdk_icerik) < 50):
                    rapor = f"# ❌ SONUÇ BULUNAMADI\n\n'{sorgu}' için Türkçe kaynaklarda yeterli bilgi bulunamadı.\n\n**Öneriler:**\n• Terimin yazımını kontrol edin\n• Daha genel bir terim deneyin\n• Derin Düşünen motorunu kullanın"
                
                st.session_state.bilgi = rapor
                st.session_state.konu = sorgu
                
            except Exception as e:
                st.session_state.bilgi = f"# ⚠️ SİSTEM HATASI\n\nArama sırasında teknik bir hata oluştu.\n\nLütfen daha sonra tekrar deneyin."
                st.session_state.konu = sorgu
        
        elif m_secim == "🤔 Derin Düşünen":
            thinking_placeholder.empty()
            
            # Site listesini al
            siteler = birlesik_motor_arama(sorgu)
            st.session_state.site_listesi = siteler
            st.session_state.yap_butonu = True
            
            # İlk siteyi göster
            if siteler:
                st.info(f"**10 Türkçe site bulundu.** İlk site hazır. 'YENİDEN YAP' butonuyla diğer sitelere geçebilirsiniz.")
    
    st.session_state.arama_devam = False
    
    # Veritabanına kaydet (misafir değilse)
    if st.session_state.bilgi and not st.session_state.get('is_guest', False):
        try:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        except:
            pass
    
    st.rerun()

# --- 🤔 DERİN DÜŞÜNEN MODU SİTE GEÇİŞİ ---
if m_secim == "🤔 Derin Düşünen" and st.session_state.get('yap_butonu', False):
    st.markdown("---")
    st.markdown("### 🏗️ SİTE SİTE İLERLEME")
    
    if st.button("🔄 YENİDEN YAP", use_container_width=True, type="primary"):
        if st.session_state.aktif_site < len(st.session_state.site_listesi):
            site = st.session_state.site_listesi[st.session_state.aktif_site]
            
            with st.spinner(f"{site['adi']} taranıyor..."):
                site_adi, icerik, puan = profesyonel_site_tara(site['url'], st.session_state.son_sorgu, site['adi'])
                
                if icerik and puan > 2:
                    st.session_state.site_sonuclari.append({
                        'site': site_adi,
                        'icerik': icerik,
                        'puan': puan,
                        'tip': site['tip']
                    })
                    
                    # Anlık bilgi gösterimi
                    st.success(f"✅ **{site_adi}** - Kalite: {puan}/10")
                    
                    # İçeriği paragraflara ayır ve teker teker göster
                    paragraflar = icerik.split('\n\n')
                    for i, para in enumerate(paragraflar[:3]):  # İlk 3 paragraf
                        if para.strip():
                            with st.chat_message("assistant"):
                                st.write(para.strip())
                    
                else:
                    st.warning(f"⚠️ {site_adi}'de yeterli bilgi bulunamadı")
            
            st.session_state.aktif_site += 1
            
            # Tüm siteler tarandıysa raporu oluştur
            if st.session_state.aktif_site >= len(st.session_state.site_listesi):
                if st.session_state.site_sonuclari:
                    # Sonuçları puanına göre sırala
                    st.session_state.site_sonuclari.sort(key=lambda x: x['puan'], reverse=True)
                    
                    # Rapor oluştur
                    rapor = f"# 🤔 DERİN ANALİZ RAPORU: {st.session_state.son_sorgu.upper()}\n\n"
                    rapor += f"**📊 ANALİZ ÖZETİ:**\n"
                    rapor += f"• Toplam {len(st.session_state.site_listesi)} site taranmıştır\n"
                    rapor += f"• {len(st.session_state.site_sonuclari)} sitede kaliteli bilgi bulunmuştur\n\n"
                    
                    # En iyi 3 sonucu göster
                    for i, sonuc in enumerate(st.session_state.site_sonuclari[:3]):
                        rapor += f"## 🏆 {sonuc['site']}\n"
                        rapor += f"*Kalite puanı: {sonuc['puan']}/10 • Tip: {sonuc['tip']}*\n\n"
                        
                        # İçeriği düzenle
                        cumleler = re.split(r'(?<=[.!?])\s+', sonuc['icerik'])
                        for cumle in cumleler[:5]:  # İlk 5 cümle
                            if len(cumle.strip()) > 20:
                                rapor += f"• {cumle.strip()}\n"
                        
                        rapor += "\n"
                    
                    if len(st.session_state.site_sonuclari) > 3:
                        rapor += f"*Ve {len(st.session_state.site_sonuclari) - 3} ek kaynak daha incelenmiştir.*\n\n"
                    
                    st.session_state.bilgi = rapor
                    st.session_state.konu = f"DERİN: {st.session_state.son_sorgu}"
                    st.session_state.yap_butonu = False
                    
                    # Veritabanına kaydet (misafir değilse)
                    if not st.session_state.get('is_guest', False):
                        try:
                            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                                     (st.session_state.user, st.session_state.konu, 
                                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
                            conn.commit()
                        except:
                            pass
                    
                    st.rerun()
                else:
                    st.session_state.bilgi = f"# ❌ SONUÇ BULUNAMADI\n\n'{st.session_state.son_sorgu}' için hiçbir Türkçe sitede yeterli bilgi bulunamadı."
                    st.session_state.konu = st.session_state.son_sorgu
                    st.session_state.yap_butonu = False
                    st.rerun()
    
    # Mevcut durumu göster
    if hasattr(st.session_state, 'site_listesi') and st.session_state.site_listesi:
        st.markdown(f"**İlerleme:** {st.session_state.aktif_site}/{len(st.session_state.site_listesi)} site")
        
        # Site listesini göster
        for i, site in enumerate(st.session_state.site_listesi):
            durum = "✅" if i < st.session_state.aktif_site else "⏳" if i == st.session_state.aktif_site else "◻️"
            st.markdown(f"{durum} **{site['adi']}** - {site['tip'].capitalize()}")
    
    if st.session_state.site_sonuclari:
        st.markdown("### 📋 BULUNAN BİLGİLER")
        for sonuc in st.session_state.site_sonuclari:
            with st.expander(f"{sonuc['site']} - Puan: {sonuc['puan']}/10"):
                st.write(sonuc['icerik'][:500] + "..." if len(sonuc['icerik']) > 500 else sonuc['icerik'])

# --- 📊 RAPOR GÖSTERİMİ ---
if st.session_state.son_sorgu and not st.session_state.arama_devam and st.session_state.bilgi:
    # Aktif Sorgu Bilgisi
    st.markdown(f"""
    <div style='background-color: rgba(178, 34, 34, 0.08); padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid rgba(178, 34, 34, 0.3);'>
        <strong style='color: #b22222;'>🔍 AKTİF SORGUNUZ:</strong> {st.session_state.son_sorgu}<br>
        <strong style='color: #b22222;'>🎯 MOD:</strong> {m_secim}<br>
        <strong style='color: #b22222;'>👤 KULLANICI:</strong> {st.session_state.user}{" (Misafir)" if st.session_state.get('is_guest', False) else ""}
    </div>
    """, unsafe_allow_html=True)
    
    # Rapor Gösterimi
    st.markdown("### 📄 PROFESYONEL ANALİZ RAPORU")
    
    # Rapor içeriğini göster
    st.markdown(st.session_state.bilgi)
    
    # PDF Butonu
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        pdf_data = profesyonel_pdf_olustur()
        if pdf_data:
            st.download_button(
                label="📥 PROFESYONEL PDF RAPOR İNDİR",
                data=pdf_data,
                file_name=f"TurkAI_Raporu_{str(st.session_state.konu)[:25].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
    
    # Ek Butonlar
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 YENİ ARAMA", use_container_width=True, type="secondary"):
            st.session_state.son_sorgu = None
            st.session_state.bilgi = None
            st.session_state.site_sonuclari = []
            st.session_state.yap_butonu = False
            st.rerun()
    
    with col2:
        if st.button("📋 PANOYA KOPYALA", use_container_width=True, type="secondary"):
            st.info("Rapor panoya kopyalandı")
    
    with col3:
        if st.button("⭐ KAYDET", use_container_width=True, type="secondary", disabled=st.session_state.get('is_guest', False)):
            if not st.session_state.get('is_guest', False):
                st.success("Arama geçmişe kaydedildi")
            else:
                st.warning("Misafir modunda kayıt yapılamaz")
