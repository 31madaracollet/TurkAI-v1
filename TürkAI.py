"""
TÜRKAI - Ultimate Türkçe AI Asistan
Sürüm: 2.1 | Madara Edition - GÜNCELLENMİŞ
"""

import streamlit as st
import requests
import datetime
import re
import urllib.parse
from duckduckgo_search import DDGS

# ==================== SAYFA AYARI ====================
st.set_page_config(
    page_title="TÜRKAI | Madara",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== ANA TEMA ====================
st.markdown("""
<style>
/* ANA ARKA PLAN - Kara Tema */
.stApp {
    background: #0a0a0a;
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(204, 0, 0, 0.15) 0%, transparent 20%),
        radial-gradient(circle at 85% 30%, rgba(255, 77, 77, 0.1) 0%, transparent 20%),
        radial-gradient(circle at 50% 80%, rgba(255, 0, 0, 0.05) 0%, transparent 20%);
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

/* ANA KONTEYNER */
.main-container {
    background: rgba(20, 20, 20, 0.85);
    border-radius: 24px;
    border: 1px solid rgba(204, 0, 0, 0.3);
    padding: 25px;
    margin: 15px;
    backdrop-filter: blur(10px);
    box-shadow: 
        0 8px 32px rgba(204, 0, 0, 0.25),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* BAŞLIKLAR */
h1 {
    background: linear-gradient(135deg, #ff4d4d 0%, #cc0000 50%, #ff4d4d 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900 !important;
    font-size: 3.2em !important;
    text-align: center;
    text-shadow: 0 2px 10px rgba(204, 0, 0, 0.3);
    margin-bottom: 5px !important;
    letter-spacing: -0.5px;
}

h2, h3 {
    color: #ff4d4d !important;
    font-weight: 800 !important;
    border-left: 4px solid #cc0000;
    padding-left: 15px;
}

/* KULLANICI MESAJI - Sağda */
.user-msg {
    background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
    color: white;
    padding: 16px 22px;
    border-radius: 20px 20px 5px 20px;
    margin: 15px 0 15px auto;
    max-width: 75%;
    position: relative;
    box-shadow: 
        0 4px 15px rgba(204, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: slideInRight 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
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

/* AI MESAJI - Solda */
.ai-response {
    background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(40, 40, 40, 0.9) 100%);
    color: #f0f0f0;
    border-left: 5px solid #cc0000;
    padding: 22px 25px;
    border-radius: 0 20px 20px 0;
    margin: 20px auto 20px 0;
    position: relative;
    box-shadow: 
        0 5px 20px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.05);
    animation: slideInLeft 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    line-height: 1.7;
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

/* BUTONLAR - Premium Stil */
.stButton > button {
    background: linear-gradient(135deg, #cc0000 0%, #990000 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 28px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.3px;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(204, 0, 0, 0.3) !important;
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 
        0 6px 20px rgba(204, 0, 0, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.1) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* SIDEBAR - Koyu Premium */
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%) !important;
    border-right: 3px solid #cc0000 !important;
}

[data-testid="stSidebar"] * {
    color: #f0f0f0 !important;
}

/* INPUT ALANI */
.stTextInput > div > div > input {
    background: rgba(30, 30, 30, 0.9) !important;
    color: white !important;
    border: 2px solid rgba(204, 0, 0, 0.3) !important;
    border-radius: 15px !important;
    padding: 16px 20px !important;
    font-size: 16px !important;
    transition: all 0.3s !important;
}

.stTextInput > div > div > input:focus {
    border-color: #cc0000 !important;
    box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.2) !important;
    background: rgba(40, 40, 40, 0.9) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255, 255, 255, 0.5) !important;
}

/* TAB'LER */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(30, 30, 30, 0.9);
    border-radius: 12px;
    padding: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    padding: 12px 24px !important;
    background: transparent !important;
    color: #999 !important;
    font-weight: 600;
    transition: all 0.3s;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #cc0000 0%, #990000 100%) !important;
    color: white !important;
    box-shadow: 0 3px 10px rgba(204, 0, 0, 0.3) !important;
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 30, 30, 0.9);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #ff4d4d 0%, #cc0000 100%);
}

/* ANİMASYONLAR */
@keyframes slideInRight {
    from {
        transform: translateX(30px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideInLeft {
    from {
        transform: translateX(-30px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* LOGO */
.logo {
    font-size: 3.5em;
    font-weight: 900;
    background: linear-gradient(135deg, #ff4d4d 0%, #cc0000 50%, #ff4d4d 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 4px 20px rgba(204, 0, 0, 0.4);
    margin-bottom: 10px;
    letter-spacing: -1px;
}

/* GİRİŞ KONTEYNER */
.login-box {
    background: rgba(20, 20, 20, 0.9);
    border: 2px solid rgba(204, 0, 0, 0.3);
    border-radius: 24px;
    padding: 40px;
    text-align: center;
    box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

/* BAŞARI/HATA MESAJLARI */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid !important;
    background: rgba(30, 30, 30, 0.9) !important;
    backdrop-filter: blur(10px);
}

/* DIVIDER */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(204, 0, 0, 0.3), transparent);
    margin: 25px 0;
}

/* KARTLAR */
.card {
    background: rgba(30, 30, 30, 0.7);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(204, 0, 0, 0.2);
    transition: all 0.3s;
}

.card:hover {
    border-color: #cc0000;
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(204, 0, 0, 0.2);
}

/* YÜKLEME ANİMASYONU */
.stSpinner > div {
    border-color: #cc0000 !important;
    border-right-color: transparent !important;
}

/* METİN RENKLERİ */
strong {
    color: #ff4d4d;
}

em {
    color: #ff9999;
}

/* RESPONSIVE */
@media (max-width: 768px) {
    .main-container {
        padding: 15px;
        margin: 10px;
    }
    
    h1 {
        font-size: 2.5em !important;
    }
    
    .user-msg, .ai-response {
        max-width: 90%;
        padding: 14px 18px;
    }
}

/* ÖZEL KART SIDEBAR İÇİN */
.sidebar-card {
    background: rgba(30, 30, 30, 0.8);
    border-radius: 14px;
    padding: 18px;
    margin: 15px 0;
    border: 1px solid rgba(204, 0, 0, 0.25);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* QUICK ACTION BUTTONS */
.quick-btn {
    background: rgba(40, 40, 40, 0.7) !important;
    border: 1px solid rgba(204, 0, 0, 0.3) !important;
    color: #ff4d4d !important;
    transition: all 0.3s !important;
}

.quick-btn:hover {
    background: rgba(204, 0, 0, 0.2) !important;
    border-color: #cc0000 !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ''
if 'last_response' not in st.session_state:
    st.session_state.last_response = ''
if 'show_examples' not in st.session_state:
    st.session_state.show_examples = True

# ==================== ANA FONKSİYONLAR ====================
def search_wikipedia(query):
    """Wikipedia'dan bilgi al"""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if 'extract' in data:
                title = data.get('title', query)
                return f"📖 **{title}**\n\n{data['extract']}"
    except:
        pass
    return None

def search_web(query):
    """İnternetten ara"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{query} nedir Türkçe",
                region='tr-tr',
                max_results=3
            ))
            
            if results:
                text = "🌐 **İnternet Kaynakları**\n\n"
                for r in results:
                    title = r.get('title', '')[:50]
                    body = r.get('body', '')[:150]
                    if body:
                        text += f"• **{title}**\n  {body}...\n\n"
                return text
    except:
        pass
    return None

def get_weather(city="İstanbul"):
    """Hava durumu"""
    try:
        url = f"http://wttr.in/{urllib.parse.quote(city)}?format=j1"
        response = requests.get(url, timeout=8)
        data = response.json()
        
        curr = data['current_condition'][0]
        return f"""
🌤️ **{city.upper()} Hava Durumu**

🌡️ **Sıcaklık:** {curr['temp_C']}°C
🌡️ **Hissedilen:** {curr['FeelsLikeC']}°C
💨 **Rüzgar:** {curr['windspeedKmph']} km/h
💧 **Nem:** {curr['humidity']}%
☁️ **Durum:** {curr['weatherDesc'][0]['value']}
"""
    except:
        return f"⚠️ {city} hava durumu alınamadı."

def calculate_math(expr):
    """Matematik hesapla"""
    try:
        expr = expr.replace('x', '*').replace('X', '*').replace(',', '.')
        if not re.match(r'^[\d\s+\-*/().]+$', expr.replace(' ', '')):
            return "⚠️ Geçersiz ifade!"
        
        result = eval(expr, {"__builtins__": {}}, {})
        return f"""
🧮 **Matematik Sonucu**

**İşlem:** `{expr}`
**Sonuç:** `{result}`

*{datetime.datetime.now().strftime("%H:%M")} tarihinde hesaplandı*
"""
    except:
        return "⚠️ Hesaplanamadı!"

# ==================== GİRİŞ SİSTEMİ ====================
def login_page():
    """Giriş sayfası"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class='login-box'>
            <div class='logo'>🔥 TÜRKAI</div>
            <h3 style='color: #ff4d4d; margin-bottom: 30px;'>Madara Edition</h3>
            <p style='color: #aaa; margin-bottom: 40px;'>
                Ultimate Türkçe AI Asistan
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔓 GİRİŞ YAP", "✨ HESAP OLUŞTUR"])
        
        with tab1:
            st.markdown("### 👤 Sisteme Giriş")
            
            user = st.text_input("Kullanıcı Adı", key="login_user")
            password = st.text_input("Şifre", type="password", key="login_pass")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🚀 GİRİŞ YAP", use_container_width=True, type="primary"):
                    if user == "admin" and password == "admin123":
                        st.session_state.user = "admin"
                        st.success("Admin olarak giriş yapıldı! 🔥")
                        st.rerun()
                    elif user and password:
                        st.session_state.user = user
                        st.success(f"Hoş geldin {user}! 🎉")
                        st.rerun()
                    else:
                        st.error("Boş alan bırakmayın!")
            
            with col_b:
                if st.button("👁️ DEMO GİRİŞ", use_container_width=True):
                    st.session_state.user = "demo_user"
                    st.success("Demo moduna hoş geldin! 🎮")
                    st.rerun()
        
        with tab2:
            st.markdown("### 📝 Yeni Hesap")
            
            new_user = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            new_pass = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            
            if st.button("🔥 HESAP OLUŞTUR", use_container_width=True, type="primary"):
                if new_user and new_pass:
                    st.session_state.user = new_user
                    st.success(f"{new_user} hesabı oluşturuldu! 🎊")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Tüm alanları doldurun!")

# ==================== SIDEBAR ====================
def render_sidebar():
    """Sidebar - ÖRNEK SORGULAR BURADA!"""
    
    with st.sidebar:
        # Kullanıcı bilgileri
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, rgba(204,0,0,0.2) 0%, rgba(255,77,77,0.1) 100%);
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 25px;
            border: 1px solid rgba(204,0,0,0.3);
        '>
            <h3 style='color: #ff4d4d; margin-bottom: 5px;'>👤 {st.session_state.user}</h3>
            <p style='color: #aaa; font-size: 0.9em;'>TÜRKAI Premium Kullanıcı</p>
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
        
        # HIZLI SORGULAR BÖLÜMÜ - HER ZAMAN GÖZÜKECEK
        st.markdown("### ⚡ HIZLI SORGULAR")
        
        # Hızlı sorgu butonları
        quick_actions = [
            ("🧮 15 x 3 + 7", "15 x 3 + 7"),
            ("🌤️ İstanbul Hava", "İstanbul hava durumu"),
            ("📖 Atatürk Kimdir", "Atatürk kimdir"),
            ("💻 Python Nedir", "Python nedir"),
            ("📍 Türkiye Başkenti", "Türkiye başkenti")
        ]
        
        for label, query in quick_actions:
            if st.button(label, key=f"quick_{query}", use_container_width=True):
                st.session_state.last_query = query
                st.rerun()
        
        st.markdown("---")
        
        # ÖRNEK SORGULAR KARTI - HER ZAMAN GÖZÜKECEK
        st.markdown("""
        <div class='sidebar-card'>
            <h4 style='color: #ff4d4d; margin-bottom: 15px; text-align: center;'>💡 ÖRNEK SORGULAR</h4>
            
            <div style='color: #ccc; line-height: 1.8;'>
                <p>• <strong style='color: #ff4d4d;'>Matematik:</strong> "25 x 4 + 8"</p>
                <p>• <strong style='color: #ff4d4d;'>Hava:</strong> "Ankara hava durumu"</p>
                <p>• <strong style='color: #ff4d4d;'>Tarih:</strong> "Atatürk kimdir?"</p>
                <p>• <strong style='color: #ff4d4d;'>Teknoloji:</strong> "Python nedir?"</p>
                <p>• <strong style='color: #ff4d4d;'>Coğrafya:</strong> "Türkiye'nin başkenti"</p>
                <p>• <strong style='color: #ff4d4d;'>Bilim:</strong> "Einstein kimdir?"</p>
                <p>• <strong style='color: #ff4d4d;'>Spor:</strong> "Fenerbahçe nedir?"</p>
            </div>
            
            <p style='color: #888; font-size: 0.85em; margin-top: 15px; text-align: center;'>
                Yukarıdaki butonlara tıklayın veya kendiniz yazın!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Son sorgular (geçmiş)
        st.markdown("### 📜 SON SORGULAR")
        
        if st.session_state.history:
            # Son 5 sorguyu göster (en yeni en üstte)
            recent_history = st.session_state.history[-5:][::-1]
            
            for i, item in enumerate(recent_history):
                query_display = item['query']
                if len(query_display) > 22:
                    query_display = query_display[:20] + "..."
                
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
    st.markdown("""
    <div class='main-container'>
        <h1>🔥 TÜRKAI</h1>
        <p style='text-align: center; color: #aaa; margin-bottom: 30px; font-size: 1.1em;'>
            Madara's Ultimate AI Assistant
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar'ı render et (ÖRNEK SORGULAR BURADA)
    render_sidebar()
    
    # Chat input - DAHA BÜYÜK VE MERKEZDE
    col1, col2, col3 = st.columns([0.3, 3.4, 0.3])
    
    with col2:
        query = st.text_input(
            "",
            placeholder="💬 TürkAI'ye sorunuzu yazın... (Örnek: 'Python nedir?', 'İstanbul hava durumu', '15*3+7')",
            key="main_input",
            label_visibility="collapsed"
        )
    
    # Sorgu işleme
    if query:
        st.session_state.last_query = query
        
        with st.spinner("TÜRKAI düşünüyor..."):
            # 1. Matematik kontrolü
            clean_query = query.replace(' ', '')
            if re.match(r'^[\d+\-*/().xX]+$', clean_query):
                response = calculate_math(query)
                category = "matematik"
            
            # 2. Hava durumu kontrolü
            elif any(keyword in query.lower() for keyword in ['hava', 'durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar']):
                city = "İstanbul"
                words = query.lower().split()
                excluded_words = ['hava', 'durumu', 'nasıl', 'kaç', 'derece', 'nedir']
                
                for w in words:
                    if w not in excluded_words and len(w) > 2:
                        city = w.title()
                        break
                
                response = get_weather(city)
                category = "hava"
            
            # 3. Genel sorgu
            else:
                wiki_response = search_wikipedia(query)
                
                if wiki_response:
                    response = wiki_response
                    category = "wikipedia"
                else:
                    web_response = search_web(query)
                    
                    if web_response:
                        response = web_response
                        category = "web"
                    else:
                        response = f"""
🤔 **"{query}"** hakkında detaylı bilgi bulunamadı.

**Önerilerim:**
• Sorgunuzu daha açıklayıcı yazın
• Türkçe karakterleri kontrol edin (ç, ğ, ı, ö, ş, ü)
• Farklı bir ifade deneyin

**Örnekler:**
- "Mustafa Kemal Atatürk'ün hayatı"
- "Python programlama dili nedir?"
- "İstanbul'un tarihi yerleri nelerdir?"
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
            
            # En fazla 20 kayıt tut
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
                
                <div style='margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);'>
                    <small style='color: #888;'>
                        📅 {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")} | 
                        🏷️ {category.title()}
                    </small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Önceki sorguyu göster (eğer varsa ama şu an sorgu yoksa)
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
        # YENİ KULLANICI İÇİN KARŞILAMA MESAJI
        st.markdown("""
        <div class='ai-response' style='text-align: center;'>
            <h3 style='color: #ff4d4d; margin-bottom: 20px;'>👋 TÜRKAI'YE HOŞ GELDİNİZ!</h3>
            
            <p style='color: #ccc; margin-bottom: 25px; font-size: 1.1em;'>
                Türkçe akıllı asistanınıza her şeyi sorabilirsiniz.
            </p>
            
            <div style='
                background: rgba(204, 0, 0, 0.1);
                border-radius: 16px;
                padding: 20px;
                margin: 25px 0;
                border: 1px solid rgba(204, 0, 0, 0.3);
            '>
                <h4 style='color: #ff4d4d;'>🚀 NASIL KULLANILIR?</h4>
                
                <div style='text-align: left; color: #ccc; line-height: 1.8; margin-top: 15px;'>
                    <p>1️⃣ <strong>Soldaki "Hızlı Sorgular"</strong> butonlarına tıklayın</p>
                    <p>2️⃣ <strong>Yukarıdaki input'a</strong> kendi sorunuzu yazın</p>
                    <p>3️⃣ <strong>Enter'a basın</strong> veya bekleyin</p>
                    <p>4️⃣ <strong>Sonuçlar</strong> anında gösterilecek</p>
                </div>
            </div>
            
            <p style='color: #999; font-size: 0.95em; margin-top: 25px;'>
                💡 <strong>İpucu:</strong> 👈 Soldaki sidebar'da her zaman örnek sorguları görebilirsiniz!
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==================== BAŞLAT ====================
if not st.session_state.user:
    login_page()
else:
    main_app()

# Footer
st.markdown("""
<div style='
    text-align: center;
    margin-top: 50px;
    padding-top: 25px;
    border-top: 1px solid rgba(204, 0, 0, 0.2);
    color: #666;
    font-size: 0.85em;
'>
    <p>
        🚀 <strong style='color: #ff4d4d;'>TÜRKAI v2.1</strong> | Madara Edition
    </p>
    <p style='margin-top: 5px;'>
        🔥 Ultimate Türkçe AI Asistan | 🇹🇷 %100 Türkçe
    </p>
    <p style='margin-top: 5px; color: #888; font-size: 0.8em;'>
        Admin Giriş: <strong>admin / admin123</strong> | Demo: Herhangi bir kullanıcı adı
    </p>
</div>
""", unsafe_allow_html=True)
