import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
import concurrent.futures
import time

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 TEMA SİSTEMİ (Karanlık/Aydınlık) ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def load_theme():
    if st.session_state.dark_mode:
        # KARANLIK MOD
        return """
        <style>
        .stApp { background-color: #0a0a0a; }
        h1, h2, h3 { color: #ff4d4d !important; font-weight: 800 !important; }
        
        .giris-kapsayici {
            background-color: #1a1a1a;
            border: 2px solid #cc0000; border-radius: 20px;
            padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.3);
        }

        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
            color: #ffffff !important;
            padding: 12px 18px; border-radius: 15px 15px 0px 15px;
            margin-bottom: 20px; width: fit-content; max-width: 70%;
            margin-left: auto; box-shadow: 0px 4px 10px rgba(204, 0, 0, 0.4);
        }
        .user-msg * { color: #ffffff !important; }

        .ai-rapor-alani {
            border-left: 6px solid #cc0000; padding: 20px 25px;
            background-color: #1e1e1e; margin-bottom: 25px;
            border-radius: 0px 15px 15px 0px; box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            color: #f0f0f0;
        }

        [data-testid="stSidebar"] { 
            background-color: #111111 !important; 
            border-right: 3px solid #cc0000 !important;
        }
        
        div.stButton > button {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%) !important;
            color: white !important; border-radius: 10px !important;
            font-weight: bold !important; border: none !important;
        }
        
        .ozel-not {
            background-color: #2a0f0f; color: #ff9999; padding: 10px; 
            border-radius: 10px; border: 1px dashed #cc0000; margin-bottom: 15px;
            font-size: 0.85rem; text-align: center;
        }
        
        .kullanim-notu {
            background-color: #1a1a1a; padding: 10px; border-radius: 10px;
            border-left: 5px solid #cc0000; font-size: 0.9rem; margin-bottom: 10px;
            color: #cccccc;
        }
        
        .stTextInput > div > div > input {
            background-color: #2a2a2a !important;
            color: white !important;
            border: 1px solid #444 !important;
        }
        
        .stSelectbox > div > div {
            background-color: #2a2a2a !important;
            color: white !important;
        }
        </style>
        """
    else:
        # AYDINLIK MOD (ORİJİNAL)
        return """
        <style>
        .stApp { background-color: #ffffff; }
        h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
        
        .giris-kapsayici {
            background-color: #fffafa;
            border: 2px solid #cc0000; border-radius: 20px;
            padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
        }

        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            color: #ffffff !important;
            padding: 12px 18px; border-radius: 15px 15px 0px 15px;
            margin-bottom: 20px; width: fit-content; max-width: 70%;
            margin-left: auto; box-shadow: 0px 4px 10px rgba(204, 0, 0, 0.2);
        }
        .user-msg * { color: #ffffff !important; }

        .ai-rapor-alani {
            border-left: 6px solid #cc0000; padding: 20px 25px;
            background-color: #fdfdfd; margin-bottom: 25px;
            border-radius: 0px 15px 15px 0px; box-shadow: 2px 2px 8px rgba(0,0,0,0.02);
        }

        [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
        div.stButton > button {
            background-color: #cc0000 !important; color: white !important;
            border-radius: 10px !important; font-weight: bold !important;
        }
        .ozel-not {
            background-color: #fff3f3; color: #cc0000; padding: 10px; 
            border-radius: 10px; border: 1px dashed #cc0000; margin-bottom: 15px;
            font-size: 0.85rem; text-align: center;
        }
        .kullanim-notu {
            background-color: #f0f2f6; padding: 10px; border-radius: 10px;
            border-left: 5px solid #cc0000; font-size: 0.9rem; margin-bottom: 10px;
        }
        </style>
        """

# Temayı yükle
st.markdown(load_theme(), unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🛡️ İÇERİK FİLTRELEME ---
def icerik_filtrele(metin):
    """Türkçe içeriği filtrele ve temizle"""
    if not metin:
        return ""
    
    # Reklam ve spam siteleri filtrele
    spam_list = [
        'money metals exchange', 'buy precious metals', 'bullion specials',
        'trusted source for buying', 'check out our', 'america\'s fastest growing',
        'silver gold platinum', 'precious metals online', 'cheap gold',
        'advertisement', 'sponsored', 'adsbygoogle', 'click here', 'sign up',
        'log in', 'register now', 'buy now', 'shop now'
    ]
    
    for spam in spam_list:
        metin = re.sub(spam, '', metin, flags=re.IGNORECASE)
    
    # HTML etiketlerini temizle
    metin = re.sub(r'<[^>]+>', '', metin)
    
    # URL'leri temizle
    metin = re.sub(r'https?://\S+', '', metin)
    
    # Fazla boşlukları temizle
    metin = re.sub(r'\s+', ' ', metin)
    
    # Türkçe karakterleri koru, diğerlerini temizle
    metin = re.sub(r'[^\w\sçğıöşüÇĞİÖŞÜ.,;:!?()\-+]', ' ', metin)
    
    return metin.strip()

# --- 🔍 TEK MOTOR SİSTEMİ (Tüm özellikler birleşik) ---
def tek_motor_analiz(sorgu, timeout=5):
    """Tüm analiz motorları birleşik"""
    sonuc = ""
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. MATEMATİK KONTROLÜ
    if re.match(r'^[\d\s+\-*/().xX]+$', sorgu.replace(' ', '')):
        try:
            expr = sorgu.replace('x', '*').replace('X', '*').replace(',', '.')
            res = eval(expr, {"__builtins__": {}}, {})
            return f"🧮 **Matematik Sonucu:**\n\n`{sorgu} = {res}`\n\n*Otomatik hesaplandı*", "Matematik"
        except:
            return "⚠️ Matematik ifadesi çözülemedi.", "Hata"
    
    # 2. HAVA DURUMU KONTROLÜ
    hava_kelimeler = ['hava', 'durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar', 'nem', 'derece']
    if any(kelime in sorgu.lower() for kelime in hava_kelimeler):
        try:
            # Şehir adını çıkar
            sehir = "İstanbul"
            kelimeler = sorgu.lower().split()
            for kelime in kelimeler:
                if kelime not in hava_kelimeler and len(kelime) > 2:
                    sehir = kelime.title()
                    break
            
            url = f"http://wttr.in/{urllib.parse.quote(sehir)}?format=j1"
            r = requests.get(url, timeout=timeout)
            data = r.json()
            curr = data['current_condition'][0]
            
            hava_bilgisi = f"""
🌤️ **{sehir.upper()} Hava Durumu**

🌡️ **Sıcaklık:** {curr['temp_C']}°C
🌡️ **Hissedilen:** {curr['FeelsLikeC']}°C
💨 **Rüzgar:** {curr['windspeedKmph']} km/h
💧 **Nem:** {curr['humidity']}%
☁️ **Durum:** {curr['weatherDesc'][0]['value']}
            """
            return hava_bilgisi.strip(), f"{sehir} Hava"
        except:
            return f"📍 **{sehir} Hava Durumu**\n\nHava bilgisi alınamadı.", "Hava"
    
    # 3. WIKIPEDIA ARAMA
    try:
        wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        r_wiki = requests.get(wiki_api, headers=headers, timeout=timeout).json()
        if 'extract' in r_wiki:
            return f"📚 **Wikipedia:**\n\n{icerik_filtrele(r_wiki['extract'])}", sorgu.title()
    except:
        pass
    
    # 4. ÇOKLU SİTE TARAMA (10 site)
    def site_tara(url):
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Sadece ana içerik al
            metin = ""
            for tag in ['p', 'article', 'main', 'div.content', 'section']:
                elements = soup.find_all(tag, limit=3)
                for el in elements:
                    text = el.get_text().strip()
                    if len(text) > 100:
                        metin += text + " "
            
            filtreli = icerik_filtrele(metin[:500])
            if filtreli and len(filtreli) > 50:
                return filtreli
        except:
            pass
        return None
    
    # 10 farklı site (Türkçe içerikli)
    turkce_siteler = [
        f"https://www.google.com/search?q={urllib.parse.quote(sorgu+' nedir')}&hl=tr",
        f"https://www.bing.com/search?q={urllib.parse.quote(sorgu+' Türkçe')}",
        f"https://www.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}",
        f"https://www.bbc.com/turkce/search?q={urllib.parse.quote(sorgu)}",
        f"https://www.hurriyet.com.tr/arama/?q={urllib.parse.quote(sorgu)}",
        f"https://www.sozcu.com.tr/search/?q={urllib.parse.quote(sorgu)}",
        f"https://www.ntv.com.tr/arama?q={urllib.parse.quote(sorgu)}",
        f"https://tr.wikipedia.org/w/index.php?search={urllib.parse.quote(sorgu)}",
        f"https://www.sabah.com.tr/arama?q={urllib.parse.quote(sorgu)}",
        f"https://www.milliyet.com.tr/arama/?q={urllib.parse.quote(sorgu)}"
    ]
    
    # Paralel site tarama
    site_sonuclari = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_site = {executor.submit(site_tara, site): site for site in turkce_siteles[:5]}
        for future in concurrent.futures.as_completed(future_to_site):
            result = future.result()
            if result:
                site_sonuclari.append(result)
    
    if site_sonuclari:
        unique_results = []
        seen = set()
        for res in site_sonuclari:
            if res not in seen and len(res) > 50:
                seen.add(res)
                unique_results.append(res)
        
        if unique_results:
            combined = "\n\n---\n\n".join(unique_results[:3])
            return f"🌐 **Çoklu Kaynak Analizi:**\n\n{combined}", sorgu.title()
    
    # 5. SON ÇARE: BASIT BILGI
    return f"""
🤔 **"{sorgu}"** hakkında detaylı analiz:

**Analiz Sonucu:** Konu hakkında yeterli Türkçe kaynak bulunamadı.

**Öneriler:**
• Daha spesifik bir sorgu deneyin
• Türkçe karakterleri kullanın (ç, ğ, ı, ö, ş, ü)
• Anahtar kelimelerle arama yapın

**Örnek:** "Python programlama dili" yerine "Python nedir"
    """, sorgu.title()

# --- 🔑 GİRİŞ SİSTEMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI</h1></div>", unsafe_allow_html=True)
        st.markdown("<div class='ozel-not'>⚠️ Sayfayı yenileyince veya sayfayı kapatıp açtığınızda oturumunuz kapanır, şu an beta olduğu için çalışıyoruz.</div>", unsafe_allow_html=True)
        
        # TEMA DEĞİŞTİRME BUTONU
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("🌙 Karanlık Mod", use_container_width=True, 
                        type="primary" if st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = True
                st.rerun()
        with col_theme2:
            if st.button("☀️ Aydınlık Mod", use_container_width=True,
                        type="primary" if not st.session_state.dark_mode else "secondary"):
                st.session_state.dark_mode = False
                st.rerun()
        
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u_in = st.text_input("Kullanıcı Adı", key="l_u")
            p_in = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş Yap"):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): 
                    st.session_state.user = u_in
                    st.rerun()
                else: 
                    st.error("Hatalı bilgi.")
        with t2:
            nu = st.text_input("Yeni Kullanıcı", key="r_u")
            np = st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kaydoldun, giriş yap!")
                except: 
                    st.error("Bu isim dolu.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    
    # TEMA DEĞİŞTİRME
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("🌙", help="Karanlık Mod", use_container_width=True,
                    type="primary" if st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = True
            st.rerun()
    with theme_col2:
        if st.button("☀️", help="Aydınlık Mod", use_container_width=True,
                    type="primary" if not st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = False
            st.rerun()
    
    if st.button("🔴 Çıkış"): 
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # ANALIZ MODU (Basitleştirilmiş)
    st.markdown("### ⚡ Hızlı Sorgular")
    
    hizli_sorgular = [
        "784+8874",
        "İstanbul hava durumu",
        "Atatürk kimdir",
        "Python nedir",
        "15*3+7",
        "Ankara hava",
        "Türkiye başkenti"
    ]
    
    for idx, sorgu in enumerate(hizli_sorgular):
        # FİX: Her butona unique key (idx kullan)
        if st.button(sorgu[:25], key=f"quick_{idx}_{time.time()}", use_container_width=True):
            st.session_state.son_sorgu = sorgu
            st.rerun()
    
    st.divider()
    
    # GEÇMİŞ - FİX: Unique key'ler ile
    st.markdown("### 📜 Son Aramalar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    history_items = c.fetchall()
    
    for idx, (k, i) in enumerate(history_items):
        # FİX: Her butona unique key (timestamp + idx)
        button_key = f"hist_{idx}_{datetime.datetime.now().timestamp()}"
        if st.button(f"📌 {k[:20]}", key=button_key, use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## TürkAI Ultimate Analiz Terminali")
st.markdown("<div class='kullanim-notu'>🚀 <b>TEK MOTOR SİSTEMİ:</b> Matematik, Hava Durumu, Wikipedia ve 10 site analizi otomatik!</div>", unsafe_allow_html=True)

sorgu = st.chat_input("Neyi analiz edelim kanka? (Matematik, Hava, Genel)")

if sorgu:
    st.session_state.son_sorgu = sorgu
    
    with st.spinner("🔍 TürkAI analiz ediyor (10 site taranıyor)..."):
        # TEK MOTOR ANALIZ
        bilgi, konu = tek_motor_analiz(sorgu)
        st.session_state.bilgi = bilgi
        st.session_state.konu = konu
        
        # VERITABANINA KAYDET
        if st.session_state.bilgi:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), 
                      "Ultimate Motor"))
            conn.commit()
            st.rerun()

# --- 📊 GÖRÜNÜM VE PDF SİSTEMİ ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # --- 📄 PDF OLUŞTURMA MOTORU ---
    def pdf_yap():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="TurkAI Ultimate Analiz Raporu", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        
        # Türkçe karakter dönüşümü
        def temizle(t):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): 
                t = t.replace(k,v)
            return t

        metin = f"""
Kullanıcı: {temizle(st.session_state.user)}
Tarih: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
Konu: {temizle(st.session_state.konu)}
Sorgu: {temizle(st.session_state.son_sorgu)}

ANALİZ RAPORU:
{temizle(st.session_state.bilgi)}

---
TürkAI Ultimate v3.0 | Tek Motor Sistemi
        """
        
        pdf.multi_cell(0, 10, txt=metin.encode('latin-1', 'replace').decode('latin-1'))
        return pdf.output(dest='S').encode('latin-1')

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            "📄 Analizi PDF Olarak İndir", 
            data=pdf_yap(), 
            file_name=f"TurkAI_{st.session_state.konu[:30].replace(' ', '_')}.pdf", 
            mime="application/pdf",
            use_container_width=True
        )

# --- 📱 FOOTER ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"**Mod:** {'🌙 Karanlık' if st.session_state.dark_mode else '☀️ Aydınlık'}")
with col2:
    st.markdown("**Motor:** Ultimate v3.0")
with col3:
    st.markdown("**Durum:** Aktif ✅")

st.markdown("<div style='text-align: center; color: #666; margin-top: 30px;'>🚀 <b>TürkAI Ultimate</b> | Tek Motor Sistemi | 🇹🇷</div>", unsafe_allow_html=True)
