import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI MOTORU ---
def db_baslat():
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def kullanici_kontrol(user, pwd):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, sifre_hashle(pwd)))
    data = c.fetchone()
    conn.close()
    return data

def yeni_kayit(user, pwd):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?)", (user, sifre_hashle(pwd)))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def analiz_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def gecmis_getir(user):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

db_baslat()

# --- 🛡️ GELİŞMİŞ ARGO FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "serefsiz", "orospu"]

def guvenli_mi(metin):
    temiz = metin.lower().replace('ı','i').replace('ş','s').replace('ç','c').replace('ğ','g').replace('ü','u').replace('ö','o')
    temiz = re.sub(r'[^a-z]', '', temiz) 
    for kelime in KARA_LISTE:
        if kelime in temiz:
            return False
    return True

# --- 🎨 AYDINLIK VE PROFESYONEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F2937; }
    .main .block-container { max-width: 850px; padding-bottom: 10rem; }
    .sonuc-karti {
        background-color: #F9FAFB;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        line-height: 1.8;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: #111827;
    }
    h1 { color: #DC2626; text-align: center; font-weight: 800; }
    .stSidebar { background-color: #F3F4F6 !important; border-right: 1px solid #E5E7EB; }
    </style>
""", unsafe_allow_html=True)

# --- 🧠 SESSION STATE ---
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🚪 GİRİŞ SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1>TürkAI Giriş Portalı</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
        with t1:
            u = st.text_input("Kullanıcı Adı", key="login_user")
            p = st.text_input("Şifre", type="password", key="login_pass")
            if st.button("Sisteme Eriş", use_container_width=True):
                if kullanici_kontrol(u, p):
                    st.session_state.giris_yapildi = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Kullanıcı adı veya şifre hatalı.")
        with t2:
            nu = st.text_input("Yeni Kullanıcı", key="reg_user")
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            if st.button("Hesabı Oluştur", use_container_width=True):
                if len(nu) > 2 and len(np) > 3:
                    if yeni_kayit(nu, np): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                    else: st.error("Bu kullanıcı adı zaten alınmış.")
                else: st.warning("Bilgiler çok kısa.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    st.markdown("📂 **Senin Arşivin**")
    
    # --- HATAYI DÜZELTEN KISIM BURASI ---
    arsiv = gecmis_getir(st.session_state.user)
    for idx, (konu_adi, icerik_metni) in enumerate(arsiv):
        # Her butona benzersiz bir 'key' (anahtar) veriyoruz
        if st.button(f"🔍 {konu_adi}", use_container_width=True, key=f"hist_{idx}_{konu_adi}"):
            st.session_state.su_anki_konu = konu_adi
            st.session_state.analiz_sonucu = icerik_metni
            st.rerun()

    st.divider()
    if st.button("Güvenli Çıkış", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

st.title("TürkAI Bilgi Merkezi")

# --- ANALİZ SONUCU GÖSTERİMİ ---
if st.session_state.analiz_sonucu:
    st.markdown(f"""
    <div class="sonuc-karti">
        <h3 style="color: #DC2626; margin-top:0;">📌 Analiz: {st.session_state.su_anki_konu}</h3>
        {st.session_state.analiz_sonucu.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
    safe_text = st.session_state.analiz_sonucu.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    st.download_button("📄 PDF Olarak İndir", pdf.output(dest='S').encode('latin-1'), f"{st.session_state.su_anki_konu}.pdf", "application/pdf")
else:
    st.markdown("<p style='text-align: center; opacity: 0.6;'>Hoş geldin. Bir konu yazarak profesyonel araştırmayı başlatabilirsin.</p>", unsafe_allow_html=True)

# --- 📥 SORGULAMA BARI ---
sorgu = st.chat_input("Araştırmak istediğiniz konuyu yazın...")

if sorgu:
    if not guvenli_mi(sorgu):
        st.warning("⚠️ Lütfen profesyonel bir dil kullanın.")
    else:
        with st.spinner("Analiz ediliyor..."):
            url = f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                metinler = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if metinler:
                    ozet = "\n\n".join(metinler[:7])
                    analiz_kaydet(st.session_state.user, sorgu, ozet)
                    st.session_state.analiz_sonucu = ozet
                    st.session_state.su_anki_konu = sorgu
                    st.rerun()
                else: st.warning("İçerik bulunamadı.")
            else: st.error("Konu başlığı mevcut değil.")
     
           

