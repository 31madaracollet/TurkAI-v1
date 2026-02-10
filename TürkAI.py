import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
import urllib.parse
import re 
from fpdf import FPDF 
import time

# --- ⚙️ AYARLAR ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz", page_icon="🇹🇷", layout="wide")
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 TEMA VE DİNAMİK RENKLER (KARANLIK/AYDINLIK MOD) ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    
    /* Dinamik Metin Renkleri */
    .stApp {
        color: inherit;
    }
    
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #800000, #cc0000); }
    
    .giris-kapsayici { 
        border: 1px solid rgba(204, 0, 0, 0.3); 
        border-radius: 12px; 
        padding: 30px; 
        background: rgba(128, 128, 128, 0.05); 
    }
    
    .apk-buton { 
        display: block; 
        background: var(--primary-red); 
        color: white !important; 
        text-align: center; 
        padding: 12px; 
        border-radius: 8px; 
        text-decoration: none; 
        font-weight: bold; 
        margin-top: 15px; 
    }
    
    .arastirma-notu {
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid var(--primary-red);
        background-color: rgba(204, 0, 0, 0.1);
        margin-top: 10px;
        font-size: 0.9rem;
    }
    
    /* Sonuç Kutusu İçin Adaptif Renk */
    .sonuc-metni {
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid rgba(128, 128, 128, 0.2);
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c
conn, c = db_baslat()

# --- 🔑 OTURUM ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "kaynak_index" not in st.session_state: st.session_state.kaynak_index = 0
if "tum_kaynaklar" not in st.session_state: st.session_state.tum_kaynaklar = []

# --- 🔧 FONKSİYONLAR (KORUNDU) ---
def yabanci_karakter_temizle(metin):
    return re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s\.,;:!\?\(\)\-\*\+=/]', '', metin)

def wikipedia_temizle(metin):
    metin = re.sub(r'\[\d+\]', '', metin)
    for s in ["İçeriğe atla", "Vikipedi, özgür ansiklopedi", "değiştir kaynağı değiştir"]:
        metin = metin.replace(s, "")
    return re.sub(r'\s+', ' ', metin).strip()

def tdk_temizle(metin):
    metin = re.sub(r'/[^ ]*', '', metin)
    return metin.replace("null", "").strip()

def pdf_olustur(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        def tr_fix(text):
            chars = {'ı':'i','İ':'I','ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C','ş':'s','Ş':'S','ğ':'g','Ğ':'G'}
            for k, v in chars.items(): text = text.replace(k, v)
            return text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, tr_fix(baslik), ln=True)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 5, tr_fix(icerik))
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

def akiskan_yazi(metin):
    placeholder = st.empty()
    full_text = ""
    for char in metin:
        full_text += char
        placeholder.markdown(f"<div class='sonuc-metni'>{full_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.001)
    placeholder.markdown(f"<div class='sonuc-metni'>{full_text}</div>", unsafe_allow_html=True)

def site_tara_brave_style(url, sorgu, site_adi):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Brave/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for j in soup(['script', 'style', 'nav', 'footer']): j.decompose()
        if "wikipedia" in url:
            content = soup.find(id="mw-content-text")
            final = wikipedia_temizle(content.get_text() if content else soup.get_text())
        else: final = soup.get_text(separator=' ')
        final = yabanci_karakter_temizle(' '.join(final.split()))
        if "sozluk.gov.tr" in url: final = tdk_temizle(final)
        return (site_adi, final) if len(final) > 50 else (site_adi, None)
    except: return (site_adi, None)

# --- 🔐 GİRİŞ & KAYIT ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h2 style='text-align:center;'>🇹🇷 TürkAI V1</h2>", unsafe_allow_html=True)
        tab_in, tab_up, tab_m = st.tabs(["🔑 Giriş", "📝 Kayıt Ol", "👤 Misafir"])
        with tab_in:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Bağlan", use_container_width=True):
                h = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Hatalı Bilgi!")
        with tab_up:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Hesap Oluştur", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kayıt Başarılı! Giriş Yapabilirsiniz.")
                except: st.error("Bu kullanıcı zaten var.")
        with tab_m:
            if st.button("Yetkisiz Giriş", use_container_width=True): st.session_state.user = "Misafir"; st.rerun()
        st.markdown(f'<a href="{APK_URL}" class="apk-buton">TürkAI Mobile APK İndir</a>', unsafe_allow_html=True)
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"**🛡️ Aktif Yetkili:** {st.session_state.user}")
    m_secim = st.radio("Sorgu Metodu:", ["V1 (Ansiklopedik)", "Sözlük (TDK)", "V3 (Matematik)", "🤔 Derin Düşünen"])
    st.divider()
    st.markdown("##### 🧮 Hızlı Hesap")
    calc = st.text_input("İşlem:")
    if calc:
        try: st.success(f"Sonuç: {eval(re.sub(r'[^0-9+\-*/(). ]', '', calc))}")
        except: st.error("Hata!")
    st.divider()
    if st.button("Oturumu Kapat"): st.session_state.clear(); st.rerun()

st.title("Araştırma Terminali")
# --- 📝 NOT EKLEMESİ ---
st.markdown("<div class='arastirma-notu'><b>Not:</b> Araştırmak istediğiniz konunun <b>ANAHTAR KELİMESİNİ</b> yazınız.</div>", unsafe_allow_html=True)

sorgu = st.chat_input("Analiz edilecek konuyu yazın...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.kaynak_index = 0
    q_enc = urllib.parse.quote(sorgu)
    
    with st.container():
        st.write("### 🔍 Analiz Süreci")
        p_bar = st.progress(0)
        status = st.empty()
        
        if m_secim == "🤔 Derin Düşünen":
            siteler = [f"https://tr.wikipedia.org/wiki/{q_enc}", f"https://www.bilgiustam.com/?s={q_enc}", f"https://www.turkcebilgi.com/{q_enc}", f"https://sozluk.gov.tr/gts?ara={q_enc}", f"https://www.nedir.com/{q_enc}", f"https://www.biyografi.info/ara?k={q_enc}", f"https://islamansiklopedisi.org.tr/ara?q={q_enc}", f"https://dergipark.org.tr/tr/search?q={q_enc}", f"https://en.wikipedia.org/wiki/{q_enc}", f"https://www.britannica.com/search?query={q_enc}", f"https://www.worldhistory.org/search/?q={q_enc}", f"https://plato.stanford.edu/search/searcher.py?query={q_enc}", f"https://www.biyografya.com/arama?q={q_enc}", f"https://tr.wiktionary.org/wiki/{q_enc}", f"https://www.etimolojiturkce.com/arama/{q_enc}"]
            bulunanlar = []
            for i, url in enumerate(siteler):
                status.info(f"Tarama yapılıyor: {urllib.parse.urlparse(url).netloc} ({i+1}/15)")
                p_bar.progress((i+1)/len(siteler))
                res = site_tara_brave_style(url, sorgu, f"Kaynak {i+1}")
                if res[1]: bulunanlar.append(res)
            st.session_state.tum_kaynaklar = bulunanlar
        elif m_secim == "Sözlük (TDK)":
            p_bar.progress(50); res = site_tara_brave_style(f"https://sozluk.gov.tr/gts?ara={q_enc}", sorgu, "TDK")
            st.session_state.tum_kaynaklar = [res] if res[1] else []
            p_bar.progress(100)
        else:
            p_bar.progress(50); res = site_tara_brave_style(f"https://tr.wikipedia.org/wiki/{q_enc}", sorgu, "V1")
            st.session_state.tum_kaynaklar = [res] if res[1] else []
            p_bar.progress(100)

        if st.session_state.tum_kaynaklar:
            st.session_state.bilgi = st.session_state.tum_kaynaklar[0][1]
            st.session_state.konu = sorgu.upper()
        else: st.session_state.bilgi = "Veri bulunamadı."
        status.empty(); p_bar.empty()
    st.rerun()

if st.session_state.bilgi:
    st.subheader(f"📊 Rapor: {st.session_state.konu}")
    active = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
    st.caption(f"📍 Kaynak: {active[0]}")
    
    st.markdown("<div style='border-left: 5px solid #cc0000; margin-bottom: 20px;'>", unsafe_allow_html=True)
    akiskan_yazi(st.session_state.bilgi)
    st.markdown("</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
        if pdf: st.download_button("📥 PDF Olarak Kaydet", pdf, "TurkAI_Rapor.pdf", use_container_width=True)
    with c2:
        if len(st.session_state.tum_kaynaklar) > 1:
            if st.button("🔄 Yeniden Yap (Sonraki Kaynak)", use_container_width=True):
                st.session_state.kaynak_index = (st.session_state.kaynak_index + 1) % len(st.session_state.tum_kaynaklar)
                st.session_state.bilgi = st.session_state.tum_kaynaklar[st.session_state.kaynak_index][1]
                st.rerun()
