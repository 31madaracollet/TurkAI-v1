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
        --primary-red: #8B0000;
        --dark-bg: #0a0a0a;
        --dark-card: #151515;
        --dark-text: #e0e0e0;
        --light-bg: #f5f5f5;
        --light-card: #ffffff;
        --light-text: #222222;
        --border-radius: 8px;
        --shadow-light: 0 4px 12px rgba(0,0,0,0.08);
        --shadow-dark: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Tema Kontrolü */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        transition: all 0.3s ease;
    }
    
    /* Başlıklar */
    h1, h2, h3 {
        color: var(--primary-red) !important;
        font-family: 'Georgia', 'Times New Roman', serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    h1 {
        font-size: 2.4rem !important;
        border-bottom: 3px solid var(--primary-red);
        padding-bottom: 12px;
        margin-bottom: 30px !important;
        text-align: center;
    }
    
    h2 {
        font-size: 1.8rem !important;
        margin-top: 25px !important;
        margin-bottom: 15px !important;
    }
    
    h3 {
        font-size: 1.4rem !important;
        color: var(--text-color) !important;
        border-left: 4px solid var(--primary-red);
        padding-left: 12px;
        margin-top: 20px !important;
    }
    
    /* Giriş Ekranı */
    .login-container {
        max-width: 500px;
        margin: 80px auto;
        padding: 50px 40px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        border: 2px solid var(--primary-red);
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    
    .login-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, var(--primary-red), #B22222);
    }
    
    /* Butonlar */
    .primary-button {
        background: linear-gradient(135deg, #8B0000, #B22222) !important;
        color: white !important;
        border: none !important;
        padding: 14px 30px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(139, 0, 0, 0.2) !important;
    }
    
    .primary-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(139, 0, 0, 0.25) !important;
    }
    
    .secondary-button {
        background-color: transparent !important;
        color: var(--primary-red) !important;
        border: 2px solid var(--primary-red) !important;
        padding: 12px 28px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }
    
    .secondary-button:hover {
        background-color: rgba(139, 0, 0, 0.1) !important;
    }
    
    /* Kartlar */
    .info-card {
        background-color: var(--card-color);
        border: 1px solid rgba(139, 0, 0, 0.2);
        border-radius: var(--border-radius);
        padding: 25px;
        margin: 20px 0;
        box-shadow: var(--shadow);
        transition: transform 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-3px);
        border-color: var(--primary-red);
    }
    
    .site-card {
        background-color: var(--card-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }
    
    .site-card.active {
        border-left: 5px solid var(--primary-red);
        background-color: rgba(139, 0, 0, 0.05);
    }
    
    /* İlerleme Göstergesi */
    .progress-container {
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 25px 0;
        border: 1px solid rgba(139, 0, 0, 0.1);
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin: 15px 0;
        padding: 10px;
        border-radius: 6px;
        background-color: rgba(139, 0, 0, 0.05);
    }
    
    .step-number {
        background-color: var(--primary-red);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 15px;
    }
    
    /* Spinner */
    .spinner-container {
        text-align: center;
        padding: 50px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        margin: 30px 0;
        border: 2px dashed rgba(139, 0, 0, 0.2);
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(139, 0, 0, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #8B0000, #B22222);
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 5px;
    }
    
    .guest-badge {
        background-color: #6c757d;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    
    /* PDF Butonu */
    .pdf-button {
        background: linear-gradient(135deg, #006400, #228B22) !important;
        color: white !important;
        border: none !important;
        padding: 12px 25px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }
    
    .pdf-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 100, 0, 0.2) !important;
    }
    
    /* Input Alanları */
    .stTextInput > div > div > input {
        border-radius: var(--border-radius) !important;
        border: 2px solid var(--border-color) !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-red) !important;
        box-shadow: 0 0 0 2px rgba(139, 0, 0, 0.2) !important;
    }
    
    /* Chat Input */
    .stChatInput > div > div > input {
        border: 2px solid var(--primary-red) !important;
        border-radius: 25px !important;
        padding: 14px 20px !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
        font-size: 15px !important;
    }
    
    /* Radio Butonları */
    .stRadio > div {
        background-color: var(--card-color);
        padding: 15px;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--card-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Tabler */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--card-color) !important;
        border-radius: 6px 6px 0 0 !important;
        border: 1px solid var(--border-color) !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-red) !important;
        color: white !important;
        border-color: var(--primary-red) !important;
    }
    
    /* Bilgi Kutuları */
    .warning-box {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
    
    .success-box {
        background-color: rgba(40, 167, 69, 0.1);
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
    
    /* Kod Blokları */
    pre {
        background-color: var(--card-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius) !important;
        padding: 15px !important;
        font-family: 'Consolas', monospace !important;
        font-size: 0.9rem !important;
    }
    
    /* Responsive Tasarım */
    @media (max-width: 768px) {
        .login-container {
            margin: 40px 20px;
            padding: 30px 20px;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
        }
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

# --- 🔑 OTURUM YÖNETİMİ ---
def init_session_state():
    """Session state değişkenlerini güvenli şekilde başlat"""
    default_values = {
        "user": None,
        "is_guest": False,
        "bilgi": None,
        "konu": "",
        "son_sorgu": None,
        "arama_devam": False,
        "aktif_site": 0,
        "site_sonuclari": [],
        "yap_butonu": False,
        "site_listesi": [],
        "mevcut_site_icerik": None
    }
    
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Session state'i başlat
init_session_state()

# --- 🔧 PROFESYONEL FONKSİYONLAR ---
def profesyonel_site_tara(url, sorgu, site_adi, timeout=8):
    """Profesyonel site tarama"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            return (site_adi, None, 0)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Reklamları temizle
        for element in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'header', 'aside', 'form', 'button', 'advertisement', 'banner']):
            element.decompose()
        
        # Türkçe içerik kontrolü
        tum_metin = soup.get_text().lower()
        turkce_kelimeler = ['veya', 'ile', 'için', 'olarak', 'göre', 'kadar', 'ancak', 'fakat', 'çünkü', 'eğer']
        turkce_puan = sum(1 for kelime in turkce_kelimeler if kelime in tum_metin)
        
        if turkce_puan < 2:
            return (site_adi, None, 0)
        
        # Ana içerik alanını bul
        icerik = ""
        
        # 1. Önce makale/ansiklopedi formatını ara
        article_selectors = [
            ('div', {'id': 'content'}),
            ('div', {'class': 'content'}),
            ('article', None),
            ('div', {'class': 'article'}),
            ('div', {'class': 'entry-content'}),
            ('section', {'class': 'content'}),
            ('div', {'class': re.compile(r'main|content|article|entry')})
        ]
        
        for tag, attrs in article_selectors:
            try:
                elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
                for elem in elements:
                    text = elem.get_text().strip()
                    if len(text) > 150:
                        # Paragrafları ayır
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if len(para) > 80 and sorgu.lower() in para.lower():
                                icerik += para + "\n\n"
                        if len(icerik) > 300:
                            break
                if len(icerik) > 300:
                    break
            except:
                continue
        
        # 2. Paragraf arama
        if len(icerik) < 200:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 60:
                    icerik += text + "\n\n"
                    if len(icerik) > 300:
                        break
        
        # İçerik temizleme
        if icerik:
            # Reklamları temizle
            temizleme_listesi = [
                r'reklam.*', r'sponsor.*', r'kaydol.*', r'üye ol.*', r'abone ol.*',
                r'bizi takip edin.*', r'yorum yap.*', r'paylaş.*', r'satın al.*',
                r'indirim.*', r'kampanya.*', r'fırsat.*', r'sepete ekle.*',
                r'©.*', r'tüm hakları saklıdır.*', r'www\..*', r'\.com.*',
                r'cookie.*', r'çerez.*', r'gizlilik.*', r'kvkk.*'
            ]
            
            for pattern in temizleme_listesi:
                icerik = re.sub(pattern, '', icerik, flags=re.IGNORECASE)
            
            icerik = re.sub(r'\s+', ' ', icerik).strip()
            
            # Kalite puanı
            puan = 0
            if 200 <= len(icerik) <= 800:
                puan += 3
            elif len(icerik) > 800:
                puan += 2
            elif len(icerik) > 100:
                puan += 1
            
            puan += turkce_puan
            
            if icerik.count('.') + icerik.count(',') > 5:
                puan += 2
            
            return (site_adi, icerik[:800], puan)
        
        return (site_adi, None, 0)
            
    except Exception as e:
        return (site_adi, None, 0)

def birlesik_motor_arama(sorgu):
    """Siteleri döndür"""
    turk_siteleri = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': '📚 Vikipedi',
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
            'url': f'https://www.turkcebilgi.com/{urllib.parse.quote(sorgu.lower().replace(" ", "_"))}',
            'adi': '📘 Türkçe Bilgi',
            'tip': 'bilgi',
            'oncelik': 5
        },
        {
            'url': f'https://www.kimkimdir.gen.tr/kimkimdir.php?k={urllib.parse.quote(sorgu)}',
            'adi': '👨‍💼 Kim Kimdir',
            'tip': 'biyografi',
            'oncelik': 4
        },
        {
            'url': f'https://www.dictionarist.com/turkish/{urllib.parse.quote(sorgu)}',
            'adi': '📕 Dictionarist',
            'tip': 'sözlük',
            'oncelik': 3
        }
    ]
    
    turk_siteleri.sort(key=lambda x: x['oncelik'], reverse=True)
    return turk_siteleri

def profesyonel_pdf_olustur():
    """Profesyonel PDF oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Başlık
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(139, 0, 0)
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
        if st.session_state.is_guest:
            user_text += " (Misafir)"
        pdf.cell(150, 8, txt=user_text, ln=True)
        pdf.ln(15)
        
        # İçerik başlığı
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(139, 0, 0)
        pdf.cell(190, 10, txt="ANALİZ SONUÇLARI", ln=True)
        pdf.ln(5)
        
        # İçerik
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        
        if st.session_state.bilgi:
            icerik = str(st.session_state.bilgi)
            
            # HTML/Markdown temizleme
            icerik = re.sub(r'#+\s*', '', icerik)
            icerik = re.sub(r'\*\*', '', icerik)
            icerik = re.sub(r'\*', '', icerik)
            
            # Türkçe karakter düzeltme
            for eski, yeni in [('İ', 'I'), ('ı', 'i'), ('Ş', 'S'), ('ş', 's'), 
                              ('Ğ', 'G'), ('ğ', 'g'), ('Ü', 'U'), ('ü', 'u'),
                              ('Ö', 'O'), ('ö', 'o'), ('Ç', 'C'), ('ç', 'c')]:
                icerik = icerik.replace(eski, yeni)
            
            # Paragraflara ayır
            paragraphs = icerik.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Uzun paragrafı böl
                    if pdf.get_string_width(para) > 180:
                        words = para.split()
                        line = ""
                        for word in words:
                            if pdf.get_string_width(line + ' ' + word) < 180:
                                line += word + ' '
                            else:
                                pdf.multi_cell(0, 6, txt=line.strip())
                                line = word + ' '
                        if line:
                            pdf.multi_cell(0, 6, txt=line.strip())
                    else:
                        pdf.multi_cell(0, 6, txt=para)
                    pdf.ln(4)
        
        # Alt bilgi
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(190, 5, txt="TürkAI Profesyonel Araştırma Sistemi", ln=True, align='C')
        pdf.cell(190, 5, txt="© 2024 - Tüm hakları saklıdır", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF oluşturma sırasında hata: {str(e)}")
        return None

# --- 🔐 PROFESYONEL GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Ana Logo ve Başlık
        st.markdown("""
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1 style='color: #8B0000; font-size: 2.8rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #666; font-size: 1.1rem; margin-top: -10px; font-style: italic;'>
                Profesyonel Araştırma ve Analiz Sistemi
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # Uyarı Mesajı
        st.markdown("""
        <div class='warning-box'>
            <b>⚠️ ÖNEMLİ UYARI:</b><br>
            Yaptığınız oturumlar geçicidir. Çıkış yaptığınızda tüm veriler silinecektir.
        </div>
        """, unsafe_allow_html=True)
        
        # Misafir Girişi
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("👤 Misafir Girişi", use_container_width=True, type="primary"):
                st.session_state.user = "Misafir_Kullanıcı"
                st.session_state.is_guest = True
                st.rerun()
        
        with col_b:
            st.markdown(f'<a href="{APK_URL}" target="_blank" class="primary-button" style="text-decoration: none; display: block; text-align: center;">📱 Uygulamayı İndir</a>', unsafe_allow_html=True)
        
        # Bilgi Kutusu
        st.markdown("""
        <div class='info-card'>
            <b>🔧 SİSTEM ÖZELLİKLERİ:</b><br>
            • Birleşik Motor (Vikipedi + TDK)<br>
            • Derin Analiz Modu<br>
            • Türkçe Kaynak Odaklı<br>
            • Profesyonel PDF Rapor<br>
            • Reklam Filtreleme
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Formları
        tab_login, tab_register = st.tabs(["🔐 SİSTEM GİRİŞİ", "📝 YENİ KAYIT"])
        
        with tab_login:
            st.markdown("### Sisteme Giriş")
            u_in = st.text_input("Kullanıcı Adı", key="login_user")
            p_in = st.text_input("Şifre", type="password", key="login_pass")
            
            if st.button("OTURUMU BAŞLAT", use_container_width=True, type="primary"):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone():
                        st.session_state.user = u_in
                        st.session_state.is_guest = False
                        st.rerun()
                    else:
                        st.error("Geçersiz kullanıcı adı veya şifre.")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")
        
        with tab_register:
            st.markdown("### Yeni Hesap Oluştur")
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
                                st.success("Hesap başarıyla oluşturuldu.")
                                time.sleep(1)
                                st.session_state.user = nu
                                st.session_state.is_guest = False
                                st.rerun()
                            except:
                                st.error("Bu kullanıcı adı zaten kullanımda.")
                        else:
                            st.error("Şifre en az 6 karakter olmalıdır.")
                    else:
                        st.error("Şifreler eşleşmiyor.")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 40px; color: #666; font-size: 0.85rem; font-style: italic;'>
            <p>TürkAI © 2024 | Tüm hakları saklıdır</p>
            <p>Profesyonel araştırma çözümleri</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 🚀 PROFESYONEL SIDEBAR ---
with st.sidebar:
    # Kullanıcı Bilgisi
    user_display = str(st.session_state.user)
    if st.session_state.is_guest:
        user_display += " <span class='guest-badge'>Misafir</span>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #8B0000, #B22222); padding: 20px; border-radius: var(--border-radius); margin-bottom: 20px; color: white;'>
        <h4 style='color: white; margin: 0;'>👤 {user_display}</h4>
        <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.85rem;'>
            {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 OTURUMU SONLANDIR", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi
    st.markdown("### 🎯 ANALİZ MOTORU")
    m_secim = st.radio(
        "",
        ["🚀 Birleşik Motor", "🤔 Derin Analiz"],
        label_visibility="collapsed"
    )
    
    # Motor Açıklamaları
    if m_secim == "🚀 Birleşik Motor":
        st.markdown("""
        <div class='info-card' style='margin-top: 10px; font-size: 0.9rem; padding: 15px;'>
        <b>BİRLEŞİK MOTOR</b><br>
        • Vikipedi + TDK<br>
        • Hızlı arama<br>
        • Özet bilgi
        </div>
        """, unsafe_allow_html=True)
    elif m_secim == "🤔 Derin Analiz":
        st.markdown("""
        <div class='info-card' style='margin-top: 10px; font-size: 0.9rem; padding: 15px;'>
        <b>DERİN ANALİZ</b><br>
        • 8 Türkçe site<br>
        • Site site ilerleme<br>
        • Detaylı tarama
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Geçmiş Aramalar
    st.markdown("### 📋 ARAMA GEÇMİŞİ")
    if not st.session_state.is_guest:
        c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,))
        results = c.fetchall()
        if results:
            for (konu,) in results:
                if konu and st.button(f"📄 {konu[:22]}", key=f"h_{konu}", use_container_width=True, type="secondary"):
                    c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1", 
                             (st.session_state.user, konu))
                    result = c.fetchone()
                    if result and result[0]:
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
    if st.button("📲 MOBİL UYGULAMA", use_container_width=True, type="primary"):
        pass
    st.markdown('</a>', unsafe_allow_html=True)

# --- 💻 ANA ARAYÜZ ---
st.markdown("""
<div style='text-align: center; margin-bottom: 25px;'>
    <h1>🔍 PROFESYONEL ARAŞTIRMA TERMİNALİ</h1>
</div>
""", unsafe_allow_html=True)

# Arama Talimatı
st.markdown("""
<div class='info-card' style='text-align: center;'>
    <p style='font-size: 1.1rem; margin: 0; color: var(--primary-red); font-weight: 600;'>
        Araştırmak istediğin konunun anahtar kelimesini yazınız.
    </p>
    <p style='font-size: 0.9rem; margin: 5px 0 0 0; color: var(--text-color); opacity: 0.8;'>
        Örnek: "Atatürk", "İstanbul", "Yapay Zeka"
    </p>
</div>
""", unsafe_allow_html=True)

# Arama Çubuğu
sorgu = st.chat_input("🔎 Anahtar kelimeyi buraya yazın...")

if sorgu and sorgu.strip():
    sorgu = sorgu.strip()
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    st.session_state.aktif_site = 0
    st.session_state.site_sonuclari = []
    st.session_state.yap_butonu = False
    st.session_state.mevcut_site_icerik = None
    
    # Düşünme Animasyonu
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(f"""
        <div class='spinner-container'>
            <div class='spinner'></div>
            <h3 style='color: #8B0000;'>TÜRKAI ANALİZ EDİYOR</h3>
            <p>"{sorgu}" için araştırma yapılıyor...</p>
            <p style='color: #888; font-size: 0.9rem; font-style: italic;'>Lütfen bekleyiniz</p>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(1.2)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        if m_secim == "🚀 Birleşik Motor":
            try:
                # Vikipedi'den başla
                wiki_icerik = ""
                try:
                    wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                    wiki_res = requests.get(wiki_api, headers=headers, timeout=8)
                    if wiki_res.status_code == 200:
                        wiki_data = wiki_res.json()
                        wiki_icerik = wiki_data.get('extract', '')
                except:
                    wiki_icerik = ''
                
                # TDK'yı dene
                tdk_icerik = ""
                try:
                    tdk_url = f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}'
                    tdk_response = requests.get(tdk_url, headers=headers, timeout=8)
                    
                    if tdk_response.status_code == 200:
                        tdk_soup = BeautifulSoup(tdk_response.content, 'html.parser')
                        
                        for element in tdk_soup.find_all(['script', 'style', 'iframe']):
                            element.decompose()
                        
                        for div in tdk_soup.find_all('div', class_=re.compile(r'(anlam|tanim|aciklama)')):
                            text = div.get_text().strip()
                            if len(text) > 50:
                                tdk_icerik += text + "\n\n"
                except:
                    tdk_icerik = ""
                
                # Birleştirilmiş rapor
                rapor = f"# 📊 BİRLEŞİK ANALİZ: {sorgu.upper()}\n\n"
                
                if wiki_icerik:
                    rapor += f"## 📚 Vikipedi\n{wiki_icerik}\n\n"
                
                if tdk_icerik and len(tdk_icerik) > 50:
                    rapor += f"## 📖 TDK Sözlük\n{tdk_icerik[:600]}...\n\n"
                
                if not wiki_icerik and (not tdk_icerik or len(tdk_icerik) < 50):
                    rapor = f"# ⚠️ SONUÇ BULUNAMADI\n\n'{sorgu}' için Türkçe kaynaklarda yeterli bilgi bulunamadı.\n\n**Öneri:** Daha genel bir terim deneyin veya Derin Analiz modunu kullanın."
                
                st.session_state.bilgi = rapor
                st.session_state.konu = sorgu
                
            except Exception as e:
                st.session_state.bilgi = f"# ⚠️ TEKNİK HATA\n\nArama sırasında bir hata oluştu.\n\nLütfen daha sonra tekrar deneyin."
                st.session_state.konu = sorgu
        
        elif m_secim == "🤔 Derin Analiz":
            thinking_placeholder.empty()
            
            # Site listesini al ve ilk siteyi tara
            siteler = birlesik_motor_arama(sorgu)
            st.session_state.site_listesi = siteler
            
            if siteler:
                # İlk siteyi tarayıp göster
                site = siteler[0]
                site_adi, icerik, puan = profesyonel_site_tara(site['url'], sorgu, site['adi'])
                
                if icerik and puan > 2:
                    st.session_state.mevcut_site_icerik = icerik
                    st.session_state.aktif_site = 1  # Bir sonraki site için hazır
                    
                    # Anlık bilgi gösterimi
                    rapor = f"# 🔍 İLK BULUNAN SİTE\n\n"
                    rapor += f"## {site_adi}\n"
                    rapor += f"*Kalite puanı: {puan}/10*\n\n"
                    rapor += f"{icerik}\n\n"
                    rapor += "---\n\n"
                    rapor += "**📌 Not:** 'YENİDEN YAP' butonuna tıklayarak bir sonraki siteye geçebilirsiniz."
                    
                    st.session_state.bilgi = rapor
                    st.session_state.konu = f"DERİN: {sorgu}"
                    st.session_state.yap_butonu = True
                    
                else:
                    st.session_state.bilgi = f"# ⚠️ İLK SİTEDE BİLGİ BULUNAMADI\n\nİlk sitede yeterli bilgi bulunamadı. 'YENİDEN YAP' butonuyla bir sonraki siteye geçebilirsiniz."
                    st.session_state.konu = sorgu
                    st.session_state.yap_butonu = True
    
    st.session_state.arama_devam = False
    
    # Veritabanına kaydet (misafir değilse)
    if st.session_state.bilgi and not st.session_state.is_guest:
        try:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        except:
            pass
    
    st.rerun()

# --- 🤔 DERİN ANALİZ MODU SİTE GEÇİŞİ ---
if m_secim == "🤔 Derin Analiz" and st.session_state.yap_butonu and st.session_state.site_listesi:
    st.markdown("---")
    st.markdown("### 🏗️ SİTE GEÇİŞ SİSTEMİ")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div class='progress-container'>
            <p><b>Geçerli Durum:</b> {}/{} site taranmıştır.</p>
            <p><b>Yapılacak İşlem:</b> Butona tıklayarak bir sonraki siteye geçebilirsiniz.</p>
        </div>
        """.format(st.session_state.aktif_site, len(st.session_state.site_listesi)), unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 YENİDEN YAP", use_container_width=True, type="primary"):
            if st.session_state.aktif_site < len(st.session_state.site_listesi):
                # Sonraki siteyi tara
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
                        
                        # Yeni site bilgisini göster
                        rapor = f"# 🔍 {st.session_state.aktif_site + 1}. SİTE BULUNDU\n\n"
                        rapor += f"## {site_adi}\n"
                        rapor += f"*Kalite puanı: {puan}/10 • Tip: {site['tip']}*\n\n"
                        rapor += f"{icerik}\n\n"
                        
                        if st.session_state.aktif_site + 1 < len(st.session_state.site_listesi):
                            rapor += "---\n\n"
                            rapor += "**📌 Not:** 'YENİDEN YAP' butonuna tıklayarak bir sonraki siteye geçebilirsiniz."
                        
                        st.session_state.bilgi = rapor
                        st.success(f"✅ {site_adi} - Kalite: {puan}/10")
                        
                    else:
                        st.warning(f"⚠️ {site_adi}'de yeterli bilgi bulunamadı")
                        rapor = f"# ⚠️ SİTE TARANAMADI\n\n{site['adi']} sitesinde yeterli bilgi bulunamadı.\n\n"
                        
                        if st.session_state.aktif_site + 1 < len(st.session_state.site_listesi):
                            rapor += "Bir sonraki site için 'YENİDEN YAP' butonuna tıklayın."
                        
                        st.session_state.bilgi = rapor
                
                st.session_state.aktif_site += 1
                
                # Tüm siteler tarandıysa özet rapor oluştur
                if st.session_state.aktif_site >= len(st.session_state.site_listesi):
                    if st.session_state.site_sonuclari:
                        # Sonuçları puanına göre sırala
                        st.session_state.site_sonuclari.sort(key=lambda x: x['puan'], reverse=True)
                        
                        # Özet rapor oluştur
                        ozet_rapor = f"# 📊 DERİN ANALİZ ÖZETİ: {st.session_state.son_sorgu.upper()}\n\n"
                        ozet_rapor += f"**📋 ANALİZ SONUÇLARI:**\n"
                        ozet_rapor += f"• Toplam {len(st.session_state.site_listesi)} site taranmıştır\n"
                        ozet_rapor += f"• {len(st.session_state.site_sonuclari)} sitede kaliteli bilgi bulunmuştur\n\n"
                        
                        # En iyi sonuçları göster
                        for i, sonuc in enumerate(st.session_state.site_sonuclari[:3]):
                            ozet_rapor += f"## 🏆 {sonuc['site']}\n"
                            ozet_rapor += f"*Kalite: {sonuc['puan']}/10*\n\n"
                            
                            cumleler = re.split(r'(?<=[.!?])\s+', sonuc['icerik'])
                            for cumle in cumleler[:3]:
                                if len(cumle.strip()) > 20:
                                    ozet_rapor += f"• {cumle.strip()}\n"
                            
                            ozet_rapor += "\n"
                        
                        if len(st.session_state.site_sonuclari) > 3:
                            ozet_rapor += f"*Ve {len(st.session_state.site_sonuclari) - 3} ek kaynak daha incelenmiştir.*\n\n"
                        
                        st.session_state.bilgi = ozet_rapor
                        st.session_state.yap_butonu = False
                        
                        # Veritabanına kaydet (misafir değilse)
                        if not st.session_state.is_guest:
                            try:
                                c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                                         (st.session_state.user, st.session_state.konu, 
                                          st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
                                conn.commit()
                            except:
                                pass
                        
                        st.rerun()
                    else:
                        st.session_state.bilgi = f"# ❌ SONUÇ BULUNAMADI\n\n'{st.session_state.son_sorgu}' için hiçbir sitede yeterli bilgi bulunamadı."
                        st.session_state.yap_butonu = False
                        st.rerun()
    
    # İlerleme adımlarını göster
    st.markdown("### 📋 SİTE LİSTESİ")
    for i, site in enumerate(st.session_state.site_listesi):
        durum = "✅" if i < st.session_state.aktif_site else "⏳" if i == st.session_state.aktif_site else "◻️"
        st.markdown(f"{durum} **{site['adi']}** - {site['tip'].capitalize()}")

# --- 📊 RAPOR GÖSTERİMİ ---
if st.session_state.son_sorgu and not st.session_state.arama_devam and st.session_state.bilgi:
    # Aktif Sorgu Bilgisi
    st.markdown("---")
    st.markdown("""
    <div class='info-card'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <strong style='color: #8B0000;'>🔍 AKTİF SORGUNUZ:</strong> {sorgu}<br>
                <strong style='color: #8B0000;'>🎯 MOD:</strong> {motor}<br>
                <strong style='color: #8B0000;'>👤 KULLANICI:</strong> {kullanici}{misafir}
            </div>
            <div style='text-align: right; color: #666; font-size: 0.9rem;'>
                {tarih}
            </div>
        </div>
    </div>
    """.format(
        sorgu=st.session_state.son_sorgu,
        motor=m_secim,
        kullanici=st.session_state.user,
        misafir=" (Misafir)" if st.session_state.is_guest else "",
        tarih=datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    ), unsafe_allow_html=True)
    
    # Rapor Gösterimi
    st.markdown("### 📄 ANALİZ RAPORU")
    st.markdown(st.session_state.bilgi)
    
    # PDF İndirme Butonu
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📥 PDF RAPOR İNDİR", use_container_width=True, type="primary"):
            pdf_data = profesyonel_pdf_olustur()
            if pdf_data:
                st.download_button(
                    label="⬇️ PDF'Yİ İNDİR",
                    data=pdf_data,
                    file_name=f"TurkAI_Raporu_{str(st.session_state.konu)[:25].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("PDF oluşturulamadı. Lütfen tekrar deneyin.")
    
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
        if st.button("📋 KOPYALA", use_container_width=True, type="secondary"):
            st.info("Rapor panoya kopyalandı")
    
    with col3:
        if st.button("💾 KAYDET", use_container_width=True, type="secondary", disabled=st.session_state.is_guest):
            if not st.session_state.is_guest:
                st.success("Arama geçmişe kaydedildi")
            else:
                st.warning("Misafir modunda kayıt yapılamaz")
