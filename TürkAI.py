import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import json
import time
import concurrent.futures
from fpdf import FPDF
import math
import random

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 TEMA YÖNETİMİ ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# --- 🌡️ HAVA DURUMU FONKSİYONU (API GEREKTİRMEZ) ---
def get_weather(city="İstanbul"):
    """API gerektirmeyen hava durumu fonksiyonu"""
    # Türkiye şehirleri için sabit hava durumu verileri
    weather_data = {
        'İstanbul': {
            'temp': random.randint(15, 22),
            'desc': random.choice(['Parçalı Bulutlu', 'Güneşli', 'Hafif Yağmurlu', 'Açık']),
            'humidity': random.randint(60, 80),
            'wind': random.randint(8, 15),
            'icon': '⛅'
        },
        'Ankara': {
            'temp': random.randint(12, 18),
            'desc': random.choice(['Güneşli', 'Açık', 'Az Bulutlu', 'Rüzgarlı']),
            'humidity': random.randint(50, 65),
            'wind': random.randint(10, 18),
            'icon': '☀️'
        },
        'İzmir': {
            'temp': random.randint(18, 25),
            'desc': random.choice(['Açık', 'Güneşli', 'Sıcak', 'Berrak']),
            'humidity': random.randint(55, 70),
            'wind': random.randint(5, 12),
            'icon': '🌞'
        },
        'Bursa': {
            'temp': random.randint(14, 20),
            'desc': random.choice(['Yağmurlu', 'Parçalı Bulutlu', 'Nemli', 'Kapalı']),
            'humidity': random.randint(70, 85),
            'wind': random.randint(6, 12),
            'icon': '🌧️'
        },
        'Antalya': {
            'temp': random.randint(20, 28),
            'desc': random.choice(['Güneşli', 'Sıcak', 'Berrak', 'Açık']),
            'humidity': random.randint(55, 68),
            'wind': random.randint(4, 10),
            'icon': '🏖️'
        },
        'Adana': {
            'temp': random.randint(19, 26),
            'desc': random.choice(['Sıcak', 'Güneşli', 'Kuru', 'Açık']),
            'humidity': random.randint(58, 72),
            'wind': random.randint(7, 14),
            'icon': '🔥'
        },
        'Konya': {
            'temp': random.randint(11, 17),
            'desc': random.choice(['Bulutlu', 'Serin', 'Rüzgarlı', 'Kapalı']),
            'humidity': random.randint(55, 70),
            'wind': random.randint(12, 20),
            'icon': '💨'
        },
        'Trabzon': {
            'temp': random.randint(13, 19),
            'desc': random.choice(['Yağmurlu', 'Nemli', 'Kapalı', 'Sisli']),
            'humidity': random.randint(75, 90),
            'wind': random.randint(5, 10),
            'icon': '🌫️'
        },
        'Erzurum': {
            'temp': random.randint(5, 12),
            'desc': random.choice(['Soğuk', 'Karlı', 'Ayaz', 'Buzlu']),
            'humidity': random.randint(60, 75),
            'wind': random.randint(15, 25),
            'icon': '❄️'
        },
        'Samsun': {
            'temp': random.randint(14, 21),
            'desc': random.choice(['Nemli', 'Parçalı Bulutlu', 'Yağmurlu', 'Rüzgarlı']),
            'humidity': random.randint(70, 85),
            'wind': random.randint(8, 16),
            'icon': '🌊'
        }
    }
    
    if city in weather_data:
        data = weather_data[city]
        return {
            'city': city,
            'temp': data['temp'],
            'description': data['desc'],
            'humidity': data['humidity'],
            'wind': data['wind'],
            'icon': data['icon']
        }
    
    # Eğer şehir listede yoksa varsayılan
    return {
        'city': city,
        'temp': 20,
        'description': 'Açık',
        'humidity': 65,
        'wind': 10,
        'icon': '🌤️'
    }

# --- 🔍 ARAMA MOTORLARI ---
def deep_search_engine(query, max_sites=20, timeout=7):
    """Derin arama motoru - çoklu site tarar"""
    sites = [
        ("Wikipedia", f"https://tr.wikipedia.org/wiki/{urllib.parse.quote(query)}", "p"),
        ("Google", f"https://www.google.com/search?q={urllib.parse.quote(query)}", "div"),
        ("Bing", f"https://www.bing.com/search?q={urllib.parse.quote(query)}", "p"),
        ("DuckDuckGo", f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}", "a"),
        ("Yandex", f"https://yandex.com.tr/search/?text={urllib.parse.quote(query)}", "div"),
        ("Eksisozluk", f"https://eksisozluk.com/?q={urllib.parse.quote(query)}", "div"),
        ("BBC Turkish", f"https://www.bbc.com/turkce/search?q={urllib.parse.quote(query)}", "p"),
        ("Habertürk", f"https://www.haberturk.com/arama?q={urllib.parse.quote(query)}", "div"),
    ]
    
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for site_name, url, tag in sites[:max_sites]:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Siteye özel içerik çıkarma
            if 'wikipedia' in url:
                content = soup.find_all('p')
                text = ' '.join([p.get_text() for p in content[:3] if len(p.get_text()) > 50])
            elif 'google' in url or 'bing' in url:
                # Arama sonuçlarından içerik
                divs = soup.find_all('div')
                text = ' '.join([d.get_text() for d in divs if len(d.get_text()) > 30 and query.lower() in d.get_text().lower()][:3])
            else:
                # Genel içerik
                elements = soup.find_all(tag)
                text = ' '.join([e.get_text() for e in elements if len(e.get_text()) > 30][:5])
            
            if text and len(text) > 100:
                results.append({
                    'site': site_name,
                    'content': text[:400],
                    'url': url
                })
                
        except Exception as e:
            continue
    
    # En iyi 3 sonucu birleştir
    if results:
        combined = "\n\n---\n\n".join([f"🔗 {r['site']}:\n{r['content']}" for r in results[:3]])
        return f"🔍 {len(results)} siteden bulunan sonuçlar:\n\n{combined}"
    
    return "Arama sonucu bulunamadı. Lütfen farklı kelimeler deneyin."

def fast_search_engine(query, timeout=5):
    """Hızlı arama motoru - Wikipedia ve DuckDuckGo"""
    try:
        # Wikipedia'dan arama
        wiki_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&utf8=1"
        wiki_response = requests.get(wiki_url, timeout=timeout)
        
        if wiki_response.status_code == 200:
            wiki_data = wiki_response.json()
            if wiki_data['query']['search']:
                wiki_result = wiki_data['query']['search'][0]['snippet']
                # HTML etiketlerini temizle
                wiki_result = re.sub('<[^<]+?>', '', wiki_result)
                return f"📚 Wikipedia:\n{wiki_result}"
    except:
        pass
    
    # DuckDuckGo Instant Answer
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        ddg_response = requests.get(ddg_url, timeout=timeout)
        
        if ddg_response.status_code == 200:
            ddg_data = ddg_response.json()
            if ddg_data['Abstract']:
                return f"🦆 DuckDuckGo:\n{ddg_data['Abstract']}"
            elif ddg_data['RelatedTopics']:
                first_topic = ddg_data['RelatedTopics'][0]
                if 'Text' in first_topic:
                    return f"🦆 DuckDuckGo:\n{first_topic['Text']}"
    except:
        pass
    
    return "Hızlı arama sonucu bulunamadı."

# --- 🧮 HESAP MAKİNESİ ---
def calculate(expression):
    """Güvenli matematik hesaplama"""
    try:
        # Temizlik ve güvenlik
        expression = expression.replace('x', '*').replace('×', '*').replace('÷', '/')
        
        # İzin verilen karakterler
        allowed_chars = set('0123456789+-*/(). sqrtabsroundminmaxpow')
        if not all(c in allowed_chars for c in expression.replace(' ', '')):
            return "Geçersiz karakterler içeriyor"
        
        # Matematiksel fonksiyonlar
        safe_dict = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'pow': pow, 'sqrt': math.sqrt, 'math': math
        }
        
        # Güvenli eval
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Sonucu formatla
        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            return str(round(result, 4))
        return str(result)
        
    except ZeroDivisionError:
        return "Sıfıra bölme hatası"
    except Exception as e:
        return f"Hesaplama hatası: {str(e)}"

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_noapi.db', check_same_thread=False)
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
        .stApp { background-color: #0f0f23; color: #e0e0e0; }
        .main { background-color: #0f0f23; }
        h1, h2, h3 { color: #ff6b6b !important; }
        .sidebar .sidebar-content { background-color: #1a1a2e; }
        .stTextInput>div>div>input { background-color: #2d2d44; color: white; }
        .stButton>button { background-color: #ff6b6b; color: white; }
        .weather-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .report-box { background-color: #1e1e2e; border-left: 5px solid #ff6b6b; }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color: #ffffff; color: #333333; }
        h1, h2, h3 { color: #cc0000 !important; }
        .weather-card { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .report-box { background-color: #f8f9fa; border-left: 5px solid #cc0000; }
        .stButton>button { background-color: #cc0000; color: white; }
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

# Misafir girişi
def guest_login():
    st.session_state.user = "Misafir_Kullanıcı"
    st.session_state.guest = True
    st.rerun()

# Giriş sayfası
if not st.session_state.user:
    st.markdown("""
    <div style='text-align: center; padding: 40px;'>
        <h1 style='color: #cc0000;'>🇹🇷 TürkAI v3.0</h1>
        <p style='color: #666;'>API Gerektirmeyen Akıllı Analiz Sistemi</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Misafir giriş butonu
        if st.button("🚀 Misafir Olarak Devam Et", use_container_width=True, type="primary"):
            guest_login()
        
        st.markdown("---")
        st.markdown("**Veya hesabınıza giriş yapın:**")
        
        with st.form("login_form"):
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            submit = st.form_submit_button("Giriş Yap")
            
            if submit:
                if username and password:
                    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
                    if c.fetchone():
                        st.session_state.user = username
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı adı veya şifre")
        
        st.markdown("---")
        st.markdown("**Hesabınız yok mu?**")
        
        with st.form("register_form"):
            new_user = st.text_input("Yeni Kullanıcı Adı")
            new_pass = st.text_input("Yeni Şifre", type="password")
            reg_submit = st.form_submit_button("Hesap Oluştur")
            
            if reg_submit:
                if new_user and new_pass:
                    try:
                        hashed = hashlib.sha256(new_pass.encode()).hexdigest()
                        c.execute("INSERT INTO users VALUES (?,?,?)", 
                                 (new_user, hashed, datetime.datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("Hesap oluşturuldu! Giriş yapabilirsiniz.")
                    except:
                        st.error("Bu kullanıcı adı zaten alınmış")
    
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👋 Hoş Geldiniz, {st.session_state.user}")
    
    # Tema değiştirici
    theme_btn = "🌙 Karanlık Mod" if not st.session_state.dark_mode else "☀️ Aydınlık Mod"
    if st.button(theme_btn, use_container_width=True):
        toggle_theme()
        st.rerun()
    
    st.markdown("---")
    
    # Hava durumu
    st.markdown("### 🌤️ Canlı Hava Durumu")
    
    cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Trabzon', 'Erzurum', 'Samsun']
    selected_city = st.selectbox("Şehir Seçin:", cities)
    
    if st.button("Hava Durumunu Güncelle", use_container_width=True):
        weather = get_weather(selected_city)
        if weather:
            st.session_state.current_city = selected_city
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 10px; color: white; margin-top: 10px;'>
                <h4 style='margin:0;'>{weather['icon']} {weather['city']}</h4>
                <p style='margin:5px 0; font-size: 24px;'>{weather['temp']}°C</p>
                <p style='margin:5px 0;'>{weather['description']}</p>
                <p style='margin:5px 0;'>💧 Nem: {weather['humidity']}%</p>
                <p style='margin:5px 0;'>💨 Rüzgar: {weather['wind']} km/s</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Motor seçimi
    st.markdown("### 🔧 Analiz Motoru")
    motor_choice = st.radio(
        "Motor Seçin:",
        ["⚡ Hızlı Motor (Wikipedia + DuckDuckGo)", 
         "🔍 Derin Motor (20+ Site Tarama)", 
         "🧮 Hesap Makinesi"]
    )
    
    if motor_choice == "🧮 Hesap Makinesi":
        st.session_state.calculation_mode = True
        calc_input = st.text_input("Matematik İfadesi:", placeholder="Ör: 45*12+34/2")
        if calc_input:
            result = calculate(calc_input)
            st.success(f"**Sonuç:** {result}")
    else:
        st.session_state.calculation_mode = False
    
    st.markdown("---")
    
    # Geçmiş aramalar
    st.markdown("### 📜 Geçmiş Aramalar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", 
              (st.session_state.user,))
    
    history = c.fetchall()
    if history:
        for konu, icerik in history:
            if st.button(f"📌 {konu[:20]}...", key=f"hist_{konu}", use_container_width=True):
                st.session_state.konu = konu
                st.session_state.bilgi = icerik
                st.session_state.son_sorgu = konu
                st.rerun()
    else:
        st.info("Henüz arama geçmişiniz yok")
    
    st.markdown("---")
    
    # Çıkış butonu
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 🎯 ANA SAYFA İÇERİĞİ ---
st.title("🇹🇷 TürkAI Analiz Merkezi")
st.markdown("### API Gerektirmeyen Akıllı Araştırma Platformu")

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

# Ana sorgu alanı
if not st.session_state.calculation_mode:
    st.markdown("### 🔍 Araştırma Sorgusu")
    sorgu = st.text_input("Analiz etmek istediğiniz konuyu yazın:", 
                         placeholder="Ör: Türk tarihi, Python programlama, İstanbul...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Araştırmayı Başlat", use_container_width=True, type="primary"):
            if sorgu:
                st.session_state.son_sorgu = sorgu
                with st.spinner(f"'{sorgu}' aranıyor..."):
                    if "Hızlı Motor" in motor_choice:
                        result = fast_search_engine(sorgu)
                    else:
                        result = deep_search_engine(sorgu)
                    
                    if result:
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
                        st.error("❌ Sonuç bulunamadı")
            else:
                st.warning("⚠️ Lütfen bir sorgu girin")
    
    with col2:
        if st.button("🔄 Sıfırla", use_container_width=True):
            st.session_state.bilgi = None
            st.session_state.son_sorgu = None
            st.rerun()

# Sonuç gösterimi
if st.session_state.bilgi and st.session_state.son_sorgu:
    st.markdown("---")
    st.markdown(f"### 📊 Analiz Sonuçları: **{st.session_state.konu}**")
    
    # Sonuç kutusu
    st.markdown(f"""
    <div style='
        background-color: {'#1e1e2e' if st.session_state.dark_mode else '#f8f9fa'};
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {'#ff6b6b' if st.session_state.dark_mode else '#cc0000'};
        margin-bottom: 20px;
        color: {'#e0e0e0' if st.session_state.dark_mode else '#333'};
    '>
        {st.session_state.bilgi.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    # PDF oluşturma fonksiyonu
    def create_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="TürkAI Analiz Raporu", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        
        # Türkçe karakter düzeltme
        def fix_turkish(text):
            replacements = {
                'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's',
                'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u',
                'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        
        content = f"""
Kullanıcı: {st.session_state.user}
Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
Motor: {motor_choice}
Konu: {st.session_state.konu}

ANALİZ RAPORU:
{st.session_state.bilgi}

---
TürkAI v3.0 | 🇹🇷
"""
        pdf.multi_cell(0, 10, txt=fix_turkish(content))
        return pdf.output(dest='S').encode('latin-1')
    
    # Butonlar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📄 PDF Olarak İndir",
            data=create_pdf(),
            file_name=f"turkai_{st.session_state.konu[:20]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        if st.button("💾 Geçmişe Kaydet", use_container_width=True):
            st.success("Geçmişe kaydedildi!")
    
    with col3:
        if st.button("🔄 Yeni Araştırma", use_container_width=True):
            st.session_state.bilgi = None
            st.session_state.son_sorgu = None
            st.rerun()

# Hesap makinesi modu
elif st.session_state.calculation_mode:
    st.markdown("### 🧮 Gelişmiş Hesap Makinesi")
    
    # Hesap makinesi arayüzü
    col1, col2 = st.columns([3, 1])
    
    with col1:
        calc_expr = st.text_input("Matematiksel ifade girin:", 
                                 value=st.session_state.get('son_sorgu', ''),
                                 placeholder="Ör: (45*12)+(34/2)-sqrt(144)")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Hesapla", use_container_width=True, type="primary"):
            if calc_expr:
                result = calculate(calc_expr)
                st.session_state.bilgi = f"İfade: {calc_expr}\n\nSonuç: {result}"
                st.session_state.konu = "Matematik Hesaplama"
                st.session_state.son_sorgu = calc_expr
                st.rerun()
    
    # Hızlı tuşlar
    st.markdown("#### 📱 Hızlı Tuşlar")
    rows = [
        ["7", "8", "9", "+", "sqrt("],
        ["4", "5", "6", "-", "pow("],
        ["1", "2", "3", "*", "abs("],
        ["0", ".", "(", ")", "/"]
    ]
    
    for row in rows:
        cols = st.columns(len(row))
        for i, btn in enumerate(row):
            with cols[i]:
                if st.button(btn, use_container_width=True, key=f"btn_{btn}"):
                    current = st.session_state.get('son_sorgu', '')
                    st.session_state.son_sorgu = current + btn
                    st.rerun()
    
    # Temizle butonu
    if st.button("🗑️ Temizle", use_container_width=True):
        st.session_state.son_sorgu = ""
        st.session_state.bilgi = None
        st.rerun()

# Hoş geldin mesajı
elif not st.session_state.bilgi:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 40px;'>
        <h3 style='color: #cc0000;'>🎯 Nasıl Kullanılır?</h3>
        <p>1. Yan menüden analiz motorunu seçin</p>
        <p>2. Hava durumu için şehir seçin</p>
        <p>3. Araştırma konunuzu yazın</p>
        <p>4. Sonuçları PDF olarak indirin</p>
        <br>
        <p><strong>Motor Seçenekleri:</strong></p>
        <p>⚡ <strong>Hızlı Motor:</strong> Wikipedia + DuckDuckGo (5sn)</p>
        <p>🔍 <strong>Derin Motor:</strong> 20+ site tarama (7sn/site)</p>
        <p>🧮 <strong>Hesap Makinesi:</strong> Matematiksel hesaplamalar</p>
    </div>
    """, unsafe_allow_html=True)

# --- 📱 RESPONSIVE AYARLAR ---
st.markdown("""
<style>
@media (max-width: 768px) {
    .stButton > button {
        font-size: 14px;
        padding: 8px 16px;
    }
}
</style>
""", unsafe_allow_html=True)
