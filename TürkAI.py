"""
TÜRKAI - Ultimate Türkçe AI Asistan
Sürüm: 3.0 | Madara Edition - TEMA DESTEKLİ
"""

import streamlit as st
import requests
import datetime
import re
import urllib.parse
from duckduckgo_search import DDGS
import json

# ==================== SAYFA AYARI ====================
st.set_page_config(
    page_title="TÜRKAI | Madara",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SESSION STATE ====================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ''
if 'last_response' not in st.session_state:
    st.session_state.last_response = ''
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Varsayılan karanlık mod
if 'theme_loaded' not in st.session_state:
    st.session_state.theme_loaded = False

# ==================== TEMA SİSTEMİ ====================
def load_theme():
    """Temayı yükle"""
    if st.session_state.dark_mode:
        # KARANLIK MOD
        return """
        <style>
        /* KARANLIK MOD */
        .stApp {
            background: #0a0a0a;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(204, 0, 0, 0.15) 0%, transparent 20%),
                radial-gradient(circle at 85% 30%, rgba(255, 77, 77, 0.1) 0%, transparent 20%);
            color: #f0f0f0;
        }
        
        .main-container {
            background: rgba(20, 20, 20, 0.85);
            border: 1px solid rgba(204, 0, 0, 0.3);
            color: #f0f0f0;
        }
        
        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .ai-response {
            background: rgba(30, 30, 30, 0.9);
            color: #f0f0f0;
            border-left: 5px solid #cc0000;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%) !important;
            color: white !important;
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%) !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(30, 30, 30, 0.9) !important;
            color: white !important;
            border: 2px solid rgba(204, 0, 0, 0.3) !important;
        }
        
        .card-dark {
            background: rgba(30, 30, 30, 0.8);
            border: 1px solid rgba(204, 0, 0, 0.25);
            color: #ccc;
        }
        
        .theme-btn {
            background: rgba(40, 40, 40, 0.7) !important;
            border: 1px solid rgba(204, 0, 0, 0.3) !important;
            color: #ff4d4d !important;
        }
        </style>
        """
    else:
        # AYDINLIK MOD (İLK SENİN TEMA)
        return """
        <style>
        /* AYDINLIK MOD - İLK SENİN TEMA */
        .stApp {
            background-color: #ffffff;
            color: #333333;
        }
        
        h1, h2, h3 {
            color: #cc0000 !important;
            font-weight: 800 !important;
        }
        
        .main-container {
            background-color: #fffafa;
            border: 2px solid #cc0000;
            color: #333333;
        }
        
        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            color: #ffffff !important;
            border: none;
        }
        
        .ai-response {
            border-left: 6px solid #cc0000;
            background-color: #fdfdfd;
            color: #333333;
            border: none;
        }
        
        .stButton > button {
            background-color: #cc0000 !important;
            color: white !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 3px solid #cc0000;
        }
        
        .stTextInput > div > div > input {
            background: white !important;
            color: #333333 !important;
            border: 2px solid #cc0000 !important;
        }
        
        .card-light {
            background-color: #f8f9fa;
            border: 1px solid #cc0000;
            color: #666666;
        }
        
        .theme-btn {
            background: #f0f0f0 !important;
            border: 1px solid #cc0000 !important;
            color: #cc0000 !important;
        }
        </style>
        """

# Ortak CSS (her iki temada da geçerli)
COMMON_CSS = """
<style>
/* ORTAK STİLLER */
.main-container {
    border-radius: 24px;
    padding: 25px;
    margin: 15px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(204, 0, 0, 0.25);
}

.user-msg {
    padding: 16px 22px;
    border-radius: 20px 20px 5px 20px;
    margin: 15px 0 15px auto;
    max-width: 75%;
    position: relative;
    box-shadow: 0 4px 15px rgba(204, 0, 0, 0.4);
    animation: slideInRight 0.3s ease-out;
}

.user-msg::before {
    content: "👤";
    position: absolute;
    left: -45px;
    top: 50%;
    transform: translateY(-50%);
    background: #cc0000;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    box-shadow: 0 3px 10px rgba(204, 0, 0, 0.3);
}

.ai-response {
    padding: 22px 25px;
    border-radius: 0 20px 20px 0;
    margin: 20px auto 20px 0;
    position: relative;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
    line-height: 1.7;
    animation: slideInLeft 0.3s ease-out;
}

.ai-response::before {
    content: "🤖";
    position: absolute;
    right: -45px;
    top: 50%;
    transform: translateY(-50%);
    background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    box-shadow: 0 3px 10px rgba(204, 0, 0, 0.3);
}

.stButton > button {
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 28px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(204, 0, 0, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(204, 0, 0, 0.4) !important;
}

.stTextInput > div > div > input {
    border-radius: 15px !important;
    padding: 16px 20px !important;
    font-size: 16px !important;
    transition: all 0.3s !important;
}

.stTextInput > div > div > input:focus {
    box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.2) !important;
}

.card-common {
    border-radius: 16px;
    padding: 20px;
    margin: 15px 0;
    transition: all 0.3s;
}

.logo {
    font-size: 3.5em;
    font-weight: 900;
    background: linear-gradient(135deg, #ff4d4d 0%, #cc0000 50%, #ff4d4d 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 4px 20px rgba(204, 0, 0, 0.4);
    margin-bottom: 10px;
}

@keyframes slideInRight {
    from { transform: translateX(30px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideInLeft {
    from { transform: translateX(-30px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(204, 0, 0, 0.3), transparent);
    margin: 25px 0;
}
</style>
"""

# Temayı yükle
st.markdown(load_theme() + COMMON_CSS, unsafe_allow_html=True)

# ==================== GELİŞMİŞ ARAMA SİSTEMİ ====================
def clean_turkish_text(text):
    """Türkçe metni temizle"""
    if not text:
        return ""
    
    # İngilizce spam siteleri filtrele - GÜNCELLENDİ!
    spam_patterns = [
        r'(?i)money metals exchange',
        r'(?i)buy precious metals',
        r'(?i)silver gold platinum',
        r'(?i)bullion specials',
        r'(?i)trusted source for buying',
        r'(?i)check out our',
        r'(?i)america\'s fastest growing',
        r'(?i)switch their paper dollars',
        r'(?i)precious metals online',
        r'(?i)cheap gold',
        r'(?i)silver certificates',
        r'(?i)gold certificates',
        r'(?i)wwii hawaii',
        r'(?i)dealer',
        r'(?i)adsbygoogle',
        r'(?i)sponsored',
        r'(?i)advertisement'
    ]
    
    for pattern in spam_patterns:
        text = re.sub(pattern, '', text)
    
    # HTML ve özel karakterleri temizle
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+', '', text)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def search_wikipedia_turkish(query):
    """Wikipedia'dan TÜRKÇE bilgi al"""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'extract' in data and data['extract']:
                title = data.get('title', query)
                extract = data['extract']
                
                # Temizle ve formatla
                clean_extract = clean_turkish_text(extract)
                if clean_extract:
                    return f"📚 **Wikipedia: {title}**\n\n{clean_extract}"
        
        # Alternatif arama
        search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=1"
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            if search_data['query']['search']:
                result = search_data['query']['search'][0]
                return f"📚 **Wikipedia Arama Sonucu:**\n\n{clean_turkish_text(result['snippet'])}..."
                
    except Exception as e:
        print(f"Wikipedia hatası: {e}")
    
    return None

def search_web_turkish(query):
    """İnternetten TÜRKÇE içerik ara - DÜZELTİLDİ!"""
    try:
        # TÜRKÇE arama için optimize edilmiş sorgu
        turkish_query = f"{query} nedir ne demek Türkçe açıklama bilgi"
        
        with DDGS() as ddgs:
            # SADECE Türkçe siteler için filtrele
            results = list(ddgs.text(
                turkish_query,
                region='tr-tr',
                safesearch='moderate',
                max_results=4,
                timelimit='m'  # Son bir ay içinde
            ))
            
            if not results:
                return None
            
            turkish_results = []
            for r in results:
                title = r.get('title', '')
                body = r.get('body', '')
                
                # TÜRKÇE kontrolü - sadece Türkçe karakter içerenleri al
                if any(char in title.lower() for char in ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']):
                    cleaned_title = clean_turkish_text(title[:60])
                    cleaned_body = clean_turkish_text(body[:180])
                    
                    if cleaned_body and len(cleaned_body) > 30:
                        turkish_results.append({
                            'title': cleaned_title,
                            'body': cleaned_body
                        })
            
            if turkish_results:
                text = "🌐 **Türkçe Kaynaklar:**\n\n"
                for i, r in enumerate(turkish_results[:3], 1):
                    text += f"{i}. **{r['title']}**\n"
                    text += f"   {r['body']}...\n\n"
                return text
            else:
                # Türkçe sonuç yoksa Wikipedia'ya yönlendir
                return "🔍 **Türkçe kaynak bulunamadı.** Wikipedia'dan bilgi almayı deneyin."
                
    except Exception as e:
        print(f"Web arama hatası: {e}")
        return None

def search_turkish_sources(query):
    """TÜRKÇE kaynaklardan ara - ANA FONKSİYON"""
    # Önce Wikipedia'dan dene
    wiki_result = search_wikipedia_turkish(query)
    
    if wiki_result:
        return wiki_result, "wikipedia"
    
    # Wikipedia'da yoksa web'den ara
    web_result = search_web_turkish(query)
    
    if web_result and "Türkçe Kaynaklar:" in web_result:
        return web_result, "web"
    
    # Hiçbir şey bulunamazsa
    return None, "not_found"

def get_weather_turkish(city="İstanbul"):
    """Hava durumu bilgisi - TÜRKÇE"""
    try:
        url = f"http://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=tr"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            weather_info = f"""
🌤️ **{city.upper()} Hava Durumu**

🌡️ **Sıcaklık:** {current.get('temp_C', 'N/A')}°C
🌡️ **Hissedilen:** {current.get('FeelsLikeC', 'N/A')}°C
💨 **Rüzgar:** {current.get('windspeedKmph', 'N/A')} km/h
🧭 **Yön:** {current.get('winddir16Point', 'N/A')}
💧 **Nem:** {current.get('humidity', 'N/A')}%
👁️ **Görüş:** {current.get('visibility', 'N/A')} km
☁️ **Durum:** {current['weatherDesc'][0]['value']}
"""
            
            return weather_info.strip()
    except:
        pass
    
    # Basit versiyon
    return f"📍 **{city} Hava Durumu**\n\n🌡️ Hava durumu bilgisi alınamadı. Lütfen şehir adını kontrol edin."

def calculate_math_safe(expression):
    """Güvenli matematik hesaplama"""
    try:
        # Güvenlik için temizle
        expr = expression.replace('x', '*').replace('X', '*')
        expr = expr.replace(',', '.').replace(' ', '')
        
        # Sadece matematiksel karakterlere izin ver
        if not re.match(r'^[\d+\-*/().]+$', expr):
            return "⚠️ Geçersiz matematik ifadesi!"
        
        # Hesapla
        result = eval(expr, {"__builtins__": {}}, {})
        
        return f"""
🧮 **Matematik Sonucu**

**İşlem:** `{expression}`
**Sonuç:** `{result}`

⏱️ {datetime.datetime.now().strftime("%H:%M")}
"""
    except:
        return "⚠️ Hesaplama yapılamadı! Lütfen geçerli bir işlem girin."

# ==================== GİRİŞ SİSTEMİ ====================
def login_page():
    """Giriş sayfası"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # TEMA DEĞİŞTİRME BUTONU (Giriş sayfasında da)
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("🌙 Karanlık Mod", use_container_width=True, 
                        type="primary" if st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = True
                st.rerun()
        with col_theme2:
            if st.button("☀️ Aydınlık Mod", use_container_width=True,
                        type="primary" if not st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = False
                st.rerun()
        
        # Logo ve başlık
        st.markdown(f"""
        <div class='main-container'>
            <div class='logo'>🔥 TÜRKAI</div>
            <h3 style='text-align: center; color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>
                {'Madara Edition - Karanlık Mod' if st.session_state.dark_mode else 'Madara Edition - Aydınlık Mod'}
            </h3>
            <p style='text-align: center; color: {'#aaa' if st.session_state.dark_mode else '#666'};'>
                Ultimate Türkçe AI Asistan
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş/Kayıt tab'leri
        tab1, tab2 = st.tabs(["🔓 GİRİŞ YAP", "✨ HESAP OLUŞTUR"])
        
        with tab1:
            st.markdown("### 👤 Sisteme Giriş")
            
            user = st.text_input("Kullanıcı Adı", key="login_user")
            password = st.text_input("Şifre", type="password", key="login_pass")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🚀 GİRİŞ YAP", use_container_width=True, type="primary"):
                    if user and password:
                        # Basit doğrulama
                        if (user == "admin" and password == "admin123") or (user == "demo" and password == "demo123"):
                            st.session_state.user = user
                            st.success(f"Hoş geldin {user}! 🎉")
                            st.rerun()
                        else:
                            # Herhangi bir kullanıcı adı kabul et
                            st.session_state.user = user
                            st.success(f"Hoş geldin {user}! 🎉")
                            st.rerun()
                    else:
                        st.error("Boş alan bırakmayın!")
            
            with col_b:
                if st.button("👁️ DEMO GİRİŞ", use_container_width=True):
                    st.session_state.user = "demo"
                    st.success("Demo moduna hoş geldin! 🎮")
                    st.rerun()
        
        with tab2:
            st.markdown("### 📝 Yeni Hesap")
            
            new_user = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            new_pass = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            confirm_pass = st.text_input("Şifre Tekrar", type="password", key="reg_confirm")
            
            if st.button("🔥 HESAP OLUŞTUR", use_container_width=True, type="primary"):
                if not all([new_user, new_pass, confirm_pass]):
                    st.error("Tüm alanları doldurun!")
                elif new_pass != confirm_pass:
                    st.error("Şifreler uyuşmuyor!")
                elif len(new_user) < 3:
                    st.error("Kullanıcı adı en az 3 karakter olmalı!")
                elif len(new_pass) < 6:
                    st.error("Şifre en az 6 karakter olmalı!")
                else:
                    st.session_state.user = new_user
                    st.success(f"{new_user} hesabı oluşturuldu! 🎊")
                    st.balloons()
                    st.rerun()

# ==================== SIDEBAR ====================
def render_sidebar():
    """Sidebar"""
    
    with st.sidebar:
        # TEMA DEĞİŞTİRME BUTONU
        theme_col1, theme_col2 = st.columns(2)
        with theme_col1:
            if st.button("🌙", help="Karanlık Mod", use_container_width=True,
                        type="primary" if st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = True
                st.rerun()
        with theme_col2:
            if st.button("☀️", help="Aydınlık Mod", use_container_width=True,
                        type="primary" if not st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = False
                st.rerun()
        
        # Kullanıcı bilgileri
        card_class = "card-dark" if st.session_state.dark_mode else "card-light"
        st.markdown(f"""
        <div class='card-common {card_class}'>
            <h4 style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'}; margin-bottom: 5px;'>
                👤 {st.session_state.user}
            </h4>
            <p style='color: {'#aaa' if st.session_state.dark_mode else '#666'}; font-size: 0.9em;'>
                TÜRKAI Premium Kullanıcı
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Çıkış butonu
        if st.button("🔴 ÇIKIŞ YAP", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.session_state.history = []
            st.session_state.last_query = ''
            st.session_state.last_response = ''
            st.rerun()
        
        st.markdown("---")
        
        # HIZLI SORGULAR
        st.markdown("### ⚡ HIZLI SORGULAR")
        
        quick_actions = [
            ("🧮 784 + 8874", "784+8874"),
            ("🌤️ İstanbul Hava", "İstanbul hava durumu"),
            ("📖 Atatürk Kimdir", "Atatürk kimdir"),
            ("💻 Python Nedir", "Python nedir"),
            ("📍 Ankara Hava", "Ankara hava durumu"),
            ("🔢 15 x 3 + 7", "15*3+7")
        ]
        
        for label, query in quick_actions:
            if st.button(label, key=f"quick_{query}", use_container_width=True,
                        type="primary" if st.session_state.last_query == query else "secondary"):
                st.session_state.last_query = query
                st.rerun()
        
        st.markdown("---")
        
        # ÖRNEK SORGULAR KARTI
        card_title_color = '#ff4d4d' if st.session_state.dark_mode else '#cc0000'
        card_text_color = '#ccc' if st.session_state.dark_mode else '#666'
        
        st.markdown(f"""
        <div class='card-common {card_class}'>
            <h4 style='color: {card_title_color}; margin-bottom: 15px; text-align: center;'>
                💡 ÖRNEK SORGULAR
            </h4>
            
            <div style='color: {card_text_color}; line-height: 1.8;'>
                <p>• <strong style='color: {card_title_color};'>Matematik:</strong> "784+8874"</p>
                <p>• <strong style='color: {card_title_color};'>Hava:</strong> "İstanbul hava durumu"</p>
                <p>• <strong style='color: {card_title_color};'>Tarih:</strong> "Atatürk kimdir?"</p>
                <p>• <strong style='color: {card_title_color};'>Teknoloji:</strong> "Python nedir?"</p>
                <p>• <strong style='color: {card_title_color};'>Coğrafya:</strong> "Türkiye başkenti"</p>
            </div>
            
            <p style='color: {'#888' if st.session_state.dark_mode else '#999'}; 
               font-size: 0.85em; margin-top: 15px; text-align: center;'>
                Yukarıdaki butonlara tıklayın!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # SON SORGULAR
        st.markdown("### 📜 SON SORGULAR")
        
        if st.session_state.history:
            recent = st.session_state.history[-5:][::-1]
            
            for i, item in enumerate(recent):
                query_display = item['query']
                if len(query_display) > 20:
                    query_display = query_display[:18] + "..."
                
                emoji = "🧮" if item['category'] == 'matematik' else "🌤️" if item['category'] == 'hava' else "📖"
                
                if st.button(f"{emoji} {query_display}", key=f"recent_{i}", use_container_width=True):
                    st.session_state.last_query = item['query']
                    st.session_state.last_response = item['response']
                    st.rerun()
        else:
            st.info("Henüz sorgu geçmişiniz yok.")

# ==================== ANA UYGULAMA ====================
def main_app():
    """Ana uygulama"""
    
    # Başlık
    title_color = '#ff4d4d' if st.session_state.dark_mode else '#cc0000'
    subtitle_color = '#aaa' if st.session_state.dark_mode else '#666'
    
    st.markdown(f"""
    <div class='main-container'>
        <h1>🔥 TÜRKAI</h1>
        <p style='text-align: center; color: {subtitle_color}; margin-bottom: 30px; font-size: 1.1em;'>
            {'Madara Edition - Karanlık Mod' if st.session_state.dark_mode else 'Madara Edition - Aydınlık Mod'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Chat input
    col1, col2, col3 = st.columns([0.3, 3.4, 0.3])
    
    with col2:
        placeholder_text = "💬 TürkAI'ye sorunuzu yazın... (Örnek: 'Python nedir?', 'İstanbul hava durumu', '784+8874')"
        query = st.text_input(
            "",
            placeholder=placeholder_text,
            key="main_input",
            label_visibility="collapsed"
        )
    
    # Sorgu işleme
    if query:
        st.session_state.last_query = query
        
        with st.spinner("🤖 TÜRKAI düşünüyor..."):
            # 1. Matematik kontrolü
            clean_query = query.replace(' ', '')
            math_pattern = r'^[\d+\-*/().xX]+$'
            
            if re.match(math_pattern, clean_query):
                response = calculate_math_safe(query)
                category = "matematik"
            
            # 2. Hava durumu kontrolü
            elif any(keyword in query.lower() for keyword in ['hava', 'durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar']):
                city = "İstanbul"
                words = query.lower().split()
                excluded = ['hava', 'durumu', 'nasıl', 'kaç', 'derece', 'nedir', 'havası']
                
                for w in words:
                    if w not in excluded and len(w) > 2:
                        city = w.title()
                        break
                
                response = get_weather_turkish(city)
                category = "hava"
            
            # 3. Genel Türkçe sorgu
            else:
                result, result_type = search_turkish_sources(query)
                
                if result:
                    response = result
                    category = result_type
                else:
                    response = f"""
🤔 **"{query}"** hakkında Türkçe kaynak bulunamadı.

**Önerilerim:**
• Sorgunuzu Türkçe karakterlerle yazın
• Daha spesifik sorun
• Farklı kelimeler deneyin

**Örnekler:**
- "Mustafa Kemal Atatürk kimdir?"
- "Python programlama dili nedir?"
- "İstanbul'un tarihi hakkında bilgi"
"""
                    category = "genel"
            
            # Geçmişe kaydet
            history_item = {
                'query': query,
                'response': response,
                'category': category,
                'time': datetime.datetime.now().strftime("%H:%M"),
                'date': datetime.datetime.now().strftime("%d.%m.%Y")
            }
            
            if len(st.session_state.history) >= 20:
                st.session_state.history.pop(0)
            
            st.session_state.history.append(history_item)
            st.session_state.last_response = response
            
            # Sonuçları göster
            st.markdown(f"""
            <div class='user-msg'>
                <b>{st.session_state.user}:</b><br>
                {query}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='ai-response'>
                {response}
                
                <div style='margin-top: 20px; padding-top: 15px; border-top: 1px solid {'rgba(255,255,255,0.1)' if st.session_state.dark_mode else 'rgba(0,0,0,0.1)'};'>
                    <small style='color: {'#888' if st.session_state.dark_mode else '#666'};'>
                        📅 {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")} | 
                        🏷️ {category.upper()}
                    </small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Önceki sorguyu göster
    elif st.session_state.last_query and st.session_state.last_response:
        st.markdown(f"""
        <div class='user-msg'>
            <b>{st.session_state.user}:</b><br>
            {st.session_state.last_query}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='ai-response'>
            {st.session_state.last_response}
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Karşılama mesajı
        welcome_color = '#ff4d4d' if st.session_state.dark_mode else '#cc0000'
        text_color = '#ccc' if st.session_state.dark_mode else '#666'
        card_bg = 'rgba(204, 0, 0, 0.1)' if st.session_state.dark_mode else 'rgba(204, 0, 0, 0.05)'
        card_border = 'rgba(204, 0, 0, 0.3)' if st.session_state.dark_mode else 'rgba(204, 0, 0, 0.2)'
        
        st.markdown(f"""
        <div class='ai-response' style='text-align: center;'>
            <h3 style='color: {welcome_color}; margin-bottom: 20px;'>👋 TÜRKAI'YE HOŞ GELDİNİZ!</h3>
            
            <p style='color: {text_color}; margin-bottom: 25px; font-size: 1.1em;'>
                Türkçe akıllı asistanınıza her şeyi sorabilirsiniz.
            </p>
            
            <div style='
                background: {card_bg};
                border-radius: 16px;
                padding: 20px;
                margin: 25px 0;
                border: 1px solid {card_border};
            '>
                <h4 style='color: {welcome_color};'>🚀 HEMEN DENEYİN</h4>
                
                <div style='text-align: left; color: {text_color}; line-height: 1.8; margin-top: 15px;'>
                    <p>• <strong>Matematik:</strong> "784+8874" veya "15*3+7"</p>
                    <p>• <strong>Hava Durumu:</strong> "İstanbul hava durumu"</p>
                    <p>• <strong>Tarih:</strong> "Atatürk kimdir?"</p>
                    <p>• <strong>Teknoloji:</strong> "Python nedir?"</p>
                    <p>• <strong>Herhangi bir konu:</strong> İstediğinizi sorun!</p>
                </div>
            </div>
            
            <p style='color: {'#999' if st.session_state.dark_mode else '#888'}; font-size: 0.95em; margin-top: 25px;'>
                💡 <strong>İpucu:</strong> 👈 Soldaki "Hızlı Sorgular" butonlarına tıklayın!
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==================== BAŞLAT ====================
if not st.session_state.user:
    login_page()
else:
    main_app()

# Footer
footer_text_color = '#666' if st.session_state.dark_mode else '#888'
st.markdown(f"""
<div style='
    text-align: center;
    margin-top: 50px;
    padding-top: 25px;
    border-top: 1px solid rgba(204, 0, 0, 0.2);
    color: {footer_text_color};
    font-size: 0.85em;
'>
    <p>
        🚀 <strong style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>TÜRKAI v3.0</strong>
        | {'🌙 Karanlık Mod' if st.session_state.dark_mode else '☀️ Aydınlık Mod'}
    </p>
    <p style='margin-top: 5px;'>
        🔥 Ultimate Türkçe AI Asistan | 🇹🇷 %100 Türkçe Kaynak
    </p>
    <p style='margin-top: 5px; color: {'#888' if st.session_state.dark_mode else '#999'}; font-size: 0.8em;'>
        Demo Giriş: <strong>demo / demo123</strong> | Admin: <strong>admin / admin123</strong>
    </p>
</div>
""", unsafe_allow_html=True)
