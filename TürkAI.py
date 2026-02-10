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

# --- 🎨 DİNAMİK TEMA (DOKUNULMADI) ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    h1, h2, h3 { color: var(--primary-red) !important; font-weight: 700 !important; }
    .giris-kapsayici { border: 1px solid rgba(204, 0, 0, 0.3); border-radius: 12px; padding: 40px; text-align: center; }
    .apk-buton-link { display: block; width: 100%; background-color: var(--primary-red); color: white !important; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-bottom: 20px; }
    .not-alani { background-color: rgba(204, 0, 0, 0.05); color: var(--primary-red); padding: 10px; border-radius: 8px; border: 1px dashed var(--primary-red); margin-bottom: 20px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
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
if "kaynak_index" not in st.session_state: st.session_state.kaynak_index = 0
if "tum_kaynaklar" not in st.session_state: st.session_state.tum_kaynaklar = []

# --- 🔧 YARDIMCI FONKSİYONLAR ---
def yabanci_karakter_temizle(metin):
    if not metin: return ""
    patern = r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s\.,;:!\?\(\)\-\*\+=/]'
    return re.sub(patern, '', metin)

def tdk_temizle(metin):
    """TDK'daki gereksiz kod parçalarını temizler"""
    metin = re.sub(r'/[^ ]*', '', metin) # /pn, gos gibi kodları siler
    metin = re.sub(r'ozelliklerListe:[^ ]*', '', metin)
    metin = re.sub(r'anlamid:[0-9]*', '', metin)
    metin = re.sub(r'[a-z]*:[0-9,]*', '', metin)
    return metin.replace("null", "").replace("  ", " ").strip()

def pdf_olustur(baslik, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        def tr_fix(text):
            chars = {'ı':'i','İ':'I','ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C','ş':'s','Ş':'S','ğ':'g','Ğ':'G'}
            for k, v in chars.items(): text = text.replace(k, v)
            return text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, tr_fix("TurkAI Analiz Raporu"), ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, tr_fix(icerik))
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

def site_tara_brave_style(url, sorgu, site_adi, t_out=10):
    """Brave mantığıyla reklamları temizler ve tam metin çeker"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Brave/120.0.0.0'}
        response = requests.get(url, headers=headers, timeout=t_out)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # BRAVE TARZI TEMİZLİK
        for junk in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe']):
            junk.decompose()
            
        # Wikipedia özel temizlik
        if "wikipedia" in url:
            for w_junk in soup.select('.mw-empty-elt, .infobox, .toc, .navbox'): w_junk.decompose()

        raw_text = soup.get_text(separator=' ')
        words = raw_text.split()
        clean_text = ' '.join(words)
        
        if len(clean_text) > 100:
            final_text = yabanci_karakter_temizle(clean_text)
            if "sozluk.gov.tr" in url: final_text = tdk_temizle(final_text)
            return (site_adi, final_text)
        return (site_adi, None)
    except: return (site_adi, None)

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🔒 Giriş", "📝 Kayıt", "👤 Misafir"])
        with t1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir", use_container_width=True):
                h = hashlib.sha256(p.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h))
                if c.fetchone(): st.session_state.user = u; st.rerun()
        with t3:
            if st.button("Misafir Girişi", use_container_width=True): st.session_state.user = "Misafir"; st.rerun()
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">Uygulamayı İndir</a>', unsafe_allow_html=True)
    st.stop()

# --- 🚀 OPERASYONEL PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    m_secim = st.radio("Metodoloji:", ["V1 (Ansiklopedik)", "Sözlük (TDK)", "V3 (Matematik)", "🤔 Derin Düşünen"])
    st.divider()
    st.markdown("##### 🧮 Hızlı Hesap Makinesi")
    calc_in = st.text_input("İşlem Girin (Örn: 25*4):")
    if calc_in:
        try:
            res_calc = eval(re.sub(r'[^0-9+\-*/(). ]', '', calc_in))
            st.success(f"Sonuç: {res_calc}")
        except: st.error("Hata!")
    st.divider()
    if st.button("Oturumu Kapat", use_container_width=True): st.session_state.clear(); st.rerun()

st.title("Araştırma Terminali")
sorgu = st.chat_input("Anahtar kelime giriniz...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.kaynak_index = 0
    q_enc = urllib.parse.quote(sorgu)
    
    with st.spinner("Brave Filtresiyle Derin Analiz Yapılıyor..."):
        if m_secim == "Sözlük (TDK)":
            res = site_tara_brave_style(f"https://sozluk.gov.tr/gts?ara={q_enc}", sorgu, "TDK Sözlük")
            st.session_state.tum_kaynaklar = [res] if res[1] else []
        
        elif m_secim == "V3 (Matematik)":
            try:
                val = eval(re.sub(r'[^0-9+\-*/(). ]', '', sorgu))
                st.session_state.tum_kaynaklar = [("Matematik Motoru", f"Analiz Sonucu: {val}")]
            except: st.session_state.tum_kaynaklar = []
            
        elif m_secim == "🤔 Derin Düşünen":
            siteler = [
                f"https://tr.wikipedia.org/wiki/{q_enc}", f"https://www.bilgiustam.com/?s={q_enc}",
                f"https://www.turkcebilgi.com/{q_enc}", f"https://www.biyografi.info/ara?k={q_enc}",
                f"https://islamansiklopedisi.org.tr/ara?q={q_enc}", f"https://www.nedir.com/{q_enc}",
                f"https://www.etimolojiturkce.com/arama/{q_enc}", f"https://sozluk.gov.tr/gts?ara={q_enc}",
                f"https://dergipark.org.tr/tr/search?q={q_enc}", f"https://en.wikipedia.org/wiki/{q_enc}",
                f"https://www.britannica.com/search?query={q_enc}", f"https://www.worldhistory.org/search/?q={q_enc}",
                f"https://plato.stanford.edu/search/searcher.py?query={q_enc}", f"https://global.britannica.com/search?query={q_enc}",
                f"https://www.biyografya.com/arama?q={q_enc}"
            ]
            bulunanlar = []
            p_bar = st.progress(0)
            status_t = st.empty()
            
            for i, s_url in enumerate(siteler):
                status_t.text(f"🔍 Derin Tarama ({i+1}/15): {urllib.parse.urlparse(s_url).netloc}")
                p_bar.progress((i+1)/len(siteler))
                # Her siteye 10 saniye limit
                res = site_tara_brave_style(s_url, sorgu, f"Kaynak {i+1}: {urllib.parse.urlparse(s_url).netloc}", t_out=10)
                if res[1]: bulunanlar.append(res)
            
            st.session_state.tum_kaynaklar = bulunanlar
            p_bar.empty()
            status_t.empty()
        
        else: # V1 Ansiklopedik
            res = site_tara_brave_style(f"https://tr.wikipedia.org/wiki/{q_enc}", sorgu, "Wikipedia")
            st.session_state.tum_kaynaklar = [res] if res[1] else []

        if st.session_state.tum_kaynaklar:
            s, i = st.session_state.tum_kaynaklar[0]
            st.session_state.bilgi, st.session_state.konu = i, sorgu.upper()
        else:
            st.session_state.bilgi = "Maalesef Brave filtresi bu konuda temiz bir veri bulamadı."
    st.rerun()

# --- 📊 SONUÇ GÖSTERİMİ ---
if st.session_state.bilgi:
    st.subheader(f"📊 Analiz Raporu: {st.session_state.konu}")
    active_res = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
    st.info(f"Aktif Kaynak: {active_res[0]}")
    
    st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; color: #333; border-left: 5px solid #cc0000;'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        pdf_f = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
        if pdf_f: st.download_button("📥 Analizi PDF İndir", pdf_f, "TurkAI_Rapor.pdf", "application/pdf", use_container_width=True)
    
    with col2:
        if len(st.session_state.tum_kaynaklar) > 1:
            if st.button("🔄 Yeniden Yap (Sonraki Siteye Geç)", use_container_width=True):
                st.session_state.kaynak_index = (st.session_state.kaynak_index + 1) % len(st.session_state.tum_kaynaklar)
                s_next, i_next = st.session_state.tum_kaynaklar[st.session_state.kaynak_index]
                st.session_state.bilgi = i_next
                st.rerun()

st.markdown("<div style='text-align:center; margin-top:50px; opacity:0.3;'>&copy; 2026 TürkAI | Kurumsal Analiz</div>", unsafe_allow_html=True)
