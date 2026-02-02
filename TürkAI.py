# -*- coding: utf-8 -*-
"""
TÜRKAI - Türkçe Akıllı Asistan (Streamlit Cloud Uyumlu)
Versiyon: 1.0 Cloud
"""

import streamlit as st
import requests
import hashlib
import datetime
import re
import json
import urllib.parse
import os
from duckduckgo_search import DDGS

# ========== SAYFA AYARLARI ==========
st.set_page_config(
    page_title="TÜRKAI - Türkçe Akıllı Asistan",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ÖZEL CSS TASARIM ==========
st.markdown("""
<style>
    /* Ana arka plan */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Ana konteyner */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 25px;
        margin: 15px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    }
    
    /* Başlıklar */
    h1 {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 10px !important;
    }
    
    h2, h3 {
        color: #cc0000 !important;
        font-weight: 800 !important;
    }
    
    /* Kullanıcı mesajı */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 14px 22px;
        border-radius: 18px 18px 5px 18px;
        margin: 12px 0;
        max-width: 75%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* AI mesajı */
    .ai-response {
        background: white;
        border-left: 5px solid #cc0000;
        padding: 18px 22px;
        border-radius: 0 18px 18px 0;
        margin: 18px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Butonlar */
    .stButton > button {
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        transition: transform 0.2s !important;
        font-size: 14px !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 3px solid #cc0000;
    }
    
    /* Giriş konteyneri */
    .login-container {
        background: white;
        border: 2px solid #cc0000;
        border-radius: 20px;
        padding: 35px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(204, 0, 0, 0.15);
        margin-top: 20px;
    }
    
    /* Logo */
    .logo {
        font-size: 2.5em;
        font-weight: 900;
        background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    
    /* Input alanları */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #ddd !important;
        padding: 12px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #cc0000 !important;
        box-shadow: 0 0 0 2px rgba(204, 0, 0, 0.1) !important;
    }
    
    /* Sekmeler */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
    }
    
    /* Başarı mesajı */
    .stAlert {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE YÖNETİMİ ==========
def init_session_state():
    """Session state'i başlat"""
    defaults = {
        'user': None,
        'last_query': '',
        'last_response': '',
        'history': [],
        'is_demo': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ========== VERİ YÖNETİMİ (Streamlit Cloud için) ==========
def save_to_session_history(username, query, response, category="genel"):
    """Geçmişi session state'te sakla"""
    history_item = {
        'username': username,
        'query': query,
        'response': response,
        'category': category,
        'timestamp': datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    
    # En fazla 20 kayıt tut
    if len(st.session_state.history) >= 20:
        st.session_state.history.pop(0)
    
    st.session_state.history.append(history_item)

def get_user_history(username):
    """Kullanıcı geçmişini getir"""
    return [item for item in st.session_state.history if item['username'] == username]

# ========== ARAMA FONKSİYONLARI ==========
def search_wikipedia(query):
    """Wikipedia'dan bilgi ara"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
        
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if 'extract' in data:
                title = data.get('title', query)
                extract = data['extract']
                return f"📚 **Wikipedia: {title}**\n\n{extract}"
        return None
    except:
        return None

def search_duckduckgo(query):
    """DuckDuckGo'dan web araması"""
    try:
        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(
                f"{query} nedir Türkçe bilgi",
                region='tr-tr',
                max_results=4,
                timelimit='y'
            ))
            
            if not results:
                return None
            
            formatted_results = "🌐 **Web Sonuçları:**\n\n"
            for i, result in enumerate(results[:3], 1):
                title = result.get('title', 'Başlık yok')[:60]
                body = result.get('body', 'İçerik yok')
                
                # Kısa bir özet oluştur
                if body and len(body) > 150:
                    body = body[:150] + "..."
                
                formatted_results += f"**{i}. {title}**\n"
                formatted_results += f"{body}\n\n"
            
            return formatted_results
    except Exception as e:
        return f"⚠️ Arama sırasında hata oluştu: {str(e)[:50]}"

def get_weather(city="İstanbul"):
    """Hava durumu bilgisi al"""
    try:
        url = f"http://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=tr"
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            
            weather_info = f"""
📍 **{city.upper()} Hava Durumu**
            
🌡️ **Sıcaklık:** {current.get('temp_C', 'N/A')}°C
🌡️ **Hissedilen:** {current.get('FeelsLikeC', 'N/A')}°C
☁️ **Durum:** {current['weatherDesc'][0]['value']}
💨 **Rüzgar:** {current.get('windspeedKmph', 'N/A')} km/h
💧 **Nem:** {current.get('humidity', 'N/A')}%
"""
            
            return weather_info.strip()
        else:
            return f"📍 **{city}** hava durumu alınamadı. Lütfen şehir adını kontrol edin."
    except:
        return f"📍 **{city}** hava durumu servisine ulaşılamıyor."

def calculate_math(expression):
    """Matematik işlemi yap"""
    try:
        # Güvenlik için temizleme
        safe_expr = expression.replace('x', '*').replace('X', '*')
        safe_expr = safe_expr.replace(',', '.')
        
        # Sadece izin verilen karakterler
        if not re.match(r'^[\d\s+\-*/().]+$', safe_expr.replace(' ', '')):
            return "⚠️ Geçersiz matematik ifadesi. Sadece sayılar ve + - * / ( ) kullanabilirsiniz."
        
        # Hesaplama
        result = eval(safe_expr, {"__builtins__": {}}, {})
        
        return f"""
🧮 **Matematik Sonucu**
        
**İşlem:** `{expression}`
**Sonuç:** `{result}`
        
ℹ️ {datetime.datetime.now().strftime('%H:%M')} tarihinde hesaplandı.
"""
    except Exception as e:
        return f"⚠️ Hesaplama hatası: {str(e)[:50]}"

# ========== METİN İŞLEME ==========
def clean_text(text):
    """Metni temizle ve formatla"""
    if not text:
        return ""
    
    # HTML etiketlerini temizle
    text = re.sub(r'<[^>]+>', '', text)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    
    # URL'leri temizle
    text = re.sub(r'https?://\S+', '', text)
    
    # Madde işaretlerini düzenle
    text = text.replace('•', '•')
    
    return text.strip()

# ========== GİRİŞ SİSTEMİ ==========
def login_system():
    """Giriş ve kayıt sistemi"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class='login-container'>
            <div class='logo'>🇹🇷 TÜRKAI</div>
            <h3>Türkçe Akıllı Asistan</h3>
            <p style='color: #666;'>
                %100 Türkçe yapay zeka deneyimi
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 **Giriş Yap**", "📝 **Kayıt Ol**"])
        
        with tab1:
            username = st.text_input("👤 Kullanıcı Adı", key="login_username")
            password = st.text_input("🔒 Şifre", type="password", key="login_password")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🚀 Giriş Yap", use_container_width=True, type="primary"):
                    if username and password:
                        # Basit bir doğrulama (gerçek uygulamada hash kullanılmalı)
                        if username == "demo" and password == "demo123":
                            st.session_state.user = "demo"
                            st.session_state.is_demo = True
                            st.success("Demo hesabına hoş geldin! 🎮")
                            st.rerun()
                        elif len(username) >= 3:
                            # Basit hash (gerçek uygulamada daha güvenli olmalı)
                            simple_hash = hashlib.md5(password.encode()).hexdigest()[:10]
                            st.session_state.user = username
                            st.session_state.is_demo = False
                            st.success(f"Hoş geldin {username}! 🎉")
                            st.rerun()
                        else:
                            st.error("Kullanıcı adı en az 3 karakter olmalı!")
                    else:
                        st.warning("Lütfen tüm alanları doldurun!")
            
            with col_b:
                if st.button("👁️ Demo Giriş", use_container_width=True):
                    st.session_state.user = "demo"
                    st.session_state.is_demo = True
                    st.success("Demo moduna hoş geldin! 🎮")
                    st.rerun()
        
        with tab2:
            new_username = st.text_input("👤 Yeni Kullanıcı Adı", key="reg_username")
            new_password = st.text_input("🔒 Yeni Şifre", type="password", key="reg_password")
            confirm_password = st.text_input("🔒 Şifre Tekrar", type="password", key="reg_confirm")
            
            if st.button("✨ Hesap Oluştur", use_container_width=True, type="primary"):
                if not all([new_username, new_password, confirm_password]):
                    st.error("Tüm alanları doldurun!")
                elif new_password != confirm_password:
                    st.error("Şifreler uyuşmuyor!")
                elif len(new_username) < 3:
                    st.error("Kullanıcı adı en az 3 karakter olmalı!")
                elif len(new_password) < 4:
                    st.error("Şifre en az 4 karakter olmalı!")
                else:
                    st.session_state.user = new_username
                    st.session_state.is_demo = False
                    st.success("🎉 Hesabınız oluşturuldu! Giriş yapılıyor...")
                    st.rerun()

# ========== SIDEBAR ==========
def render_sidebar():
    """Sidebar içeriğini oluştur"""
    
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 15px; 
             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             border-radius: 12px; color: white; margin-bottom: 15px;'>
            <h4>👤 {st.session_state.user}</h4>
            <small>{'Demo Modu' if st.session_state.is_demo else 'Aktif Kullanıcı'}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔴 Çıkış Yap", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.session_state.is_demo = False
            st.rerun()
        
        st.divider()
        
        # Geçmiş sorgular
        st.markdown("### 📋 Son Aramalar")
        
        user_history = get_user_history(st.session_state.user)
        
        if user_history:
            # En son 5 kaydı göster
            for item in user_history[-5:][::-1]:  # En yeni en üstte
                query_short = item['query'][:22] + "..." if len(item['query']) > 22 else item['query']
                
                if st.button(f"📌 {query_short}", key=f"hist_{item['timestamp']}", 
                           use_container_width=True, help=item['query']):
                    st.session_state.last_query = item['query']
                    st.session_state.last_response = item['response']
                    st.rerun()
        else:
            st.info("📝 Henüz arama geçmişiniz yok.")
        
        st.divider()
        
        # Hızlı başlangıç soruları
        st.markdown("### 💡 Hızlı Sorular")
        
        quick_questions = [
            ("Atatürk kimdir?", "tarih"),
            ("İstanbul hava", "hava"),
            ("15 x 3 + 7", "matematik"),
            ("Python nedir?", "teknoloji"),
            ("Türkiye başkenti", "coğrafya")
        ]
        
        for q, cat in quick_questions:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state.last_query = q
                # Hemen işlem yapmak için
                st.rerun()

# ========== ANA UYGULAMA ==========
def main_app():
    """Ana uygulama arayüzü"""
    
    # Başlık
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1>🤖 TÜRKAI Analiz Merkezi</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Türkçe akıllı asistanınıza her şeyi sorabilirsiniz!</p>", 
                   unsafe_allow_html=True)
    
    # Sidebar'ı render et
    render_sidebar()
    
    # Sorgu girişi - Daha büyük ve merkezde
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    
    with col2:
        query = st.text_input(
            " ",
            placeholder="💭 TürkAI'ye sorunuzu yazın... (Örnek: 'Python nedir?', 'İstanbul hava durumu', '25*4+8')",
            key="main_query_input",
            label_visibility="collapsed"
        )
    
    # Sorguyu işle
    if query:
        st.session_state.last_query = query
        
        with st.spinner("🤖 TÜRKAI düşünüyor..."):
            
            # 1. Matematik işlemi kontrolü
            math_pattern = r'^[\d\s+\-*/().xX]+$'
            clean_query = query.replace(' ', '')
            
            if re.match(math_pattern, clean_query):
                response = calculate_math(query)
                category = "matematik"
            
            # 2. Hava durumu kontrolü
            elif any(keyword in query.lower() for keyword in ['hava', 'hava durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar']):
                # Şehir adını çıkar
                words = query.lower().split()
                city_keywords = ['hava', 'durumu', 'sıcaklık', 'kaç', 'derece', 'nedir']
                city = "İstanbul"  # Varsayılan
                
                for word in words:
                    if word not in city_keywords and len(word) > 2:
                        city = word.title()
                        break
                
                response = get_weather(city)
                category = "hava durumu"
            
            # 3. Genel sorgu
            else:
                # Önce Wikipedia'dan dene
                wiki_response = search_wikipedia(query)
                
                if wiki_response:
                    response = wiki_response
                    category = "wikipedia"
                else:
                    # Wikipedia'da yoksa web'den ara
                    ddg_response = search_duckduckgo(query)
                    
                    if ddg_response and "Web Sonuçları:" in ddg_response:
                        response = ddg_response
                        category = "web arama"
                    else:
                        # Hiçbir şey bulunamadı
                        response = f"""
                        🤔 **"{query}"** hakkında detaylı bilgi bulunamadı.
                        
                        **Önerilerim:**
                        • Sorgunuzu daha açıklayıcı yazın
                        • Türkçe karakterleri kontrol edin
                        • Farklı bir ifade deneyin
                        
                        **Örnekler:**
                        - "Mustafa Kemal Atatürk kimdir?"
                        - "Python programlama dili nedir?"
                        - "İstanbul'un nüfusu kaç?"
                        """
                        category = "genel"
            
            # Metni temizle
            response = clean_text(response)
            
            # Geçmişe kaydet
            save_to_session_history(
                st.session_state.user,
                query,
                response,
                category
            )
            
            # Sonuçları göster
            st.markdown(f"""
            <div class='user-message'>
                <strong>👤 Siz:</strong><br>
                {query}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='ai-response'>
                <strong>🤖 TÜRKAI:</strong><br><br>
                {response}
            </div>
            """, unsafe_allow_html=True)
            
            # Ekstra özellikler
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Yeni Sorgu", use_container_width=True):
                    st.session_state.last_query = ""
                    st.session_state.last_response = ""
                    st.rerun()
            
            with col2:
                if st.button("📋 Geçmişi Temizle", use_container_width=True):
                    st.session_state.history = []
                    st.success("Geçmiş temizlendi!")
                    st.rerun()
            
            with col3:
                # Basit bir indirme butonu
                timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M")
                filename = f"turkai_cevap_{timestamp}.txt"
                
                st.download_button(
                    label="📥 Cevabı İndir",
                    data=response,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Önceki sorguyu göster (eğer varsa)
    elif st.session_state.last_query:
        st.markdown(f"""
        <div class='user-message'>
            <strong>👤 Siz:</strong><br>
            {st.session_state.last_query}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='ai-response'>
            <strong>🤖 TÜRKAI:</strong><br><br>
            {st.session_state.last_response}
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Karşılama mesajı
        st.markdown("""
        <div class='ai-response' style='text-align: center;'>
            <h3>👋 Hoş Geldiniz!</h3>
            <p>TürkAI'ye istediğiniz konuda soru sorabilirsiniz.</p>
            
            <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0;'>
                <h4>💡 Örnek Sorular:</h4>
                <ul style='text-align: left;'>
                    <li><strong>Matematik:</strong> "15 x 3 + 7 kaç eder?"</li>
                    <li><strong>Hava Durumu:</strong> "İstanbul'da hava nasıl?"</li>
                    <li><strong>Bilgi:</strong> "Atatürk kimdir?"</li>
                    <li><strong>Teknoloji:</strong> "Python nedir?"</li>
                </ul>
            </div>
            
            <p>👈 Soldaki menüden hızlı sorulara ulaşabilirsiniz.</p>
        </div>
        """, unsafe_allow_html=True)

# ========== UYGULAMA BAŞLATMA ==========
def main():
    """Uygulamayı başlat"""
    
    # Session state'i başlat
    init_session_state()
    
    # Giriş kontrolü
    if not st.session_state.user:
        login_system()
    else:
        main_app()
    
    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 40px; padding-top: 20px; 
         border-top: 1px solid #eee; color: #666; font-size: 0.85em;'>
        <p>
            🚀 <strong>TÜRKAI v1.0 Cloud</strong> | 🇹🇷 %100 Türkçe Akıllı Asistan<br>
            <span style='color: #cc0000;'>Streamlit Cloud Uyumlu</span>
        </p>
        <p style='margin-top: 5px;'>
            🔥 Geliştirici: Madara | 📧 Demo hesap: <strong>demo / demo123</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== BAŞLAT ==========
if __name__ == "__main__":
    main()
