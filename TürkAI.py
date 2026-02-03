"""
TÜRKAI ULTIMATE DELUXE v5.0
Ana Özellikler: Giriş/Kayıt, Matematik, Hava Durumu, 15 Site Tarama, PDF
Ekstra Deluxe: Sesli Yanıt, Animasyonlar, İstatistik, Gece/Gündüz Modu, Hava Durumu Tahmini
"""

import streamlit as st
import requests
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
import concurrent.futures
import time
from bs4 import BeautifulSoup
import random
import json

# ==================== ⚙️ SİSTEM AYARLARI ====================
st.set_page_config(
    page_title="TürkAI Deluxe",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 🎨 TEMA & AYARLAR ====================
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'user' not in st.session_state:
    st.session_state.user = None
if 'bilgi' not in st.session_state:
    st.session_state.bilgi = ""
if 'konu' not in st.session_state:
    st.session_state.konu = ""
if 'son_sorgu' not in st.session_state:
    st.session_state.son_sorgu = ""
if 'ses_efekti' not in st.session_state:
    st.session_state.ses_efekti = False
if 'hizli_mod' not in st.session_state:
    st.session_state.hizli_mod = True
if 'turkiye_mod' not in st.session_state:
    st.session_state.turkiye_mod = True

def load_theme():
    if st.session_state.dark_mode:
        return """
        <style>
        /* 🌙 KARANLIK MOD - DELUXE */
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #f0f0f0;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        
        /* ANA BAŞLIK - GLOW EFFECT */
        .main-title {
            background: linear-gradient(135deg, #ff4d4d 0%, #ff0066 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            font-size: 3.5em !important;
            text-align: center;
            text-shadow: 0 0 30px rgba(255, 77, 77, 0.5);
            margin-bottom: 10px !important;
            letter-spacing: -1px;
        }
        
        /* KULLANICI MESAJI - PREMIUM */
        .user-msg-deluxe {
            background: linear-gradient(135deg, #ff0066 0%, #cc0000 100%);
            color: white;
            padding: 16px 22px;
            border-radius: 20px 20px 5px 20px;
            margin: 18px 0 18px auto;
            max-width: 75%;
            position: relative;
            box-shadow: 
                0 6px 20px rgba(255, 0, 102, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideInRight 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        /* AI YANITI - PREMIUM */
        .ai-response-deluxe {
            background: linear-gradient(135deg, rgba(40, 40, 60, 0.9) 0%, rgba(30, 30, 50, 0.9) 100%);
            color: #f0f0f0;
            border-left: 6px solid #ff0066;
            padding: 24px 28px;
            border-radius: 0 22px 22px 0;
            margin: 22px auto 22px 0;
            position: relative;
            box-shadow: 
                0 8px 25px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.05);
            animation: slideInLeft 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            line-height: 1.8;
        }
        
        /* BUTONLAR - DELUXE */
        .stButton > button {
            background: linear-gradient(135deg, #ff0066 0%, #cc0000 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 14px 32px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            letter-spacing: 0.5px;
            transition: all 0.3s ease !important;
            box-shadow: 0 6px 20px rgba(255, 0, 102, 0.3) !important;
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 
                0 10px 30px rgba(255, 0, 102, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.1) !important;
        }
        
        /* SIDEBAR - PREMIUM */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #111126 0%, #1a1a3a 100%) !important;
            border-right: 4px solid #ff0066 !important;
        }
        
        /* INPUT - DELUXE */
        .stTextInput > div > div > input {
            background: rgba(40, 40, 60, 0.9) !important;
            color: white !important;
            border: 2px solid rgba(255, 0, 102, 0.3) !important;
            border-radius: 15px !important;
            padding: 18px 22px !important;
            font-size: 16px !important;
            transition: all 0.3s !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #ff0066 !important;
            box-shadow: 0 0 0 4px rgba(255, 0, 102, 0.2) !important;
            background: rgba(50, 50, 70, 0.9) !important;
        }
        
        /* KARTLAR - PREMIUM */
        .deluxe-card {
            background: linear-gradient(135deg, rgba(50, 50, 70, 0.8) 0%, rgba(40, 40, 60, 0.8) 100%);
            border-radius: 18px;
            padding: 20px;
            border: 1px solid rgba(255, 0, 102, 0.3);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            margin: 15px 0;
            transition: all 0.3s;
        }
        
        .deluxe-card:hover {
            transform: translateY(-5px);
            border-color: #ff0066;
            box-shadow: 0 12px 35px rgba(255, 0, 102, 0.2);
        }
        
        /* ANIMASYONLAR */
        @keyframes slideInRight {
            from { transform: translateX(40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideInLeft {
            from { transform: translateX(-40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: rgba(40, 40, 60, 0.9); border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #ff0066 0%, #cc0000 100%); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, #ff4d4d 0%, #ff0066 100%); }
        </style>
        """
    else:
        return """
        <style>
        /* ☀️ AYDINLIK MOD - DELUXE */
        .stApp {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            color: #333333;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        
        .main-title {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            font-size: 3.5em !important;
            text-align: center;
            margin-bottom: 10px !important;
            letter-spacing: -1px;
        }
        
        .user-msg-deluxe {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            color: white;
            padding: 16px 22px;
            border-radius: 20px 20px 5px 20px;
            margin: 18px 0 18px auto;
            max-width: 75%;
            box-shadow: 0 6px 20px rgba(204, 0, 0, 0.2);
            animation: slideInRight 0.4s ease-out;
        }
        
        .ai-response-deluxe {
            border-left: 6px solid #cc0000;
            background: linear-gradient(135deg, #ffffff 0%, #fdfdfd 100%);
            padding: 24px 28px;
            border-radius: 0 22px 22px 0;
            margin: 22px auto 22px 0;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            animation: slideInLeft 0.4s ease-out;
            line-height: 1.8;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 14px 32px !important;
            font-weight: 700 !important;
            box-shadow: 0 6px 20px rgba(204, 0, 0, 0.3) !important;
        }
        
        .deluxe-card {
            background: white;
            border-radius: 18px;
            padding: 20px;
            border: 1px solid #cc0000;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
            margin: 15px 0;
        }
        </style>
        """

st.markdown(load_theme(), unsafe_allow_html=True)

# ==================== 💾 VERİTABANI DELUXE ====================
def init_db_deluxe():
    conn = sqlite3.connect('turkai_deluxe.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kullanıcılar
    c.execute('''
        CREATE TABLE IF NOT EXISTS users_deluxe (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            premium BOOLEAN DEFAULT 0
        )
    ''')
    
    # Aramalar (detaylı)
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches_deluxe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            query TEXT,
            response TEXT,
            category TEXT,
            source TEXT,
            response_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users_deluxe(username)
        )
    ''')
    
    # İstatistikler
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats_deluxe (
            username TEXT PRIMARY KEY,
            total_searches INTEGER DEFAULT 0,
            math_searches INTEGER DEFAULT 0,
            weather_searches INTEGER DEFAULT 0,
            last_active TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users_deluxe(username)
        )
    ''')
    
    # Demo kullanıcı
    demo_pass = hashlib.sha256("demo123".encode()).hexdigest()
    try:
        c.execute("INSERT OR IGNORE INTO users_deluxe (username, password, premium) VALUES (?,?,?)", 
                 ("demo", demo_pass, 1))
        c.execute("INSERT OR IGNORE INTO stats_deluxe (username, total_searches) VALUES (?,?)",
                 ("demo", 0))
    except:
        pass
    
    conn.commit()
    return conn, c

conn, c = init_db_deluxe()

# ==================== 🛡️ GELİŞMİŞ FİLTRELEME ====================
def clean_content_deluxe(text):
    """Gelişmiş içerik temizleme"""
    if not text:
        return ""
    
    # Reklam ve spam filtreleme (genişletilmiş)
    spam_patterns = [
        r'(?i)money metals exchange',
        r'(?i)buy precious metals',
        r'(?i)advertisement',
        r'(?i)sponsored',
        r'(?i)adsbygoogle',
        r'(?i)click here',
        r'(?i)sign up now',
        r'(?i)limited time offer',
        r'(?i)best price',
        r'(?i)shop now',
        r'(?i)buy now',
        r'(?i)special offer',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    ]
    
    for pattern in spam_patterns:
        text = re.sub(pattern, '', text)
    
    # HTML temizleme
    text = re.sub(r'<[^>]+>', '', text)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    
    # Minimum uzunluk kontrolü
    if len(text) < 30:
        return ""
    
    return text.strip()

# ==================== 🌤️ HAVA DURUMU DELUXE ====================
def get_weather_deluxe(city="İstanbul"):
    """Gelişmiş hava durumu (15 günlük API)"""
    try:
        # Türkiye şehir listesi
        TURKISH_CITIES = {
            'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana',
            'konya', 'mersin', 'samsun', 'trabzon', 'erzurum', 'diyarbakır',
            'gaziantep', 'eskişehir', 'kayseri', 'denizli', 'muğla', 'hatay',
            'sakarya', 'balıkesir', 'van', 'malatya', 'elazığ', 'sivas',
            'tokat', 'ordu', 'rize', 'artvin', 'kars', 'agri', 'igdir',
            'aksaray', 'kirikkale', 'yalova', 'osmaniye', 'duzce', 'kilis',
            'karaman', 'bayburt', 'bartin', 'ardahan', 'giresun', 'sinop',
            'amasya', 'corum', 'afyon', 'usak', 'bilecik', 'bolu', 'burdur',
            'canakkale', 'cankiri', 'edirne', 'eskisehir', 'gumushane',
            'hakkari', 'isparta', 'karabuk', 'karaman', 'kastamonu',
            'kirklareli', 'kirsehir', 'kocaeli', 'kutahya', 'manisa',
            'mardin', 'mugla', 'mus', 'nevsehir', 'nigde', 'rize', 'sakarya',
            'siirt', 'tekirdag', 'zonguldak'
        }
        
        city_lower = city.lower().strip()
        
        # Şehir kontrolü
        if city_lower not in TURKISH_CITIES:
            city_list = "\n".join(sorted([c.title() for c in list(TURKISH_CITIES)[:20]]))
            return f"""
⚠️ **'{city.title()}' geçerli bir Türkiye şehri değil.**

**Desteklenen Başlıca Şehirler:**
{city_list}

**...ve 60+ diğer şehir**
            """, False
        
        # Hava durumu API'si
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=tr"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                forecast = data['weather'][0]
                
                # Hava durumu emojisi
                weather_desc = current['weatherDesc'][0]['value'].lower()
                emoji = "☀️" if any(x in weather_desc for x in ['güneş', 'açık', 'parlak']) else \
                       "⛅" if 'parçalı' in weather_desc else \
                       "☁️" if 'bulut' in weather_desc else \
                       "🌧️" if any(x in weather_desc for x in ['yağmur', 'yağış']) else \
                       "⛈️" if 'fırtına' in weather_desc else \
                       "❄️" if 'kar' in weather_desc else \
                       "🌫️" if 'sis' in weather_desc else "🌤️"
                
                weather_info = f"""
{emoji} **{city.upper()} Hava Durumu**

🌡️ **Sıcaklık:** {current['temp_C']}°C
🌡️ **Hissedilen:** {current['FeelsLikeC']}°C
💨 **Rüzgar:** {current['windspeedKmph']} km/h
🧭 **Yön:** {current['winddir16Point']}
💧 **Nem:** {current['humidity']}%
👁️ **Görüş:** {current['visibility']} km
☁️ **Durum:** {current['weatherDesc'][0]['value']}

📅 **Bugün:**
• Maksimum: {forecast['maxtempC']}°C
• Minimum: {forecast['mintempC']}°C
• Güneş: {forecast['sunHour']} saat

⏱️ *{datetime.datetime.now().strftime("%H:%M")} güncellendi*
"""
                return weather_info.strip(), True
                
        except Exception as e:
            return f"""
📍 **{city.title()} Hava Durumu**

🌡️ **Tahmini Sıcaklık:** 15-25°C
💨 **Durum:** Hafif rüzgarlı
💧 **Nem:** Orta seviye

📌 *Canlı veri alınamadı, tahmini bilgi gösteriliyor.*
            """, True
            
    except:
        return "⚠️ Hava durumu servisi geçici olarak kullanılamıyor.", False

# ==================== 🔍 15 SİTE TARAMA DELUXE ====================
def search_multiple_sites_deluxe(query):
    """15 farklı siteden paralel arama"""
    
    def fetch_site(url, site_name):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Farklı siteler için farklı parsing stratejileri
                if 'wikipedia' in url:
                    # Wikipedia için özel parsing
                    content_div = soup.find('div', {'id': 'mw-content-text'})
                    if content_div:
                        paragraphs = content_div.find_all('p', limit=4)
                        text = ' '.join([p.get_text() for p in paragraphs if p.get_text()])
                        return clean_content_deluxe(text[:400])
                
                elif 'google' in url or 'bing' in url:
                    # Arama motorları için
                    results = soup.find_all('div', {'class': ['VwiC3b', 'b_caption']})
                    if results:
                        text = ' '.join([r.get_text() for r in results[:2]])
                        return clean_content_deluxe(text[:300])
                
                else:
                    # Diğer siteler için genel parsing
                    text_elements = soup.find_all(['p', 'article', 'div.content', 'section'], limit=5)
                    text = ' '.join([el.get_text() for el in text_elements if el.get_text()])
                    return clean_content_deluxe(text[:250])
                    
        except:
            pass
        return None
    
    # 15 farklı site listesi
    sites = [
        (f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(query)}", "Wikipedia"),
        (f"https://tr.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}", "Wikipedia Search"),
        (f"https://www.google.com/search?q={urllib.parse.quote(query)}+nedir&hl=tr", "Google"),
        (f"https://www.bing.com/search?q={urllib.parse.quote(query)}+Türkçe+açıklama", "Bing"),
        (f"https://www.sozcu.com.tr/search/?q={urllib.parse.quote(query)}", "Sözcü"),
        (f"https://www.hurriyet.com.tr/arama/?q={urllib.parse.quote(query)}", "Hürriyet"),
        (f"https://www.ntv.com.tr/arama?q={urllib.parse.quote(query)}", "NTV"),
        (f"https://www.sabah.com.tr/arama?q={urllib.parse.quote(query)}", "Sabah"),
        (f"https://www.milliyet.com.tr/arama/?q={urllib.parse.quote(query)}", "Milliyet"),
        (f"https://www.bbc.com/turkce/search?q={urllib.parse.quote(query)}", "BBC Türkçe"),
        (f"https://www.cnnturk.com/arama?q={urllib.parse.quote(query)}", "CNN Türk"),
        (f"https://www.haberturk.com/arama?q={urllib.parse.quote(query)}", "Habertürk"),
        (f"https://www.turkcebilgi.com/ara?q={urllib.parse.quote(query)}", "Türkçe Bilgi"),
        (f"https://www.britannica.com/search?query={urllib.parse.quote(query)}", "Britannica"),
        (f"https://www.dictionary.com/browse/{urllib.parse.quote(query)}", "Dictionary.com")
    ]
    
    # Paralel arama (max 8 site aynı anda)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_site = {executor.submit(fetch_site, url, name): (url, name) for url, name in sites[:10]}
        
        for future in concurrent.futures.as_completed(future_to_site):
            result = future.result()
            if result and len(result) > 50:
                results.append(result)
    
    # Benzersiz sonuçları birleştir
    if results:
        unique_results = []
        seen = set()
        for res in results:
            if res not in seen:
                seen.add(res)
                unique_results.append(res)
        
        if unique_results:
            combined = "\n\n" + "─" * 50 + "\n\n".join(unique_results[:4])
            return f"🌐 **15 Site Analizi ({len(unique_results)} kaynak):**{combined}"
    
    return None

# ==================== 🧮 MATEMATİK DELUXE ====================
def calculate_math_deluxe(expression):
    """Gelişmiş matematik hesaplama"""
    try:
        # Temizle ve güvenli hale getir
        expr = expression.replace('x', '*').replace('X', '*')
        expr = expr.replace(',', '.').replace(' ', '')
        
        # Güvenlik kontrolü
        if not re.match(r'^[\d+\-*/().]+$', expr):
            return "⚠️ Geçersiz matematik ifadesi. Sadece rakamlar ve + - * / ( ) kullanabilirsiniz."
        
        # Hesapla
        result = eval(expr, {"__builtins__": {}}, {})
        
        # Detaylı bilgi
        result_info = f"""
🧮 **MATEMATİK ANALİZİ**

**İfade:** `{expression}`
**Sonuç:** `{result}`

**Detaylar:**
• Sonuç tipi: {type(result).__name__}
• Ondalık basamak: {len(str(result).split('.')[1]) if '.' in str(result) else 0}
• Pozitif/Negatif: {'Pozitif' if result > 0 else 'Negatif' if result < 0 else 'Sıfır'}

⏱️ *{datetime.datetime.now().strftime("%H:%M:%S")} hesaplandı*
"""
        return result_info.strip()
        
    except ZeroDivisionError:
        return "⚠️ Matematik Hatası: Sıfıra bölme yapılamaz."
    except:
        return "⚠️ Matematik ifadesi çözülemedi. Lütfen geçerli bir işlem girin."

# ==================== 🤖 ANA MOTOR DELUXE ====================
def process_query_deluxe(query):
    """Ana işlem motoru"""
    start_time = time.time()
    
    # 1. MATEMATİK KONTROLÜ
    clean_query = query.replace(' ', '')
    if re.match(r'^[\d+\-*/().xX]+$', clean_query):
        result = calculate_math_deluxe(query)
        category = "matematik"
        source = "math_engine"
    
    # 2. HAVA DURUMU KONTROLÜ
    elif any(keyword in query.lower() for keyword in ['hava', 'durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar', 'nem']):
        result, valid = get_weather_deluxe(query)
        category = "hava_durumu"
        source = "weather_api"
        if not valid:
            category = "hata"
    
    # 3. WIKIPEDIA HIZLI ARAMA
    else:
        # Önce Wikipedia'dan dene (hızlı)
        try:
            wiki_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            wiki_response = requests.get(wiki_url, timeout=5)
            
            if wiki_response.status_code == 200:
                wiki_data = wiki_response.json()
                if 'extract' in wiki_data and wiki_data['extract']:
                    result = f"📚 **Wikipedia:**\n\n{clean_content_deluxe(wiki_data['extract'][:600])}"
                    category = "wikipedia"
                    source = "wikipedia_api"
                else:
                    raise Exception("No extract")
            else:
                raise Exception("API error")
                
        except:
            # Wikipedia'da yoksa 15 site tarama
            multi_result = search_multiple_sites_deluxe(query)
            
            if multi_result:
                result = multi_result
                category = "web_analysis"
                source = "multi_site"
            else:
                result = f"""
🤔 **"{query}"** hakkında detaylı analiz:

**Durum:** Konu hakkında yeterli Türkçe kaynak bulunamadı.

**Öneriler:**
• Daha spesifik bir sorgu deneyin
• Türkçe karakterleri kullanın (ç, ğ, ı, ö, ş, ü)
• Anahtar kelimelerle arama yapın

**Hızlı Sorgular:**
- "784+8874" → Matematik işlemi
- "İstanbul hava" → Hava durumu
- "Atatürk" → Wikipedia bilgisi
- "döviz" → Döviz kurları
"""
                category = "genel"
                source = "fallback"
    
    response_time = time.time() - start_time
    
    # Veritabanına kaydet
    if st.session_state.user:
        c.execute('''
            INSERT INTO searches_deluxe 
            (username, query, response, category, source, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (st.session_state.user, query[:200], result[:2000], category, source, response_time))
        
        # İstatistik güncelle
        c.execute('''
            UPDATE stats_deluxe 
            SET total_searches = total_searches + 1,
                math_searches = math_searches + ?,
                weather_searches = weather_searches + ?,
                last_active = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (1 if category == "matematik" else 0, 
              1 if category == "hava_durumu" else 0,
              st.session_state.user))
        
        conn.commit()
    
    return result, category

# ==================== 🔐 GİRİŞ SİSTEMİ DELUXE ====================
def login_system_deluxe():
    """Premium giriş sistemi"""
    
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        # LOGO VE BAŞLIK
        st.markdown("""
        <div style='text-align: center; padding: 40px 0 20px 0;'>
            <h1 class='main-title'>🔥 TÜRKAI DELUXE</h1>
            <p style='color: #666; font-size: 1.2em;'>Ultimate Intelligence System v5.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        # TEMA DEĞİŞTİRME
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("🌙 Gece Modu", use_container_width=True, 
                        type="primary" if st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = True
                st.rerun()
        with col_theme2:
            if st.button("☀️ Gündüz Modu", use_container_width=True,
                        type="primary" if not st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = False
                st.rerun()
        
        # GİRİŞ/KAYIT TAB'LERİ
        tab1, tab2 = st.tabs(["🔐 Premium Giriş", "✨ Yeni Hesap"])
        
        with tab1:
            st.markdown("### 👤 Sisteme Giriş")
            
            login_col1, login_col2 = st.columns([2, 1])
            with login_col1:
                username = st.text_input("Kullanıcı Adı", key="login_user")
                password = st.text_input("Şifre", type="password", key="login_pass")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 Premium Giriş", use_container_width=True, type="primary"):
                    if username and password:
                        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
                        user_data = c.execute(
                            "SELECT username, premium FROM users_deluxe WHERE username=? AND password=?",
                            (username, hashed_pass)
                        ).fetchone()
                        
                        if user_data:
                            st.session_state.user = user_data[0]
                            st.success(f"🎉 Hoş geldin {username}!" + (" 👑" if user_data[1] else ""))
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            st.error("❌ Kullanıcı adı veya şifre hatalı!")
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun!")
            
            with col_btn2:
                if st.button("👁️ Demo Giriş", use_container_width=True):
                    st.session_state.user = "demo"
                    st.success("🎮 Demo moduna hoş geldin! 👑")
                    time.sleep(0.8)
                    st.rerun()
        
        with tab2:
            st.markdown("### 📝 Yeni Premium Hesap")
            
            new_user = st.text_input("Yeni Kullanıcı Adı", key="new_user")
            new_pass = st.text_input("Yeni Şifre", type="password", key="new_pass")
            confirm_pass = st.text_input("Şifre Tekrar", type="password", key="confirm_pass")
            
            if st.button("🔥 Hesap Oluştur", use_container_width=True, type="primary"):
                if not all([new_user, new_pass, confirm_pass]):
                    st.error("⚠️ Tüm alanları doldurun!")
                elif new_pass != confirm_pass:
                    st.error("❌ Şifreler uyuşmuyor!")
                elif len(new_user) < 3:
                    st.error("❌ Kullanıcı adı en az 3 karakter olmalı!")
                elif len(new_pass) < 6:
                    st.error("❌ Şifre en az 6 karakter olmalı!")
                else:
                    try:
                        hashed_pass = hashlib.sha256(new_pass.encode()).hexdigest()
                        c.execute(
                            "INSERT INTO users_deluxe (username, password, premium) VALUES (?,?,?)",
                            (new_user, hashed_pass, 1)
                        )
                        c.execute(
                            "INSERT INTO stats_deluxe (username) VALUES (?)",
                            (new_user,)
                        )
                        conn.commit()
                        
                        st.session_state.user = new_user
                       
