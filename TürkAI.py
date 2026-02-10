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
st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 DİNAMİK TEMA VE KURUMSAL TASARIM ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    
    h1, h2, h3 { 
        color: var(--primary-red) !important; 
        font-weight: 700 !important;
    }

    .giris-kapsayici {
        border: 1px solid rgba(204, 0, 0, 0.3);
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        background-color: transparent;
    }

    .apk-buton-link {
        display: block;
        width: 100%;
        background-color: var(--primary-red);
        color: white !important;
        text-align: center;
        padding: 14px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 20px;
        transition: 0.3s;
    }

    .sidebar-indir-link {
        display: block;
        background-color: transparent;
        color: inherit !important;
        text-align: center;
        padding: 8px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid var(--primary-red);
        font-size: 13px;
        margin-top: 10px;
    }

    .not-alani {
        background-color: rgba(204, 0, 0, 0.05);
        color: var(--primary-red);
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed var(--primary-red);
        margin-bottom: 20px;
        font-size: 0.85rem;
        text-align: center;
    }

    .tuyo-metni {
        font-size: 0.9rem;
        opacity: 0.8;
        margin-bottom: 20px;
        padding: 10px;
        border-left: 3px solid var(--primary-red);
    }
    
    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        margin: 20px 0;
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(204, 0, 0, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .motor-badge {
        background-color: var(--primary-red);
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI YÖNETİMİ ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
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
if "kaynak_index" not in st.session_state: st.session_state.kaynak_index = 0
if "tum_kaynaklar" not in st.session_state: st.session_state.tum_kaynaklar = []

# --- 🔧 YARDIMCI FONKSİYONLAR (DÜZELTİLDİ) ---
def yabanci_karakter_temizle(metin):
    if not metin: return ""
    patern = r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s\.,;:!\?\(\)\-\*\+=/]'
    return re.sub(patern, '', metin)

def pdf_olustur(baslik, icerik):
    """Unicode hatasını çözen güvenli PDF fonksiyonu"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        def tr_fix(text):
            if not text: return ""
            chars = {'ı':'i','İ':'I','ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C','ş':'s','Ş':'S','ğ':'g','Ğ':'G'}
            for k, v in chars.items(): text = text.replace(k, v)
            # Latin-1'de olmayan tüm karakterleri tamamen siler (Hata almanı engeller)
            return text.encode('latin-1', 'ignore').decode('latin-1')

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, tr_fix("TurkAI Analiz Raporu"), ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, tr_fix(f"Konu: {baslik}"), ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, tr_fix(icerik))
        # Çıktı alırken latin-1 encode hatasını 'ignore' ile geçiyoruz
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except:
        return None

def site_tara(url, sorgu, site_adi):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.content, 'html.parser')
        icerik = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 80 and sorgu.lower() in text.lower():
                icerik += text + "\n\n"
        if len(icerik) > 50:
            return (site_adi, yabanci_karakter_temizle(icerik[:2000]))
        return (site_adi, None)
    except: return (site_adi, None)

def derin_arama_yap(sorgu):
    site_listesi = [
        {'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}', 'adi': 'Wikipedia (TR)'},
        {'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}', 'adi': 'Biyografi.info'},
        {'url': f'https://www.google.com/search?q={urllib.parse.quote(sorgu)}+nedir', 'adi': 'Genel Kaynaklar'}
    ]
    tum_bilgiler = []
    for site in site_listesi:
        res = site_tara(site['url'], sorgu, site['adi'])
        if res[1]: tum_bilgiler.append(res)
    return tum_bilgiler

def hesap_makinesi(ifade):
    try:
        guvenli = re.sub(r'[^0-9+\-*/(). ]', '', ifade)
        return f"**Sonuç:** {eval(guvenli, {'__builtins__': {}}, {})}"
    except: return "Hesaplama hatası."

# --- 🔐 KİMLİK DOĞRULAMA ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🔒 Giriş", "📝 Kayıt", "👤 Misafir"])
        with tab1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir", use_container_width=True):
                h = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Hatalı!")
        with tab3:
            if st.button("Misafir Girişi", use_container_width=True):
                st.session_state.user = "Misafir_User"; st.rerun()
        with tab2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Tamam!")
                except: st.error("Mevcut!")
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TürkAI Mobil Uygulamasını İndir</a>', unsafe_allow_html=True)
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    if st.button("Oturumu Kapat"): st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Metodoloji:", ["V1 (Ansiklopedik)", "V2 (Global)", "V3 (Matematik)", "🤔 Derin Düşünen"])
    st.divider()
    st.markdown("##### 🧮 Hızlı Hesap")
    hesap = st.text_input("İşlem:")
    if hesap: st.success(hesap_makinesi(hesap))

st.title("Araştırma Terminali")
sorgu = st.chat_input("Veri girişi yapınız...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.kaynak_index = 0
    if m_secim == "V3 (Matematik)":
        st.session_state.bilgi = hesap_makinesi(sorgu)
        st.session_state.konu = "MATEMATİK"
    else:
        with st.spinner("Analiz ediliyor..."):
            st.session_state.tum_kaynaklar = derin_arama_yap(sorgu)
            if st.session_state.tum_kaynaklar:
                site, icerik = st.session_state.tum_kaynaklar[0]
                st.session_state.bilgi = f"### 📚 Kaynak: {site}\n\n{icerik}"
                st.session_state.konu = sorgu.upper()
            else: st.session_state.bilgi = "Sonuç bulunamadı."
    st.rerun()

if st.session_state.bilgi:
    st.subheader(f"📊 Sonuç: {st.session_state.konu}")
    st.markdown(st.session_state.bilgi)
    
    c1, c2 = st.columns(2)
    with c1:
        pdf_data = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
        if pdf_data:
            st.download_button("📥 Analizi PDF İndir", pdf_data, "TurkAI_Rapor.pdf", "application/pdf", use_container_width=True)
    with c2:
        if m_secim != "V3 (Matematik)" and len(st.session_state.tum_kaynaklar) > 1:
            if st.button("🔄 Sonraki Kaynağa Geç", use_container_width=True):
                st.session_state.kaynak_index = (st.session_state.kaynak_index + 1) % len(st.session_state.tum_kaynaklar)
                site, icerik = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
                st.session_state.bilgi = f"### 📚 Kaynak: {site}\n\n{icerik}"
                st.rerun()

st.markdown("<div style='text-align:center; margin-top:50px; opacity:0.5;'>&copy; 2026 TürkAI</div>", unsafe_allow_html=True)
