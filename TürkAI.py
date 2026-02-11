import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
import urllib.parse
import re 
import json # TDK için JSON desteği şart
from fpdf import FPDF 
import time
import os
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# --- ⚙️ SİSTEM VE TEMA AYARLARI (Bozulmadı) ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz", page_icon="🇹🇷", layout="wide")
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/2381a04f5686fa8cefff.apk"

# --- 🎨 GELİŞMİŞ CSS (Bozulmadı) ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; --hover-red: #990000; }
    h1, h2, h3 { color: var(--primary-red) !important; }
    .giris-kapsayici { border: 1px solid rgba(204, 0, 0, 0.3); border-radius: 15px; padding: 30px; background: rgba(128, 128, 128, 0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #800000, #cc0000); }
    .apk-buton { display: block; background: var(--primary-red); color: white !important; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; transition: 0.3s; }
    .apk-buton:hover { background: var(--hover-red); transform: scale(1.02); }
    .arastirma-notu { padding: 15px; border-radius: 10px; border-left: 5px solid var(--primary-red); background-color: rgba(204, 0, 0, 0.05); margin: 10px 0 20px 0; font-size: 0.95rem; }
    .sonuc-metni { padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); line-height: 1.7; background: rgba(128, 128, 128, 0.02); font-size: 1.05rem; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI (Bozulmadı) ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    return conn, c
conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ (Bozulmadı) ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "kaynak_index" not in st.session_state: st.session_state.kaynak_index = 0
if "tum_kaynaklar" not in st.session_state: st.session_state.tum_kaynaklar = []

# --- 🔧 ÖZEL AYIKLAMA FONKSİYONLARI (Yeni Geliştirilen Kısım) ---

def tdk_json_analiz(ham_veri):
    """TDK JSON çıktısını insan diline çevirir."""
    try:
        data = json.loads(ham_veri)
        sonuclar = []
        for madde in data:
            if "anlamlarListe" in madde:
                for anl in madde["anlamlarListe"]:
                    sonuclar.append(f"• {anl['anlam']}")
        return "\n".join(sonuclar) if sonuclar else "Anlam bulunamadı."
    except: return "TDK verisi işlenemedi."

def siteye_ozel_temizlik(soup, url):
    """Her site için ayrı temizlik yapar (Linkleri ve menüleri siler)."""
    # Genel silinecek etiketler
    for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'button', 'input']):
        s.decompose()

    # Wikipedia özel temizliği
    if "wikipedia.org" in url:
        for ref in soup.find_all(['sup', 'span'], class_=['reflist', 'mw-editsection', 'noprint']):
            ref.decompose()
    
    # Bilgiustam ve diğerleri için ortak reklam/menü temizliği
    for garbage in soup.find_all(['div', 'ul', 'li'], class_=re.compile(r'menu|sidebar|footer|social|comment|ads|share|header')):
        garbage.decompose()

    metin = soup.get_text(separator=' ')
    # 1. Köşeli parantezli referansları sil ([1], [değiştir] vb.)
    metin = re.sub(r'\[.*?\]', '', metin)
    # 2. Fazla boşlukları temizle
    metin = ' '.join(metin.split())
    
    # 3. Kısa ve anlamsız satırları (genelde link yazılarıdır) süzgeçten geçir
    # Eğer metin çok kısaysa (link listesi gibiyse) reddet
    return metin if len(metin) > 150 else ""

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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # Eğer TDK sorgusuysa JSON olarak işle
        if "sozluk.gov.tr" in url:
            final = tdk_json_analiz(response.text)
            return (site_adi, final)
            
        soup = BeautifulSoup(response.content, 'html.parser')
        # SİTEYE ÖZEL AYIKLAMA BURADA ÇALIŞIR
        final = siteye_ozel_temizlik(soup, url)
        
        return (site_adi, final) if len(final) > 100 else (site_adi, None)
    except: return (site_adi, None)

# --- 🔐 GİRİŞ & KAYIT (Bozulmadı) ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI V1</h1>", unsafe_allow_html=True)
        st.warning("⚠️ Bu bir yapay zeka değil, araştırma botudur.")
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
                        conn.commit(); st.success("Kayıt başarılı!")
                    except: st.error("Bu kullanıcı adı zaten alınmış.")
        with tab_m:
            if st.button("Yetkisiz (Misafir) Girişi", use_container_width=True): 
                st.session_state.user = "Misafir"; st.rerun()
        st.markdown(f'<a href="{APK_URL}" class="apk-buton">TürkAI Mobile APK İndir</a>', unsafe_allow_html=True)
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    m_secim = st.radio("Sorgu Metodu:", ["V1 (Ansiklopedik)", "Sözlük (TDK)", "V3 (Matematik)", "🤔 Derin Düşünen", "🖼️ Görselden PDF"])
    st.divider()
    st.markdown("##### 🧮 Hızlı Hesap")
    calc = st.text_input("İşlem örn: (5*5)/2")
    if calc:
        if re.search(r'[a-zA-Z]', calc):
            st.error("Lütfen sadece işlem yazınız.")
        else:
            try: st.success(f"Sonuç: {eval(re.sub(r'[^0-9+\-*/(). ]', '', calc))}")
            except: st.error("Hatalı işlem!")
    st.divider()
    if st.button("Oturumu Kapat", use_container_width=True): st.session_state.clear(); st.rerun()

st.title("Araştırma Terminali")

# 🟡 GÖRSEL OCR MODU (Bozulmadı)
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
                    if extracted_text.strip():
                        st.text_area("Okunan Metin:", extracted_text, height=200)
                        pdf_data = pdf_olustur("TurkAI OCR Raporu", extracted_text)
                        st.download_button("📥 PDF İndir", pdf_data, "TurkAI_OCR.pdf", "application/pdf")
                except Exception as e: st.error(f"OCR Hatası: {e}")

else:
    st.markdown("<div class='arastirma-notu'><b>Not:</b> Anahtar kelimeyi yazınız.</div>", unsafe_allow_html=True)
    sorgu = st.chat_input("Analiz edilecek konu...")

    if sorgu:
        if m_secim == "V3 (Matematik)" and re.search(r'[a-zA-Z]', sorgu):
            st.error("Lütfen sadece işlem yazınız.")
        else:
            st.session_state.son_sorgu = sorgu
            st.session_state.kaynak_index = 0
            q_enc = urllib.parse.quote(sorgu)
            
            with st.container():
                st.write("### 🔍 Analiz Süreci")
                p_bar = st.progress(0); status = st.empty()
                
                # DERİN DÜŞÜNEN: Her site için ayrı temizlik yapar
                if m_secim == "🤔 Derin Düşünen":
                    siteler = [f"https://tr.wikipedia.org/wiki/{q_enc}", f"https://www.bilgiustam.com/?s={q_enc}", f"https://www.turkcebilgi.com/{q_enc}"]
                    bulunanlar = []
                    for i, url in enumerate(siteler):
                        status.info(f"Tarama: {url}")
                        res = site_tara_brave_style(url, sorgu, f"Kaynak {i+1}")
                        if res[1]: bulunanlar.append(res)
                        p_bar.progress((i+1)/len(siteler))
                    st.session_state.tum_kaynaklar = bulunanlar

                elif m_secim == "Sözlük (TDK)":
                    res = site_tara_brave_style(f"https://sozluk.gov.tr/gts?ara={q_enc}", sorgu, "TDK")
                    st.session_state.tum_kaynaklar = [res] if res[1] else []

                elif m_secim == "V3 (Matematik)":
                    try:
                        res_val = eval(re.sub(r'[^0-9+\-*/(). ]', '', sorgu))
                        st.session_state.tum_kaynaklar = [("Matematik", f"Sonuç: {res_val}")]
                    except: st.session_state.tum_kaynaklar = []

                else: # V1 Ansiklopedik
                    res = site_tara_brave_style(f"https://tr.wikipedia.org/wiki/{q_enc}", sorgu, "Wikipedia")
                    st.session_state.tum_kaynaklar = [res] if res[1] else []

                if st.session_state.tum_kaynaklar:
                    st.session_state.bilgi = st.session_state.tum_kaynaklar[0][1]
                    st.session_state.konu = sorgu.upper()
                else: st.session_state.bilgi = "Üzgünüm, temiz veri bulunamadı."
                status.empty(); p_bar.empty()
            st.rerun()

    # --- 📊 RAPORLAMA (Bozulmadı) ---
    if st.session_state.bilgi:
        st.subheader(f"📊 Rapor: {st.session_state.konu}")
        active = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
        st.info(f"📍 Aktif Kaynak: {active[0]}")
        st.markdown(f"<div class='sonuc-metni'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            pdf = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
            if pdf: st.download_button("📥 PDF İndir", pdf, f"TurkAI_{st.session_state.konu}.pdf", use_container_width=True)
        with c2:
            if len(st.session_state.tum_kaynaklar) > 1:
                if st.button("🔄 Sonraki Kaynağa Geç", use_container_width=True):
                    st.session_state.kaynak_index = (st.session_state.kaynak_index + 1) % len(st.session_state.tum_kaynaklar)
                    st.session_state.bilgi = st.session_state.tum_kaynaklar[st.session_state.kaynak_index][1]
                    st.rerun()

st.markdown("<div style='text-align:center; margin-top:50px; opacity:0.3;'>2026 TürkAI | Kurumsal Analiz Platformu</div>", unsafe_allow_html=True)
