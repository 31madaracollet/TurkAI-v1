import streamlit as st
import requests
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
from duckduckgo_search import DDGS
import concurrent.futures
from typing import Optional, Tuple

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(
    page_title="TürkAI Analiz Merkezi",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 CANVA MODERN TEMASI (GÜZELLEŞTİRİLMİŞ) ---
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 20px;
    }
    h1, h2, h3 { 
        color: #cc0000 !important; 
        font-weight: 900 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .giris-kapsayici {
        background: white;
        border: 3px solid #cc0000;
        border-radius: 25px;
        padding: 40px;
        text-align: center;
        box-shadow: 0px 8px 25px rgba(204, 0, 0, 0.15);
        margin: 20px 0;
    }
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 15px 22px;
        border-radius: 20px 20px 5px 20px;
        margin: 20px 0;
        width: fit-content;
        max-width: 75%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        animation: slideIn 0.3s ease-out;
    }
    .ai-rapor-alani {
        border-left: 8px solid #cc0000;
        padding: 25px 30px;
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        margin: 25px 0;
        border-radius: 0 20px 20px 0;
        white-space: pre-wrap;
        font-family: 'Segoe UI', sans-serif;
        line-height: 1.8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        animation: fadeIn 0.5s ease-out;
    }
    [data-testid="stSidebar"] { 
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-right: 4px solid #cc0000;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 15px rgba(204, 0, 0, 0.2) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(204, 0, 0, 0.3) !important;
    }
    .chat-input-container {
        position: fixed;
        bottom: 20px;
        width: calc(100% - 40px);
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
        z-index: 100;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .logo {
        font-size: 2.5em;
        font-weight: 900;
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI VE HAFIZA ---
@st.cache_resource
def get_db():
    """Veritabanı bağlantısını oluştur"""
    conn = sqlite3.connect('turkai_v3.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_date TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aramalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici TEXT,
            konu TEXT,
            icerik TEXT,
            tarih TEXT,
            motor TEXT,
            FOREIGN KEY(kullanici) REFERENCES users(username)
        )
    ''')
    return conn

conn = get_db()
c = conn.cursor()

# Session state yönetimi
if "user" not in st.session_state:
    st.session_state.user = None
if "bilgi" not in st.session_state:
    st.session_state.bilgi = ""
if "konu" not in st.session_state:
    st.session_state.konu = ""
if "son_sorgu" not in st.session_state:
    st.session_state.son_sorgu = ""
if "gecmis_yuklendi" not in st.session_state:
    st.session_state.gecmis_yuklendi = False

# --- 🛡️ GELİŞMİŞ İÇERİK FİLTRESİ ---
def analiz_temizle(text: str) -> str:
    """Metni temizle ve formatla"""
    if not text:
        return ""
    
    # 1. Reklam ve spam içerikleri temizle
    spam_patterns = [
        r'microsoft.*sign.*in',
        r'yelp.*review',
        r'tripadvisor.*rating',
        r'log\s*in.*sign\s*up',
        r'best.*espresso.*near',
        r'restaurants.*in',
        r'adsbygoogle',
        r'cookie.*policy',
        r'privacy.*policy',
        r'terms.*service'
    ]
    
    for pattern in spam_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 2. Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    
    # 3. Türkçe karakterleri koru, diğerlerini temizle
    text = re.sub(r'[^\w\sçğıöşüÇĞİÖŞÜ.,;:!?()\-+\*/%@=]', ' ', text)
    
    # 4. Paragraf düzeni oluştur
    sentences = re.split(r'[.!?]+', text)
    cleaned_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and not sentence.startswith('http'):
            # İlk harfi büyük yap
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
            cleaned_sentences.append(sentence)
    
    return '. '.join(cleaned_sentences) + ('.' if cleaned_sentences else '')

# --- 🔍 GELİŞMİŞ ARAMA MOTORLARI ---
def wiki_sorgu(sorgu: str) -> Tuple[str, str]:
    """Wikipedia'dan bilgi al"""
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'extract' in data and data['extract']:
            return f"📚 **Wikipedia'dan:**\n\n{data['extract']}\n", "wikipedia"
        return "", ""
    except requests.exceptions.RequestException as e:
        return f"⚠️ Wikipedia'ya ulaşılamadı: {str(e)}", "error"
    except Exception as e:
        return f"⚠️ Wikipedia aramasında hata: {str(e)}", "error"

def web_sorgu(sorgu: str) -> Tuple[str, str]:
    """Web'den güncel bilgi ara"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{sorgu} nedir ne demek Türkçe bilgi",
                region='tr-tr',
                max_results=5,
                timelimit='y'
            ))
            
            if not results:
                return "", ""
            
            res_text = "🌍 **İnternet Kaynakları:**\n\n"
            for idx, r in enumerate(results[:3], 1):
                title = r.get('title', 'Başlıksız')
                body = r.get('body', '')
                
                if body and len(body) > 50:
                    # Çok uzun metinleri kısalt
                    if len(body) > 200:
                        body = body[:200] + "..."
                    res_text += f"{idx}. **{title}**\n   {body}\n\n"
            
            return res_text, "web"
    except Exception as e:
        return f"⚠️ İnternet aramasında hata: {str(e)}", "error"

def hava_durumu_sorgu(sehir: str) -> Tuple[str, str]:
    """Hava durumu bilgisi al"""
    try:
        if not sehir:
            sehir = "İstanbul"
        
        url = f"https://wttr.in/{urllib.parse.quote(sehir)}?format=j1&lang=tr"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        curr = data['current_condition'][0]
        saatlik = data['weather'][0]['hourly'][0]
        
        hava_bilgisi = f"""
📍 **{sehir.upper()} Hava Durumu:**
🌡️ **Sıcaklık:** {curr['temp_C']}°C (Hissedilen: {curr['FeelsLikeC']}°C)
☁️ **Durum:** {curr['lang_tr'][0]['value']}
💨 **Rüzgar:** {curr['windspeedKmph']} km/h
💧 **Nem:** {curr['humidity']}%
🌧️ **Yağış:** {saatlik['precipMM']} mm
☀️ **UV İndex:** {curr['uvIndex']}
        """
        
        return hava_bilgisi.strip(), "hava"
    except Exception as e:
        return f"⚠️ Hava durumu bilgisi alınamadı: {str(e)}", "error"

# --- 🔐 GELİŞMİŞ GİRİŞ SİSTEMİ ---
def login_page():
    """Giriş ve kayıt sayfası"""
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
            <div class='giris-kapsayici'>
                <div class='logo'>🇹🇷 TürkAI</div>
                <p style='color: #666; margin-bottom: 30px;'>Türkçe Akıllı Analiz Sistemi</p>
            </div>
        """, unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 **Giriş Yap**", "📝 **Kayıt Ol**"])
        
        with t1:
            st.markdown("### Sisteme Giriş")
            u = st.text_input("👤 Kullanıcı Adı", key="login_user")
            p = st.text_input("🔒 Şifre", type="password", key="login_pass")
            
            if st.button("🚀 Giriş Yap", use_container_width=True):
                if not u or not p:
                    st.error("Lütfen tüm alanları doldurun!")
                else:
                    hp = hashlib.sha256(p.encode()).hexdigest()
                    result = c.execute(
                        "SELECT username FROM users WHERE username=? AND password=?",
                        (u, hp)
                    ).fetchone()
                    
                    if result:
                        st.session_state.user = u
                        st.success(f"Hoş geldiniz, {u}! 🎉")
                        st.rerun()
                    else:
                        st.error("Kullanıcı adı veya şifre hatalı!")
        
        with t2:
            st.markdown("### Yeni Hesap Oluştur")
            nu = st.text_input("👤 Yeni Kullanıcı Adı", key="register_user")
            np = st.text_input("🔒 Yeni Şifre", type="password", key="register_pass")
            np_confirm = st.text_input("🔒 Şifre Tekrar", type="password", key="register_pass_confirm")
            
            if st.button("✨ Kayıt Ol", use_container_width=True):
                if not nu or not np:
                    st.error("Lütfen tüm alanları doldurun!")
                elif np != np_confirm:
                    st.error("Şifreler uyuşmuyor!")
                elif len(nu) < 3:
                    st.error("Kullanıcı adı en az 3 karakter olmalı!")
                elif len(np) < 6:
                    st.error("Şifre en az 6 karakter olmalı!")
                else:
                    try:
                        hp = hashlib.sha256(np.encode()).hexdigest()
                        c.execute(
                            "INSERT INTO users VALUES (?,?,?)",
                            (nu, hp, datetime.datetime.now().isoformat())
                        )
                        conn.commit()
                        st.success("🎉 Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
                        st.balloons()
                    except sqlite3.IntegrityError:
                        st.error("Bu kullanıcı adı zaten kullanımda!")

# --- 🚀 ANA UYGULAMA ---
if not st.session_state.user:
    login_page()
    st.stop()

# --- 📊 SIDEBAR (GÜNCELLENMİŞ) ---
with st.sidebar:
    st.markdown(f"""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             border-radius: 15px; color: white; margin-bottom: 20px;'>
            <h3>👤 {st.session_state.user}</h3>
            <p>TürkAI Analiz Merkezi</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔴 Çıkış Yap", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📋 Son Aramalar")
    
    # Geçmiş yükleme
    if not st.session_state.gecmis_yuklendi:
        gecmis = c.execute(
            "SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10",
            (st.session_state.user,)
        ).fetchall()
        st.session_state.gecmis_liste = gecmis
        st.session_state.gecmis_yuklendi = True
    
    if st.session_state.gecmis_liste:
        for idx, (k, i) in enumerate(st.session_state.gecmis_liste):
            if st.button(f"📌 {k[:25]}", key=f"hist_{idx}", use_container_width=True):
                st.session_state.bilgi = i
                st.session_state.konu = k
                st.session_state.son_sorgu = k
    else:
        st.info("Henüz arama geçmişiniz yok.")

# --- 💻 AKILLI ANALİZ SİSTEMİ ---
st.markdown("""
    <div class='main-container'>
        <h1 style='text-align: center;'>🤖 TürkAI Analiz Terminali</h1>
        <p style='text-align: center; color: #666; margin-bottom: 30px;'>
            Türkçe akıllı asistanınıza hoş geldiniz!
        </p>
    </div>
""", unsafe_allow_html=True)

# Chat input
col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
with col2:
    sorgu = st.chat_input("💭 TürkAI'ye sorunuzu yazın...", key="main_input")

if sorgu and sorgu.strip():
    st.session_state.son_sorgu = sorgu.strip()
    
    with st.spinner('🔄 TürkAI analiz ediyor...'):
        sorgu_lower = sorgu.lower()
        
        # 1. Matematik işlemleri
        if re.match(r'^[\d\s+\-*/().,xX]+$', sorgu):
            try:
                # Güvenli matematik işlemi
                expr = sorgu.replace('x', '*').replace('X', '*').replace(',', '.')
                # Tehlikeli fonksiyonları engelle
                allowed_names = {}
                result = eval(expr, {"__builtins__": {}}, allowed_names)
                st.session_state.bilgi = f"""
🧮 **Matematik Sonucu:**
