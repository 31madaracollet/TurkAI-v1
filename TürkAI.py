import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
import urllib.parse
import re 
from fpdf import FPDF 
import time
import os
from PIL import Image
import pytesseract # Resimden yazı okumak için

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
# İsim ve ikon SucukAI olarak güncellendi
st.set_page_config(page_title="SucukAI | Kurumsal Analiz", page_icon="🌭", layout="wide")

# --- 🎨 GELİŞMİŞ CSS (Sucuk Temalı Kırmızı Tonları) ---
st.markdown("""
    <style>
    :root { --primary-red: #a80000; --hover-red: #7a0000; }
    h1, h2, h3 { color: var(--primary-red) !important; }
    .giris-kapsayici { border: 1px solid rgba(168, 0, 0, 0.3); border-radius: 15px; padding: 30px; background: rgba(128, 128, 128, 0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #5e0000, #a80000); }
    .apk-buton { display: block; background: var(--primary-red); color: white !important; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; transition: 0.3s; }
    .apk-buton:hover { background: var(--hover-red); transform: scale(1.02); }
    .arastirma-notu { padding: 15px; border-radius: 10px; border-left: 5px solid var(--primary-red); background-color: rgba(168, 0, 0, 0.05); margin: 10px 0 20px 0; font-size: 0.95rem; }
    .sonuc-metni { padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); line-height: 1.7; background: rgba(128, 128, 128, 0.02); font-size: 1.05rem; }
    /* Menüleri gizleyerek daha uygulama gibi görünmesini sağlar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('sucukai_v1.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c
conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "kaynak_index" not in st.session_state: st.session_state.kaynak_index = 0
if "tum_kaynaklar" not in st.session_state: st.session_state.tum_kaynaklar = []

# --- 🔧 YARDIMCI FONKSİYONLAR ---
def yabanci_karakter_temizle(metin):
    if not metin: return ""
    return re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s\.,;:!\?\(\)\-\*\+=/]', '', metin)

def wikipedia_temizle(metin):
    metin = re.sub(r'\[\d+\]', '', metin)
    silinecekler = ["İçeriğe atla", "Vikipedi, özgür ansiklopedi", "değiştir kaynağı değiştir", "Ayrıca bakınız", "Kaynakça"]
    for s in silinecekler: metin = metin.replace(s, "")
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
        pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, tr_fix(baslik), ln=True, align='C')
        pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 5, tr_fix(icerik))
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

def site_tara_brave_style(url, sorgu, site_adi):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Brave/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for j in soup(['script', 'style', 'nav', 'footer', 'header']): j.decompose()
        if "wikipedia" in url:
            content = soup.find(id="mw-content-text")
            final = wikipedia_temizle(content.get_text() if content else soup.get_text())
        else: final = soup.get_text(separator=' ')
        final = yabanci_karakter_temizle(' '.join(final.split()))
        if "sozluk.gov.tr" in url: final = tdk_temizle(final)
        return (site_adi, final) if len(final) > 100 else (site_adi, None)
    except: return (site_adi, None)

# --- 🔐 GİRİŞ & KAYIT ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🌭 SucukAI V1</h1>", unsafe_allow_html=True)
        st.warning("⚠️ Bu bir yapay zeka değil, hızlı araştırma ve analiz botudur.")
        
        tab_in, tab_up, tab_m = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol", "👤 Misafir"])
        with tab_in:
            u = st.text_input("Kullanıcı Adı", key="login_u")
            p = st.text_input("Şifre", type="password", key="login_p")
            if st.button("Sisteme Giriş", use_container_width=True):
                h = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                if c.fetchone(): st.session_state.user = u; st.rerun()
                else: st.error("Hatalı kullanıcı adı veya şifre!")
        with tab_up:
            nu = st.text_input("Yeni Kullanıcı Adı", key="reg_u")
            np = st.text_input("Yeni Şifre", type="password", key="reg_p")
            if st.button("Hesabı Oluştur", use_container_width=True):
                if nu and np:
                    try:
                        c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                        conn.commit(); st.success("SucukAI ailesine hoş geldiniz! Giriş yapabilirsiniz.")
                    except: st.error("Bu kullanıcı adı zaten alınmış.")
                else: st.warning("Lütfen tüm alanları doldurun.")
        with tab_m:
            if st.button("Misafir Olarak Devam Et", use_container_width=True): 
                st.session_state.user = "Misafir"; st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 🌭 Kullanıcı: {st.session_state.user}")
    m_secim = st.radio("Sorgu Metodu:", ["V1 (Ansiklopedik)", "Sözlük (TDK)", "V3 (Matematik)", "🤔 Derin Düşünen", "🖼️ Görselden PDF"])
    st.divider()
    if st.button("Oturumu Kapat", use_container_width=True): st.session_state.clear(); st.rerun()

st.title("🌭 SucukAI Araştırma Terminali")

# 🟡 GÖRSEL OCR MODU
if m_secim == "🖼️ Görselden PDF":
    st.markdown("<div class='arastirma-notu'><b>Mod:</b> Görseldeki yazıları okuyup PDF'e aktarma aracı (OCR).</div>", unsafe_allow_html=True)
    yuklenen_dosya = st.file_uploader("Okunacak görseli seçin", type=['png', 'jpg', 'jpeg'])
    
    if yuklenen_dosya:
        image = Image.open(yuklenen_dosya)
        st.image(image, caption='Analiz Edilen Görsel', width=400)
        
        if st.button("📄 Yazıları Çıkar ve PDF Yap", use_container_width=True):
            with st.spinner('Yazılar okunuyor...'):
                try:
                    extracted_text = pytesseract.image_to_string(image, lang='tur')
                    if not extracted_text.strip():
                        st.error("Okunabilir yazı bulunamadı!")
                    else:
                        st.success("Yazı başarıyla okundu!")
                        st.text_area("Okunan Metin:", extracted_text, height=200)
                        pdf_data = pdf_olustur("SucukAI OCR Analiz", extracted_text)
                        st.download_button("📥 PDF İndir", pdf_data, "SucukAI_OCR.pdf", "application/pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Sistemde Tesseract yüklü olmalıdır. Hata: {e}")

else:
    st.markdown("<div class='arastirma-notu'><b>SucukAI İpucu:</b> Aradığınız konuyu girin, sizin yerinize tüm interneti tarasın.</div>", unsafe_allow_html=True)
    sorgu = st.chat_input("Analiz edilecek konuyu buraya yazın...")

    if sorgu:
        st.session_state.son_sorgu = sorgu
        st.session_state.kaynak_index = 0
        q_enc = urllib.parse.quote(sorgu)
        
        with st.container():
            st.write("### 🔍 SucukAI Taraması Başladı")
            p_bar = st.progress(0)
            status = st.empty()
            
            if m_secim == "🤔 Derin Düşünen":
                siteler = [f"https://tr.wikipedia.org/wiki/{q_enc}", f"https://www.turkcebilgi.com/{q_enc}", f"https://sozluk.gov.tr/gts?ara={q_enc}", f"https://en.wikipedia.org/wiki/{q_enc}", f"https://islamansiklopedisi.org.tr/ara?q={q_enc}"]
                bulunanlar = []
                for i, url in enumerate(siteler):
                    status.info(f"Tarama yapılıyor: {urllib.parse.urlparse(url).netloc}")
                    p_bar.progress((i+1)/len(siteler))
                    res = site_tara_brave_style(url, sorgu, f"Kaynak {i+1}")
                    if res[1]: bulunanlar.append(res)
                st.session_state.tum_kaynaklar = bulunanlar
            elif m_secim == "V3 (Matematik)":
                try:
                    res_val = eval(re.sub(r'[^0-9+\-*/(). ]', '', sorgu))
                    st.session_state.tum_kaynaklar = [("Matematik Motoru", f"İşlem Sonucu: {res_val}")]
                except: st.session_state.tum_kaynaklar = []
            else:
                res = site_tara_brave_style(f"https://tr.wikipedia.org/wiki/{q_enc}", sorgu, "Wikipedia")
                st.session_state.tum_kaynaklar = [res] if res[1] else []

            if st.session_state.tum_kaynaklar:
                st.session_state.bilgi = st.session_state.tum_kaynaklar[0][1]
                st.session_state.konu = sorgu.upper()
            else:
                st.session_state.bilgi = "Maalesef SucukAI bu konuda veri bulamadı."
            st.rerun()

    if st.session_state.bilgi:
        st.subheader(f"📊 SucukAI Raporu: {st.session_state.konu}")
        st.markdown(f"<div class='sonuc-metni'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
        pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
        if pdf: st.download_button("📥 Raporu PDF Olarak Al", pdf, f"SucukAI_{st.session_state.konu}.pdf", use_container_width=True)

st.markdown("<div style='text-align:center; margin-top:50px; opacity:0.3;'>2026 SucukAI | Lezzetli Analizler</div>", unsafe_allow_html=True)
