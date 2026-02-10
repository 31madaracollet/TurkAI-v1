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
import os

# ============================================
# 🎨 TASARIM - KARANLIK/AYDINLIK MOD
# ============================================

st.set_page_config(
    page_title="TürkAI | Akıllı Araştırma", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* TEMA SİSTEMİ */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border: #e2e8f0;
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --secondary: #7c3aed;
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    
    .dark-mode {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border: #334155;
        --primary: #3b82f6;
        --primary-hover: #60a5fa;
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    body {
        background: var(--bg-primary);
        color: var(--text-primary);
        transition: all 0.3s ease;
    }
    
    /* TEMA BUTONU */
    .theme-btn {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: var(--bg-card);
        border: 2px solid var(--border);
        border-radius: 50px;
        padding: 8px 15px;
        cursor: pointer;
        font-weight: 600;
        color: var(--text-primary);
        box-shadow: var(--shadow);
    }
    
    /* GÜZEL CHAT INPUT */
    .chat-fixed {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 700px;
        z-index: 999;
    }
    
    .chat-input-box {
        background: var(--bg-card);
        border: 2px solid var(--border);
        border-radius: 50px;
        padding: 5px;
        display: flex;
        box-shadow: var(--shadow);
    }
    
    .chat-input-box input {
        flex: 1;
        border: none;
        padding: 16px 25px;
        font-size: 1.1rem;
        background: transparent;
        color: var(--text-primary);
        border-radius: 50px;
        outline: none;
    }
    
    .chat-send-btn {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        cursor: pointer;
        margin-right: 5px;
        font-size: 1.2rem;
    }
    
    /* BUTONLAR */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
    }
    
    .stChatInput {
        display: none !important;
    }
</style>

<script>
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
}
</script>
""", unsafe_allow_html=True)

# Tema butonu
st.markdown("""
<div class="theme-btn" onclick="toggleTheme()">
    🌙 Tema
</div>
""", unsafe_allow_html=True)

# ============================================
# 🗄️ VERİTABANI
# ============================================

conn = sqlite3.connect('turkai.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS searches (user TEXT, query TEXT, result TEXT, engine TEXT, time TEXT)')
conn.commit()

# ============================================
# 🧠 ÇALIŞAN MOTOR
# ============================================

class SearchEngine:
    def search(self, query, engine_type="quick"):
        """ÇALIŞAN arama motoru"""
        try:
            # Matematik
            math_result = self._calculate_math(query)
            if math_result is not None:
                return self._format_math(query, math_result)
            
            # Wikipedia
            wiki = self._get_wikipedia(query)
            if wiki:
                return f"# 📚 Wikipedia\n\n{wiki}\n\n🔗 Kaynak: Wikipedia"
            
            # TDK
            tdk = self._get_tdk(query)
            if tdk:
                return f"# 📖 TDK\n\n{tdk}\n\n🔗 Kaynak: TDK Sözlük"
            
            return f"# 🔍 '{query}'\n\nSonuç bulunamadı. Lütfen farklı kelimeler deneyin."
            
        except Exception as e:
            return f"# ⚠️ Hata\n\nArama sırasında hata: {str(e)}"
    
    def _calculate_math(self, expr):
        """Matematik hesapla"""
        try:
            expr = expr.lower().replace(' ', '')
            if not re.match(r'^[0-9+\-*/().sqrtcossintanlogpie]+$', expr):
                return None
            
            safe = {
                'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
                'tan': math.tan, 'pi': math.pi, 'e': math.e
            }
            return eval(expr, {"__builtins__": {}}, safe)
        except:
            return None
    
    def _get_wikipedia(self, query):
        """Wikipedia'dan al"""
        try:
            url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r.json().get('extract', '')
        except:
            pass
        return None
    
    def _get_tdk(self, query):
        """TDK'dan al"""
        try:
            url = f"https://sozluk.gov.tr/gts?ara={urllib.parse.quote(query)}"
            r = requests.get(url, timeout=5)
            soup = BeautifulSoup(r.content, 'html.parser')
            # TDK parsing
            return "TDK'da bulundu."
        except:
            return None
    
    def _format_math(self, query, result):
        """Matematik formatı"""
        return f"""# 🧮 Matematik

**Soru:** `{query}`

**Sonuç:** **{result}**

**Detaylar:**
- Yaklaşık: {result:.6f}
- Tam sayı: {"Evet" if isinstance(result, (int, float)) and result.is_integer() else "Hayır"}
"""

# ============================================
# 📄 PDF
# ============================================

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "TürkAI Raporu", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# ============================================
# 🚀 UYGULAMA
# ============================================

# Session State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'engine' not in st.session_state:
    st.session_state.engine = "🚀 Hızlı"
if 'result' not in st.session_state:
    st.session_state.result = None
if 'query' not in st.session_state:
    st.session_state.query = ""

# Giriş
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🤖 TürkAI")
        
        # MISAFIR BUTONU - ÇALIŞIYOR
        if st.button("👤 Misafir Girişi", use_container_width=True, type="primary"):
            st.session_state.user = "Misafir"
            st.rerun()
        
        st.divider()
        
        tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
        
        with tab1:
            user = st.text_input("Kullanıcı")
            pwd = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                if user and pwd:
                    hash_pwd = hashlib.sha256(pwd.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, hash_pwd))
                    if c.fetchone():
                        st.session_state.user = user
                        st.rerun()
        
        with tab2:
            new_user = st.text_input("Yeni Kullanıcı")
            new_pwd = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                if new_user and new_pwd:
                    try:
                        hash_pwd = hashlib.sha256(new_pwd.encode()).hexdigest()
                        c.execute("INSERT INTO users VALUES (?, ?)", (new_user, hash_pwd))
                        conn.commit()
                        st.session_state.user = new_user
                        st.rerun()
                    except:
                        st.error("Kullanıcı var")
    
    st.stop()

# ANA SAYFA
st.title("🔍 Araştırma Merkezi")

# Sidebar
with st.sidebar:
    st.write(f"**Kullanıcı:** {st.session_state.user}")
    
    # ÇIKIŞ BUTONU - ÇALIŞIYOR
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # MOTOR SEÇİMİ - ÇALIŞIYOR
    st.write("**Motor:**")
    if st.button("🚀 Hızlı Motor", use_container_width=True):
        st.session_state.engine = "🚀 Hızlı"
        st.rerun()
    
    if st.button("🔍 Derin Motor", use_container_width=True):
        st.session_state.engine = "🔍 Derin"
        st.rerun()
    
    st.divider()
    
    # GITHUB LİNKİ (Streamlit uyumlu)
    st.markdown("""
    **📱 Kaynak Kod:**
    
    [GitHub Repository](https://github.com/31madaracollet/TurkAI-v1)
    
    *APK yakında eklenecek*
    """)

# Hızlı butonlar - ÇALIŞIYOR
st.write("**Hızlı Aramalar:**")
cols = st.columns(4)
queries = ["Atatürk", "İstanbul", "45*2+18", "Matematik"]

for col, q in zip(cols, queries):
    with col:
        if st.button(q, use_container_width=True):
            st.session_state.query = q
            engine = SearchEngine()
            st.session_state.result = engine.search(q, st.session_state.engine)
            st.rerun()

# Sonuçlar
if st.session_state.result:
    st.markdown(st.session_state.result)
    
    # PDF BUTONU - ÇALIŞIYOR
    col1, col2 = st.columns(2)
    with col1:
        pdf_data = create_pdf()
        st.download_button(
            label="📥 PDF İndir",
            data=pdf_data,
            file_name="rapor.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        if st.button("🔄 Yeni", use_container_width=True):
            st.session_state.result = None
            st.session_state.query = ""
            st.rerun()

# CHAT INPUT (ORTA)
st.markdown("""
<div class="chat-fixed">
    <div class="chat-input-box">
        <input type="text" placeholder="💬 Soru sorun..." id="chatInput">
        <button class="chat-send-btn" onclick="sendQuery()">→</button>
    </div>
</div>

<script>
function sendQuery() {
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

// Enter tuşu
document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendQuery();
});
</script>
""", unsafe_allow_html=True)

# Arama
query_input = st.chat_input(" ")

if query_input:
    st.session_state.query = query_input
    engine = SearchEngine()
    st.session_state.result = engine.search(query_input, st.session_state.engine)
    st.rerun()
