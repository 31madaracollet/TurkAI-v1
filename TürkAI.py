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

# ============================================
# 🎨 GÜZEL TASARIM VE STILLER
# ============================================

st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 🌈 MODERN RENK PALETİ */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --primary-light: #3b82f6;
        --secondary: #7c3aed;
        --accent: #f59e0b;
        --success: #10b981;
        --danger: #ef4444;
        --dark: #1e293b;
        --light: #f8fafc;
        --gray: #64748b;
        --card-bg: #ffffff;
        --border: #e2e8f0;
    }
    
    /* 🎯 ANA SAYFA DÜZENİ */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* ✨ GÜZEL CHAT INPUT (ORTAYA HİZALI) */
    .beautiful-chat-container {
        position: fixed;
        bottom: 40px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 1000;
    }
    
    .beautiful-chat-input {
        background: white;
        border-radius: 50px;
        padding: 5px;
        box-shadow: 0 10px 40px rgba(37, 99, 235, 0.15);
        border: 2px solid var(--border);
        display: flex;
        align-items: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .beautiful-chat-input:focus-within {
        box-shadow: 0 15px 50px rgba(37, 99, 235, 0.25);
        border-color: var(--primary);
        transform: translateY(-2px);
    }
    
    .chat-input-field {
        flex: 1;
        border: none;
        padding: 18px 25px;
        font-size: 1.1rem;
        background: transparent;
        color: var(--dark);
        border-radius: 50px;
        outline: none;
    }
    
    .chat-input-field::placeholder {
        color: var(--gray);
    }
    
    .chat-send-btn {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        width: 55px;
        height: 55px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin-right: 5px;
        transition: all 0.3s ease;
        font-size: 1.2rem;
    }
    
    .chat-send-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(37, 99, 235, 0.3);
    }
    
    /* 🎨 GÜZEL KARTLAR */
    .beautiful-card {
        background: var(--card-bg);
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        border: 1px solid var(--border);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .beautiful-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border-color: var(--primary-light);
    }
    
    /* 🎯 MOTOR KARTLARI */
    .engine-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .engine-card:hover {
        transform: translateY(-5px);
        border-color: var(--primary);
        box-shadow: 0 15px 30px rgba(37, 99, 235, 0.1);
    }
    
    .engine-card.active {
        border-color: var(--primary);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.05), white);
    }
    
    .engine-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
    }
    
    /* 🔥 BUTONLAR */
    .beautiful-btn {
        padding: 14px 28px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
    }
    
    .btn-secondary {
        background: transparent;
        color: var(--primary);
        border: 2px solid var(--primary);
    }
    
    .btn-secondary:hover {
        background: rgba(37, 99, 235, 0.1);
    }
    
    /* 📱 RESPONSIVE */
    @media (max-width: 768px) {
        .beautiful-chat-container {
            width: 95%;
            bottom: 20px;
        }
        
        .chat-input-field {
            padding: 15px 20px;
            font-size: 1rem;
        }
    }
    
    /* 🎭 BAŞLIKLAR */
    h1, h2, h3 {
        color: var(--dark);
        font-weight: 700;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    /* 🔧 STREAMLIT ÖZEL */
    .stChatInput {
        display: none !important;
    }
    
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 🗄️ VERİTABANI
# ============================================

def db_baslat():
    conn = sqlite3.connect('turkai_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            query TEXT,
            result TEXT,
            engine TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# ============================================
# 🧠 AKILLI MOTORLAR (ÇALIŞAN)
# ============================================

class SmartSearchEngine:
    """ÇALIŞAN arama motorları"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def wikipedia_search(self, query):
        """Wikipedia'dan güvenilir bilgi"""
        try:
            url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get('extract', '')
                title = data.get('title', query)
                
                result = f"""
                # 📚 Wikipedia - {title}
                
                {extract}
                
                **Kaynak:** [Wikipedia](https://tr.wikipedia.org/wiki/{urllib.parse.quote(query)})
                """
                return result
            else:
                # Alternatif yaklaşım
                url2 = f"https://tr.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}"
                response2 = requests.get(url2, headers=self.headers, timeout=8)
                soup = BeautifulSoup(response2.content, 'html.parser')
                
                # İçerik bulmaya çalış
                content_div = soup.find('div', {'class': 'mw-parser-output'})
                if content_div:
                    paragraphs = content_div.find_all('p', limit=3)
                    text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if text:
                        return f"# 📚 Wikipedia\n\n{text[:800]}..."
                
                return None
                
        except Exception as e:
            return None
    
    def tdk_search(self, query):
        """TDK'dan kelime anlamı"""
        try:
            url = f"https://sozluk.gov.tr/gts?ara={urllib.parse.quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # TDK yeni yapısı için arama
                meanings = []
                
                # Anlamları bul
                for li in soup.find_all('li', {'class': 'lexical'}):
                    meaning = li.get_text().strip()
                    if meaning and len(meaning) > 10:
                        meanings.append(f"• {meaning}")
                
                if meanings:
                    return f"# 📖 TDK Sözlük - {query}\n\n" + "\n".join(meanings[:5])
                
                return None
                
        except:
            return None
    
    def biyografi_search(self, query):
        """Biyografi bilgisi"""
        try:
            # Biyografi.info
            url = f"https://www.biyografi.info/kisi/{urllib.parse.quote(query.lower().replace(' ', '-'))}"
            response = requests.get(url, headers=self.headers, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # İçerik bul
                content = soup.find('div', {'class': 'content'})
                if content:
                    paragraphs = content.find_all('p', limit=4)
                    text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if text:
                        return f"# 👤 Biyografi - {query}\n\n{text[:1000]}..."
            
            return None
                
        except:
            return None
    
    def calculate_math(self, expression):
        """Matematik hesaplama (GÜÇLENDİRİLMİŞ)"""
        try:
            # Temizle
            expr = expression.strip()
            
            # Basit kontrol
            if expr.isdigit():
                return float(expr)
            
            # Matematiksel ifade kontrolü
            math_pattern = r'^[0-9+\-*/(). sqrtcossintanlogpie]+$'
            if not re.match(math_pattern, expr.lower()):
                return None
            
            # Güvenli globals
            safe_globals = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log10,
                'log10': math.log10,
                'ln': math.log,
                'pi': math.pi,
                'e': math.e,
                'abs': abs,
                'round': round
            }
            
            # Hesapla
            result = eval(expr, {"__builtins__": {}}, safe_globals)
            return result
            
        except:
            return None
    
    def quick_search(self, query):
        """Hızlı motor: Wikipedia + Matematik"""
        # Önce matematik kontrolü
        math_result = self.calculate_math(query)
        if math_result is not None:
            return f"""
            # 🧮 Matematik Sonucu
            
            **İfade:** `{query}`
            
            **Sonuç:** **{math_result}**
            
            **Detaylar:**
            • Tam sayı: {int(math_result) if isinstance(math_result, (int, float)) and math_result.is_integer() else "Hayır"}
            • Karekök: {math.sqrt(math_result) if isinstance(math_result, (int, float)) and math_result >= 0 else "Negatif"}
            • Karesi: {math_result ** 2 if isinstance(math_result, (int, float)) else "Hesaplanamadı"}
            """
        
        # Wikipedia ara
        wiki_result = self.wikipedia_search(query)
        if wiki_result:
            return wiki_result
        
        # TDK ara
        tdk_result = self.tdk_search(query)
        if tdk_result:
            return tdk_result
        
        return f"""
        # 🔍 Arama Sonucu - {query}
        
        **Sonuç bulunamadı.**
        
        **Öneriler:**
        1. Farklı anahtar kelimeler deneyin
        2. Daha spesifik arama yapın
        3. Premium motoru kullanın
        """
    
    def deep_search(self, query):
        """Derin motor: Tüm kaynaklar"""
        results = []
        
        # Matematik kontrolü
        math_result = self.calculate_math(query)
        if math_result is not None:
            results.append(f"### 🧮 Matematik\n\n**Sonuç:** {math_result}")
        
        # Tüm kaynakları ara
        sources = [
            ("Wikipedia", self.wikipedia_search(query)),
            ("TDK Sözlük", self.tdk_search(query)),
            ("Biyografi", self.biyografi_search(query))
        ]
        
        for source_name, content in sources:
            if content:
                results.append(f"### {source_name}\n\n{content}")
        
        if results:
            header = f"# 🔍 Derin Analiz - {query}\n\n"
            header += f"**{len(results)} kaynaktan bilgi bulundu:**\n\n"
            return header + "\n\n---\n\n".join(results)
        else:
            return f"""
            # 🔍 Arama Sonucu - {query}
            
            **Hiçbir kaynakta bilgi bulunamadı.**
            
            **Lütfen deneyin:**
            1. Anahtar kelimeleri değiştirin
            2. Türkçe karakter kontrolü yapın
            3. Daha genel bir arama yapın
            """

# ============================================
# 📄 PDF OLUŞTURUCU (TÜRKÇE FIX)
# ============================================

def create_beautiful_pdf():
    """Güzel PDF oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Font ekle (Türkçe için)
        try:
            if os.path.exists("DejaVuSans.ttf"):
                pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
                font_name = 'DejaVu'
            else:
                font_name = 'Arial'
        except:
            font_name = 'Arial'
        
        # Başlık
        pdf.set_font(font_name, 'B', 20)
        pdf.set_text_color(37, 99, 235)  # Mavi renk
        pdf.cell(0, 15, "TÜRKAI ARAŞTIRMA RAPORU", ln=True, align='C')
        
        # Çizgi
        pdf.set_draw_color(37, 99, 235)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # Bilgiler
        pdf.set_font(font_name, '', 12)
        pdf.set_text_color(0, 0, 0)
        
        # Konu
        pdf.cell(30, 10, "Konu:", 0, 0)
        pdf.set_font(font_name, 'B', 12)
        konu = st.session_state.get('current_query', 'Belirtilmemiş')
        # Türkçe karakter fix
        konu = konu.replace('İ', 'I').replace('ı', 'i').replace('Ş', 'S').replace('ş', 's')
        pdf.cell(0, 10, konu[:50], ln=True)
        
        # Tarih
        pdf.set_font(font_name, '', 12)
        pdf.cell(30, 10, "Tarih:", 0, 0)
        pdf.cell(0, 10, datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), ln=True)
        
        # Motor
        pdf.cell(30, 10, "Motor:", 0, 0)
        motor = st.session_state.get('current_engine', 'Hızlı Motor')
        pdf.cell(0, 10, motor, ln=True)
        
        pdf.ln(15)
        
        # Sonuçlar
        if st.session_state.get('search_result'):
            pdf.set_font(font_name, 'B', 16)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 10, "ANALİZ SONUÇLARI", ln=True)
            pdf.ln(5)
            
            pdf.set_font(font_name, '', 11)
            pdf.set_text_color(0, 0, 0)
            
            result = st.session_state.search_result
            # HTML temizle
            result = re.sub(r'#+\s*', '', result)
            result = re.sub(r'\*\*', '', result)
            result = re.sub(r'`', '', result)
            
            # Satırları işle
            lines = result.split('\n')
            for line in lines[:100]:  # İlk 100 satır
                line = line.strip()
                if line:
                    if len(line) > 80:
                        # Uzun satırı böl
                        pdf.multi_cell(0, 5, line)
                    else:
                        pdf.cell(0, 5, line, ln=True)
                    pdf.ln(2)
        
        # Alt bilgi
        pdf.ln(20)
        pdf.set_font(font_name, 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, "TürkAI - Akıllı Araştırma Asistanı", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')
        
    except Exception as e:
        # Basit PDF fallback
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "TürkAI Raporu", ln=True)
        return pdf.output(dest='S').encode('latin-1')

# ============================================
# 🚀 ANA UYGULAMA
# ============================================

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'is_guest' not in st.session_state:
    st.session_state.is_guest = False
if 'search_result' not in st.session_state:
    st.session_state.search_result = None
if 'current_query' not in st.session_state:
    st.session_state.current_query = ""
if 'current_engine' not in st.session_state:
    st.session_state.current_engine = "🚀 Hızlı Motor"
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Giriş ekranı
if not st.session_state.user:
    st.markdown("""
    <div class="main-container" style="text-align: center; padding-top: 100px;">
        <h1>🤖 TürkAI</h1>
        <p style="color: var(--gray); font-size: 1.2rem; margin-bottom: 50px;">
            Akıllı Araştırma ve Analiz Platformu
        </p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Giriş kartı
        st.markdown('<div class="beautiful-card">', unsafe_allow_html=True)
        
        st.markdown("### Hoş Geldiniz")
        
        # Misafir girişi
        if st.button("👤 Misafir Olarak Devam Et", 
                    use_container_width=True,
                    type="primary"):
            st.session_state.user = "Misafir"
            st.session_state.is_guest = True
            st.rerun()
        
        st.divider()
        
        # Giriş formları
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        with tab1:
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            
            if st.button("Giriş Yap", use_container_width=True):
                if username and password:
                    sifre_hash = hashlib.sha256(password.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                             (username, sifre_hash))
                    if c.fetchone():
                        st.session_state.user = username
                        st.session_state.is_guest = False
                        st.rerun()
                    else:
                        st.error("Kullanıcı adı veya şifre hatalı")
        
        with tab2:
            new_user = st.text_input("Yeni Kullanıcı")
            new_pass = st.text_input("Yeni Şifre", type="password")
            confirm_pass = st.text_input("Şifre Tekrar", type="password")
            
            if st.button("Hesap Oluştur", use_container_width=True):
                if new_user and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        try:
                            sifre_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                            c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                                     (new_user, sifre_hash, datetime.datetime.now()))
                            conn.commit()
                            st.session_state.user = new_user
                            st.session_state.is_guest = False
                            st.success("Hesap oluşturuldu!")
                            time.sleep(1)
                            st.rerun()
                        except:
                            st.error("Bu kullanıcı adı zaten alınmış")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ANA SAYFA
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div class="beautiful-card">
        <h4>👤 {st.session_state.user}</h4>
        <p style="color: var(--gray); font-size: 0.9rem;">
            {'🎯 Misafir Modu' if st.session_state.is_guest else '✅ Premium Kullanıcı'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor seçimi
    st.markdown("### 🔧 Arama Motoru")
    engine_options = ["🚀 Hızlı Motor", "🔍 Derin Motor"]
    
    for engine in engine_options:
        is_active = engine == st.session_state.current_engine
        st.markdown(f"""
        <div class="engine-card {'active' if is_active else ''}" 
             onclick="selectEngine('{engine}')" style="margin-bottom: 10px;">
            <div class="engine-icon">{engine.split()[0]}</div>
            <h4>{engine}</h4>
            <p style="color: var(--gray); font-size: 0.9rem;">
                {'Wikipedia + Matematik + Hızlı' if 'Hızlı' in engine else 'Tüm kaynaklar + Detaylı'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Geçmiş
    if st.session_state.search_history:
        st.markdown("### 📜 Geçmiş")
        for query in st.session_state.search_history[-5:]:
            if st.button(f"🔍 {query[:25]}", key=f"hist_{query}", use_container_width=True):
                st.session_state.current_query = query
                # Arama yap
                engine = SmartSearchEngine()
                if st.session_state.current_engine == "🚀 Hızlı Motor":
                    result = engine.quick_search(query)
                else:
                    result = engine.deep_search(query)
                
                st.session_state.search_result = result
                st.rerun()

# Ana içerik
st.markdown("""
<div style="text-align: center; margin-bottom: 40px;">
    <h1>🔍 Araştırma Merkezi</h1>
    <p style="color: var(--gray);">
        Her türlü soru için akıllı cevaplar
    </p>
</div>
""", unsafe_allow_html=True)

# Motor bilgisi
st.markdown(f"""
<div class="beautiful-card" style="text-align: center;">
    <h4>🎯 Aktif Motor: {st.session_state.current_engine}</h4>
    <p>
        { 'Wikipedia + TDK + Matematik desteği' if 'Hızlı' in st.session_state.current_engine 
          else '7+ kaynak + Derin analiz + Matematik' }
    </p>
</div>
""", unsafe_allow_html=True)

# Sonuç gösterimi
if st.session_state.search_result:
    st.markdown('<div class="beautiful-card">', unsafe_allow_html=True)
    
    # Başlık
    st.markdown(f"### 📊 Sonuç: {st.session_state.current_query}")
    
    # Sonuç içeriği
    st.markdown(st.session_state.search_result)
    
    # PDF butonu
    pdf_data = create_beautiful_pdf()
    if pdf_data:
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 PDF İndir",
                data=pdf_data,
                file_name=f"turkai_{st.session_state.current_query[:20]}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col2:
            if st.button("🔄 Yeni Arama", use_container_width=True):
                st.session_state.search_result = None
                st.session_state.current_query = ""
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# 💬 GÜZEL CHAT INPUT (ORTAYA HİZALI)
# ============================================

# JavaScript için engine seçimi
st.markdown("""
<script>
function selectEngine(engineName) {
    // Streamlit'e motor değişikliğini bildir
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: 'ENGINE:' + engineName
    }, '*');
}

function handleChatSubmit() {
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    if (query) {
        // Streamlit'e gönder
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: query
        }, '*');
        input.value = '';
    }
}

// Enter tuşu desteği
document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        handleChatSubmit();
    }
});
</script>
""", unsafe_allow_html=True)

# Güzel chat input
st.markdown("""
<div class="beautiful-chat-container">
    <div class="beautiful-chat-input">
        <input type="text" 
               class="chat-input-field" 
               placeholder="🔍 Ne öğrenmek istiyorsunuz? 'Atatürk', '45*2+18/3', 'İstanbul tarihi'..."
               id="chatInput">
        <button class="chat-send-btn" onclick="handleChatSubmit()">
            →
        </button>
    </div>
</div>
""", unsafe_allow_html=True)

# Arama işlemi
query_input = st.chat_input(" ", key="main_chat_input")

if query_input:
    # Motor değişikliği mi kontrol et
    if query_input.startswith('ENGINE:'):
        new_engine = query_input.replace('ENGINE:', '')
        st.session_state.current_engine = new_engine
        st.success(f"✓ Motor değiştirildi: {new_engine}")
        st.rerun()
    
    else:
        # Normal arama
        st.session_state.current_query = query_input
        
        # Arama yap
        with st.spinner(f"🔍 '{query_input}' aranıyor..."):
            engine = SmartSearchEngine()
            
            if st.session_state.current_engine == "🚀 Hızlı Motor":
                result = engine.quick_search(query_input)
            else:
                result = engine.deep_search(query_input)
            
            st.session_state.search_result = result
            
            # Geçmişe ekle
            if query_input not in st.session_state.search_history:
                st.session_state.search_history.append(query_input)
            
            # Veritabanına kaydet (misafir değilse)
            if not st.session_state.is_guest:
                try:
                    c.execute("INSERT INTO searches (user, query, result, engine) VALUES (?, ?, ?, ?)",
                             (st.session_state.user, query_input, result, st.session_state.current_engine))
                    conn.commit()
                except:
                    pass
        
        st.rerun()
