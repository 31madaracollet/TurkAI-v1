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

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma Sistemi", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔗 GITHUB DIREKT INDIRME LİNKİ ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 PROFESYONEL TASARIM (KARANLIK/AYDINLIK MOD) ---
st.markdown("""
    <style>
    :root {
        --primary-red: #8B0000;
        --dark-bg: #0a0a0a;
        --dark-card: #151515;
        --dark-text: #e0e0e0;
        --light-bg: #f5f5f5;
        --light-card: #ffffff;
        --light-text: #222222;
        --border-radius: 8px;
    }
    
    /* Tema Kontrolü */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: var(--dark-bg);
            --card-color: var(--dark-card);
            --text-color: var(--dark-text);
            --border-color: #333;
            --shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --bg-color: var(--light-bg);
            --card-color: var(--light-card);
            --text-color: var(--light-text);
            --border-color: #ddd;
            --shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
    }
    
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }
    
    h1, h2, h3 {
        color: var(--primary-red) !important;
        font-family: 'Georgia', 'Times New Roman', serif !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 2.4rem !important;
        border-bottom: 3px solid var(--primary-red);
        padding-bottom: 12px;
        margin-bottom: 30px !important;
        text-align: center;
    }
    
    .login-container {
        max-width: 500px;
        margin: 80px auto;
        padding: 50px 40px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        border: 2px solid var(--primary-red);
        box-shadow: var(--shadow);
    }
    
    .primary-button {
        background: linear-gradient(135deg, #8B0000, #B22222) !important;
        color: white !important;
        border: none !important;
        padding: 14px 30px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    .secondary-button {
        background-color: transparent !important;
        color: var(--primary-red) !important;
        border: 2px solid var(--primary-red) !important;
        padding: 12px 28px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    .info-card {
        background-color: var(--card-color);
        border: 1px solid rgba(139, 0, 0, 0.2);
        border-radius: var(--border-radius);
        padding: 25px;
        margin: 20px 0;
        box-shadow: var(--shadow);
    }
    
    .site-card {
        background-color: var(--card-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 12px 0;
    }
    
    .site-card.active {
        border-left: 5px solid var(--primary-red);
        background-color: rgba(139, 0, 0, 0.05);
    }
    
    .spinner-container {
        text-align: center;
        padding: 50px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        margin: 30px 0;
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(139, 0, 0, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #8B0000, #B22222);
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0 5px;
    }
    
    .guest-badge {
        background-color: #6c757d;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    
    .pdf-button {
        background: linear-gradient(135deg, #006400, #228B22) !important;
        color: white !important;
        border: none !important;
        padding: 12px 25px !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: var(--border-radius) !important;
        border: 2px solid var(--border-color) !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
        padding: 12px 15px !important;
    }
    
    .stChatInput > div > div > input {
        border: 2px solid var(--primary-red) !important;
        border-radius: 25px !important;
        padding: 14px 20px !important;
        background-color: var(--card-color) !important;
        color: var(--text-color) !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: var(--card-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI YÖNETİMİ ---
def db_baslat():
    conn = sqlite3.connect('turkai_profesyonel.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
def init_session_state():
    default_values = {
        "user": None,
        "is_guest": False,
        "bilgi": None,
        "konu": "",
        "son_sorgu": None,
        "arama_devam": False,
        "aktif_site": 0,
        "site_sonuclari": [],
        "yap_butonu": False,
        "site_listesi": []
    }
    
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# --- 🔧 PROFESYONEL FONKSİYONLAR ---
def profesyonel_site_tara(url, sorgu, site_adi, timeout=8):
    """Profesyonel site tarama"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            return (site_adi, None, 0)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Reklamları temizle
        for element in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Ana içerik alanını bul
        icerik = ""
        
        # 1. Önce makale/ansiklopedi formatını ara
        article_selectors = [
            ('div', {'id': 'content'}),
            ('div', {'class': 'content'}),
            ('article', None),
            ('div', {'class': 'article'}),
            ('section', {'class': 'content'})
        ]
        
        for tag, attrs in article_selectors:
            try:
                elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
                for elem in elements:
                    text = elem.get_text().strip()
                    if len(text) > 150:
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if len(para) > 80:
                                icerik += para + "\n\n"
                        if len(icerik) > 300:
                            break
                if len(icerik) > 300:
                    break
            except:
                continue
        
        # 2. Paragraf arama
        if len(icerik) < 200:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 60:
                    icerik += text + "\n\n"
                    if len(icerik) > 300:
                        break
        
        # İçerik temizleme
        if icerik:
            # Reklamları temizle
            temizleme_listesi = [
                r'reklam.*', r'sponsor.*', r'kaydol.*', r'üye ol.*', r'abone ol.*',
                r'bizi takip edin.*', r'yorum yap.*', r'paylaş.*', r'satın al.*'
            ]
            
            for pattern in temizleme_listesi:
                icerik = re.sub(pattern, '', icerik, flags=re.IGNORECASE)
            
            icerik = re.sub(r'\s+', ' ', icerik).strip()
            
            # Kalite puanı
            puan = 0
            if 200 <= len(icerik) <= 800:
                puan += 3
            elif len(icerik) > 800:
                puan += 2
            elif len(icerik) > 100:
                puan += 1
            
            if icerik.count('.') + icerik.count(',') > 5:
                puan += 2
            
            return (site_adi, icerik[:800], puan)
        
        return (site_adi, None, 0)
            
    except:
        return (site_adi, None, 0)

def birlesik_motor_arama(sorgu):
    """Siteleri döndür"""
    turk_siteleri = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': '📚 Vikipedi',
            'tip': 'ansiklopedi',
            'oncelik': 10
        },
        {
            'url': f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}',
            'adi': '📖 TDK Sözlük',
            'tip': 'sözlük',
            'oncelik': 9
        },
        {
            'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '👤 Biyografi.info',
            'tip': 'biyografi',
            'oncelik': 8
        },
        {
            'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}',
            'adi': '🔤 Etimoloji Türkçe',
            'tip': 'etimoloji',
            'oncelik': 7
        },
        {
            'url': f'https://www.nedir.com/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '💡 Nedir.com',
            'tip': 'açıklama',
            'oncelik': 6
        },
        {
            'url': f'https://www.turkcebilgi.com/{urllib.parse.quote(sorgu.lower().replace(" ", "_"))}',
            'adi': '📘 Türkçe Bilgi',
            'tip': 'bilgi',
            'oncelik': 5
        },
        {
            'url': f'https://www.kimkimdir.gen.tr/kimkimdir.php?k={urllib.parse.quote(sorgu)}',
            'adi': '👨‍💼 Kim Kimdir',
            'tip': 'biyografi',
            'oncelik': 4
        },
        {
            'url': f'https://www.dictionarist.com/turkish/{urllib.parse.quote(sorgu)}',
            'adi': '📕 Dictionarist',
            'tip': 'sözlük',
            'oncelik': 3
        }
    ]
    
    turk_siteleri.sort(key=lambda x: x['oncelik'], reverse=True)
    return turk_siteleri

def matematik_islemi_yap(ifade):
    """Güvenli matematik işlemi yapar"""
    try:
        # Önce temel matematik işlemleri için kontrol
        if not ifade.strip():
            return None
            
        # Özel matematiksel fonksiyonlar için izin verilen karakterler
        izinli_karakterler = set('0123456789+-*/(). ')
        ozel_fonksiyonlar = ['sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'pi']
        
        # İfadeyi küçük harfe çevir
        ifade_lower = ifade.lower()
        
        # Özel matematik fonksiyonlarını kontrol et
        for fonk in ozel_fonksiyonlar:
            if fonk in ifade_lower:
                # Güvenli matematik ifadesi oluştur
                if fonk == 'sqrt':
                    # Karekök işlemi
                    num = re.search(r'sqrt\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.sqrt(float(num.group(1)))
                elif fonk == 'pi':
                    return math.pi
                elif fonk == 'sin':
                    num = re.search(r'sin\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.sin(math.radians(float(num.group(1))))
                elif fonk == 'cos':
                    num = re.search(r'cos\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.cos(math.radians(float(num.group(1))))
                elif fonk == 'tan':
                    num = re.search(r'tan\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.tan(math.radians(float(num.group(1))))
                elif fonk == 'log':
                    num = re.search(r'log\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.log10(float(num.group(1)))
                elif fonk == 'exp':
                    num = re.search(r'exp\((\d+\.?\d*)\)', ifade_lower)
                    if num:
                        return math.exp(float(num.group(1)))
        
        # Basit matematik işlemleri için güvenli kontrol
        guvenli_ifade = ''
        for char in ifade:
            if char in izinli_karakterler:
                guvenli_ifade += char
        
        if not guvenli_ifade:
            return None
            
        # Matematik işlemini yap
        result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        return result
        
    except Exception as e:
        return None

def profesyonel_pdf_olustur():
    """Profesyonel PDF oluştur - Türkçe karakter sorunu çözüldü"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # UTF-8 encoding için
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        pdf.add_font('DejaVu', 'I', 'DejaVuSansCondensed-Oblique.ttf', uni=True)
        
        # Başlık
        pdf.set_font('DejaVu', 'B', 18)
        pdf.set_text_color(139, 0, 0)
        pdf.cell(190, 15, txt="TÜRKAI ANALİZ RAPORU", ln=True, align='C')
        pdf.ln(5)
        
        # Çizgi
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # Konu bilgisi
        pdf.set_font('DejaVu', 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 10, txt="Konu:", ln=0)
        pdf.set_font('DejaVu', '', 14)
        konu_text = str(st.session_state.konu)[:50]
        pdf.cell(150, 10, txt=konu_text.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.ln(5)
        
        # Tarih
        pdf.set_font('DejaVu', 'B', 12)
        pdf.cell(40, 8, txt="Tarih:", ln=0)
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(150, 8, txt=datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), ln=True)
        
        # Kullanıcı
        pdf.set_font('DejaVu', 'B', 12)
        pdf.cell(40, 8, txt="Kullanıcı:", ln=0)
        pdf.set_font('DejaVu', '', 12)
        user_text = str(st.session_state.user)
        if st.session_state.is_guest:
            user_text += " (Misafir)"
        pdf.cell(150, 8, txt=user_text.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.ln(15)
        
        # İçerik başlığı
        pdf.set_font('DejaVu', 'B', 16)
        pdf.set_text_color(139, 0, 0)
        pdf.cell(190, 10, txt="ANALİZ SONUÇLARI", ln=True)
        pdf.ln(5)
        
        # İçerik
        pdf.set_font('DejaVu', '', 11)
        pdf.set_text_color(0, 0, 0)
        
        if st.session_state.bilgi:
            icerik = str(st.session_state.bilgi)
            
            # Türkçe karakterleri Latin-1'e çevir
            icerik_latin1 = icerik.encode('latin-1', 'replace').decode('latin-1')
            
            # HTML/Markdown temizleme
            icerik_latin1 = re.sub(r'#+\s*', '', icerik_latin1)
            icerik_latin1 = re.sub(r'\*\*', '', icerik_latin1)
            icerik_latin1 = re.sub(r'\*', '', icerik_latin1)
            
            # Paragraflara ayır
            paragraphs = icerik_latin1.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Uzun paragrafı böl
                    if pdf.get_string_width(para) > 180:
                        words = para.split()
                        line = ""
                        for word in words:
                            if pdf.get_string_width(line + ' ' + word) < 180:
                                line += word + ' '
                            else:
                                pdf.multi_cell(0, 6, txt=line.strip())
                                line = word + ' '
                        if line:
                            pdf.multi_cell(0, 6, txt=line.strip())
                    else:
                        pdf.multi_cell(0, 6, txt=para)
                    pdf.ln(4)
        
        # Alt bilgi
        pdf.ln(20)
        pdf.set_font('DejaVu', 'I', 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(190, 5, txt="TürkAI Profesyonel Araştırma Sistemi", ln=True, align='C')
        pdf.cell(190, 5, txt="© 2024", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        # DejaVu fontu yoksa alternatif
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Alternatif yaklaşım - sadece ASCII karakterler
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="TURKAI RAPORU", ln=True, align='C')
            
            pdf.set_font("Arial", '', 12)
            pdf.cell(190, 10, txt=f"Konu: {st.session_state.konu[:30]}", ln=True)
            pdf.cell(190, 10, txt=f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}", ln=True)
            
            # İçeriği ASCII karakterlere çevir
            if st.session_state.bilgi:
                content = str(st.session_state.bilgi)
                # Türkçe karakterleri İngilizce karşılıklarına çevir
                char_map = {
                    'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G',
                    'ğ': 'g', 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o',
                    'Ç': 'C', 'ç': 'c'
                }
                
                for tr_char, en_char in char_map.items():
                    content = content.replace(tr_char, en_char)
                
                # Sadece ASCII karakterleri al
                content_ascii = ''.join(char for char in content if ord(char) < 128)
                
                pdf.multi_cell(0, 6, txt=content_ascii[:500])
            
            return pdf.output(dest='S').encode('latin-1')
        except:
            return None

# --- 🔐 PROFESYONEL GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Ana Logo ve Başlık
        st.markdown("""
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1 style='color: #8B0000; font-size: 2.8rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #666; font-size: 1.1rem; margin-top: -10px;'>
                Profesyonel Araştırma ve Analiz Sistemi
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        # Uyarı Mesajı
        st.markdown("""
        <div class='info-card' style='background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107;'>
            <b>⚠️ ÖNEMLİ UYARI:</b><br>
            Yaptığınız oturumlar geçicidir. Çıkış yaptığınızda tüm veriler silinecektir.
        </div>
        """, unsafe_allow_html=True)
        
        # Misafir Girişi
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("👤 Misafir Girişi", use_container_width=True, type="primary"):
                st.session_state.user = "Misafir_Kullanıcı"
                st.session_state.is_guest = True
                st.rerun()
        
        with col_b:
            st.markdown(f'<a href="{APK_URL}" target="_blank" class="primary-button" style="text-decoration: none; display: block; text-align: center;">📱 Uygulamayı İndir</a>', unsafe_allow_html=True)
        
        # Bilgi Kutusu
        st.markdown("""
        <div class='info-card'>
            <b>🔧 SİSTEM ÖZELLİKLERİ:</b><br>
            • Birleşik Motor<br>
            • Derin Analiz + Matematik<br>
            • Türkçe Kaynak Odaklı<br>
            • Profesyonel PDF Rapor
        </div>
        """, unsafe_allow_html=True)
        
        # Giriş Formları
        tab_login, tab_register = st.tabs(["🔐 SİSTEM GİRİŞİ", "📝 YENİ KAYIT"])
        
        with tab_login:
            st.markdown("### Sisteme Giriş")
            u_in = st.text_input("Kullanıcı Adı", key="login_user")
            p_in = st.text_input("Şifre", type="password", key="login_pass")
            
            if st.button("OTURUMU BAŞLAT", use_container_width=True, type="primary"):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone():
                        st.session_state.user = u_in
                        st.session_state.is_guest = False
                        st.rerun()
                    else:
                        st.error("Geçersiz kullanıcı adı veya şifre.")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")
        
        with tab_register:
            st.markdown("### Yeni Hesap Oluştur")
            nu = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            np2 = st.text_input("Şifre Tekrar", type="password", key="reg_pass2")
            
            if st.button("HESAP OLUŞTUR", use_container_width=True, type="primary"):
                if nu and np and np2:
                    if np == np2:
                        if len(np) >= 6:
                            try:
                                c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                                conn.commit()
                                st.success("Hesap başarıyla oluşturuldu.")
                                time.sleep(1)
                                st.session_state.user = nu
                                st.session_state.is_guest = False
                                st.rerun()
                            except:
                                st.error("Bu kullanıcı adı zaten kullanımda.")
                        else:
                            st.error("Şifre en az 6 karakter olmalıdır.")
                    else:
                        st.error("Şifreler eşleşmiyor.")
                else:
                    st.warning("Lütfen tüm alanları doldurun.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 40px; color: #666; font-size: 0.85rem;'>
            <p>TürkAI © 2024 | Tüm hakları saklıdır</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 🚀 PROFESYONEL SIDEBAR ---
with st.sidebar:
    # Kullanıcı Bilgisi
    user_display = str(st.session_state.user)
    if st.session_state.is_guest:
        user_display += " <span class='guest-badge'>Misafir</span>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #8B0000, #B22222); padding: 20px; border-radius: var(--border-radius); margin-bottom: 20px; color: white;'>
        <h4 style='color: white; margin: 0;'>👤 {user_display}</h4>
        <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.85rem;'>
            {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 OTURUMU SONLANDIR", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi - MATEMATİK EKLENDİ
    st.markdown("### 🎯 ANALİZ MOTORU")
    m_secim = st.radio(
        "",
        ["🚀 Birleşik Motor", "🤔 Derin Analiz + Matematik"],
        label_visibility="collapsed"
    )
    
    # Motor Açıklamaları
    if m_secim == "🚀 Birleşik Motor":
        st.markdown("""
        <div class='info-card' style='margin-top: 10px; font-size: 0.9rem; padding: 15px;'>
        <b>BİRLEŞİK MOTOR</b><br>
        • Vikipedi + TDK<br>
        • Hızlı arama<br>
        • Özet bilgi
        </div>
        """, unsafe_allow_html=True)
    elif m_secim == "🤔 Derin Analiz + Matematik":
        st.markdown("""
        <div class='info-card' style='margin-top: 10px; font-size: 0.9rem; padding: 15px;'>
        <b>DERİN ANALİZ + MATEMATİK</b><br>
        • 8 Türkçe site<br>
        • Matematik işlemleri<br>
        • Site site ilerleme
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Geçmiş Aramalar
    st.markdown("### 📋 ARAMA GEÇMİŞİ")
    if not st.session_state.is_guest:
        c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,))
        results = c.fetchall()
        if results:
            for (konu,) in results:
                if konu and st.button(f"📄 {konu[:22]}", key=f"h_{konu}", use_container_width=True, type="secondary"):
                    c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1", 
                             (st.session_state.user, konu))
                    result = c.fetchone()
                    if result and result[0]:
                        st.session_state.bilgi = result[0]
                        st.session_state.konu = konu
                        st.session_state.son_sorgu = konu
                        st.rerun()
        else:
            st.info("Henüz arama geçmişi yok")
    else:
        st.info("Misafir modunda geçmiş kaydedilmez")
    
    st.divider()
    
    # APK İndirme
    st.markdown(f'<a href="{APK_URL}" target="_blank" style="text-decoration: none;">', unsafe_allow_html=True)
    if st.button("📲 MOBİL UYGULAMA", use_container_width=True, type="primary"):
        pass
    st.markdown('</a>', unsafe_allow_html=True)

# --- 💻 ANA ARAYÜZ ---
st.markdown("""
<div style='text-align: center; margin-bottom: 25px;'>
    <h1>🔍 PROFESYONEL ARAŞTIRMA TERMİNALİ</h1>
</div>
""", unsafe_allow_html=True)

# Arama Talimatı
st.markdown("""
<div class='info-card' style='text-align: center;'>
    <p style='font-size: 1.1rem; margin: 0; color: var(--primary-red); font-weight: 600;'>
        Araştırmak istediğin konunun anahtar kelimesini yazınız.
    </p>
    <p style='font-size: 0.9rem; margin: 5px 0 0 0; color: var(--text-color); opacity: 0.8;'>
        Örnek: "Atatürk", "İstanbul", "45*2+18/3", "sqrt(16)"
    </p>
</div>
""", unsafe_allow_html=True)

# Arama Çubuğu
sorgu = st.chat_input("🔎 Anahtar kelime veya matematik ifadesi yazın...")

if sorgu and sorgu.strip():
    sorgu = sorgu.strip()
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    st.session_state.aktif_site = 0
    st.session_state.site_sonuclari = []
    st.session_state.yap_butonu = False
    
    # Matematik kontrolü
    matematik_sonucu = matematik_islemi_yap(sorgu)
    
    if matematik_sonucu is not None:
        # Matematik işlemi bulundu
        st.session_state.bilgi = f"# 🧮 MATEMATİKSEL İŞLEM SONUCU\n\n"
        st.session_state.bilgi += f"**İfade:** {sorgu}\n\n"
        st.session_state.bilgi += f"**Sonuç:** **{matematik_sonucu}**\n\n"
        
        # Ek matematiksel açıklamalar
        if isinstance(matematik_sonucu, (int, float)):
            st.session_state.bilgi += f"**Detaylar:**\n"
            st.session_state.bilgi += f"• Yaklaşık değer: {matematik_sonucu:.4f}\n"
            
            if matematik_sonucu >= 0:
                st.session_state.bilgi += f"• Karekök: {math.sqrt(matematik_sonucu):.4f}\n"
                st.session_state.bilgi += f"• Karesi: {matematik_sonucu**2:.4f}\n"
            
        st.session_state.konu = f"MATEMATİK: {sorgu}"
        st.session_state.arama_devam = False
        
    else:
        # Normal arama yap
        with st.spinner(""):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(f"""
            <div class='spinner-container'>
                <div class='spinner'></div>
                <h3 style='color: #8B0000;'>TÜRKAI ANALİZ EDİYOR</h3>
                <p>"{sorgu}" için araştırma yapılıyor...</p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if m_secim == "🚀 Birleşik Motor":
                try:
                    # Vikipedi'den başla
                    wiki_icerik = ""
                    try:
                        wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                        wiki_res = requests.get(wiki_api, headers=headers, timeout=8)
                        if wiki_res.status_code == 200:
                            wiki_data = wiki_res.json()
                            wiki_icerik = wiki_data.get('extract', '')
                    except:
                        wiki_icerik = ''
                    
                    # TDK'yı dene
                    tdk_icerik = ""
                    try:
                        tdk_url = f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}'
                        tdk_response = requests.get(tdk_url, headers=headers, timeout=8)
                        
                        if tdk_response.status_code == 200:
                            tdk_soup = BeautifulSoup(tdk_response.content, 'html.parser')
                            
                            for div in tdk_soup.find_all('div', class_=re.compile(r'(anlam|tanim|aciklama)')):
                                text = div.get_text().strip()
                                if len(text) > 50:
                                    tdk_icerik += text + "\n\n"
                    except:
                        tdk_icerik = ""
                    
                    # Birleştirilmiş rapor
                    rapor = f"# 📊 BİRLEŞİK ANALİZ: {sorgu.upper()}\n\n"
                    
                    if wiki_icerik:
                        rapor += f"## 📚 Vikipedi\n{wiki_icerik}\n\n"
                    
                    if tdk_icerik and len(tdk_icerik) > 50:
                        rapor += f"## 📖 TDK Sözlük\n{tdk_icerik[:600]}...\n\n"
                    
                    if not wiki_icerik and (not tdk_icerik or len(tdk_icerik) < 50):
                        rapor = f"# ⚠️ SONUÇ BULUNAMADI\n\n'{sorgu}' için Türkçe kaynaklarda yeterli bilgi bulunamadı."
                    
                    st.session_state.bilgi = rapor
                    st.session_state.konu = sorgu
                    
                except Exception as e:
                    st.session_state.bilgi = f"# ⚠️ TEKNİK HATA\n\nArama sırasında bir hata oluştu."
                    st.session_state.konu = sorgu
            
            elif m_secim == "🤔 Derin Analiz + Matematik":
                thinking_placeholder.empty()
                
                # Site listesini al ve ilk siteyi tara
                siteler = birlesik_motor_arama(sorgu)
                st.session_state.site_listesi = siteler
                
                if siteler:
                    # İlk siteyi tarayıp göster
                    site = siteler[0]
                    site_adi, icerik, puan = profesyonel_site_tara(site['url'], sorgu, site['adi'])
                    
                    if icerik and puan > 2:
                        st.session_state.aktif_site = 1
                        
                        # Anlık bilgi gösterimi
                        rapor = f"# 🔍 İLK BULUNAN SİTE\n\n"
                        rapor += f"## {site_adi}\n"
                        rapor += f"*Kalite puanı: {puan}/10*\n\n"
                        rapor += f"{icerik}\n\n"
                        rapor += "---\n\n"
                        rapor += "**📌 Not:** 'YENİDEN YAP' butonuna tıklayarak bir sonraki siteye geçebilirsiniz."
                        
                        st.session_state.bilgi = rapor
                        st.session_state.konu = f"DERİN: {sorgu}"
                        st.session_state.yap_butonu = True
                        
                    else:
                        st.session_state.bilgi = f"# ⚠️ İLK SİTEDE BİLGİ BULUNAMADI\n\n'YENİDEN YAP' butonuyla bir sonraki siteye geçebilirsiniz."
                        st.session_state.konu = sorgu
                        st.session_state.yap_butonu = True
    
    st.session_state.arama_devam = False
    
    # Veritabanına kaydet (misafir değilse)
    if st.session_state.bilgi and not st.session_state.is_guest:
        try:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        except:
            pass
    
    st.rerun()

# --- 🤔 DERİN ANALİZ MODU SİTE GEÇİŞİ ---
if m_secim == "🤔 Derin Analiz + Matematik" and st.session_state.yap_butonu and st.session_state.site_listesi:
    st.markdown("---")
    st.markdown("### 🏗️ SİTE GEÇİŞ SİSTEMİ")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class='info-card'>
            <p><b>Geçerli Durum:</b> {st.session_state.aktif_site}/{len(st.session_state.site_listesi)} site taranmıştır.</p>
            <p><b>Yapılacak İşlem:</b> Butona tıklayarak bir sonraki siteye geçebilirsiniz.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 YENİDEN YAP", use_container_width=True, type="primary"):
            if st.session_state.aktif_site < len(st.session_state.site_listesi):
                # Sonraki siteyi tara
                site = st.session_state.site_listesi[st.session_state.aktif_site]
                
                with st.spinner(f"{site['adi']} taranıyor..."):
                    site_adi, icerik, puan = profesyonel_site_tara(site['url'], st.session_state.son_sorgu, site['adi'])
                    
                    if icerik and puan > 2:
                        st.session_state.site_sonuclari.append({
                            'site': site_adi,
                            'icerik': icerik,
                            'puan': puan,
                            'tip': site['tip']
                        })
                        
                        # Yeni site bilgisini göster
                        rapor = f"# 🔍 {st.session_state.aktif_site + 1}. SİTE BULUNDU\n\n"
                        rapor += f"## {site_adi}\n"
                        rapor += f"*Kalite puanı: {puan}/10 • Tip: {site['tip']}*\n\n"
                        rapor += f"{icerik}\n\n"
                        
                        if st.session_state.aktif_site + 1 < len(st.session_state.site_listesi):
                            rapor += "---\n\n"
                            rapor += "**📌 Not:** 'YENİDEN YAP' butonuna tıklayarak bir sonraki siteye geçebilirsiniz."
                        
                        st.session_state.bilgi = rapor
                        st.success(f"✅ {site_adi} - Kalite: {puan}/10")
                        
                    else:
                        st.warning(f"⚠️ {site_adi}'de yeterli bilgi bulunamadı")
                        rapor = f"# ⚠️ SİTE TARANAMADI\n\n{site['adi']} sitesinde yeterli bilgi bulunamadı.\n\n"
                        
                        if st.session_state.aktif_site + 1 < len(st.session_state.site_listesi):
                            rapor += "Bir sonraki site için 'YENİDEN YAP' butonuna tıklayın."
                        
                        st.session_state.bilgi = rapor
                
                st.session_state.aktif_site += 1
                
                # Tüm siteler tarandıysa özet rapor oluştur
                if st.session_state.aktif_site >= len(st.session_state.site_listesi):
                    if st.session_state.site_sonuclari:
                        # Sonuçları puanına göre sırala
                        st.session_state.site_sonuclari.sort(key=lambda x: x['puan'], reverse=True)
                        
                        # Özet rapor oluştur
                        ozet_rapor = f"# 📊 DERİN ANALİZ ÖZETİ: {st.session_state.son_sorgu.upper()}\n\n"
                        ozet_rapor += f"**📋 ANALİZ SONUÇLARI:**\n"
                        ozet_rapor += f"• Toplam {len(st.session_state.site_listesi)} site taranmıştır\n"
                        ozet_rapor += f"• {len(st.session_state.site_sonuclari)} sitede kaliteli bilgi bulunmuştur\n\n"
                        
                        # En iyi sonuçları göster
                        for i, sonuc in enumerate(st.session_state.site_sonuclari[:3]):
                            ozet_rapor += f"## 🏆 {sonuc['site']}\n"
                            ozet_rapor += f"*Kalite: {sonuc['puan']}/10*\n\n"
                            
                            cumleler = re.split(r'(?<=[.!?])\s+', sonuc['icerik'])
                            for cumle in cumleler[:3]:
                                if len(cumle.strip()) > 20:
                                    ozet_rapor += f"• {cumle.strip()}\n"
                            
                            ozet_rapor += "\n"
                        
                        if len(st.session_state.site_sonuclari) > 3:
                            ozet_rapor += f"*Ve {len(st.session_state.site_sonuclari) - 3} ek kaynak daha incelenmiştir.*\n\n"
                        
                        st.session_state.bilgi = ozet_rapor
                        st.session_state.yap_butonu = False
                        
                        # Veritabanına kaydet (misafir değilse)
                        if not st.session_state.is_guest:
                            try:
                                c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                                         (st.session_state.user, st.session_state.konu, 
                                          st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
                                conn.commit()
                            except:
                                pass
                        
                        st.rerun()
                    else:
                        st.session_state.bilgi = f"# ❌ SONUÇ BULUNAMADI\n\n'{st.session_state.son_sorgu}' için hiçbir sitede yeterli bilgi bulunamadı."
                        st.session_state.yap_butonu = False
                        st.rerun()
    
    # İlerleme adımlarını göster
    st.markdown("### 📋 SİTE LİSTESİ")
    for i, site in enumerate(st.session_state.site_listesi):
        durum = "✅" if i < st.session_state.aktif_site else "⏳" if i == st.session_state.aktif_site else "◻️"
        st.markdown(f"{durum} **{site['adi']}** - {site['tip'].capitalize()}")

# --- 📊 RAPOR GÖSTERİMİ ---
if st.session_state.son_sorgu and not st.session_state.arama_devam and st.session_state.bilgi:
    # Aktif Sorgu Bilgisi
    st.markdown("---")
    st.markdown(f"""
    <div class='info-card'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <strong style='color: #8B0000;'>🔍 AKTİF SORGUNUZ:</strong> {st.session_state.son_sorgu}<br>
                <strong style='color: #8B0000;'>🎯 MOD:</strong> {m_secim}<br>
                <strong style='color: #8B0000;'>👤 KULLANICI:</strong> {st.session_state.user}{" (Misafir)" if st.session_state.is_guest else ""}
            </div>
            <div style='text-align: right; color: #666; font-size: 0.9rem;'>
                {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Rapor Gösterimi
    st.markdown("### 📄 ANALİZ RAPORU")
    st.markdown(st.session_state.bilgi)
    
    # PDF İndirme Butonu
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📥 PDF RAPOR İNDİR", use_container_width=True, type="primary"):
            with st.spinner("PDF oluşturuluyor..."):
                pdf_data = profesyonel_pdf_olustur()
                if pdf_data:
                    # PDF İndirme butonu
                    st.download_button(
                        label="⬇️ PDF'Yİ İNDİR",
                        data=pdf_data,
                        file_name=f"TurkAI_Raporu_{str(st.session_state.konu)[:25].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.error("PDF oluşturulamadı. Lütfen daha basit bir raporla tekrar deneyin.")
    
    # Ek Butonlar - KOPYALAMA DÜZELTİLDİ
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 YENİ ARAMA", use_container_width=True, type="secondary"):
            st.session_state.son_sorgu = None
            st.session_state.bilgi = None
            st.session_state.site_sonuclari = []
            st.session_state.yap_butonu = False
            st.rerun()
    
    with col2:
        # Panoya kopyalama düzeltildi
        if st.button("📋 PANOYA KOPYALA", use_container_width=True, type="secondary"):
            try:
                # Raporu kopyalanabilir formata getir
                kopya_metni = f"TürkAI Raporu - {st.session_state.konu}\n"
                kopya_metni += f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                kopya_metni += "=" * 50 + "\n\n"
                
                # HTML/Markdown temizleme
                temiz_metin = st.session_state.bilgi
                temiz_metin = re.sub(r'#+\s*', '', temiz_metin)
                temiz_metin = re.sub(r'\*\*(.*?)\*\*', r'\1', temiz_metin)
                temiz_metin = re.sub(r'\*', '', temiz_metin)
                
                kopya_metni += temiz_metin
                
                # Streamlit'in built-in kopyalama özelliği
                st.code(kopya_metni[:1000] + ("..." if len(kopya_metni) > 1000 else ""), language='text')
                st.info("Rapor kopyalanabilir formatta gösterildi. Metni seçip Ctrl+C ile kopyalayabilirsiniz.")
            except:
                st.warning("Kopyalama sırasında bir hata oluştu.")
    
    with col3:
        if st.button("💾 KAYDET", use_container_width=True, type="secondary", disabled=st.session_state.is_guest):
            if not st.session_state.is_guest:
                st.success("Arama geçmişe kaydedildi")
            else:
                st.warning("Misafir modunda kayıt yapılamaz")
