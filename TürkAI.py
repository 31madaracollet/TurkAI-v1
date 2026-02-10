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
    
    .site-bilgi {
        background-color: rgba(0, 100, 0, 0.05);
        border-left: 4px solid #006400;
        padding: 12px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
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

# --- 🔧 YARDIMCI FONKSİYONLAR ---
def yabanci_karakter_temizle(metin):
    """Latin ve Türkçe karakterler dışındaki alfabeleri temizler"""
    # Latin harfleri, Türkçe karakterler, sayılar ve standart sembolleri korur
    patern = r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s\.,;:!\?\(\)\-\*\+=/]'
    temiz_metin = re.sub(patern, '', metin)
    return temiz_metin

def pdf_olustur(baslik, icerik):
    """FPDF ile PDF raporu oluşturur"""
    pdf = FPDF()
    pdf.add_page()
    # Standart fontlar Türkçe karakter desteklemediği için karakterleri dönüştürürüz
    # Gerçek uygulamada .ttf font yüklenmesi önerilir
    def tr_fix(text):
        return text.replace('ı','i').replace('İ','I').replace('ü','u').replace('Ü','U').replace('ö','o').replace('Ö','O').replace('ç','c').replace('Ç','C').replace('ş','s').replace('Ş','S').replace('ğ','g').replace('Ğ','G')

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, tr_fix(f"TurkAI Analiz Raporu"), ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, tr_fix(f"Konu: {baslik}"), ln=True)
    pdf.cell(0, 10, tr_fix(f"Tarih: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, tr_fix(icerik))
    return pdf.output(dest='S').encode('latin-1')

def site_tara(url, sorgu, site_adi, timeout=10):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        icerik = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 80 and sorgu.lower() in text.lower():
                icerik += text + "\n\n"
        if len(icerik) < 100:
            all_text = soup.get_text()
            lines = all_text.split('\n')
            for line in lines:
                clean_line = line.strip()
                if len(clean_line) > 60 and sorgu.lower() in clean_line.lower():
                    icerik += clean_line + "\n\n"
        icerik = re.sub(r'\s+', ' ', icerik).strip()
        if len(icerik) > 50:
            return (site_adi, yabanci_karakter_temizle(icerik[:2000]))
        return (site_adi, None)
    except: return (site_adi, None)

def derin_arama_yap(sorgu):
    site_listesi = [
        {'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}', 'adi': 'Wikipedia (TR)', 'oncelik': 10},
        {'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}', 'adi': 'Biyografi.info', 'oncelik': 9},
        {'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}', 'adi': 'Etimoloji TR', 'oncelik': 8},
        {'url': f'https://www.google.com/search?q={urllib.parse.quote(sorgu)}+ansiklopedi', 'adi': 'Google Ansiklopedik', 'oncelik': 7}
    ]
    site_listesi.sort(key=lambda x: x['oncelik'], reverse=True)
    tum_bilgiler = []
    
    p_bar = st.progress(0)
    for i, site in enumerate(site_listesi):
        p_bar.progress((i + 1) / len(site_listesi))
        res = site_tara(site['url'], sorgu, site['adi'])
        if res[1]: tum_bilgiler.append(res)
    p_bar.empty()
    return tum_bilgiler

def hesap_makinesi(ifade):
    try:
        guvenli_ifade = re.sub(r'[^0-9+\-*/(). ]', '', ifade)
        result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        return f"**Sonuç:** {ifade} = **{result}**"
    except: return "Hesaplama hatası."

# --- 🔐 KİMLİK DOĞRULAMA EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        st.markdown("<div class='not-alani'>Derin Düşünen motoru ile hızlı ve kaliteli arama</div>", unsafe_allow_html=True)
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TürkAI Mobil Uygulamasını Yükle</a>', unsafe_allow_html=True)
        
        tab_login, tab_register, tab_guest = st.tabs(["🔒 Giriş", "📝 Kayıt", "👤 Misafir"])
        
        with tab_login:
            u_in = st.text_input("Kullanıcı")
            p_in = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): st.session_state.user = u_in; st.rerun()
                else: st.error("Hatalı!")

        with tab_guest:
            st.warning("Misafir girişi ile yapılan aramalar veritabanına kaydedilmez.")
            if st.button("Misafir Olarak Devam Et", use_container_width=True):
                st.session_state.user = "Misafir_User"
                st.rerun()

        with tab_register:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Başarılı!")
                except: st.error("Mevcut.")
    st.stop()

# --- 🚀 OPERASYONEL PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Metodoloji:", ["V1 (Ansiklopedik)", "V2 (Global)", "V3 (Matematik)", "🤔 Derin Düşünen"])
    
    st.divider()
    st.markdown("##### 🧮 Hızlı Hesap")
    hesap_ifade = st.text_input("İşlem:", key="hesap_m", placeholder="45*2")
    if hesap_ifade: st.success(hesap_makinesi(hesap_ifade))
    
    st.divider()
    st.markdown("##### 📜 Geçmiş")
    if st.session_state.user != "Misafir_User":
        c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,))
        for k, i in c.fetchall():
            if st.button(f"📄 {k[:20]}", key=f"h_{time.time()}_{k}"):
                st.session_state.bilgi, st.session_state.konu = i, k; st.rerun()

# --- 💻 ARAŞTIRMA ALANI ---
st.title("Araştırma Terminali")
sorgu = st.chat_input("Veri girişi yapınız...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.kaynak_index = 0
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("<div class='spinner-container'><div class='spinner'></div><h3 style='color:#cc0000;'>TürkAI Analiz Ediyor...</h3></div>", unsafe_allow_html=True)
        
        if m_secim == "V3 (Matematik)":
            try:
                res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "))
                st.session_state.bilgi = f"**Matematik Analizi:** {sorgu} = {res}"
                st.session_state.konu = "MATEMATİK"
            except: st.session_state.bilgi = "Hata!"
        else:
            st.session_state.tum_kaynaklar = derin_arama_yap(sorgu)
            if st.session_state.tum_kaynaklar:
                site, icerik = st.session_state.tum_kaynaklar[0]
                st.session_state.bilgi = f"### 📚 Kaynak: {site}\n\n{icerik}"
                st.session_state.konu = sorgu.upper()
            else: st.session_state.bilgi = "Kaynak bulunamadı."
        
        thinking_placeholder.empty()
        if st.session_state.user != "Misafir_User":
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()

if st.session_state.bilgi:
    st.subheader(f"📊 Sonuç: {st.session_state.konu}")
    st.markdown(st.session_state.bilgi)
    
    col1, col2 = st.columns(2)
    with col1:
        # PDF BUTONU
        pdf_bytes = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
        st.download_button(label="📥 Analizi PDF Olarak İndir", data=pdf_bytes, file_name="TurkAI_Rapor.pdf", mime="application/pdf", use_container_width=True)
    
    with col2:
        # SONRAKİ KAYNAK BUTONU (Matematik hariç)
        if m_secim != "V3 (Matematik)" and len(st.session_state.tum_kaynaklar) > 1:
            if st.button("🔄 Sonraki Kaynağa Geç", use_container_width=True):
                st.session_state.kaynak_index = (st.session_state.kaynak_index + 1) % len(st.session_state.tum_kaynaklar)
                site, icerik = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
                st.session_state.bilgi = f"### 📚 Kaynak: {site}\n\n{icerik}"
                st.rerun()

st.markdown("<div class='footer'><p>&copy; 2026 TürkAI | Kurumsal Analiz</p></div>", unsafe_allow_html=True)
