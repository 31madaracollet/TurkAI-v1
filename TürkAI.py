"""
TÜRKAI - Ultimate Türkçe AI Asistan
Sürüm: 3.5 | Madara Edition - PDF DESTEKLİ
"""

import streamlit as st
import requests
import datetime
import re
import urllib.parse
from duckduckgo_search import DDGS
from fpdf import FPDF
import base64

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
    st.session_state.dark_mode = True

# ==================== TEMA SİSTEMİ ====================
def load_theme():
    if st.session_state.dark_mode:
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
        return """
        <style>
        /* AYDINLIK MOD */
        .stApp { background-color: #ffffff; color: #333333; }
        h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
        .main-container { background-color: #fffafa; border: 2px solid #cc0000; color: #333333; }
        .user-msg { background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%); color: #ffffff !important; }
        .ai-response { border-left: 6px solid #cc0000; background-color: #fdfdfd; color: #333333; }
        .stButton > button { background-color: #cc0000 !important; color: white !important; }
        [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
        .stTextInput > div > div > input { background: white !important; color: #333333 !important; border: 2px solid #cc0000 !important; }
        .card-light { background-color: #f8f9fa; border: 1px solid #cc0000; color: #666666; }
        .theme-btn { background: #f0f0f0 !important; border: 1px solid #cc0000 !important; color: #cc0000 !important; }
        </style>
        """

COMMON_CSS = """
<style>
.main-container { border-radius: 24px; padding: 25px; margin: 15px; backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(204, 0, 0, 0.25); }
.user-msg { padding: 16px 22px; border-radius: 20px 20px 5px 20px; margin: 15px 0 15px auto; max-width: 75%; position: relative; box-shadow: 0 4px 15px rgba(204, 0, 0, 0.4); animation: slideInRight 0.3s ease-out; }
.user-msg::before { content: "👤"; position: absolute; left: -45px; top: 50%; transform: translateY(-50%); background: #cc0000; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 3px 10px rgba(204, 0, 0, 0.3); }
.ai-response { padding: 22px 25px; border-radius: 0 20px 20px 0; margin: 20px auto 20px 0; position: relative; box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3); line-height: 1.7; animation: slideInLeft 0.3s ease-out; }
.ai-response::before { content: "🤖"; position: absolute; right: -45px; top: 50%; transform: translateY(-50%); background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%); width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 3px 10px rgba(204, 0, 0, 0.3); }
.stButton > button { border: none !important; border-radius: 12px !important; padding: 12px 28px !important; font-weight: 700 !important; font-size: 15px !important; transition: all 0.3s ease !important; box-shadow: 0 4px 15px rgba(204, 0, 0, 0.3) !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(204, 0, 0, 0.4) !important; }
.stTextInput > div > div > input { border-radius: 15px !important; padding: 16px 20px !important; font-size: 16px !important; transition: all 0.3s !important; }
.stTextInput > div > div > input:focus { box-shadow: 0 0 0 3px rgba(204, 0, 0, 0.2) !important; }
.card-common { border-radius: 16px; padding: 20px; margin: 15px 0; transition: all 0.3s; }
.logo { font-size: 3.5em; font-weight: 900; background: linear-gradient(135deg, #ff4d4d 0%, #cc0000 50%, #ff4d4d 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 4px 20px rgba(204, 0, 0, 0.4); margin-bottom: 10px; }
@keyframes slideInRight { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideInLeft { from { transform: translateX(-30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(204, 0, 0, 0.3), transparent); margin: 25px 0; }
</style>
"""

# Temayı yükle
st.markdown(load_theme() + COMMON_CSS, unsafe_allow_html=True)

# ==================== PDF OLUŞTURMA ====================
def create_pdf(query, response, username):
    """PDF oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Türkçe karakterler için font
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # Logo
        pdf.set_font('DejaVu', 'B', 20)
        pdf.cell(200, 10, txt='🔥 TÜRKAI RAPORU', ln=True, align='C')
        pdf.ln(5)
        
        # Kullanıcı bilgisi
        pdf.set_font('DejaVu', '', 11)
        pdf.cell(200, 10, txt=f'Kullanıcı: {username}', ln=True)
        pdf.cell(200, 10, txt=f'Tarih: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}', ln=True)
        pdf.ln(10)
        
        # Sorgu
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(200, 10, txt='SORU:', ln=True)
        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 10, txt=query[:500])
        pdf.ln(5)
        
        # Cevap
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(200, 10, txt='CEVAP:', ln=True)
        pdf.set_font('DejaVu', '', 11)
        
        # Metni parçalara ayır
        lines = response.split('\n')
        for line in lines:
            if len(line) > 90:
                # Uzun satırları böl
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if len(current_line + ' ' + word) <= 90:
                        current_line += ' ' + word
                    else:
                        pdf.multi_cell(0, 6, txt=current_line.strip())
                        current_line = word
                if current_line:
                    pdf.multi_cell(0, 6, txt=current_line.strip())
            else:
                pdf.multi_cell(0, 6, txt=line)
            pdf.ln(2)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('DejaVu', 'I', 10)
        pdf.cell(0, 10, txt='TÜRKAI - Ultimate Türkçe AI Asistan | Madara Edition', ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception:
        # Fallback: Basit PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Türkçe karakterleri düzelt
        def fix_turkish(text):
            replacements = {
                'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's',
                'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u',
                'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'
            }
            for tr, en in replacements.items():
                text = text.replace(tr, en)
            return text
        
        pdf.cell(200, 10, txt="TURKAI RAPORU", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Kullanici: {username}", ln=True)
        pdf.cell(200, 10, txt=f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
        pdf.ln(10)
        pdf.multi_cell(0, 10, txt=fix_turkish(f"SORU: {query}\n\nCEVAP: {response}"))
        
        return pdf.output(dest='S').encode('latin-1')

# ==================== ARAMA FONKSİYONLARI ====================
def search_wikipedia_turkish(query):
    """Wikipedia'dan TÜRKÇE bilgi"""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if 'extract' in data and data['extract']:
                title = data.get('title', query)
                return f"📚 **Wikipedia: {title}**\n\n{data['extract'][:500]}..."
    except:
        pass
    return None

def search_web_turkish(query):
    """İnternetten TÜRKÇE içerik"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{query} nedir Türkçe",
                region='tr-tr',
                max_results=3
            ))
            
            if results:
                text = "🌐 **İnternet Kaynakları:**\n\n"
                for i, r in enumerate(results, 1):
                    title = r.get('title', '')[:50]
                    body = r.get('body', '')[:150]
                    if body and any(char in title.lower() for char in ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']):
                        text += f"{i}. **{title}**\n   {body}...\n\n"
                return text if "**" in text else None
    except:
        pass
    return None

def get_weather_turkish(city="İstanbul"):
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
        return f"📍 **{city} Hava Durumu**\n\nHava bilgisi alınamadı."

def calculate_math_safe(expression):
    """Matematik hesaplama"""
    try:
        expr = expression.replace('x', '*').replace('X', '*').replace(',', '.')
        if not re.match(r'^[\d+\-*/().]+$', expr.replace(' ', '')):
            return "⚠️ Geçersiz ifade!"
        
        result = eval(expr, {"__builtins__": {}}, {})
        return f"""
🧮 **Matematik Sonucu**

**İşlem:** `{expression}`
**Sonuç:** `{result}`

⏱️ {datetime.datetime.now().strftime("%H:%M")}
"""
    except:
        return "⚠️ Hesaplanamadı!"

# ==================== GİRİŞ SİSTEMİ ====================
def login_page():
    """Giriş sayfası"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # TEMA DEĞİŞTİRME
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
        
        # LOGO
        st.markdown(f"""
        <div class='main-container'>
            <div class='logo'>🔥 TÜRKAI</div>
            <h3 style='text-align: center; color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>
                {'Madara Edition - Karanlık Mod' if st.session_state.dark_mode else 'Madara Edition - Aydınlık Mod'}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # GİRİŞ/KAYIT
        tab1, tab2 = st.tabs(["🔓 GİRİŞ YAP", "✨ HESAP OLUŞTUR"])
        
        with tab1:
            user = st.text_input("Kullanıcı Adı", key="login_user")
            password = st.text_input("Şifre", type="password", key="login_pass")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🚀 GİRİŞ YAP", use_container_width=True, type="primary"):
                    if user:
                        st.session_state.user = user
                        st.success(f"Hoş geldin {user}! 🎉")
                        st.rerun()
            with col_b:
                if st.button("👁️ DEMO", use_container_width=True):
                    st.session_state.user = "demo"
                    st.success("Demo moduna hoş geldin! 🎮")
                    st.rerun()
        
        with tab2:
            new_user = st.text_input("Yeni Kullanıcı", key="reg_user")
            new_pass = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            
            if st.button("🔥 KAYIT OL", use_container_width=True, type="primary"):
                if new_user:
                    st.session_state.user = new_user
                    st.success(f"{new_user} hesabı oluşturuldu! 🎊")
                    st.rerun()

# ==================== SIDEBAR ====================
def render_sidebar():
    """Sidebar"""
    
    with st.sidebar:
        # TEMA
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
        
        # KULLANICI
        card_class = "card-dark" if st.session_state.dark_mode else "card-light"
        st.markdown(f"""
        <div class='card-common {card_class}'>
            <h4 style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>
                👤 {st.session_state.user}
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        # ÇIKIŞ
        if st.button("🔴 ÇIKIŞ", use_container_width=True, type="secondary"):
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
            ("🔢 15 x 3 + 7", "15*3+7")
        ]
        
        for label, query in quick_actions:
            if st.button(label, key=f"quick_{query}", use_container_width=True):
                st.session_state.last_query = query
                st.rerun()
        
        st.markdown("---")
        
        # SON SORGULAR
        st.markdown("### 📜 SON SORGULAR")
        
        if st.session_state.history:
            recent = st.session_state.history[-5:][::-1]
            for i, item in enumerate(recent):
                query_display = item['query'][:20] + "..." if len(item['query']) > 20 else item['query']
                if st.button(f"📌 {query_display}", key=f"recent_{i}", use_container_width=True):
                    st.session_state.last_query = item['query']
                    st.session_state.last_response = item['response']
                    st.rerun()
        else:
            st.info("Henüz sorgu yok.")

# ==================== ANA UYGULAMA ====================
def main_app():
    """Ana uygulama"""
    
    # BAŞLIK
    st.markdown(f"""
    <div class='main-container'>
        <h1>🔥 TÜRKAI</h1>
        <p style='text-align: center; color: {'#aaa' if st.session_state.dark_mode else '#666'};'>
            {'Karanlık Mod' if st.session_state.dark_mode else 'Aydınlık Mod'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # SIDEBAR
    render_sidebar()
    
    # CHAT INPUT
    col1, col2, col3 = st.columns([0.3, 3.4, 0.3])
    with col2:
        query = st.text_input(
            "",
            placeholder="💬 Sorunuzu yazın... (Matematik, Hava, Genel)",
            key="main_input",
            label_visibility="collapsed"
        )
    
    # SORGU İŞLEME
    if query:
        st.session_state.last_query = query
        
        with st.spinner("🤖 TÜRKAI düşünüyor..."):
            # MATEMATİK
            clean_query = query.replace(' ', '')
            if re.match(r'^[\d+\-*/().xX]+$', clean_query):
                response = calculate_math_safe(query)
                category = "matematik"
            
            # HAVA DURUMU
            elif any(keyword in query.lower() for keyword in ['hava', 'durumu', 'sıcaklık']):
                city = "İstanbul"
                words = query.lower().split()
                for w in words:
                    if w not in ['hava', 'durumu', 'nasıl'] and len(w) > 2:
                        city = w.title()
                        break
                response = get_weather_turkish(city)
                category = "hava"
            
            # GENEL SORGU
            else:
                wiki = search_wikipedia_turkish(query)
                if wiki:
                    response = wiki
                    category = "wikipedia"
                else:
                    web = search_web_turkish(query)
                    if web:
                        response = web
                        category = "web"
                    else:
                        response = f"""
🤔 **"{query}"** hakkında bilgi bulunamadı.

**Öneriler:**
• Türkçe karakter kullanın
• Daha açıklayıcı yazın
• Farklı kelimeler deneyin
"""
                        category = "genel"
            
            # GEÇMİŞE KAYDET
            history_item = {
                'query': query,
                'response': response,
                'category': category,
                'time': datetime.datetime.now().strftime("%H:%M")
            }
            
            if len(st.session_state.history) >= 20:
                st.session_state.history.pop(0)
            
            st.session_state.history.append(history_item)
            st.session_state.last_response = response
            
            # SONUÇLARI GÖSTER
            st.markdown(f"""
            <div class='user-msg'>
                <b>{st.session_state.user}:</b><br>
                {query}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class='ai-response'>
                {response}
            </div>
            """, unsafe_allow_html=True)
            
            # PDF İNDİRME BUTONU
            st.markdown("---")
            col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 1, 1])
            
            with col_pdf2:
                try:
                    pdf_data = create_pdf(query, response, st.session_state.user)
                    filename = f"turkai_rapor_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    
                    st.download_button(
                        label="📥 PDF OLARAK KAYDET",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                except Exception as e:
                    st.error("PDF oluşturulamadı!")
    
    # ÖNCEKİ SORGU
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
        
        # PDF BUTONU (önceki sorgu için)
        st.markdown("---")
        col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 1, 1])
        
        with col_pdf2:
            try:
                pdf_data = create_pdf(
                    st.session_state.last_query,
                    st.session_state.last_response,
                    st.session_state.user
                )
                filename = f"turkai_rapor_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                st.download_button(
                    label="📥 PDF OLARAK KAYDET",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except:
                st.warning("PDF oluşturulamadı!")
    
    else:
        # KARŞILAMA
        st.markdown(f"""
        <div class='ai-response' style='text-align: center;'>
            <h3 style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>👋 HOŞ GELDİNİZ!</h3>
            
            <div style='
                background: {'rgba(204, 0, 0, 0.1)' if st.session_state.dark_mode else 'rgba(204, 0, 0, 0.05)'};
                border-radius: 16px;
                padding: 20px;
                margin: 25px 0;
                border: 1px solid {'rgba(204, 0, 0, 0.3)' if st.session_state.dark_mode else 'rgba(204, 0, 0, 0.2)'};
            '>
                <h4 style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>🚀 HEMEN DENEYİN</h4>
                
                <div style='text-align: left; color: {'#ccc' if st.session_state.dark_mode else '#666'};'>
                    <p>• Matematik: "784+8874"</p>
                    <p>• Hava: "İstanbul hava durumu"</p>
                    <p>• Tarih: "Atatürk kimdir?"</p>
                    <p>• PDF olarak kaydedebilirsiniz! 📥</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== BAŞLAT ====================
if not st.session_state.user:
    login_page()
else:
    main_app()

# FOOTER
st.markdown(f"""
<div style='
    text-align: center;
    margin-top: 50px;
    padding-top: 25px;
    border-top: 1px solid rgba(204, 0, 0, 0.2);
    color: {'#666' if st.session_state.dark_mode else '#888'};
    font-size: 0.85em;
'>
    <p>
        🚀 <strong style='color: {'#ff4d4d' if st.session_state.dark_mode else '#cc0000'};'>TÜRKAI v3.5</strong>
        | PDF DESTEKLİ
    </p>
    <p style='margin-top: 5px;'>
        🔥 Her cevabı PDF olarak kaydedin! | 🇹🇷 %100 Türkçe
    </p>
</div>
""", unsafe_allow_html=True)
