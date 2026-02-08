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
import math
import base64
from io import BytesIO
import os

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
        --shadow-light: 0 4px 20px rgba(0,0,0,0.08);
        --shadow-dark: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    /* Otomatik Tema Algılama */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: var(--dark-bg);
            --card-color: var(--dark-card);
            --text-color: var(--dark-text);
            --border-color: #2a2a2a;
            --shadow: var(--shadow-dark);
            --hover-bg: rgba(178, 34, 34, 0.1);
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --bg-color: var(--light-bg);
            --card-color: var(--light-card);
            --text-color: var(--light-text);
            --border-color: #e0e0e0;
            --shadow: var(--shadow-light);
            --hover-bg: rgba(178, 34, 34, 0.05);
        }
    }
    
    /* Ana Stiller */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif !important;
    }
    
    h1, h2, h3, h4 {
        color: var(--primary-red) !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        text-align: center;
        padding-bottom: 15px;
        margin-bottom: 2rem !important;
        position: relative;
    }
    
    h1:after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-red), #ff4444);
        border-radius: 2px;
    }
    
    h2 {
        font-size: 1.8rem !important;
        border-left: 4px solid var(--primary-red);
        padding-left: 15px;
        margin-top: 2rem !important;
    }
    
    h3 {
        font-size: 1.4rem !important;
        color: var(--text-color) !important;
        margin-top: 1.5rem !important;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(178, 34, 34, 0.2);
    }
    
    /* Giriş Konteyneri - YENİ TASARIM */
    .login-container {
        max-width: 480px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: var(--card-color);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
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
        height: 4px;
        background: linear-gradient(90deg, var(--primary-red), #ff4444);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid rgba(178, 34, 34, 0.1);
    }
    
    .login-feature {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 12px 0;
        padding: 10px;
        background: var(--hover-bg);
        border-radius: 8px;
        font-size: 0.95rem;
    }
    
    .feature-icon {
        font-size: 1.2rem;
        color: var(--primary-red);
    }
    
    /* Butonlar */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #b22222, #dc3545) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 12px rgba(178, 34, 34, 0.3) !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(178, 34, 34, 0.4) !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background: transparent !important;
        color: var(--primary-red) !important;
        border: 2px solid var(--primary-red) !important;
        padding: 10px 22px !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: var(--hover-bg) !important;
    }
    
    /* Kartlar */
    .info-card {
        background: var(--card-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .warning-card {
        background: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .success-card {
        background: rgba(40, 167, 69, 0.1);
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Site Kartları */
    .site-card {
        background: var(--card-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .site-card:hover {
        border-color: var(--primary-red);
        background: var(--hover-bg);
        transform: translateX(5px);
    }
    
    .site-card.active {
        border-left: 4px solid var(--primary-red);
        background: var(--hover-bg);
    }
    
    .site-icon {
        font-size: 1.5rem;
    }
    
    .site-info {
        flex: 1;
    }
    
    .site-name {
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 0.25rem;
    }
    
    .site-type {
        font-size: 0.85rem;
        color: #888;
    }
    
    /* Spinner */
    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        background: var(--card-color);
        border-radius: var(--border-radius);
        margin: 2rem 0;
        border: 2px dashed rgba(178, 34, 34, 0.3);
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 4px solid rgba(178, 34, 34, 0.1);
        border-top: 4px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1.5rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Badge */
    .badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #b22222, #dc3545);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 0.25rem;
    }
    
    .guest-badge {
        background: #6c757d;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
    }
    
    /* Progress Bar */
    .progress-container {
        background: var(--card-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin: 1rem 0;
        padding: 0.75rem;
        border-radius: 8px;
        background: var(--hover-bg);
    }
    
    .step-number {
        background: var(--primary-red);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    
    /* Input Alanları */
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 2px solid var(--border-color) !important;
        background: var(--card-color) !important;
        color: var(--text-color) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-red) !important;
        box-shadow: 0 0 0 3px rgba(178, 34, 34, 0.1) !important;
    }
    
    /* Chat Input */
    .stChatInput > div > div > input {
        border: 2px solid var(--primary-red) !important;
        border-radius: 25px !important;
        padding: 0.875rem 1.25rem !important;
        background: var(--card-color) !important;
        color: var(--text-color) !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--card-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Radio Butonları */
    .stRadio > div {
        background: var(--card-color);
        padding: 1rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .stRadio > div > label {
        color: var(--text-color) !important;
        font-weight: 500 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: var(--card-color);
        padding: 4px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-color) !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--hover-bg) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-red) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* PDF Butonu */
    .pdf-button-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    /* Rapor Alanı */
    .report-container {
        background: var(--card-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
        line-height: 1.8;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .report-container h3 {
        color: var(--primary-red) !important;
        margin-top: 0 !important;
    }
    
    .report-container p {
        margin-bottom: 1rem;
        color: var(--text-color);
    }
    
    /* Kopyalama Butonu */
    .copy-button {
        background: linear-gradient(135deg, #6c757d, #495057) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .login-container {
            margin: 1rem;
            padding: 1.5rem;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
        }
        
        .report-container {
            padding: 1rem;
            max-height: 400px;
        }
    }
    
    /* Motor Etiketleri */
    .motor-tag {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #b22222, #ff4444);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.25rem;
        box-shadow: 0 2px 8px rgba(178, 34, 34, 0.2);
    }
    
    /* Matematik Badge */
    .math-badge {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    /* Giriş Özellikleri */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin: 20px 0;
    }
    
    .feature-item {
        background: var(--hover-bg);
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 0.85rem;
        transition: all 0.3s ease;
    }
    
    .feature-item:hover {
        transform: translateY(-2px);
        background: rgba(178, 34, 34, 0.15);
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
        "current_site_index": 0,
        "pdf_generated": False
    }
    
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# --- 🔧 PROFESYONEL FONKSİYONLAR ---
def safe_eval_matematik(ifade):
    """Güvenli matematik değerlendirmesi"""
    try:
        # İzin verilen matematiksel karakterler ve fonksiyonlar
        guvenli_globals = {
            '__builtins__': None,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log10,
            'log10': math.log10,
            'log2': math.log2,
            'ln': math.log,
            'pi': math.pi,
            'e': math.e,
            'abs': abs,
            'round': round,
            'pow': pow,
            'max': max,
            'min': min,
            'sum': sum
        }
        
        # Temizleme: sadece güvenli karakterler
        guvenli_ifade = re.sub(r'[^0-9+\-*/(). sqrtcossintanlogpie]', '', ifade.lower())
        
        # Matematiksel fonksiyon kontrolü
        if any(func in guvenli_ifade for func in ['sqrt', 'sin', 'cos', 'tan', 'log', 'ln']):
            # Fonksiyon çağrılarını eval için hazırla
            result = eval(guvenli_ifade, {"__builtins__": {}}, guvenli_globals)
        else:
            # Basit matematik işlemleri
            result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        
        return result
    except:
        return None

def is_matematik_ifadesi(text):
    """Metnin matematiksel ifade olup olmadığını kontrol et"""
    matematik_karakterler = set('+-*/()0123456789. sqrtcossintanlog')
    matematik_kelimeler = ['sqrt', 'sin', 'cos', 'tan', 'log', 'ln', 'pi', 'e']
    
    text_lower = text.lower().replace(' ', '')
    
    # Matematik kelimeleri içeriyor mu?
    for kelime in matematik_kelimeler:
        if kelime in text_lower:
            return True
    
    # Matematik karakter oranı yüksek mi?
    matematik_char_count = sum(1 for char in text if char in matematik_karakterler)
    if matematik_char_count / max(len(text), 1) > 0.6:
        return True
    
    return False

def profesyonel_site_tara(url, sorgu, site_adi, timeout=8):
    """Profesyonel site tarama"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            return (site_adi, None, 0)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Reklamları temizle
        for element in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'header', 'aside', 'form', 'button']):
            element.decompose()
        
        # Ana içerik alanını bul
        icerik = ""
        
        # Öncelikle makale/ansiklopedi formatını ara
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
                    if len(text) > 150 and (sorgu.lower() in text.lower() or len(sorgu) < 3):
                        paragraphs = text.split('\n\n')
                        for para in paragraphs[:5]:  # İlk 5 paragraf
                            para = para.strip()
                            if len(para) > 80:
                                icerik += para + "\n\n"
                        if len(icerik) > 300:
                            break
                if len(icerik) > 300:
                    break
            except:
                continue
        
        # Paragraf arama
        if len(icerik) < 200:
            paragraphs = soup.find_all('p')
            for p in paragraphs[:10]:  # İlk 10 paragraf
                text = p.get_text().strip()
                if len(text) > 60:
                    icerik += text + "\n\n"
                    if len(icerik) > 400:
                        break
        
        # İçerik temizleme
        if icerik:
            # Reklamları temizle
            temizleme_listesi = [
                r'reklam.*', r'sponsor.*', r'kaydol.*', r'üye ol.*', r'abone ol.*',
                r'bizi takip edin.*', r'yorum yap.*', r'paylaş.*', r'satın al.*',
                r'indirim.*', r'kampanya.*', r'fırsat.*', r'sepete ekle.*',
                r'©.*', r'tüm hakları saklıdır.*', r'www\..*', r'\.com.*'
            ]
            
            for pattern in temizleme_listesi:
                icerik = re.sub(pattern, '', icerik, flags=re.IGNORECASE)
            
            icerik = re.sub(r'\s+', ' ', icerik).strip()
            
            # Kalite puanı
            puan = 0
            if 200 <= len(icerik) <= 1000:
                puan += 3
            elif len(icerik) > 1000:
                puan += 2
            elif len(icerik) > 100:
                puan += 1
            
            if icerik.count('.') + icerik.count(';') > 3:
                puan += 2
            
            return (site_adi, icerik[:1200], puan)
        
        return (site_adi, None, 0)
            
    except:
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
        }
    ]
    
    turk_siteleri.sort(key=lambda x: x['oncelik'], reverse=True)
    return turk_siteleri

def profesyonel_pdf_olustur():
    """Profesyonel PDF oluştur - Unicode desteğiyle"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Unicode desteği için özel ayar
        pdf.set_margins(15, 15, 15)
        
        # DejaVu font kontrolü
        font_paths = [
            'DejaVuSansCondensed.ttf',
            'fonts/DejaVuSansCondensed.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf'
        ]
        
        dejavu_found = False
        for path in font_paths:
            if os.path.exists(path):
                try:
                    # Unicode font ekle
                    pdf.add_font('DejaVu', '', path, uni=True)
                    pdf.add_font('DejaVu', 'B', path.replace('.ttf', '-Bold.ttf'), uni=True)
                    pdf.add_font('DejaVu', 'I', path.replace('.ttf', '-Oblique.ttf'), uni=True)
                    dejavu_found = True
                    break
                except:
                    continue
        
        if not dejavu_found:
            # Fallback: Standart Arial (daha az Unicode desteği)
            pdf.add_font('Arial', '', '', uni=True)
        
        # Başlık
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'B', 16)
        pdf.set_text_color(178, 34, 34)
        pdf.cell(0, 15, "TÜRKAI PROFESYONEL ANALİZ RAPORU", ln=True, align='C')
        
        # Çizgi
        pdf.set_draw_color(178, 34, 34)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # Rapor bilgileri
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        
        # Konu
        pdf.cell(30, 8, "Konu:", 0, 0)
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 12)
        konu = st.session_state.konu[:50] if st.session_state.konu else "Belirtilmemiş"
        pdf.cell(0, 8, konu, ln=True)
        
        # Tarih
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'B', 12)
        pdf.cell(30, 8, "Tarih:", 0, 0)
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 12)
        pdf.cell(0, 8, datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), ln=True)
        
        # Kullanıcı
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'B', 12)
        pdf.cell(30, 8, "Kullanıcı:", 0, 0)
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 12)
        user_text = str(st.session_state.user)
        if st.session_state.is_guest:
            user_text += " (Misafir)"
        pdf.cell(0, 8, user_text[:40], ln=True)
        
        pdf.ln(10)
        
        # İçerik başlığı
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'B', 14)
        pdf.set_text_color(178, 34, 34)
        pdf.cell(0, 10, "ANALİZ SONUÇLARI", ln=True)
        pdf.ln(5)
        
        # İçerik
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        if st.session_state.bilgi:
            icerik = str(st.session_state.bilgi)
            
            # HTML/Markdown temizleme
            icerik = re.sub(r'<[^>]*>', '', icerik)  # HTML tagları temizle
            icerik = re.sub(r'#+\s*', '', icerik)
            icerik = re.sub(r'\*\*', '', icerik)
            icerik = re.sub(r'\*', '', icerik)
            icerik = re.sub(r'`', '', icerik)
            icerik = re.sub(r'!\[.*?\]\(.*?\)', '', icerik)  # Resimleri temizle
            
            # Satırları işle
            lines = icerik.split('\n')
            max_lines = 200  # Maksimum satır sayısı
            
            for i, line in enumerate(lines[:max_lines]):
                line = line.strip()
                if line:
                    # Çok uzun satırları parçala
                    if len(line) > 80:
                        chunks = [line[j:j+80] for j in range(0, len(line), 80)]
                        for chunk in chunks:
                            if pdf.get_y() > 250:
                                pdf.add_page()
                                pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 10)
                            pdf.multi_cell(0, 5, chunk)
                            pdf.ln(2)
                    else:
                        if pdf.get_y() > 250:
                            pdf.add_page()
                            pdf.set_font('DejaVu' if dejavu_found else 'Arial', '', 10)
                        pdf.multi_cell(0, 5, line)
                        pdf.ln(2)
            
            if len(lines) > max_lines:
                if pdf.get_y() > 250:
                    pdf.add_page()
                pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'I', 9)
                pdf.multi_cell(0, 5, f"... ve {len(lines) - max_lines} satır daha (rapor kısaltıldı)")
        
        # Alt bilgi
        pdf.ln(15)
        pdf.set_font('DejaVu' if dejavu_found else 'Arial', 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "TürkAI Profesyonel Araştırma Sistemi", ln=True, align='C')
        pdf.cell(0, 5, "© 2024 - Tüm hakları saklıdır", ln=True, align='C')
        
        # PDF'yi bytes'a çevir
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    
    except Exception as e:
        # Basit fallback PDF
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "TURKAI RAPORU", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Konu: {st.session_state.konu[:30] if st.session_state.konu else 'Bilinmiyor'}", ln=True)
            pdf.cell(0, 10, f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}", ln=True)
            pdf.ln(10)
            
            if st.session_state.bilgi:
                icerik = str(st.session_state.bilgi)[:500] + "..." if len(str(st.session_state.bilgi)) > 500 else str(st.session_state.bilgi)
                icerik = icerik.replace('\n', ' ')
                pdf.multi_cell(0, 5, icerik)
            
            return pdf.output(dest='S').encode('latin-1', 'ignore')
        except:
            return None

# --- 🔐 YENİLENMİŞ GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Ana Başlık ve Logo
        st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='margin-bottom: 10px;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #666; font-size: 1.2rem; margin-top: -10px; font-weight: 500;'>
                Profesyonel Araştırma ve Analiz Sistemi
            </p>
            <div style='margin: 20px 0; padding: 15px; background: linear-gradient(135deg, rgba(178,34,34,0.1), rgba(220,53,69,0.1)); 
                    border-radius: 10px; border: 1px solid rgba(178,34,34,0.2);'>
                <p style='margin: 0; color: #b22222; font-weight: 600;'>
                    <span class='badge'>AI</span> Yapay Zeka Destekli 
                    <span class='badge'>🇹🇷</span> Türkçe Odaklı 
                    <span class='badge'>📊</span> Detaylı Analiz
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hızlı Erişim Butonları
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 HEMEN BAŞLA (Misafir)", 
                        use_container_width=True, 
                        type="primary",
                        help="Hesap oluşturmadan hızlı başla"):
                st.session_state.user = "Misafir_Kullanıcı"
                st.session_state.is_guest = True
                st.rerun()
        
        with col_b:
            st.markdown(f'<a href="{APK_URL}" target="_blank" style="text-decoration: none;">', unsafe_allow_html=True)
            if st.button("📱 MOBİL UYGULAMA", 
                        use_container_width=True, 
                        type="secondary",
                        help="Android uygulamasını indir"):
                pass
            st.markdown('</a>', unsafe_allow_html=True)
        
        # Giriş Konteyneri
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # Özellikler
        st.markdown("""
        <div class='login-header'>
            <h3 style='margin: 0; color: var(--primary-red);'>🎯 SİSTEM ÖZELLİKLERİ</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1_feat, col2_feat = st.columns(2)
        with col1_feat:
            st.markdown("""
            <div class='feature-grid'>
                <div class='feature-item'>🚀 Hızlı Arama</div>
                <div class='feature-item'>🔍 Derin Analiz</div>
                <div class='feature-item'>📚 Türkçe Kaynak</div>
                <div class='feature-item'>🧮 Matematik</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2_feat:
            st.markdown("""
            <div class='feature-grid'>
                <div class='feature-item'>📊 PDF Rapor</div>
                <div class='feature-item'>🛡️ Reklam Engelle</div>
                <div class='feature-item'>💾 Geçmiş Kayıt</div>
                <div class='feature-item'>📱 Mobil Uyum</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Uyarı
        st.markdown("""
        <div class='warning-card' style='margin: 20px 0;'>
            <div style='display: flex; align-items: flex-start; gap: 10px;'>
                <span style='font-size: 1.2rem;'>⚠️</span>
                <div>
                    <b>GEÇİCİ OTURUM:</b><br>
                    Misafir girişinde veriler oturum sonunda silinir. 
                    Kalıcı kayıt için lütfen hesap oluşturun.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Sekmeleri
        tab1, tab2 = st.tabs(["🔐 SİSTEM GİRİŞİ", "📝 YENİ KAYIT"])
        
        with tab1:
            st.markdown("### Mevcut Hesabınızla Giriş")
            
            u_in = st.text_input("Kullanıcı Adı", 
                                placeholder="Kullanıcı adınızı girin",
                                key="login_user")
            
            p_in = st.text_input("Şifre", 
                                type="password",
                                placeholder="Şifrenizi girin",
                                key="login_pass")
            
            if st.button("🔓 OTURUMU BAŞLAT", 
                        use_container_width=True, 
                        type="primary",
                        disabled=not (u_in and p_in)):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone():
                        st.session_state.user = u_in
                        st.session_state.is_guest = False
                        st.rerun()
                    else:
                        st.error("❌ Geçersiz kullanıcı adı veya şifre.")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun.")
        
        with tab2:
            st.markdown("### Yeni Hesap Oluştur")
            
            nu = st.text_input("Yeni Kullanıcı Adı",
                              placeholder="En az 3 karakter",
                              key="reg_user")
            
            np = st.text_input("Yeni Şifre",
                              type="password",
                              placeholder="En az 6 karakter",
                              key="reg_pass")
            
            np2 = st.text_input("Şifre Tekrar",
                               type="password",
                               placeholder="Şifreyi tekrar girin",
                               key="reg_pass2")
            
            if st.button("✅ HESAP OLUŞTUR", 
                        use_container_width=True, 
                        type="primary",
                        disabled=not (nu and np and np2)):
                if nu and np and np2:
                    if np == np2:
                        if len(np) >= 6:
                            if len(nu) >= 3:
                                try:
                                    c.execute("INSERT INTO users VALUES (?,?)", 
                                             (nu, hashlib.sha256(np.encode()).hexdigest()))
                                    conn.commit()
                                    st.success("✅ Hesap başarıyla oluşturuldu!")
                                    time.sleep(1)
                                    st.session_state.user = nu
                                    st.session_state.is_guest = False
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("❌ Bu kullanıcı adı zaten kullanımda.")
                            else:
                                st.error("❌ Kullanıcı adı en az 3 karakter olmalıdır.")
                        else:
                            st.error("❌ Şifre en az 6 karakter olmalıdır.")
                    else:
                        st.error("❌ Şifreler eşleşmiyor.")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid var(--border-color);'>
            <p style='color: #666; font-size: 0.9rem; margin: 5px 0;'>
                <strong>TürkAI v2.0</strong> | Profesyonel Araştırma Çözümleri
            </p>
            <p style='color: #888; font-size: 0.8rem; margin: 5px 0;'>
                © 2024 Tüm hakları saklıdır. | 🇹🇷 Made in Turkey
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 🚀 PROFESYONEL SIDEBAR ---
with st.sidebar:
    # Kullanıcı Bilgisi
    user_display = str(st.session_state.user)
    if st.session_state.is_guest:
        user_badge = "<span class='guest-badge'>Misafir</span>"
    else:
        user_badge = "<span class='badge'>Premium</span>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #b22222, #dc3545); 
                padding: 20px; 
                border-radius: var(--border-radius); 
                margin-bottom: 20px; 
                color: white;
                box-shadow: var(--shadow);'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div>
                <h4 style='color: white; margin: 0; font-size: 1.1rem;'>👤 {user_display[:15]}</h4>
                <div style='margin-top: 5px;'>{user_badge}</div>
            </div>
            <div style='font-size: 1.5rem;'>🇹🇷</div>
        </div>
        <p style='color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 0.85rem;'>
            {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Oturum Kapatma
    if st.button("🚪 OTURUMU SONLANDIR", 
                 use_container_width=True, 
                 type="secondary",
                 help="Mevcut oturumu kapatır"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi
    st.markdown("### 🎯 ANALİZ MOTORU")
    m_secim = st.radio(
        "",
        ["🚀 Birleşik Motor", "🤔 Derin Analiz + Matematik"],
        label_visibility="collapsed",
        key="motor_secim",
        help="Arama modunu seçin"
    )
    
    # Motor Açıklamaları
    if m_secim == "🚀 Birleşik Motor":
        st.info("""
        **Hızlı ve Özet Bilgi:**
        • Vikipedi + TDK
        • Matematik desteği
        • 5 saniye içinde sonuç
        """)
    else:
        st.info("""
        **Derin Analiz:**
        • 7 Türkçe site taraması
        • Matematik işlemleri
        • Site-site ilerleme
        • Detaylı içerik
        """)
    
    st.divider()
    
    # Geçmiş Aramalar
    st.markdown("### 📋 ARAMA GEÇMİŞİ")
    if not st.session_state.is_guest:
        c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
        results = c.fetchall()
        if results:
            for (konu,) in results:
                if konu and len(konu) > 1:
                    if st.button(f"📄 {konu[:22]}", 
                               key=f"h_{hashlib.md5(konu.encode()).hexdigest()[:8]}", 
                               use_container_width=True,
                               type="secondary",
                               help="Bu aramayı tekrar yükle"):
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
    if st.button("📲 MOBİL UYGULAMA İNDİR", 
                 use_container_width=True, 
                 type="primary",
                 help="Android uygulamasını indir"):
        pass
    st.markdown('</a>', unsafe_allow_html=True)

# --- 💻 ANA ARAYÜZ ---
st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h1>🔍 PROFESYONEL ARAŞTIRMA TERMİNALİ</h1>
    <p style='color: #666; font-size: 1rem; margin-top: 5px;'>
        Brave gibi reklam engelleme ile Türkçe analiz
    </p>
</div>
""", unsafe_allow_html=True)

# Arama Talimatı
st.markdown("""
<div class='info-card' style='text-align: center; background: linear-gradient(135deg, rgba(178,34,34,0.05), rgba(220,53,69,0.05));'>
    <p style='font-size: 1.1rem; margin: 0; color: var(--primary-red); font-weight: 600;'>
        🔎 Araştırmak istediğiniz konuyu yazınız
    </p>
    <p style='font-size: 0.9rem; margin: 8px 0 0 0; color: var(--text-color); opacity: 0.8;'>
        Örnekler: "Atatürk", "İstanbul", "45*2+18/3", "sqrt(16)", "Türk tarihi"
    </p>
</div>
""", unsafe_allow_html=True)

# Arama Çubuğu
sorgu = st.chat_input("🔍 Anahtar kelime veya matematik ifadesi yazın...")

if sorgu and sorgu.strip():
    sorgu = sorgu.strip()
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    st.session_state.aktif_site = 0
    st.session_state.site_sonuclari = []
    st.session_state.yap_butonu = False
    st.session_state.current_site_index = 0
    
    # Matematik kontrolü önce yap
    if is_matematik_ifadesi(sorgu):
        matematik_sonucu = safe_eval_matematik(sorgu)
        if matematik_sonucu is not None:
            # Matematik işlemi bulundu
            st.session_state.bilgi = f"# 🧮 MATEMATİKSEL İŞLEM SONUCU\n\n"
            st.session_state.bilgi += f"**İfade:** `{sorgu}`\n\n"
            st.session_state.bilgi += f"**Sonuç:** **{matematik_sonucu}**\n\n"
            
            # Ek bilgiler
            if isinstance(matematik_sonucu, (int, float)):
                st.session_state.bilgi += f"**Detaylı Bilgiler:**\n"
                st.session_state.bilgi += f"• Yaklaşık değer: `{matematik_sonucu:.6f}`\n"
                if matematik_sonucu >= 0:
                    st.session_state.bilgi += f"• Karekök: `{math.sqrt(matematik_sonucu):.6f}`\n"
                    st.session_state.bilgi += f"• Karesi: `{matematik_sonucu**2:.6f}`\n"
            
            st.session_state.konu = f"MATEMATİK: {sorgu}"
            st.session_state.arama_devam = False
    
    # Matematik değilse normal arama
    if not st.session_state.bilgi:
        with st.spinner(""):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(f"""
            <div class='spinner-container'>
                <div class='spinner'></div>
                <h3 style='color: #b22222;'>TÜRKAI ANALİZ EDİYOR</h3>
                <p>"{sorgu}" için araştırma yapılıyor...</p>
                <div style='margin-top: 20px;'>
                    <div class='progress-step'>
                        <div class='step-number'>1</div>
                        <div>Motor seçimi yapılıyor...</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            
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
                        rapor += f"## 📖 TDK Sözlük\n{tdk_icerik[:800]}...\n\n"
                    
                    if not wiki_icerik and (not tdk_icerik or len(tdk_icerik) < 50):
                        rapor = f"# ⚠️ SONUÇ BULUNAMADI\n\n'{sorgu}' için Türkçe kaynaklarda yeterli bilgi bulunamadı.\n\n**Öneri:** Daha genel bir terim deneyin veya Derin Analiz modunu kullanın."
                    
                    st.session_state.bilgi = rapor
                    st.session_state.konu = sorgu
                    
                except Exception as e:
                    st.session_state.bilgi = f"# ⚠️ TEKNİK HATA\n\nArama sırasında bir hata oluştu.\n\nLütfen daha sonra tekrar deneyin."
                    st.session_state.konu = sorgu
            
            elif m_secim == "🤔 Derin Analiz + Matematik":
                thinking_placeholder.empty()
                
                # Site listesini al ve ilk siteyi tara
                siteler = birlesik_motor_arama(sorgu)
                st.session_state.site_listesi = siteler
                
                if siteler:
                    # İlk siteyi tarayıp göster
                    site = siteler[0]
                    site_adi, icerik, puan = profesyonel_site_tara(site['url'], sorgu, site['adi'])
                    
                    if icerik and puan > 1:
                        st.session_state.current_site_index = 1
                        
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
                        st.session_state.bilgi = f"# ⚠️ İLK SİTEDE BİLGİ BULUNAMADI\n\n'YENİDEN YAP' butonuyla bir sonraki siteye geçebilirsiniz."
                        st.session_state.konu = sorgu
                        st.session_state.yap_butonu = True
                else:
                    st.session_state.bilgi = f"# ❌ SİTE BULUNAMADI\n\n'{sorgu}' için uygun site bulunamadı."
                    st.session_state.konu = sorgu
    
    st.session_state.arama_devam = False
    
    # Veritabanına kaydet (misafir değilse)
    if st.session_state.bilgi and not st.session_state.is_guest:
        try:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        except Exception as e:
            st.error(f"Kayıt hatası: {str(e)}")
    
    st.rerun()

# --- 🤔 DERİN ANALİZ MODU SİTE GEÇİŞİ ---
if m_secim == "🤔 Derin Analiz + Matematik" and st.session_state.yap_butonu and st.session_state.site_listesi:
    st.markdown("---")
    st.markdown("### 🏗️ SİTE GEÇİŞ SİSTEMİ")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class='info-card'>
            <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                <div class='badge'>{st.session_state.current_site_index}/{len(st.session_state.site_listesi)}</div>
                <div>
                    <p style='margin: 0;'><b>Geçerli Durum:</b> {st.session_state.current_site_index} site taranmıştır.</p>
                    <p style='margin: 5px 0 0 0; color: #666; font-size: 0.9rem;'>
                        Bir sonraki site için butona tıklayın.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 SONRAKİ SİTE", 
                     use_container_width=True, 
                     type="primary", 
                     key="sonraki_site",
                     disabled=st.session_state.current_site_index >= len(st.session_state.site_listesi)):
            if st.session_state.current_site_index < len(st.session_state.site_listesi):
                # Sonraki siteyi tara
                site = st.session_state.site_listesi[st.session_state.current_site_index]
                
                with st.spinner(f"{site['adi']} taranıyor..."):
                    site_adi, icerik, puan = profesyonel_site_tara(site['url'], st.session_state.son_sorgu, site['adi'])
                    
                    if icerik and puan > 1:
                        st.session_state.site_sonuclari.append({
                            'site': site_adi,
                            'icerik': icerik,
                            'puan': puan,
                            'tip': site['tip']
                        })
                        
                        # Yeni site bilgisini göster
                        rapor = f"# 🔍 {st.session_state.current_site_index + 1}. SİTE BULUNDU\n\n"
                        rapor += f"## {site_adi}\n"
                        rapor += f"*Kalite puanı: {puan}/10 • Tip: {site['tip']}*\n\n"
                        rapor += f"{icerik}\n\n"
                        
                        if st.session_state.current_site_index + 1 < len(st.session_state.site_listesi):
                            rapor += "---\n\n"
                            rapor += "**📌 Not:** 'SONRAKİ SİTE' butonuna tıklayarak bir sonraki siteye geçebilirsiniz."
                        
                        st.session_state.bilgi = rapor
                        st.success(f"✅ {site_adi} - Kalite: {puan}/10")
                        
                    else:
                        st.warning(f"⚠️ {site_adi}'de yeterli bilgi bulunamadı")
                        rapor = f"# ⚠️ SİTE TARANAMADI\n\n{site['adi']} sitesinde yeterli bilgi bulunamadı.\n\n"
                        
                        if st.session_state.current_site_index + 1 < len(st.session_state.site_listesi):
                            rapor += "Bir sonraki site için 'SONRAKİ SİTE' butonuna tıklayın."
                        
                        st.session_state.bilgi = rapor
                
                st.session_state.current_site_index += 1
                
                # Tüm siteler tarandıysa özet rapor oluştur
                if st.session_state.current_site_index >= len(st.session_state.site_listesi):
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
                            ozet_rapor += f"## 🏆 {i+1}. {sonuc['site']}\n"
                            ozet_rapor += f"*Kalite: {sonuc['puan']}/10 • Tip: {sonuc['tip']}*\n\n"
                            
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
        durum = "✅" if i < st.session_state.current_site_index else "⏳" if i == st.session_state.current_site_index else "◻️"
        st.markdown(f"""
        <div class='site-card {'active' if i == st.session_state.current_site_index else ''}'>
            <div class='site-icon'>{site['adi'].split(' ')[0]}</div>
            <div class='site-info'>
                <div class='site-name'>{site['adi']}</div>
                <div class='site-type'>{site['tip'].capitalize()} • {durum}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 📊 RAPOR GÖSTERİMİ ---
if st.session_state.son_sorgu and not st.session_state.arama_devam and st.session_state.bilgi:
    # Aktif Sorgu Bilgisi
    st.markdown("---")
    st.markdown(f"""
    <div class='info-card'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
            <div>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <strong style='color: #b22222; font-size: 1.1rem;'>🔍 AKTİF SORGUNUZ:</strong>
                    <span style='background: rgba(178, 34, 34, 0.1); padding: 6px 15px; border-radius: 20px; 
                                font-weight: 500; border: 1px solid rgba(178, 34, 34, 0.3);'>
                        {st.session_state.son_sorgu}
                    </span>
                </div>
                <div style='display: flex; flex-wrap: wrap; gap: 15px;'>
                    <span style='display: flex; align-items: center; gap: 5px;'>
                        <strong style='color: #b22222;'>🎯 MOD:</strong> {m_secim}
                    </span>
                    <span style='display: flex; align-items: center; gap: 5px;'>
                        <strong style='color: #b22222;'>👤 KULLANICI:</strong> 
                        {st.session_state.user}{" (Misafir)" if st.session_state.is_guest else ""}
                    </span>
                    <span style='display: flex; align-items: center; gap: 5px;'>
                        <strong style='color: #b22222;'>📅 TARİH:</strong>
                        {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
                    </span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rapor Gösterimi
    st.markdown("### 📄 ANALİZ RAPORU")
    
    # Kaydırılabilir rapor alanı
    report_html = f"""
    <div class="report-container">
        {st.session_state.bilgi}
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)
    
    # PDF İndirme Butonu
    st.markdown("---")
    st.markdown('<div class="pdf-button-container">', unsafe_allow_html=True)
    
    # PDF oluşturma butonu
    if st.button("📥 PROFESYONEL PDF RAPOR OLUŞTUR VE İNDİR",
                use_container_width=True,
                type="primary",
                key="pdf_olustur"):
        
        with st.spinner("PDF raporu oluşturuluyor..."):
            pdf_data = profesyonel_pdf_olustur()
            
            if pdf_data:
                # PDF'i indirme butonu olarak göster
                st.download_button(
                    label="✅ PDF'Yİ İNDİRMEK İÇİN TIKLAYIN",
                    data=pdf_data,
                    file_name=f"TurkAI_Raporu_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}_{st.session_state.konu[:20].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                st.success("PDF raporu başarıyla oluşturuldu!")
            else:
                st.error("PDF oluşturulurken bir hata oluştu. Lütfen daha kısa bir raporla deneyin.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Ek Butonlar
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 YENİ ARAMA", 
                     use_container_width=True, 
                     type="secondary", 
                     key="yeni_arama_2"):
            st.session_state.son_sorgu = None
            st.session_state.bilgi = None
            st.session_state.site_sonuclari = []
            st.session_state.yap_butonu = False
            st.session_state.current_site_index = 0
            st.rerun()
    
    with col2:
        # Kopyalama butonu
        if st.button("📋 RAPORU KOPYALA", 
                     use_container_width=True, 
                     type="secondary", 
                     key="kopyala_2"):
            try:
                # Raporu temizle
                temiz_metin = st.session_state.bilgi
                temiz_metin = re.sub(r'<[^>]*>', '', temiz_metin)
                temiz_metin = re.sub(r'#+\s*', '', temiz_metin)
                temiz_metin = re.sub(r'\*\*(.*?)\*\*', r'\1', temiz_metin)
                temiz_metin = re.sub(r'\*', '', temiz_metin)
                temiz_metin = re.sub(r'`', '', temiz_metin)
                
                kopya_metni = f"TürkAI Raporu\n"
                kopya_metni += f"Konu: {st.session_state.konu}\n"
                kopya_metni += f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                kopya_metni += "=" * 50 + "\n\n"
                kopya_metni += temiz_metin
                
                # JavaScript ile panoya kopyala
                js_code = f"""
                <script>
                function copyToClipboard() {{
                    const text = `{kopya_metni.replace('`', '\\`').replace('$', '\\$')}`;
                    navigator.clipboard.writeText(text).then(() => {{
                        console.log('Metin kopyalandı');
                    }}).catch(err => {{
                        console.error('Kopyalama hatası:', err);
                    }});
                }}
                copyToClipboard();
                </script>
                """
                st.components.v1.html(js_code, height=0)
                st.info("✅ Rapor panoya kopyalandı! Ctrl+V ile yapıştırabilirsiniz.")
                
            except Exception as e:
                st.error(f"Kopyalama hatası: {str(e)}")
                with st.expander("Raporu kopyalamak için tıklayın"):
                    st.code(kopya_metni[:2000] + "..." if len(kopya_metni) > 2000 else kopya_metni, language='text')
    
    with col3:
        if st.button("💾 GEÇMİŞE KAYDET", 
                     use_container_width=True, 
                     type="secondary", 
                     disabled=st.session_state.is_guest,
                     key="kaydet_2"):
            if not st.session_state.is_guest:
                try:
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                             (st.session_state.user, st.session_state.konu, 
                              st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
                    conn.commit()
                    st.success("✅ Arama geçmişe kaydedildi!")
                except Exception as e:
                    st.error(f"Kayıt hatası: {str(e)}")
            else:
                st.warning("⚠️ Misafir modunda kayıt yapılamaz")

# --- 📱 MOBİL UYARI ---
st.markdown("""
<div style='margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border-color); text-align: center;'>
    <p style='color: #666; font-size: 0.9rem;'>
        <strong>📱 MOBİL KULLANIM:</strong> Daha iyi deneyim için mobil uygulamamızı indirin!
    </p>
    <p style='color: #888; font-size: 0.8rem; margin-top: 5px;'>
        🇹🇷 TürkAI v2.0 | Profesyonel Araştırma Sistemi
    </p>
</div>
""", unsafe_allow_html=True)
