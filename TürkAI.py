import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re 
from fpdf import FPDF 

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
# Not: Sistem modu için Streamlit ayarlarında 'theme' kısmının 'system' olması yeterlidir.
st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 DİNAMİK TEMA VE CİDDİ TASARIM ---
st.markdown("""
    <style>
    /* Dinamik Metin Renkleri - Sistem moduna göre uyum sağlar */
    :root {
        --primary-red: #cc0000;
    }
    
    h1, h2, h3 { 
        color: var(--primary-red) !important; 
        font-weight: 700 !important;
        letter-spacing: -1px;
    }

    /* Giriş Ekranı Konteyneri */
    .giris-kapsayici {
        border: 1px solid rgba(204, 0, 0, 0.3);
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        background-color: transparent;
        backdrop-filter: blur(5px);
    }

    /* Profesyonel Buton Tasarımı */
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
        margin-bottom: 30px;
        transition: all 0.3s ease;
    }
    .apk-buton-link:hover {
        opacity: 0.9;
        box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.2);
    }

    /* Rapor Alanı */
    .ai-rapor-alani {
        border-left: 4px solid var(--primary-red);
        padding: 25px;
        background-color: rgba(128, 128, 128, 0.05);
        border-radius: 4px;
        line-height: 1.6;
        margin-top: 20px;
    }

    /* Yan Panel */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    .stTextInput > div > div > input {
        border-radius: 6px !important;
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

# --- 🔐 KİMLİK DOĞRULAMA EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1><p style='font-size: 0.9rem; opacity: 0.7;'>Geleceğin Veri Analiz Platformu</p></div>", unsafe_allow_html=True)
        
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TÜRKAI MOBİL UYGULAMASINI İNDİR (APK)</a>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Sistem Girişi", "📝 Yeni Kayıt"])
        
        with tab_login:
            u_in = st.text_input("Kullanıcı Kimliği", placeholder="Kullanıcı adınızı giriniz")
            p_in = st.text_input("Erişim Şifresi", type="password", placeholder="••••••••")
            if st.button("Sisteme Eriş", use_container_width=True):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in
                    st.rerun()
                else:
                    st.error("Kimlik doğrulama başarısız. Bilgilerinizi kontrol ediniz.")
        
        with tab_register:
            nu = st.text_input("Belirlenecek Kullanıcı Adı")
            np = st.text_input("Belirlenecek Şifre", type="password")
            if st.button("Kaydı Tamamla", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kayıt işlemi başarılı. Giriş sekmesini kullanabilirsiniz.")
                except:
                    st.error("Bu kullanıcı adı sistemde zaten kayıtlı.")
    st.stop()

# --- 🚀 OPERASYONEL PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    
    m_secim = st.radio("Analiz Metodolojisi:", ["V1 (Ansiklopedik)", "V2 (Global Kaynaklar)", "V3 (Hesaplama Birimi)"])
    st.divider()
    
    st.markdown("##### 📜 Geçmiş Kayıtlar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📄 {k[:22]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()
    
    st.divider()
    st.markdown(f'<a href="{APK_URL}" style="text-decoration:none; color:inherit; font-size:12px; opacity:0.6;">📥 Mobil Sürüm v1.0</a>', unsafe_allow_html=True)

# --- 💻 ARAŞTIRMA VE VERİ GİRİŞİ ---
st.title("Araştırma ve Analiz Terminali")
sorgu = st.chat_input("Analiz edilecek anahtar kelime veya veri girişi yapınız...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    if m_secim == "V1 (Ansiklopedik)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
            title = r['query']['search'][0]['title']
            page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}", headers=headers).text
            soup = BeautifulSoup(page, 'html.parser')
            info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
            st.session_state.bilgi, st.session_state.konu = info, title
        except: st.session_state.bilgi = "Sistem belirtilen anahtar kelimeye dair veri bulamadı."
    
    elif m_secim == "V2 (Global Kaynaklar)":
        try:
            wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
            res = requests.get(wiki_api, headers=headers).json()
            st.session_state.bilgi, st.session_state.konu = res.get('extract', "Veri çekme hatası."), sorgu.upper()
        except: st.session_state.bilgi = "Global sunucularla bağlantı kurulamadı."
    
    elif m_secim == "V3 (Hesaplama Birimi)":
        try:
            result = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"İşlem Sonucu: {result}", "MATEMATİKSEL ANALİZ"
        except: st.session_state.bilgi = "Geçersiz matematiksel ifade."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit()
        st.rerun()

# --- 📊 VERİ ÇIKTISI VE RAPORLAMA ---
if st.session_state.son_sorgu:
    st.info(f"**Sorgulanan Veri:** {st.session_state.son_sorgu}")

if st.session_state.bilgi:
    st.subheader(f"Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    def rapor_pdf_olustur():
        try:
            pdf = FPDF()
            pdf.add_page()
            def tr_fix(t):
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): t = t.replace(k,v)
                return re.sub(r'[^\x00-\x7F]+', ' ', t)
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="TURKAI RESMI RAPORU", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            content = f"\nKonu: {tr_fix(st.session_state.konu)}\n\nAnaliz Sonucu:\n{tr_fix(st.session_state.bilgi)}\n\nOlusturan: {tr_fix(st.session_state.user)}"
            pdf.multi_cell(0, 10, txt=content)
            return pdf.output(dest='S').encode('latin-1', 'replace')
        except: return None

    pdf_v = rapor_pdf_olustur()
    if pdf_v:
        st.download_button(label="📊 Raporu PDF Olarak Arşivle", data=pdf_v, file_name=f"TurkAI_Rapor_{st.session_state.konu}.pdf", mime="application/pdf")
