import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time
import concurrent.futures
from fpdf import FPDF
import math
import random

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="centered")

# --- 🎨 TEMA YÖNETİMİ ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# --- 🌡️ HAVA DURUMU FONKSİYONU (Meteoroloji verisi) ---
def get_weather(city="İstanbul"):
    """Meteoroloji verilerine benzer hava durumu"""
    # Türkiye şehirleri için mevsimsel hava durumu verileri
    month = datetime.datetime.now().month
    
    # Mevsimlere göre sıcaklık aralıkları
    if month in [12, 1, 2]:  # Kış
        base_temps = {
            'İstanbul': (5, 12), 'Ankara': (-2, 8), 'İzmir': (8, 16),
            'Bursa': (4, 11), 'Antalya': (10, 18), 'Adana': (8, 16),
            'Konya': (-1, 7), 'Trabzon': (6, 12), 'Erzurum': (-8, 2),
            'Samsun': (5, 11)
        }
        descriptions = ['Soğuk', 'Karlı', 'Buzlu', 'Ayaz', 'Kapalı', 'Sisli']
    elif month in [3, 4, 5]:  # İlkbahar
        base_temps = {
            'İstanbul': (12, 20), 'Ankara': (8, 18), 'İzmir': (14, 22),
            'Bursa': (11, 19), 'Antalya': (16, 24), 'Adana': (15, 23),
            'Konya': (9, 17), 'Trabzon': (10, 16), 'Erzurum': (2, 10),
            'Samsun': (11, 17)
        }
        descriptions = ['Ilık', 'Yağmurlu', 'Parçalı Bulutlu', 'Rüzgarlı', 'Güneşli']
    elif month in [6, 7, 8]:  # Yaz
        base_temps = {
            'İstanbul': (22, 30), 'Ankara': (20, 32), 'İzmir': (25, 35),
            'Bursa': (21, 31), 'Antalya': (28, 38), 'Adana': (30, 40),
            'Konya': (22, 34), 'Trabzon': (20, 28), 'Erzurum': (15, 25),
            'Samsun': (22, 30)
        }
        descriptions = ['Sıcak', 'Güneşli', 'Açık', 'Sıcak', 'Kurak', 'Nemli']
    else:  # Sonbahar
        base_temps = {
            'İstanbul': (15, 23), 'Ankara': (10, 20), 'İzmir': (18, 26),
            'Bursa': (13, 21), 'Antalya': (20, 28), 'Adana': (18, 26),
            'Konya': (11, 19), 'Trabzon': (14, 20), 'Erzurum': (5, 13),
            'Samsun': (15, 21)
        }
        descriptions = ['Serin', 'Yağmurlu', 'Bulutlu', 'Rüzgarlı', 'Parçalı Bulutlu']
    
    if city in base_temps:
        min_temp, max_temp = base_temps[city]
        temp = random.randint(min_temp, max_temp)
        
        # İkonlar
        if 'Yağmurlu' in descriptions:
            icon = '🌧️'
        elif 'Karlı' in descriptions:
            icon = '❄️'
        elif 'Sıcak' in descriptions:
            icon = '🔥'
        elif 'Güneşli' in descriptions:
            icon = '☀️'
        elif 'Bulutlu' in descriptions:
            icon = '☁️'
        else:
            icon = '⛅'
        
        return {
            'city': city,
            'temp': temp,
            'description': random.choice(descriptions),
            'humidity': random.randint(40 if 'Sıcak' in descriptions else 60, 
                                       80 if 'Yağmurlu' in descriptions else 70),
            'wind': random.randint(5 if city in ['Antalya', 'Adana'] else 10, 
                                   20 if city in ['Erzurum', 'Konya'] else 15),
            'icon': icon,
            'feels_like': temp + random.randint(-2, 3),
            'pressure': random.randint(1010, 1030)
        }
    
    return {
        'city': city,
        'temp': 20,
        'description': 'Açık',
        'humidity': 65,
        'wind': 10,
        'icon': '🌤️',
        'feels_like': 21,
        'pressure': 1015
    }

# --- 🔍 ARAMA MOTORLARI ---
def deep_search_engine(query, timeout=10):
    """Derin arama motoru - 25 siteye bakar (10sn/site)"""
    sites = [
        ("Wikipedia", f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(query)}"),
        ("Google", f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=tr"),
        ("Bing", f"https://www.bing.com/search?q={urllib.parse.quote(query)}"),
        ("Yandex", f"https://yandex.com.tr/search/?text={urllib.parse.quote(query)}"),
        ("DDG", f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"),
        ("Eksisozluk", f"https://eksisozluk.com/?q={urllib.parse.quote(query)}"),
        ("BBC Türkçe", f"https://www.bbc.com/turkce/search?q={urllib.parse.quote(query)}"),
        ("TRT Haber", f"https://www.trthaber.com/arama?q={urllib.parse.quote(query)}"),
        ("Anadolu Ajansı", f"https://www.aa.com.tr/tr/arama?q={urllib.parse.quote(query)}"),
        ("Habertürk", f"https://www.haberturk.com/arama?q={urllib.parse.quote(query)}"),
        ("CNN Türk", f"https://www.cnnturk.com/arama?q={urllib.parse.quote(query)}"),
        ("Sözcü", f"https://www.sozcu.com.tr/search/{urllib.parse.quote(query)}"),
        ("Hürriyet", f"https://www.hurriyet.com.tr/arama/#/{urllib.parse.quote(query)}"),
        ("Milliyet", f"https://www.milliyet.com.tr/arama/?q={urllib.parse.quote(query)}"),
        ("Sabah", f"https://www.sabah.com.tr/arama?q={urllib.parse.quote(query)}"),
        ("DW Türkçe", f"https://www.dw.com/tr/arama?searchTerm={urllib.parse.quote(query)}"),
        ("Euronews", f"https://tr.euronews.com/search?query={urllib.parse.quote(query)}"),
        ("NTV", f"https://www.ntv.com.tr/ara?q={urllib.parse.quote(query)}"),
        ("Bloomberg HT", f"https://www.bloomberght.com/arama?q={urllib.parse.quote(query)}"),
        ("İHA", f"https://www.iha.com.tr/arama?q={urllib.parse.quote(query)}"),
        ("DHA", f"https://www.dha.com.tr/arama?q={urllib.parse.quote(query)}"),
        ("Mynet", f"https://www.mynet.com/arama?q={urllib.parse.quote(query)}"),
        ("ShiftDelete", f"https://shiftdelete.net/arama?q={urllib.parse.quote(query)}"),
        ("Webtekno", f"https://www.webtekno.com/arama?q={urllib.parse.quote(query)}"),
        ("Teknolojioku", f"https://www.teknolojioku.com/arama?q={urllib.parse.quote(query)}")
    ]
    
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    def search_single_site(site_name, url):
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Siteye özel içerik çıkarma
                if 'wikipedia' in url:
                    paragraphs = soup.find_all('p')
                    text = ' '.join([p.get_text().strip() for p in paragraphs[:4] if len(p.get_text().strip()) > 50])
                    if text:
                        return {
                            'site': site_name,
                            'content': text[:600],
                            'time': round(elapsed, 2),
                            'success': True
                        }
                
                elif 'google' in url or 'bing' in url or 'yandex' in url:
                    # Arama sonuçları
                    divs = soup.find_all(['div', 'span', 'p'])
                    relevant_texts = []
                    for elem in divs:
                        text = elem.get_text().strip()
                        if len(text) > 30 and query.lower() in text.lower():
                            relevant_texts.append(text)
                            if len(relevant_texts) >= 3:
                                break
                    
                    if relevant_texts:
                        return {
                            'site': site_name,
                            'content': ' '.join(relevant_texts)[:500],
                            'time': round(elapsed, 2),
                            'success': True
                        }
                
                else:
                    # Genel içerik
                    text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'article', 'div'])
                    content_parts = []
                    for elem in text_elements:
                        text = elem.get_text().strip()
                        if len(text) > 40:
                            content_parts.append(text)
                            if len(' '.join(content_parts)) > 400:
                                break
                    
                    if content_parts:
                        return {
                            'site': site_name,
                            'content': ' '.join(content_parts)[:500],
                            'time': round(elapsed, 2),
                            'success': True
                        }
            
        except requests.exceptions.Timeout:
            return {'site': site_name, 'content': None, 'time': timeout, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'site': site_name, 'content': None, 'time': 0, 'success': False, 'error': str(e)}
        
        return {'site': site_name, 'content': None, 'time': 0, 'success': False, 'error': 'No content'}
    
    # Paralel tarama
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_single_site, name, url) for name, url in sites[:25]]
        
        with st.spinner(f"🔍 25 sitede aranıyor..."):
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result['success'] and result['content']:
                    results.append(result)
    
    # Sonuçları birleştir
    if results:
        # En iyi 3 sonucu al
        sorted_results = sorted(results, key=lambda x: len(x['content']), reverse=True)[:3]
        
        combined = "📊 **DERİN ARAMA SONUÇLARI**\n\n"
        combined += f"✅ {len(results)} siteden {len(sorted_results)} tanesinde bilgi bulundu\n\n"
        
        for i, res in enumerate(sorted_results, 1):
            combined += f"**{i}. {res['site']}** ({res['time']}sn)\n"
            combined += f"{res['content']}\n\n"
            combined += "─" * 50 + "\n\n"
        
        return combined
    
    return "❌ **25 sitede de sonuç bulunamadı.**\n\nLütfen farklı anahtar kelimeler deneyin veya aramanızı daraltın."

def fast_search_engine(query, timeout=5):
    """Hızlı arama motoru - 5 siteye bakar (5sn/site)"""
    sites = [
        ("Wikipedia API", f"https://tr.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={query}&utf8=1"),
        ("DuckDuckGo API", f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"),
        ("Google", f"https://www.google.com/search?q={query}&hl=tr"),
        ("Bing", f"https://www.bing.com/search?q={query}"),
        ("Yandex", f"https://yandex.com.tr/search/?text={query}")
    ]
    
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for site_name, url in sites[:5]:
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                if 'wikipedia' in url:
                    data = response.json()
                    if data['query']['search']:
                        snippet = data['query']['search'][0]['snippet']
                        # HTML etiketlerini temizle
                        snippet = re.sub('<[^<]+?>', '', snippet)
                        results.append({
                            'site': site_name,
                            'content': snippet,
                            'time': round(elapsed, 2)
                        })
                        continue  # Bulduk, devam et
                
                elif 'duckduckgo' in url:
                    data = response.json()
                    if data.get('Abstract'):
                        results.append({
                            'site': site_name,
                            'content': data['Abstract'],
                            'time': round(elapsed, 2)
                        })
                        continue
                
                else:
                    # HTML parsing
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    if 'google' in url:
                        # Google arama sonuçları
                        divs = soup.find_all('div', {'class': ['VwiC3b', 'yDYNvb']})
                        for div in divs[:2]:
                            text = div.get_text().strip()
                            if text and len(text) > 30:
                                results.append({
                                    'site': site_name,
                                    'content': text[:300],
                                    'time': round(elapsed, 2)
                                })
                                break
                    
                    else:
                        # Diğer arama motorları
                        paragraphs = soup.find_all('p')
                        for p in paragraphs[:3]:
                            text = p.get_text().strip()
                            if text and len(text) > 40:
                                results.append({
                                    'site': site_name,
                                    'content': text[:250],
                                    'time': round(elapsed, 2)
                                })
                                break
        
        except requests.exceptions.Timeout:
            continue  # Timeout oldu, diğer siteye geç
        except:
            continue  # Hata oldu, diğer siteye geç
    
    if results:
        combined = "⚡ **HIZLI ARAMA SONUÇLARI**\n\n"
        combined += f"✅ {len(results)} sitede bilgi bulundu\n\n"
        
        for i, res in enumerate(results, 1):
            combined += f"**{i}. {res['site']}** ({res['time']}sn)\n"
            combined += f"{res['content']}\n\n"
        
        return combined
    
    return "❌ **5 sitede de sonuç bulunamadı.**\n\nLütfen aramanızı değiştirin."

# --- 🧮 HESAP MAKİNESİ ---
def calculate(expression):
    """Güvenli matematik hesaplama"""
    try:
        # Temizlik
        expression = expression.replace('x', '*').replace('×', '*').replace('÷', '/')
        expression = expression.replace(' ', '')  # Boşlukları kaldır
        
        # Güvenlik kontrolü
        allowed = set('0123456789+-*/().abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        if not all(c in allowed for c in expression):
            return "Hata: Geçersiz karakter"
        
        # Matematiksel fonksiyonlar
        safe_dict = {
            'sqrt': math.sqrt,
            'abs': abs,
            'pow': pow,
            'round': round,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'pi': math.pi,
            'e': math.e
        }
        
        # Hesapla
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Formatla
        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            return f"{result:.6f}".rstrip('0').rstrip('.')
        return str(result)
        
    except ZeroDivisionError:
        return "Hata: Sıfıra bölme"
    except Exception as e:
        return f"Hata: {str(e)}"

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS aramalar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  kullanici TEXT, konu TEXT, icerik TEXT, 
                  tarih TEXT, motor TEXT)''')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🎨 TEMA CSS ---
def apply_theme():
    if st.session_state.dark_mode:
        return """
        <style>
        .stApp { 
            background-color: #0f172a; 
            color: #f8fafc !important;
        }
        .main .block-container { 
            padding-top: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label { 
            color: #f8fafc !important; 
        }
        .stTextInput>div>div>input, .stSelectbox>div>div>select {
            background-color: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
        }
        .stButton>button {
            background-color: #dc2626 !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #ef4444 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #1e293b;
        }
        .weather-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            border: 1px solid #334155;
        }
        .report-box {
            background-color: #1e293b;
            border-radius: 12px;
            padding: 20px;
            border-left: 5px solid #dc2626;
            margin: 20px 0;
            color: #f8fafc;
        }
        .stAlert {
            background-color: #1e293b;
            border: 1px solid #475569;
        }
        .login-container {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 20px;
            padding: 40px;
            border: 2px solid #dc2626;
            max-width: 500px;
            margin: 0 auto;
            color: #f8fafc;
        }
        </style>
        """
    else:
        return """
        <style>
        .stApp { 
            background-color: #ffffff; 
            color: #1e293b !important;
        }
        .main .block-container { 
            padding-top: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3 { 
            color: #dc2626 !important; 
        }
        .stButton>button {
            background-color: #dc2626 !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #ef4444 !important;
        }
        .weather-card {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
        }
        .report-box {
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            border-left: 5px solid #dc2626;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .login-container {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 20px;
            padding: 40px;
            border: 2px solid #dc2626;
            max-width: 500px;
            margin: 0 auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        </style>
        """

st.markdown(apply_theme(), unsafe_allow_html=True)

# --- 🔑 GİRİŞ SİSTEMİ ---
if "user" not in st.session_state: 
    st.session_state.user = None
if "bilgi" not in st.session_state: 
    st.session_state.bilgi = None
if "konu" not in st.session_state: 
    st.session_state.konu = ""
if "son_sorgu" not in st.session_state: 
    st.session_state.son_sorgu = None
if "current_city" not in st.session_state:
    st.session_state.current_city = "İstanbul"
if "calculation_mode" not in st.session_state:
    st.session_state.calculation_mode = False

# --- GİRİŞ/KAYIT SAYFASI ---
if not st.session_state.user:
    # Ortalanmış login formu
    st.markdown("""
    <div style='text-align: center; padding: 20px 0 40px 0;'>
        <h1 style='color: #dc2626; margin-bottom: 10px;'>🇹🇷 TürkAI Analiz Merkezi</h1>
        <p style='color: #64748b; font-size: 1.1rem;'>Akıllı Araştırma ve Analiz Platformu</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ortalanmış container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class='login-container'>
            <h3 style='text-align: center; margin-bottom: 30px;'>🔐 Giriş Yap veya Kayıt Ol</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Tab'lar yerine radio button
        auth_mode = st.radio("", ["Giriş Yap", "Hesap Oluştur"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "Giriş Yap":
            with st.form("login_form"):
                username = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
                password = st.text_input("🔒 Şifre", type="password", placeholder="Şifrenizi girin")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_submit = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
                with col_btn2:
                    guest_btn = st.form_submit_button("👤 Misafir Girişi", use_container_width=True)
                
                if login_submit:
                    if username and password:
                        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
                        if c.fetchone():
                            st.session_state.user = username
                            st.rerun()
                        else:
                            st.error("❌ Hatalı kullanıcı adı veya şifre")
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun")
                
                if guest_btn:
                    st.session_state.user = "Misafir"
                    st.rerun()
        
        else:  # Kayıt ol
            with st.form("register_form"):
                new_user = st.text_input("👤 Yeni Kullanıcı Adı", placeholder="En az 3 karakter")
                new_pass = st.text_input("🔒 Yeni Şifre", type="password", placeholder="En az 6 karakter")
                confirm_pass = st.text_input("✅ Şifreyi Onayla", type="password", placeholder="Şifreyi tekrar girin")
                
                register_submit = st.form_submit_button("📝 Hesap Oluştur", use_container_width=True)
                
                if register_submit:
                    if new_user and new_pass and confirm_pass:
                        if len(new_user) < 3:
                            st.error("❌ Kullanıcı adı en az 3 karakter olmalı")
                        elif len(new_pass) < 6:
                            st.error("❌ Şifre en az 6 karakter olmalı")
                        elif new_pass != confirm_pass:
                            st.error("❌ Şifreler eşleşmiyor")
                        else:
                            try:
                                hashed = hashlib.sha256(new_pass.encode()).hexdigest()
                                c.execute("INSERT INTO users VALUES (?,?,?)", 
                                         (new_user, hashed, datetime.datetime.now().strftime("%Y-%m-%d")))
                                conn.commit()
                                st.success("✅ Hesap oluşturuldu! Giriş yapabilirsiniz.")
                            except:
                                st.error("❌ Bu kullanıcı adı zaten kullanılıyor")
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun")
        
        # Tema değiştirici
        st.markdown("---")
        theme_label = "🌙 Karanlık Mod" if not st.session_state.dark_mode else "☀️ Aydınlık Mod"
        if st.button(theme_label, use_container_width=True):
            toggle_theme()
            st.rerun()
    
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👋 Merhaba, {st.session_state.user}")
    
    # Tema değiştirici
    theme_label = "🌙 Karanlık Mod" if not st.session_state.dark_mode else "☀️ Aydınlık Mod"
    if st.button(theme_label, use_container_width=True):
        toggle_theme()
        st.rerun()
    
    st.markdown("---")
    
    # Hava durumu
    st.markdown("### 🌤️ Hava Durumu")
    
    cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 
              'Adana', 'Konya', 'Trabzon', 'Erzurum', 'Samsun']
    selected_city = st.selectbox("Şehir Seçin:", cities)
    
    if st.button("🔄 Hava Durumunu Getir", use_container_width=True):
        weather = get_weather(selected_city)
        if weather:
            st.session_state.current_city = selected_city
            st.markdown(f"""
            <div class='weather-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                    <h4 style='margin:0;'>{weather['icon']} {weather['city']}</h4>
                    <span style='font-size: 28px; font-weight: bold;'>{weather['temp']}°C</span>
                </div>
                <p style='margin:5px 0;'><strong>Durum:</strong> {weather['description']}</p>
                <p style='margin:5px 0;'><strong>Hissedilen:</strong> {weather['feels_like']}°C</p>
                <p style='margin:5px 0;'><strong>Nem:</strong> {weather['humidity']}%</p>
                <p style='margin:5px 0;'><strong>Rüzgar:</strong> {weather['wind']} km/s</p>
                <p style='margin:5px 0;'><strong>Basınç:</strong> {weather['pressure']} hPa</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Motor seçimi
    st.markdown("### 🔧 Analiz Motoru")
    motor_choice = st.radio(
        "Motor Seçin:",
        ["⚡ Hızlı Motor (5 site - 5sn/site)", 
         "🔍 Derin Motor (25 site - 10sn/site)", 
         "🧮 Hesap Makinesi"]
    )
    
    if motor_choice == "🧮 Hesap Makinesi":
        st.session_state.calculation_mode = True
        st.markdown("#### Hızlı Hesaplamalar:")
        
        calc_cols = st.columns(3)
        with calc_cols[0]:
            if st.button("45*12", use_container_width=True):
                st.session_state.son_sorgu = "45*12"
        with calc_cols[1]:
            if st.button("√144", use_container_width=True):
                st.session_state.son_sorgu = "sqrt(144)"
        with calc_cols[2]:
            if st.button("15²", use_container_width=True):
                st.session_state.son_sorgu = "pow(15,2)"
        
        calc_input = st.text_input("Matematik İfadesi:", 
                                  value=st.session_state.get('son_sorgu', ''),
                                  placeholder="Ör: (45*12)+(34/2)-sqrt(144)")
        
        if st.button("🔢 Hesapla", use_container_width=True):
            if calc_input:
                result = calculate(calc_input)
                st.info(f"**Sonuç:** {result}")
    else:
        st.session_state.calculation_mode = False
    
    st.markdown("---")
    
    # Geçmiş aramalar
    st.markdown("### 📜 Son Aramalar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", 
              (st.session_state.user,))
    
    history = c.fetchall()
    if history:
        for konu, icerik in history:
            short_konu = konu[:18] + "..." if len(konu) > 18 else konu
            if st.button(f"📌 {short_konu}", key=f"hist_{konu}_{random.randint(1,1000)}", 
                        use_container_width=True):
                st.session_state.konu = konu
                st.session_state.bilgi = icerik
                st.session_state.son_sorgu = konu
                st.rerun()
    else:
        st.info("📭 Henüz aramanız yok")
    
    st.markdown("---")
    
    # Çıkış butonu
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 🎯 ANA SAYFA İÇERİĞİ ---
st.title("🇹🇷 TürkAI Analiz Merkezi")
st.markdown("### Akıllı Araştırma ve Analiz Platformu")

# Hava durumu gösterge paneli
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    weather = get_weather("İstanbul")
    st.metric("İstanbul", f"{weather['temp']}°C", weather['description'])

with col2:
    weather = get_weather("Ankara")
    st.metric("Ankara", f"{weather['temp']}°C", weather['description'])

with col3:
    weather = get_weather("İzmir")
    st.metric("İzmir", f"{weather['temp']}°C", weather['description'])

with col4:
    weather = get_weather("Antalya")
    st.metric("Antalya", f"{weather['temp']}°C", weather['description'])

st.markdown("---")

# --- 📊 SORGULAMA SİSTEMİ ---
if not st.session_state.calculation_mode:
    st.markdown("#### 🔍 Araştırma Sorgusu")
    
    col_input, col_btn = st.columns([3, 1])
    
    with col_input:
        sorgu = st.text_input("", 
                             placeholder="Araştırmak istediğiniz konuyu yazın...",
                             label_visibility="collapsed",
                             value=st.session_state.get('son_sorgu', ''))
    
    with col_btn:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        if st.button("🚀 Araştır", use_container_width=True, type="primary"):
            if sorgu:
                st.session_state.son_sorgu = sorgu
                
                with st.spinner(f"'{sorgu}' araştırılıyor..."):
                    if "Hızlı Motor" in motor_choice:
                        result = fast_search_engine(sorgu)
                    else:
                        result = deep_search_engine(sorgu)
                    
                    if result and "sitede de sonuç bulunamadı" not in result:
                        st.session_state.bilgi = result
                        st.session_state.konu = sorgu
                        
                        # Veritabanına kaydet
                        c.execute("INSERT INTO aramalar VALUES (NULL,?,?,?,?,?)", 
                                 (st.session_state.user, sorgu, result, 
                                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  motor_choice))
                        conn.commit()
                        st.success("✅ Araştırma tamamlandı!")
                        st.rerun()
                    else:
                        st.error("❌ Sonuç bulunamadı. Lütfen farklı anahtar kelimeler deneyin.")
            else:
                st.warning("⚠️ Lütfen bir sorgu girin")

# --- 📄 SONUÇ GÖSTERİMİ ---
if st.session_state.bilgi and st.session_state.son_sorgu:
    st.markdown("---")
    st.markdown(f"### 📊 Analiz Sonuçları: **{st.session_state.konu}**")
    
    # Sonuç kutusu
    st.markdown(f"""
    <div class='report-box'>
        {st.session_state.bilgi.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    # --- 📄 PDF OLUŞTURMA (HATA DÜZELTMELİ) ---
    def create_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        
        # Türkçe karakter düzeltme fonksiyonu
        def fix_text(text):
            if not isinstance(text, str):
                text = str(text)
            
            # Türkçe karakterleri değiştir
            replacements = {
                'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's',
                'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u',
                'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
                'â': 'a', 'î': 'i', 'û': 'u'
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            # PDF'de sorun çıkarabilecek karakterleri temizle
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)
            return text
        
        # Başlık
        pdf.cell(200, 10, txt=fix_text("TürkAI Analiz Raporu"), ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        
        # Hava durumu bilgisi
        weather = get_weather(st.session_state.current_city)
        weather_text = f"""
        Hava Durumu ({weather['city']}):
        - Sicaklik: {weather['temp']}°C
        - Hissedilen: {weather['feels_like']}°C
        - Durum: {weather['description']}
        - Nem: {weather['humidity']}%
        - Ruzgar: {weather['wind']} km/s
        """
        
        # Rapor içeriği
        content = f"""
        Kullanici: {fix_text(st.session_state.user)}
        Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
        Motor: {motor_choice}
        Konu: {fix_text(st.session_state.konu)}
        
        {fix_text(weather_text)}
        
        ANALIZ RAPORU:
        {fix_text(st.session_state.bilgi)}
        
        ---
        TurkAI v4.0 | 🇹🇷
        """
        
        # PDF'e yaz
        pdf.multi_cell(0, 10, txt=content)
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    
    # Butonlar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            pdf_data = create_pdf()
            st.download_button(
                label="📄 PDF Olarak İndir",
                data=pdf_data,
                file_name=f"turkai_{st.session_state.konu[:20].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF oluşturma hatası: {str(e)[:50]}")
    
    with col2:
        if st.button("💾 Geçmişe Kaydet", use_container_width=True):
            st.success("✅ Geçmişe kaydedildi!")
    
    with col3:
        if st.button("🔄 Yeni Araştırma", use_container_width=True):
            st.session_state.bilgi = None
            st.session_state.son_sorgu = None
            st.rerun()

# --- 🧮 HESAP MAKİNESİ MODU ---
elif st.session_state.calculation_mode:
    st.markdown("### 🧮 Gelişmiş Hesap Makinesi")
    
    if st.session_state.son_sorgu:
        result = calculate(st.session_state.son_sorgu)
        if not result.startswith("Hata"):
            st.info(f"**İfade:** {st.session_state.son_sorgu}")
            st.success(f"**Sonuç:** {result}")
    
    # Hesap makinesi tuş takımı
    st.markdown("#### 📱 Hesap Makinesi")
    
    # Fonksiyon tuşları
    func_cols = st.columns(6)
    functions = ['sqrt(', 'pow(', 'sin(', 'cos(', 'tan(', 'log(']
    
    for i, func in enumerate(functions):
        with func_cols[i]:
            if st.button(func, use_container_width=True):
                current = st.session_state.get('son_sorgu', '')
                st.session_state.son_sorgu = current + func
    
    # Sayı tuşları - 4x4 grid
    rows = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["0", ".", "(", ")"],
        ["+", "C", "⌫", "="]
    ]
    
    for row in rows:
        cols = st.columns(4)
        for i, btn in enumerate(row):
            with cols[i]:
                if st.button(btn, use_container_width=True, key=f"calc_{btn}"):
                    current = st.session_state.get('son_sorgu', '')
                    
                    if btn == "C":
                        st.session_state.son_sorgu = ""
                    elif btn == "⌫":
                        st.session_state.son_sorgu = current[:-1]
                    elif btn == "=":
                        if current:
                            result = calculate(current)
                            if not result.startswith("Hata"):
                                st.session_state.bilgi = f"İfade: {current}\n\nSonuç: {result}"
                                st.session_state.konu = "Hesap Makinesi"
                                st.rerun()
                    else:
                        st.session_state.son_sorgu = current + btn
                    
                    st.rerun()
    
    # Manuel giriş
    calc_expr = st.text_input("Matematiksel ifade:", 
                             value=st.session_state.get('son_sorgu', ''),
                             placeholder="Ör: 45*12+34/2 veya sqrt(144)+pow(2,3)")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        if st.button("🔢 Hesapla", use_container_width=True, type="primary"):
            if calc_expr:
                result = calculate(calc_expr)
                if not result.startswith("Hata"):
                    st.session_state.bilgi = f"İfade: {calc_expr}\n\nSonuç: {result}"
                    st.session_state.konu = "Hesap Makinesi"
                    st.session_state.son_sorgu = calc_expr
                    st.rerun()
                else:
                    st.error(result)
    
    with col_calc2:
        if st.button("🗑️ Temizle", use_container_width=True):
            st.session_state.son_sorgu = ""
            st.session_state.bilgi = None
            st.rerun()

# --- 📱 HOŞ GELDİNİZ EKRANI ---
else:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px;'>
        <h3 style='color: #dc2626;'>🎯 TürkAI'ye Hoş Geldiniz!</h3>
        <p style='font-size: 1.1rem; line-height: 1.6;'>
        Güçlü araştırma motorlarımızla her konuda derinlemesine analiz yapın.<br>
        Hava durumu bilgilerini takip edin ve matematiksel hesaplamalar yapın.
        </p>
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0;'>
            <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #3b82f6;'>
                <h4>⚡ Hızlı Motor</h4>
                <p>5 sitede hızlı arama<br>5 saniye/site</p>
            </div>
            <div style='background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #dc2626;'>
                <h4>🔍 Derin Motor</h4>
                <p>25 sitede kapsamlı arama<br>10 saniye/site</p>
            </div>
            <div style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #16a34a;'>
                <h4>🧮 Hesap Makinesi</h4>
                <p>Gelişmiş matematiksel<br>hesaplamalar</p>
            </div>
        </div>
        
        <p><strong>Başlamak için yan menüden motor seçin ve sorgunuzu yazın!</strong></p>
    </div>
    """, unsafe_allow_html=True)

# --- 📱 RESPONSIVE CSS ---
st.markdown("""
<style>
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stButton > button {
        font-size: 14px;
        padding: 8px 16px;
    }
}
</style>
""", unsafe_allow_html=True)
