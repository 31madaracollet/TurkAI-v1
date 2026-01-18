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

# --- 💾 VERİTABANI MOTORU (GELİŞMİŞ) ---
def db_baslat():
    conn = sqlite3.connect('turkai_data.db')
    c = conn.cursor()
    # Kullanıcılar Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Aramalar Tablosu (İçerik dahil edildi ki geri açılsın)
    c.execute('''CREATE TABLE IF NOT EXISTS aramalar
                 (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)''')
    conn.commit()
    conn.close()

def sifre_hashle(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def kullanici_olustur(user, pwd):
    conn = sqlite3.connect('turkai_data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?)", (user, sifre_hashle(pwd)))
        conn.commit()
        return True
    except:
        return False
    finally: conn.close()

def giris_kontrol(user, pwd):
    conn = sqlite3.connect('turkai_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, sifre_hashle(pwd)))
    data = c.fetchone()
    conn.close()
    return data

def analiz_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_data.db')
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def ozel_gecmis_getir(user):
    conn = sqlite3.connect('turkai_data.db')
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

db_baslat()

# --- 🧠 SESSION STATE ---
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🛡️ GÜVENLİK FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt"]
def guvenli_mi(metin):
    temiz = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    return not any(k in temiz for k in KARA_LISTE)

# --- 🎨 CSS (PROFESYONEL GEMINI STYLE) ---
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    .main .block-container { max-width: 850px; padding-bottom: 10rem; }
    .sonuc-karti {
        background-color: #1e1f20; padding: 25px; border-radius: 20px;
        border: 1px solid #333; line-height: 1.7; margin-bottom: 20px;
    }
    .stSidebar { background-color: #1e1f20 !important; }
    h1 { text-align: center; color: #e63946; }
    </style>
""", unsafe_allow_html=True)

# --- 🚪 GİRİŞ & KAYIT EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1>TürkAI Güvenli Giriş</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        u = st.text_input("Kullanıcı Adı", key="login_u")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Sisteme Eriş"):
            if giris_kontrol(u, p):
                st.session_state.giris_yapildi = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre!")
            
    with tab2:
        new_u = st.text_input("Yeni Kullanıcı Adı")
        new_p = st.text_input("Yeni Şifre", type="password")
        if st.button("Hesap Oluştur"):
            if len(new_u) > 2 and len(new_p) > 3:
                if kullanici_olustur(new_u, new_p): st.success("Hesap açıldı! Giriş yapabilirsin.")
                else: st.error("Bu kullanıcı adı alınmış.")
            else: st.warning("Bilgiler çok kısa!")
    st.stop()

# --- 🚀 ANA PLATFORM ---

# YAN PANEL: ÖZEL GEÇMİŞ VE TIKLANABİLİR LİSTE
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    st.divider()
    st.markdown("📂 **Senin Analizlerin**")
    gecmis_veriler = ozel_gecmis_getir(st.session_state.user)
    
    for konu_adi, icerik_metni in gecmis_veriler:
        if st.button(f"📄 {konu_adi}", use_container_width=True, key=f"btn_{konu_adi}"):
            st.session_state.su_anki_konu = konu_adi
            st.session_state.analiz_sonucu = icerik_metni

    st.divider()
    if st.button("Güvenli Çıkış"):
        st.session_state.giris_yapildi = False
        st.rerun()

# İÇERİK ALANI
st.markdown("<h1>TürkAI Bilgi Merkezi</h1>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    st.markdown(f'<div class="sonuc-karti"><h3>📌 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    
    # PDF Butonu
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, txt=st.session_state.analiz_sonucu.encode('latin-1', 'ignore').decode('latin-1'))
    st.download_button("📄 PDF Olarak İndir", pdf.output(dest='S').encode('latin-1'), f"{st.session_state.su_anki_konu}.pdf", "application/pdf")

# ALT ARAMA BARI
sorgu = st.chat_input("Yeni bir analiz başlat...")

if sorgu:
    if guvenli_mi(sorgu):
        with st.spinner("Analiz ediliyor..."):
            url = f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                paragraflar = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if paragraflar:
                    sonuc = "\n\n".join(paragraflar[:6])
                    analiz_kaydet(st.session_state.user, sorgu, sonuc)
                    st.session_state.analiz_sonucu = sonuc
                    st.session_state.su_anki_konu = sorgu
                    st.rerun()
                else: st.warning("İçerik bulunamadı.")
            else: st.error("Konu bulunamadı.")
    else: st.error("⛔ Uygunsuz içerik!")


  
    
