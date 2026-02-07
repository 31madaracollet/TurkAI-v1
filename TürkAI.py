import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time
from fpdf import FPDF
# --- KRİTİK DÜZELTME: Bu kütüphane şart ---
try:
    from duckduckgo_search import DDGS
except ImportError:
    st.error("Kütüphane eksik! requirements.txt dosyasına 'duckduckgo-search' eklediğinden emin ol.")

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

# --- 🔄 GELİŞMİŞ MOTOR FONKSİYONLARI ---
def yazi_efekti(text):
    """Yazıyı tane tane yazar (Typewriter effect)"""
    placeholder = st.empty()
    full_text = ""
    for word in text.split():
        full_text += word + " "
        placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.02) # Hız
    placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}</div>", unsafe_allow_html=True)

def derin_arama(sorgu):
    """GÜÇLENDİRİLMİŞ DERİN ARAMA (DuckDuckGo Kütüphanesi ile)"""
    durum = st.empty()
    try:
        # 1. Adım: Arama Sonuçlarını Çek (Kütüphane kullanarak - Engellenmez)
        linkler = []
        # 'wt-wt' yerine 'tr-tr' bölgesi kullanıyoruz
        ddgs = DDGS()
        results = ddgs.text(keywords=sorgu, region='tr-tr', safesearch='moderate', max_results=25)
        
        for r in results:
            linkler.append(r['href'])
        
        if not linkler:
            return wiki_arama(sorgu)

        # 2. Adım: Siteleri tek tek gez
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        taranan = 0
        
        for link in linkler:
            taranan += 1
            durum.caption(f"🧠 Ağ Analizi Yapılıyor ({taranan}/25): {link[:50]}...")
            
            try:
                # 10 saniye mühlet veriyoruz
                resp = requests.get(link, headers=headers, timeout=10)
                if resp.status_code != 200: continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # REKLAM VE ÇÖP TEMİZLİĞİ
                for gereksiz in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                    gereksiz.extract()
                
                # En dolu paragrafı bul
                paragraflar = soup.find_all('p')
                metinler = [p.get_text().strip() for p in paragraflar if len(p.get_text().strip()) > 150]
                
                # Eğer sağlam bir metin bulduysak (En az 300 karakter)
                ana_metin = "\n\n".join(metinler[:5]) # İlk 5 dolu paragrafı al
                
                if len(ana_metin) > 300:
                    durum.empty()
                    return ana_metin, f"{sorgu.title()} (Kaynak: Global Ağ)"
            
            except Exception as e:
                continue # Hata veren siteyi pas geç
        
        durum.empty()
        return wiki_arama(sorgu) # Hiçbir siteden veri çıkmazsa Wiki'ye dön
        
    except Exception as e:
        durum.empty()
        # Eğer kütüphane hata verirse Wiki'ye dön
        return wiki_arama(sorgu)

def wiki_arama(sorgu):
    """Hızlı Motor"""
    try:
        r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json").json()
        if not r['query']['search']:
            return "Veri tabanlarında bu konuyla ilgili bilgi bulunamadı.", "Sonuç Yok"
            
        title = r['query']['search'][0]['title']
        page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}").text
        soup = BeautifulSoup(page, 'html.parser')
        
        # Sadece <p> etiketlerini alıp birleştir
        info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
        
        if not info: return "İçerik çekilemedi.", title
        return info, title
    except:
        return "Bağlantı hatası veya veri yok.", "Hata"

# --- 🔑 GİRİŞ İŞLEMLERİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

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
                if st.button("👤 Misafir Girişi", use_container_width=True):
                    st.session_state.user = "Misafir_Kullanıcı"; st.rerun()
        with t2:
            nu, np = st.text_input("Yeni Ad"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol", use_container_width=True):
                try: c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest())); conn.commit(); st.success("Kayıt Tamam.")
                except: st.error("Kullanıcı adı dolu.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ {st.session_state.user}")
    if st.button("Oturumu Kapat", use_container_width=True): st.session_state.clear(); st.rerun()
    st.divider()
    
    st.markdown("**Analiz Motoru:**")
    motor = st.selectbox("", ["🚀 Hızlı Motor (Wiki+)", "🧠 Derin Düşünen (Global-25)", "🧮 Matematik Birimi"], label_visibility="collapsed")
    if motor == "🧮 Matematik Birimi": st.info("ℹ️ Çarpma için '*' kullanın.")
    
    st.divider()
    st.markdown("##### 📜 Geçmiş")
    c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,))
    for k in c.fetchall(): st.button(f"📄 {k[0][:15]}...", disabled=True)
    
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link">📥 Uygulamayı İndir</a>', unsafe_allow_html=True)

# --- 💻 TERMİNAL ---
st.title("Araştırma Terminali")
st.markdown("<div style='opacity:0.7; font-size:14px; margin-bottom:10px;'>💡 <b>İpucu:</b> Örn: 'Mustafa Kemal Atatürk' (Hatalı: Kimdir?)</div>", unsafe_allow_html=True)

sorgu = st.chat_input("Veri girişi yapınız...")

if sorgu:
    st.session_state.bilgi = None 
    
    with st.spinner('TürkAI Veri Madenciliği Yapıyor...'):
        if motor == "🚀 Hızlı Motor (Wiki+)":
            bilgi, baslik = wiki_arama(sorgu)
            
        elif motor == "🧠 Derin Düşünen (Global-25)":
            bilgi, baslik = derin_arama(sorgu)
            
        elif motor == "🧮 Matematik Birimi":
            try:
                res = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
                bilgi, baslik = f"Sonuç: {res}", "Matematik"
            except:
                bilgi, baslik = "Hata.", "Matematik"

    # Sonuçları ekrana bas
    st.subheader(f"Rapor: {baslik}")
    yazi_efekti(bilgi)
    
    st.session_state.bilgi = bilgi
    st.session_state.konu = baslik
    
    if st.session_state.user != "Misafir_Kullanıcı":
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, str(datetime.datetime.now()), motor))
        conn.commit()

# --- 🔽 AKSİYONLAR ---
if st.session_state.bilgi:
    col1, col2 = st.columns(2)
    with col1:
        # PDF
        def create_pdf():
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "TURKAI RAPORU", ln=True, align='C')
                pdf.set_font("Arial", size=12)
                # Basit karakter düzeltme
                tr_map = str.maketrans("ğĞüÜşŞİıöÖçÇ", "gGuUsSiioOcC")
                clean_text = st.session_state.bilgi.translate(tr_map)
                clean_title = st.session_state.konu.translate(tr_map)
                pdf.multi_cell(0, 10, f"\nKONU: {clean_title}\n\n{clean_text}")
                return pdf.output(dest='S').encode('latin-1')
            except: return None
            
        st.download_button("📊 PDF İndir", data=create_pdf(), file_name="rapor.pdf", mime="application/pdf", use_container_width=True)
    
    with col2:
        if st.button("👎 Beğenmedim", use_container_width=True):
            st.toast("Geri bildirim alındı, algoritma eğitiliyor...")
