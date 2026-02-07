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
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        
        # Giriş Notu
        st.markdown("<div class='not-alani'>Şuan betada olduğu için, çalışmalar sürdürülüyor.</div>", unsafe_allow_html=True)
        
        # Giriş APK Butonu
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TürkAI Mobil Uygulamasını Yükle</a>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Sistem Girişi", "📝 Yeni Kayıt"])
        
        with tab_login:
            u_in = st.text_input("Kullanıcı Kimliği")
            p_in = st.text_input("Erişim Şifresi", type="password")
            if st.button("Sisteme Eriş", use_container_width=True):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in
                    st.rerun()
                else:
                    st.error("Giriş bilgileri hatalı.")
        
        with tab_register:
            nu = st.text_input("Yeni Kullanıcı Adı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydı Tamamla", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kayıt başarılı. Giriş yapabilirsiniz.")
                except:
                    st.error("Bu isim sistemde mevcut.")
    st.stop()

# --- 🚀 OPERASYONEL PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    
    m_secim = st.radio("Analiz Metodolojisi:", ["V1 (Ansiklopedik)", "V2 (Global Kaynaklar)", "V3 (Matematik Birimi)"])
    
    # Matematik Modu Notu
    if m_secim == "V3 (Matematik Birimi)":
        st.info("⚠️ Not: Çarpı (x) yerine yıldız (*) kullanınız.")
        
    st.divider()
    st.markdown("##### 📜 Geçmiş Kayıtlar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📄 {k[:22]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()
    
    # Sidebar İndirme Butonu
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link">📥 Uygulamayı İndir</a>', unsafe_allow_html=True)

# --- 💻 ARAŞTIRMA ALANI ---
st.title("Araştırma Terminali")
st.markdown("<div class='tuyo-metni'>💡 <b>Kullanım Yönergesi:</b> Araştırmak istediğiniz şeyin anahtar kelimesini yazınız (Örn: Türk kimdir? ❌ <b>Türk</b> ✅)</div>", unsafe_allow_html=True)

sorgu = st.chat_input("Veri girişi yapınız...")

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
        except: st.session_state.bilgi = "Sorgu sonucu bulunamadı."
    
    elif m_secim == "V2 (Global Kaynaklar)":
        try:
            wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
            res = requests.get(wiki_api, headers=headers).json()
            st.session_state.bilgi, st.session_state.konu = res.get('extract', "Veri çekilemedi."), sorgu.upper()
        except: st.session_state.bilgi = "Sunucu bağlantı hatası."
    
    elif m_secim == "V3 (Matematik Birimi)":
        try:
            result = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
            st.session_state.bilgi, st.session_state.konu = f"İşlem Sonucu: {result}", "MATEMATİKSEL ANALİZ"
        except: st.session_state.bilgi = "Hatalı matematiksel ifade."

    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
        conn.commit()
        st.rerun()

# --- 📊 RAPORLAMA ---
if st.session_state.son_sorgu:
    st.info(f"**Aktif Sorgu:** {st.session_state.son_sorgu}")

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
            pdf.cell(190, 10, txt="TURKAI RESMI ANALIZ RAPORU", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            content = f"\nKonu: {tr_fix(st.session_state.konu)}\n\nAnaliz Sonucu:\n{tr_fix(st.session_state.bilgi)}\n\nYetkili: {tr_fix(st.session_state.user)}"
            pdf.multi_cell(0, 10, txt=content)
            return pdf.output(dest='S').encode('latin-1', 'replace')
        except: return None

    pdf_v = rapor_pdf_olustur()
    if pdf_v:
        st.download_button(label="📊 Raporu Arşivle (PDF)", data=pdf_v, file_name=f"TurkAI_Rapor_{st.session_state.konu}.pdf", mime="application/pdf")
