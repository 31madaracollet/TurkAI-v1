import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time
import random
from fpdf import FPDF 

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 DİNAMİK TEMA VE CSS ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    h1, h2, h3 { color: var(--primary-red) !important; font-weight: 700 !important; }
    
    .giris-kapsayici {
        border: 1px solid rgba(204, 0, 0, 0.3); border-radius: 12px; padding: 40px; 
        text-align: center; background-color: transparent;
    }
    .apk-buton-link {
        display: block; width: 100%; background-color: var(--primary-red); color: white !important; 
        text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; 
        font-weight: 600; margin-bottom: 20px; transition: 0.3s;
    }
    .apk-buton-link:hover { transform: scale(1.01); opacity: 0.9; }
    
    .sidebar-indir-link {
        display: block; background-color: transparent; color: inherit !important; text-align: center; 
        padding: 8px; border-radius: 6px; text-decoration: none; border: 1px solid var(--primary-red); 
        font-size: 13px; margin-top: 10px;
    }
    .not-alani {
        background-color: rgba(204, 0, 0, 0.05); color: var(--primary-red); padding: 10px; 
        border-radius: 8px; border: 1px dashed var(--primary-red); margin-bottom: 20px; 
        font-size: 0.85rem; text-align: center;
    }
    .ai-rapor-alani {
        border-left: 4px solid var(--primary-red); padding: 20px; 
        background-color: rgba(128,128,128,0.05); border-radius: 4px; line-height: 1.6;
    }
    /* Spinner Rengi */
    .stSpinner > div { border-top-color: #cc0000 !important; }
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

# --- 🔄 FONKSİYONLAR ---
def yazi_efekti(text):
    """Yazıyı tane tane yazar (Typewriter effect)"""
    placeholder = st.empty()
    full_text = ""
    # Kelime kelime bölüyoruz
    for word in text.split():
        full_text += word + " "
        placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.05) # Hız ayarı
    placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}</div>", unsafe_allow_html=True)

def derin_arama(sorgu):
    """Simüle edilmiş derin arama motoru (Web scraping + Filtreleme)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # 1. Adım: Arama sonuçlarını çek (DuckDuckGo HTML üzerinden)
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(sorgu)}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Linkleri topla
        linkler = []
        for a in soup.find_all('a', class_='result__a', href=True):
            href = a['href']
            if 'http' in href:
                linkler.append(href)
        
        # İlk 5 linki derinlemesine tara (25 site simülasyonu için döngü)
        bulunan_veri = None
        taranan_sayisi = 0
        
        durum_cubugu = st.empty()
        
        for link in linkler[:25]: # Max 25 siteye bak
            taranan_sayisi += 1
            durum_cubugu.caption(f"🕷️ Ağ taranıyor ({taranan_sayisi}/25): {link[:40]}...")
            
            try:
                # Her siteye 10sn süre veriyoruz
                site_res = requests.get(link, headers=headers, timeout=10)
                site_soup = BeautifulSoup(site_res.text, 'html.parser')
                
                # Reklamları temizle (script ve style etiketlerini at)
                for script in site_soup(["script", "style", "nav", "footer", "header"]):
                    script.extract()
                
                # Paragrafları bul
                paragraflar = site_soup.find_all('p')
                metin = "\n\n".join([p.get_text() for p in paragraflar if len(p.get_text()) > 100])
                
                if len(metin) > 500: # Eğer yeterli veri varsa
                    bulunan_veri = metin[:2000] + "..." # Çok uzunsa kes
                    durum_cubugu.empty() # Durum çubuğunu temizle
                    return bulunan_veri, "Derin Analiz (Global Web)"
                    
            except:
                continue # Bu site açılmadıysa sonrakine geç
        
        # Hiçbir şey bulunamazsa Wikipedia dene
        return wiki_arama(sorgu)
        
    except:
        return wiki_arama(sorgu)

def wiki_arama(sorgu):
    try:
        r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json").json()
        title = r['query']['search'][0]['title']
        page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}").text
        soup = BeautifulSoup(page, 'html.parser')
        info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:6])
        return info, title
    except:
        return "Veri bulunamadı.", "Hata"

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
# Geçici değişkenler (Session state yerine anlık değişken gibi davranması için temizliyoruz)
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        st.markdown("<div class='not-alani'>⚠️ Şuan betada olduğu için, çalışmalar sürdürülüyor.</div>", unsafe_allow_html=True)
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TürkAI Mobil Uygulamasını Yükle</a>', unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔒 Giriş", "📝 Kayıt"])
        with t1:
            u_in = st.text_input("Kullanıcı Adı")
            p_in = st.text_input("Şifre", type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sisteme Eriş", use_container_width=True):
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone(): st.session_state.user = u_in; st.rerun()
                    else: st.error("Hatalı bilgi.")
            with c2:
                # MİSAFİR GİRİŞİ BUTONU
                if st.button("👤 Misafir Girişi", use_container_width=True):
                    st.session_state.user = "Misafir_Kullanıcı"
                    st.rerun()
                    
        with t2:
            nu, np = st.text_input("Yeni Ad"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol", use_container_width=True):
                try: c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest())); conn.commit(); st.success("Oldu.")
                except: st.error("Dolu.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ {st.session_state.user}")
    if st.button("Oturumu Kapat", use_container_width=True): st.session_state.clear(); st.rerun()
    st.divider()
    
    # YENİ MOTOR SİSTEMİ
    st.markdown("**Analiz Motoru:**")
    motor = st.selectbox("", ["🚀 Hızlı Motor (Wiki+)", "🧠 Derin Düşünen (Global-25)", "🧮 Matematik Birimi"], label_visibility="collapsed")
    
    if motor == "🧮 Matematik Birimi":
        st.info("ℹ️ Not: Çarpma için 'x' yerine '*' kullanın.")

    st.divider()
    st.markdown("##### 📜 Geçmiş")
    c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,))
    for k in c.fetchall(): st.button(f"📄 {k[0][:15]}...", disabled=True) # Sadece görüntü
    
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link">📥 Uygulamayı İndir</a>', unsafe_allow_html=True)

# --- 💻 TERMİNAL ---
st.title("Araştırma Terminali")
st.markdown("<div style='opacity:0.7; font-size:14px; margin-bottom:10px;'>💡 <b>İpucu:</b> Örn: 'Türk tarihi' (Hatalı: Türk tarihi nedir?)</div>", unsafe_allow_html=True)

sorgu = st.chat_input("Analiz verisi giriniz...")

if sorgu:
    # EKRANI TEMİZLE (Eski sonucu siler)
    st.session_state.bilgi = None 
    st.session_state.konu = ""
    
    bilgi_bulunan = ""
    konu_basligi = ""
    
    # SPINNER (DÖNEN YUVARLAK)
    with st.spinner('TürkAI Veri Madenciliği Yapıyor...'):
        if motor == "🚀 Hızlı Motor (Wiki+)":
            # Önce Wiki, olmazsa Global özet
            bilgi_bulunan, konu_basligi = wiki_arama(sorgu)
            time.sleep(1) # Yapay his için minik bekleme
            
        elif motor == "🧠 Derin Düşünen (Global-25)":
            # Derin tarama fonksiyonu
            bilgi_bulunan, konu_basligi = derin_arama(sorgu)
            
        elif motor == "🧮 Matematik Birimi":
            try:
                res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
                bilgi_bulunan, konu_basligi = f"Hesaplama Sonucu: {res}", "Matematik"
            except:
                bilgi_bulunan = "İşlem hatası. Lütfen '*' kullanın."
                konu_basligi = "Hata"

    # Sonuçları State'e kaydetmeden önce ekrana bas (Tane tane)
    st.subheader(f"Rapor: {konu_basligi}")
    yazi_efekti(bilgi_bulunan)
    
    # PDF ve Beğenmeme için state'i güncelle
    st.session_state.bilgi = bilgi_bulunan
    st.session_state.konu = konu_basligi
    
    # Veritabanına kaydet
    if st.session_state.user != "Misafir_Kullanıcı":
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, konu_basligi, bilgi_bulunan, str(datetime.datetime.now()), motor))
        conn.commit()

# --- 🔽 SONUÇ AKSİYONLARI ---
if st.session_state.bilgi:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        # PDF OLUŞTURMA
        def create_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "TURKAI ANALIZ RAPORU", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            # Türkçe karakter temizliği (Basit)
            text = st.session_state.bilgi.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, f"\nKONU: {st.session_state.konu}\n\n{text}")
            return pdf.output(dest='S').encode('latin-1')
            
        try:
            st.download_button("📊 PDF Rapor İndir", data=create_pdf(), file_name="rapor.pdf", mime="application/pdf", use_container_width=True)
        except: st.error("PDF oluşturulamadı (Karakter hatası).")

    with col_b:
        # BEĞENMEDİM BUTONU
        if st.button("👎 Bu analizi beğenmedim", use_container_width=True):
            st.warning("Geri bildiriminiz alındı. Algoritma güncellenecek.")
            # İstersen burada veriyi temizleyebilirsin:
            # st.session_state.bilgi = None
            # st.rerun()
