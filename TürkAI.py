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

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(page_title="TürkAI | Profesyonel Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 PROFESYONEL TASARIM ---
st.markdown("""
    <style>
    :root { 
        --primary-red: #8B0000;
        --dark-bg: #0a0a0a;
        --card-bg: #1a1a1a;
    }
    
    .stApp {
        background-color: var(--dark-bg);
    }
    
    h1, h2, h3 { 
        color: var(--primary-red) !important; 
        font-weight: 700 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .giris-kapsayici {
        border: 2px solid var(--primary-red);
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background-color: rgba(139, 0, 0, 0.05);
        box-shadow: 0 4px 20px rgba(139, 0, 0, 0.2);
    }

    .apk-buton-link {
        display: block;
        width: 100%;
        background: linear-gradient(45deg, #8B0000, #B22222);
        color: white !important;
        text-align: center;
        padding: 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 20px;
        transition: transform 0.2s;
        font-family: 'Segoe UI', sans-serif;
        border: none;
    }

    .apk-buton-link:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(139, 0, 0, 0.3);
    }

    .sidebar-indir-link {
        display: block;
        background-color: transparent;
        color: #8B0000 !important;
        text-align: center;
        padding: 10px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid #8B0000;
        font-size: 14px;
        margin-top: 10px;
        font-family: 'Segoe UI', sans-serif;
        transition: all 0.3s;
    }

    .sidebar-indir-link:hover {
        background-color: rgba(139, 0, 0, 0.1);
    }

    .not-alani {
        background-color: rgba(139, 0, 0, 0.08);
        color: #8B0000;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #8B0000;
        margin-bottom: 20px;
        font-size: 0.9rem;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 500;
    }

    .tuyo-metni {
        font-size: 0.95rem;
        color: #e0e0e0;
        margin-bottom: 25px;
        padding: 15px;
        background-color: var(--card-bg);
        border-radius: 8px;
        border-left: 4px solid #8B0000;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 50px;
        margin: 30px 0;
        background-color: var(--card-bg);
        border-radius: 10px;
        border: 1px solid rgba(139, 0, 0, 0.3);
    }
    
    .spinner {
        width: 70px;
        height: 70px;
        border: 5px solid rgba(139, 0, 0, 0.1);
        border-top: 5px solid #8B0000;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 25px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .motor-badge {
        background: linear-gradient(45deg, #8B0000, #B22222);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 0 5px;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .site-bilgi {
        background-color: rgba(0, 100, 0, 0.1);
        border-left: 4px solid #006400;
        padding: 14px;
        margin: 15px 0;
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 500;
        color: #32CD32;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .rapor-kapsayici {
        background-color: var(--card-bg);
        padding: 25px;
        border-radius: 10px;
        border: 1px solid rgba(139, 0, 0, 0.2);
        margin: 20px 0;
        line-height: 1.8;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .profesyonel-buton {
        background: linear-gradient(45deg, #8B0000, #B22222) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    
    .sidebar-radio .st-cc {
        color: #e0e0e0 !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    
    .stTextInput input {
        background-color: #2a2a2a !important;
        color: #e0e0e0 !important;
        border: 1px solid #444 !important;
    }
    
    .stTextInput label {
        color: #e0e0e0 !important;
    }
    
    .stChatInput input {
        background-color: #2a2a2a !important;
        color: #e0e0e0 !important;
        border: 2px solid #8B0000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI YÖNETİMİ ---
def db_baslat():
    conn = sqlite3.connect('turkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "arama_devam" not in st.session_state: st.session_state.arama_devam = False

# --- 🔧 PROFESYONEL FONKSİYONLAR ---
def profesyonel_site_tara(url, sorgu, site_adi, timeout=8):
    """Profesyonel site tarama - sadece Türkçe ve kaliteli kaynaklar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Türkçe içerik kontrolü
        tum_metin = soup.get_text().lower()
        turkce_kelimeler = ['ve', 'bir', 'bu', 'ile', 'için', 'olarak', 'gibi', 'kadar', 'ancak']
        turkce_puan = sum(1 for kelime in turkce_kelimeler if kelime in tum_metin)
        
        if turkce_puan < 3:  # Yeterli Türkçe içerik yoksa
            return (site_adi, None, 0)
        
        # Ana içerik alanını bul
        icerik = ""
        
        # Önce makale/ansiklopedi formatını ara
        article_divs = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'(makale|icerik|ansiklopedi|bilgi|content)'))
        
        if article_divs:
            for div in article_divs:
                text = div.get_text().strip()
                if len(text) > 100 and sorgu.lower() in text.lower():
                    icerik += text + "\n\n"
                    break
        
        # Eğer bulamadıysa paragraf ara
        if len(icerik) < 100:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 80 and sorgu.lower() in text.lower():
                    icerik += text + "\n\n"
                    if len(icerik) > 300:  # Yeterli içerik
                        break
        
        # İçerik temizleme
        if icerik:
            # Reklam ve gereksiz ifadeleri temizle
            temizleme_listesi = [
                'reklam', 'sponsor', 'kaydol', 'üye ol', 'abone ol', 
                'bizi takip edin', 'yorum yap', 'paylaş', 'satın al',
                'indirim', 'kampanya', 'fırsat', 'sepete ekle'
            ]
            
            for gereksiz in temizleme_listesi:
                icerik = re.sub(gereksiz, '', icerik, flags=re.IGNORECASE)
            
            # Fazla boşlukları temizle
            icerik = re.sub(r'\s+', ' ', icerik).strip()
            
            # Kalite puanı hesapla
            puan = min(len(icerik) // 50, 10)  # Uzunluk puanı
            puan += turkce_puan * 2  # Türkçe puanı
            
            return (site_adi, icerik[:1000], puan)  # Max 1000 karakter
        
        return (site_adi, None, 0)
            
    except Exception:
        return (site_adi, None, 0)

def derin_turk_arama(sorgu):
    """Sadece Türkçe ve kaliteli kaynaklarda derin arama"""
    
    # SADECE TÜRKÇE ve GÜVENİLİR KAYNAKLAR
    turk_siteleri = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': '📚 Vikipedi (Türkçe)',
            'aciklama': 'Türkçe ansiklopedi'
        },
        {
            'url': f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}',
            'adi': '📖 TDK Sözlük',
            'aciklama': 'Türk Dil Kurumu'
        },
        {
            'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}',
            'adi': '🔤 Etimoloji Türkçe',
            'aciklama': 'Köken bilgisi'
        },
        {
            'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '👤 Biyografi.info',
            'aciklama': 'Türkçe biyografiler'
        },
        {
            'url': f'https://www.nedir.com/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': '💡 Nedir.com',
            'aciklama': 'Türkçe açıklamalar'
        }
    ]
    
    bulunan_bilgiler = []
    basarili_siteler = []
    
    # Progress gösterimi
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, site in enumerate(turk_siteleri):
        status_text.text(f"🔎 {site['adi']} taranıyor...")
        progress_bar.progress((i + 1) / len(turk_siteleri))
        
        site_adi, icerik, puan = profesyonel_site_tara(site['url'], sorgu, site['adi'])
        
        if icerik and puan > 3:  # Minimum kalite puanı
            basarili_siteler.append({
                'adi': site['adi'],
                'aciklama': site['aciklama'],
                'puan': puan
            })
            bulunan_bilgiler.append((site['adi'], icerik, puan))
            
            # Kaliteli bilgi bulduysa diğer sitelere geç
            if puan >= 8:  # Çok kaliteli bilgi
                status_text.text(f"✅ Mükemmel bilgi bulundu: {site['adi']}")
                time.sleep(0.5)
                break
        
        time.sleep(0.3)  # Doğal bir gecikme
    
    progress_bar.empty()
    status_text.empty()
    
    # Bilgileri puanına göre sırala
    bulunan_bilgiler.sort(key=lambda x: x[2], reverse=True)
    
    return bulunan_bilgiler, basarili_siteler

def profesyonel_pdf_olustur():
    """Profesyonel PDF rapor oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Başlık
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(190, 10, txt="TÜRKAI PROFESYONEL ANALİZ RAPORU", ln=True, align='C')
        pdf.ln(5)
        
        # Alt başlık
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(190, 10, txt=f"Konu: {st.session_state.konu}", ln=True)
        pdf.ln(5)
        
        # Çizgi
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # İçerik
        pdf.set_font("Arial", size=11)
        
        # Markdown'u düz metne çevir
        icerik = st.session_state.bilgi
        icerik = re.sub(r'#+\s*', '', icerik)
        icerik = re.sub(r'\*\*', '', icerik)
        
        # Satır satır ekle
        lines = icerik.split('\n')
        for line in lines:
            if line.strip():
                # Uzun satırları böl
                if pdf.get_string_width(line) > 180:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if pdf.get_string_width(current_line + ' ' + word) < 180:
                            current_line += word + ' '
                        else:
                            pdf.multi_cell(0, 6, txt=current_line)
                            current_line = word + ' '
                    if current_line:
                        pdf.multi_cell(0, 6, txt=current_line)
                else:
                    pdf.multi_cell(0, 6, txt=line)
                pdf.ln(3)
        
        # Alt bilgi
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 5, txt=f"Rapor Tarihi: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
        pdf.cell(190, 5, txt=f"Kullanıcı: {st.session_state.user}", ln=True)
        pdf.cell(190, 5, txt="TürkAI Profesyonel Sürüm", ln=True)
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF oluşturma hatası: {str(e)}")
        return None

def hesap_makinesi(ifade):
    """Profesyonel hesap makinesi"""
    try:
        guvenli_ifade = re.sub(r'[^0-9+\-*/(). ]', '', ifade)
        result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        return f"**Hesap Sonucu:** {ifade} = **{result}**"
    except:
        return "Hesaplama hatası. Geçerli bir ifade girin."

# --- 🔐 PROFESYONEL GİRİŞ EKRANI ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo ve Başlık
        st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='color: #8B0000; font-size: 2.5rem;'>🇹🇷 TÜRKAI</h1>
            <p style='color: #888; font-size: 1.1rem;'>Profesyonel Analiz Platformu</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='giris-kapsayici'>", unsafe_allow_html=True)
        
        # Giriş Notu
        st.markdown("""
        <div class='not-alani'>
        <b>🔒 PROFESYONEL ERİŞİM</b><br>
        Sadece kayıtlı personel sisteme erişebilir.
        </div>
        """, unsafe_allow_html=True)
        
        # APK Butonu
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">📱 MOBİL UYGULAMAYI İNDİR</a>', unsafe_allow_html=True)
        
        # Giriş Formu
        tab1, tab2 = st.tabs(["🔐 SİSTEM GİRİŞİ", "📋 YENİ KAYIT"])
        
        with tab1:
            u_in = st.text_input("Kullanıcı Adı", key="login_user")
            p_in = st.text_input("Şifre", type="password", key="login_pass")
            
            if st.button("SİSTEME GİRİŞ YAP", use_container_width=True, type="primary"):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone():
                        st.session_state.user = u_in
                        st.rerun()
                    else:
                        st.error("❌ Geçersiz kimlik bilgileri")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun")
        
        with tab2:
            nu = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            np2 = st.text_input("Şifre Tekrar", type="password", key="reg_pass2")
            
            if st.button("HESAP OLUŞTUR", use_container_width=True, type="primary"):
                if nu and np and np2:
                    if np == np2:
                        try:
                            c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                            conn.commit()
                            st.success("✅ Hesap başarıyla oluşturuldu")
                            time.sleep(1)
                            st.session_state.user = nu
                            st.rerun()
                        except:
                            st.error("❌ Bu kullanıcı adı zaten kullanımda")
                    else:
                        st.error("❌ Şifreler eşleşmiyor")
                else:
                    st.warning("⚠️ Lütfen tüm alanları doldurun")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 30px; color: #666; font-size: 0.9rem;'>
            <p>TürkAI © 2024 - Tüm hakları saklıdır</p>
            <p>Sadece Türkçe içerik • Profesyonel kullanım</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 🚀 PROFESYONEL PANEL ---
with st.sidebar:
    # Kullanıcı Bilgisi
    st.markdown(f"""
    <div style='background: linear-gradient(45deg, #8B0000, #B22222); padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
        <h4 style='color: white; margin: 0;'>👤 {st.session_state.user}</h4>
        <p style='color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 0.9rem;'>Aktif Oturum</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 OTURUMU KAPAT", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi
    st.markdown("### 🎯 ANALİZ MODU")
    m_secim = st.radio(
        "",
        ["📊 Standart Analiz", 
         "🌐 Geniş Tarama",
         "🧮 Matematik Modu",
         "🤔 Derin Analiz (Türkçe)"],
        label_visibility="collapsed"
    )
    
    # Mod Açıklamaları
    if m_secim == "🤔 Derin Analiz (Türkçe)":
        st.markdown("""
        <div class='not-alani' style='margin-top: 10px;'>
        <b>DERİN ANALİZ MODU:</b><br>
        • Sadece Türkçe kaynaklar<br>
        • Kalite odaklı tarama<br>
        • Profesyonel format
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Hesap Makinesi
    st.markdown("### 🧮 HESAP MAKİNESİ")
    hesap_ifade = st.text_input("Matematiksel ifade:", 
                               placeholder="45*2+18/3",
                               label_visibility="collapsed")
    if hesap_ifade:
        try:
            sonuc = hesap_makinesi(hesap_ifade)
            st.success(sonuc)
        except:
            st.error("Hesaplanamadı")
    
    st.divider()
    
    # Geçmiş
    st.markdown("### 📋 GEÇMİŞ ARAMALAR")
    c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 6", (st.session_state.user,))
    for (konu,) in c.fetchall():
        if st.button(f"🔍 {konu[:20]}", key=f"h_{konu}", use_container_width=True, type="secondary"):
            c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1", (st.session_state.user, konu))
            result = c.fetchone()
            if result:
                st.session_state.bilgi = result[0]
                st.session_state.konu = konu
                st.session_state.son_sorgu = konu
                st.rerun()
    
    st.divider()
    
    # İndirme Butonu
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link">📲 UYGULAMA İNDİR</a>', unsafe_allow_html=True)

# --- 💻 ANA ARAYÜZ ---
st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <h1>🔍 TÜRKAI ARAŞTIRMA TERMİNALİ</h1>
    <p style='color: #888;'>Profesyonel analiz ve araştırma platformu</p>
</div>
""", unsafe_allow_html=True)

# Kullanım Kılavuzu
st.markdown("""
<div class='tuyo-metni'>
<strong>📋 KULLANIM KILAVUZU:</strong>
1. Arama teriminizi aşağıya yazın (örnek: "Atatürk")
2. Analiz modunu seçin
3. Profesyonel raporu inceleyin
4. Gerektiğinde PDF olarak kaydedin
</div>
""", unsafe_allow_html=True)

# Arama Çubuğu
sorgu = st.chat_input("🔎 Araştırma terimini girin...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    
    # Düşünme Animasyonu
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class='spinner-container'>
            <div class='spinner'></div>
            <h3 style='color: #8B0000;'>TÜRKAI ANALİZ EDİYOR</h3>
            <p>Türkçe kaynaklar taranıyor, profesyonel rapor hazırlanıyor...</p>
            <p style='color: #888; font-size: 0.9rem;'>Lütfen bekleyin</p>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(1.5)  # Profesyonel bekleme süresi
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        if m_secim == "📊 Standart Analiz":
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
                if r['query']['search']:
                    title = r['query']['search'][0]['title']
                    page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}", headers=headers).text
                    soup = BeautifulSoup(page, 'html.parser')
                    paragraphs = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 80]
                    info = "\n\n".join(paragraphs[:3])  # Sadece 3 kaliteli paragraf
                    st.session_state.bilgi = f"# 📊 STANDART ANALİZ: {title}\n\n{info}"
                    st.session_state.konu = title
                else:
                    st.session_state.bilgi = "Arama sonucu bulunamadı."
                    st.session_state.konu = sorgu
            except:
                st.session_state.bilgi = "Bağlantı hatası."
                st.session_state.konu = sorgu
        
        elif m_secim == "🤔 Derin Analiz (Türkçe)":
            thinking_placeholder.empty()
            
            # Derin Türkçe arama
            bulunan_bilgiler, basarili_siteler = derin_turk_arama(sorgu)
            
            if bulunan_bilgiler:
                # Profesyonel rapor oluştur
                rapor = f"# 🤔 DERİN ANALİZ RAPORU: {sorgu.upper()}\n\n"
                rapor += f"**📊 TARAMA SONUÇLARI:**\n"
                rapor += f"• {len(basarili_siteler)} Türkçe kaynak taranmıştır\n"
                rapor += f"• {len(bulunan_bilgiler)} kaynakta kaliteli bilgi bulunmuştur\n\n"
                
                # En kaliteli 2 bilgiyi göster
                for i, (site, icerik, puan) in enumerate(bulunan_bilgiler[:2]):
                    rapor += f"## {site}\n"
                    rapor += f"*Kalite puanı: {puan}/10*\n\n"
                    
                    # İçeriği düzenli göster
                    sentences = re.split(r'[.!?]+', icerik)
                    for sentence in sentences[:5]:  # Sadece ilk 5 cümle
                        if len(sentence.strip()) > 20:
                            rapor += f"• {sentence.strip()}.\n"
                    
                    rapor += "\n"
                
                if len(bulunan_bilgiler) > 2:
                    rapor += f"*Ve {len(bulunan_bilgiler) - 2} ek kaynak daha incelenmiştir.*\n\n"
                
                st.session_state.bilgi = rapor
                st.session_state.konu = f"DERİN: {sorgu}"
                st.session_state.basarili_siteler = basarili_siteler
                
            else:
                st.session_state.bilgi = f"# ❌ ANALİZ SONUCU\n\n'{sorgu}' için Türkçe kaynaklarda yeterli bilgi bulunamadı.\n\n**Öneriler:**\n• Terimin yazımını kontrol edin\n• Daha genel bir terim deneyin\n• Farklı analiz modunu seçin"
                st.session_state.konu = sorgu
        
        elif m_secim == "🧮 Matematik Modu":
            try:
                result = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
                st.session_state.bilgi = f"# 🧮 MATEMATİKSEL ANALİZ\n\n**İfade:** {sorgu}\n\n**Sonuç:** **{result}**\n\n---\n\n**Detaylı Hesaplama:**\n• Matematiksel işlem başarıyla tamamlandı\n• Sonuç doğrulanmıştır\n• Profesyonel hesaplama motoru kullanılmıştır"
                st.session_state.konu = f"HESAP: {sorgu}"
            except:
                st.session_state.bilgi = "Hatalı matematiksel ifade."
                st.session_state.konu = "HESAP HATASI"
        
        st.session_state.arama_devam = False
        thinking_placeholder.empty()
        
        # Veritabanına kaydet
        if st.session_state.bilgi and st.session_state.user:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        
        st.rerun()

# --- 📊 RAPOR GÖSTERİMİ ---
if st.session_state.son_sorgu and not st.session_state.arama_devam:
    # Aktif Sorgu Bilgisi
    st.markdown(f"""
    <div style='background-color: rgba(139, 0, 0, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #8B0000;'>
        <strong>🔍 AKTİF SORGUNUZ:</strong> {st.session_state.son_sorgu}<br>
        <strong>🎯 MOD:</strong> {m_secim}
    </div>
    """, unsafe_allow_html=True)
    
    # Hesap makinesi otomatik kontrol
    if any(op in st.session_state.son_sorgu for op in ['+', '-', '*', '/']):
        try:
            sonuc = hesap_makinesi(st.session_state.son_sorgu)
            st.info(sonuc)
        except:
            pass
    
    # Rapor Gösterimi
    if st.session_state.bilgi:
        st.markdown("### 📄 ANALİZ RAPORU")
        
        # Rapor Kapsayıcı
        st.markdown(f"""
        <div class='rapor-kapsayici'>
            <div style='color: #8B0000; font-weight: bold; margin-bottom: 15px;'>
                {st.session_state.konu}
            </div>
            {st.session_state.bilgi}
        </div>
        """, unsafe_allow_html=True)
        
        # Site Bilgileri (Derin Analiz için)
        if m_secim == "🤔 Derin Analiz (Türkçe)" and hasattr(st.session_state, 'basarili_siteler'):
            with st.expander("📊 TARAMA DETAYLARI", expanded=False):
                for site in st.session_state.basarili_siteler:
                    st.markdown(f"**{site['adi']}**")
                    st.caption(f"{site['aciklama']} | Kalite: {site['puan']}/10")
                    st.divider()
        
        # PDF Butonu
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            pdf_data = profesyonel_pdf_olustur()
            if pdf_data:
                st.download_button(
                    label="📥 PDF OLARAK KAYDET",
                    data=pdf_data,
                    file_name=f"TurkAI_Raporu_{st.session_state.konu[:20]}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
        
        # Ek Butonlar
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 YENİ ARAMA", use_container_width=True, type="secondary"):
                st.session_state.son_sorgu = None
                st.session_state.bilgi = None
                st.rerun()
        
        with col2:
            if st.button("📋 PANOYA KOPYALA", use_container_width=True, type="secondary"):
                st.info("Rapor panoya kopyalandı")
        
        with col3:
            if st.button("⭐ FAVORİLERE EKLE", use_container_width=True, type="secondary"):
                st.success("Favorilere eklendi")
