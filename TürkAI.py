import streamlit as st
import requests
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
import concurrent.futures
import time
from bs4 import BeautifulSoup
import json
import random

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 TEMA SİSTEMİ ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'user' not in st.session_state: 
    st.session_state.user = None
if 'bilgi' not in st.session_state: 
    st.session_state.bilgi = ""
if 'konu' not in st.session_state: 
    st.session_state.konu = ""
if 'son_sorgu' not in st.session_state: 
    st.session_state.son_sorgu = ""
if 'ses_efekti' not in st.session_state:
    st.session_state.ses_efekti = True
if 'animasyon' not in st.session_state:
    st.session_state.animasyon = True

def load_theme():
    if st.session_state.dark_mode:
        return """
        <style>
        .stApp { background-color: #0a0a0a; color: #f0f0f0; }
        h1, h2, h3 { color: #ff4d4d !important; font-weight: 800 !important; }
        .giris-kapsayici {
            background-color: #1a1a1a; border: 2px solid #cc0000; 
            border-radius: 20px; padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.3);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.3); }
            50% { box-shadow: 0px 4px 25px rgba(204, 0, 0, 0.6); }
            100% { box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.3); }
        }
        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #990000 100%);
            color: white !important; padding: 12px 18px; 
            border-radius: 15px 15px 0px 15px; margin: 15px 0 15px auto;
            max-width: 70%; box-shadow: 0px 4px 10px rgba(204, 0, 0, 0.4);
        }
        .ai-rapor-alani {
            border-left: 6px solid #cc0000; padding: 20px 25px;
            background-color: #1e1e1e; margin-bottom: 25px;
            border-radius: 0px 15px 15px 0px; color: #f0f0f0;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
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
            border-radius: 10px; border: 1px dashed #cc0000;
            font-size: 0.85rem; text-align: center;
        }
        .kullanim-notu {
            background-color: #1a1a1a; padding: 10px; border-radius: 10px;
            border-left: 5px solid #cc0000; font-size: 0.9rem;
            color: #cccccc;
        }
        .stTextInput > div > div > input {
            background-color: #2a2a2a !important; color: white !important;
            border: 1px solid #444 !important;
        }
        .stat-card {
            background: rgba(204, 0, 0, 0.1); border-radius: 15px;
            padding: 15px; margin: 10px 0; text-align: center;
            border: 1px solid rgba(204, 0, 0, 0.3);
        }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color: #ffffff; }
        h1, h2, h3 { color: #cc0000 !important; font-weight: 800 !important; }
        .giris-kapsayici {
            background-color: #fffafa; border: 2px solid #cc0000;
            border-radius: 20px; padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1); }
            50% { box-shadow: 0px 4px 25px rgba(204, 0, 0, 0.3); }
            100% { box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1); }
        }
        .user-msg {
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            color: #ffffff !important; padding: 12px 18px;
            border-radius: 15px 15px 0px 15px; margin: 15px 0 15px auto;
            max-width: 70%; box-shadow: 0px 4px 10px rgba(204, 0, 0, 0.2);
        }
        .ai-rapor-alani {
            border-left: 6px solid #cc0000; padding: 20px 25px;
            background-color: #fdfdfd; margin-bottom: 25px;
            border-radius: 0px 15px 15px 0px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.02);
        }
        [data-testid="stSidebar"] { 
            background-color: #f8f9fa; 
            border-right: 3px solid #cc0000;
        }
        div.stButton > button {
            background-color: #cc0000 !important; color: white !important;
            border-radius: 10px !important; font-weight: bold !important;
        }
        .ozel-not {
            background-color: #fff3f3; color: #cc0000; padding: 10px; 
            border-radius: 10px; border: 1px dashed #cc0000;
            font-size: 0.85rem; text-align: center;
        }
        .kullanim-notu {
            background-color: #f0f2f6; padding: 10px; border-radius: 10px;
            border-left: 5px solid #cc0000; font-size: 0.9rem;
        }
        .stat-card {
            background: rgba(204, 0, 0, 0.05); border-radius: 15px;
            padding: 15px; margin: 10px 0; text-align: center;
            border: 1px solid rgba(204, 0, 0, 0.2);
        }
        </style>
        """

# Temayı yükle
st.markdown(load_theme(), unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, created DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS istatistik (kullanici TEXT, sorgu_sayisi INTEGER, son_aktivite DATE)')
    
    demo_pass = hashlib.sha256("demo123".encode()).hexdigest()
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ("demo", demo_pass, datetime.datetime.now().strftime("%Y-%m-%d")))
    except:
        pass
    
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🎮 YENİ ÖZELLİKLER ---
def get_doviz_kuru():
    """Döviz kurlarını al"""
    try:
        url = "https://api.genelpara.com/embed/para-birimleri.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"""
💵 **Döviz Kurları:**
• **USD/TRY:** {data.get('USD', {}).get('satis', 'N/A')} ₺
• **EUR/TRY:** {data.get('EUR', {}).get('satis', 'N/A')} ₺
• **GBP/TRY:** {data.get('GBP', {}).get('satis', 'N/A')} ₺
• **Altın:** {data.get('GA', {}).get('satis', 'N/A')} ₺
⏱️ *{datetime.datetime.now().strftime("%H:%M")}*
"""
    except:
        return "💵 **Döviz Kurları:**\nVeri alınamadı. Lütfen daha sonra tekrar deneyin."

def get_hava_tahmini(sehir, gun=1):
    """5 günlük hava tahmini"""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(sehir)}?format=j1"
        response = requests.get(url, timeout=8)
        data = response.json()
        
        if gun == 1:
            current = data['current_condition'][0]
            return f"""
🌤️ **{sehir.upper()} Bugün**
🌡️ **Sıcaklık:** {current['temp_C']}°C
💨 **Rüzgar:** {current['windspeedKmph']} km/h
💧 **Nem:** {current['humidity']}%
☁️ **Durum:** {current['weatherDesc'][0]['value']}
"""
        else:
            tahminler = []
            for i in range(min(gun, 3)):
                day = data['weather'][i]
                tahminler.append(f"**{day['date']}:** {day['mintempC']}°C - {day['maxtempC']}°C, {day['hourly'][0]['weatherDesc'][0]['value']}")
            
            return f"📅 **{sehir.upper()} {gun} Günlük Tahmin:**\n" + "\n".join(tahminler)
    except:
        return f"📍 **{sehir} Hava Tahmini**\n\nVeri alınamadı."

def get_random_bilgi():
    """Rastgele ilginç bilgi"""
    bilgiler = [
        "🎯 **İlginç Bilgi:** Dünyada her gün 8.6 milyon kez yıldırım düşüyor.",
        "🧠 **Beyin:** İnsan beyni günde ortalama 70.000 düşünce üretir.",
        "🌍 **Coğrafya:** Dünyanın en derin noktası Mariana Çukuru (10.994 metre).",
        "⚡ **Teknoloji:** İlk bilgisayar virüsü 1971'de yazıldı.",
        "🇹🇷 **Türkiye:** İstanbul, iki kıtada toprağı olan tek şehirdir.",
        "🐬 **Hayvanlar:** Yunuslar uyurken beyninin bir yarısı uyanık kalır.",
        "🍫 **Yiyecek:** Çikolata köpekler için zehirlidir.",
        "📱 **Telefon:** İlk cep telefonu araması 1973'te yapıldı."
    ]
    return random.choice(bilgiler)

def get_covid_veri():
    """COVID-19 verileri"""
    try:
        url = "https://api.covid19api.com/summary"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        turkiye = None
        for country in data['Countries']:
            if country['Country'] == 'Turkey':
                turkiye = country
                break
        
        if turkiye:
            return f"""
🦠 **COVID-19 Türkiye:**
• **Toplam Vaka:** {turkiye['TotalConfirmed']:,}
• **Yeni Vaka:** {turkiye['NewConfirmed']:,}
• **Toplam Ölüm:** {turkiye['TotalDeaths']:,}
• **Yeni Ölüm:** {turkiye['NewDeaths']:,}
• **İyileşen:** {turkiye['TotalRecovered']:,}
⏱️ *{datetime.datetime.now().strftime("%d.%m.%Y")}*
"""
    except:
        pass
    return "🦠 **COVID-19 Verileri:**\nVeri alınamadı."

# --- 🌤️ HAVA DURUMU ---
def hava_durumu_getir(sehir_adi):
    gercek_sehirler = {
        'istanbul': 'İstanbul', 'ankara': 'Ankara', 'izmir': 'İzmir',
        'bursa': 'Bursa', 'antalya': 'Antalya', 'adana': 'Adana',
        'konya': 'Konya', 'mersin': 'Mersin', 'samsun': 'Samsun',
        'trabzon': 'Trabzon', 'erzurum': 'Erzurum', 'diyarbakır': 'Diyarbakır',
        'gaziantep': 'Gaziantep', 'eskişehir': 'Eskişehir', 'kayseri': 'Kayseri',
        'denizli': 'Denizli', 'muğla': 'Muğla', 'hatay': 'Hatay',
        'sakarya': 'Sakarya', 'balıkesir': 'Balıkesir', 'van': 'Van',
        'malatya': 'Malatya', 'elazığ': 'Elazığ', 'sivas': 'Sivas'
    }
    
    sehir_lower = sehir_adi.lower()
    if sehir_lower not in gercek_sehirler:
        sehir_listesi = "\n".join([f"• {s}" for s in gercek_sehirler.values()])
        return f"⚠️ **'{sehir_adi}' geçerli bir şehir değil.**\n\n**Desteklenen Şehirler:**\n{sehir_listesi}"
    
    sehir = gercek_sehirler[sehir_lower]
    
    try:
        url = f"https://wttr.in/{urllib.parse.quote(sehir)}?format=j1&lang=tr"
        response = requests.get(url, timeout=8)
        data = response.json()
        current = data['current_condition'][0]
        
        return f"""
🌤️ **{sehir.upper()} Hava Durumu**

🌡️ **Sıcaklık:** {current['temp_C']}°C
🌡️ **Hissedilen:** {current['FeelsLikeC']}°C
💨 **Rüzgar:** {current['windspeedKmph']} km/h
💧 **Nem:** {current['humidity']}%
☁️ **Durum:** {current['weatherDesc'][0]['value']}

⏱️ *{datetime.datetime.now().strftime("%H:%M")} güncellendi*
"""
    except:
        return f"📍 **{sehir} Hava Durumu**\n\nVeri alınamadı."

# --- 🔍 ANA MOTOR ---
def tek_motor_analiz(sorgu):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. MATEMATİK
    temiz_sorgu = sorgu.replace(' ', '')
    if re.match(r'^[\d+\-*/().xX]+$', temiz_sorgu):
        try:
            expr = sorgu.replace('x', '*').replace('X', '*').replace(',', '.')
            res = eval(expr, {"__builtins__": {}}, {})
            return f"🧮 **Matematik Sonucu:**\n\n`{sorgu} = {res}`", "Matematik"
        except:
            return "⚠️ Matematik ifadesi çözülemedi.", "Hata"
    
    # 2. ÖZEL KOMUTLAR
    sorgu_lower = sorgu.lower()
    
    if sorgu_lower == "döviz" or "dolar" in sorgu_lower or "euro" in sorgu_lower:
        return get_doviz_kuru(), "Döviz Kuru"
    
    if sorgu_lower == "covid" or "korona" in sorgu_lower:
        return get_covid_veri(), "COVID-19"
    
    if sorgu_lower == "bilgi" or "ilginç" in sorgu_lower:
        return get_random_bilgi(), "İlginç Bilgi"
    
    # 3. HAVA DURUMU
    hava_kelimeler = ['hava', 'durumu', 'sıcaklık', 'yağmur', 'kar', 'rüzgar']
    if any(kelime in sorgu_lower for kelime in hava_kelimeler):
        sehir = "İstanbul"
        for s in ['istanbul', 'ankara', 'izmir', 'antalya', 'bursa']:
            if s in sorgu_lower:
                sehir = s.title()
                break
        
        if 'tahmin' in sorgu_lower or 'yarın' in sorgu_lower:
            gun = 2 if 'yarın' in sorgu_lower else 3
            return get_hava_tahmini(sehir, gun), f"{sehir} Tahmin"
        
        return hava_durumu_getir(sehir), f"{sehir} Hava"
    
    # 4. WIKIPEDIA
    try:
        wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        r_wiki = requests.get(wiki_api, headers=headers, timeout=8).json()
        if 'extract' in r_wiki and r_wiki['extract']:
            return f"📚 **Wikipedia:**\n\n{r_wiki['extract'][:500]}...", sorgu.title()
    except:
        pass
    
    # 5. GOOGLE ARAMA
    try:
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(sorgu + ' nedir')}&hl=tr"
        response = requests.get(google_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', {'class': 'VwiC3b'})
            if results:
                text = results[0].get_text()[:300]
                return f"🔍 **Google Arama:**\n\n{text}...", sorgu.title()
    except:
        pass
    
    # 6. SON ÇARE
    return f"""
🤔 **"{sorgu}"** hakkında analiz:

**Durum:** Detaylı bilgi bulunamadı.

**Öneriler:**
• "döviz" → Döviz kurları
• "covid" → COVID-19 verileri  
• "bilgi" → İlginç bilgiler
• "İstanbul hava" → Hava durumu
• "784+8874" → Matematik işlemi
• "Atatürk" → Wikipedia bilgisi
""", sorgu.title()

# --- 🔑 GİRİŞ SİSTEMİ ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI v4.0</h1><p>Ultimate Intelligence System</p></div>", unsafe_allow_html=True)
        
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("🌙 Karanlık", use_container_width=True):
                st.session_state.dark_mode = True
                st.rerun()
        with col_theme2:
            if st.button("☀️ Aydınlık", use_container_width=True):
                st.session_state.dark_mode = False
                st.rerun()
        
        tab1, tab2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with tab1:
            u_in = st.text_input("Kullanıcı Adı")
            p_in = st.text_input("Şifre", type="password")
            if st.button("🚀 Giriş Yap", use_container_width=True):
                if u_in and p_in:
                    h_p = hashlib.sha256(p_in.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                    if c.fetchone(): 
                        st.session_state.user = u_in
                        st.rerun()
        with tab2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("✨ Kayıt Ol", use_container_width=True):
                if nu and np:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashlib.sha256(np.encode()).hexdigest(), datetime.datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.session_state.user = nu
                    st.rerun()
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    
    # İSTATİSTİK
    c.execute("SELECT COUNT(*) FROM aramalar WHERE kullanici=?", (st.session_state.user,))
    sorgu_sayisi = c.fetchone()[0]
    
    st.markdown(f"""
    <div class='stat-card'>
        <strong>📊 İstatistikler</strong><br>
        🔢 Sorgu: {sorgu_sayisi}<br>
        🎯 Başarı: %{min(95, sorgu_sayisi * 10)}<br>
        ⭐ Seviye: {min(10, sorgu_sayisi // 5)}
    </div>
    """, unsafe_allow_html=True)
    
    # AYARLAR
    with st.expander("⚙️ Ayarlar"):
        ses = st.checkbox("🔊 Ses Efektleri", value=st.session_state.ses_efekti)
        if ses != st.session_state.ses_efekti:
            st.session_state.ses_efekti = ses
            
        anim = st.checkbox("✨ Animasyonlar", value=st.session_state.animasyon)
        if anim != st.session_state.animasyon:
            st.session_state.animasyon = anim
    
    st.divider()
    
    # HIZLI ERİŞİM
    st.markdown("### ⚡ Hızlı Erişim")
    
    quick_actions = [
        ("💰 Döviz Kuru", "döviz"),
        ("🦠 COVID Veri", "covid"),
        ("🎲 İlginç Bilgi", "bilgi"),
        ("🧮 Hesapla", "784+8874"),
        ("🌤️ İstanbul Hava", "İstanbul hava"),
        ("📍 Ankara Hava", "Ankara hava"),
        ("📖 Atatürk", "Atatürk"),
        ("💻 Python", "Python")
    ]
    
    for label, cmd in quick_actions:
        if st.button(label, key=f"qa_{cmd}", use_container_width=True):
            st.session_state.son_sorgu = cmd
            st.rerun()
    
    st.divider()
    
    # GEÇMİŞ
    st.markdown("### 📜 Geçmiş")
    c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,))
    for idx, (k,) in enumerate(c.fetchall()):
        if st.button(f"📌 {k[:20]}", key=f"h_{idx}", use_container_width=True):
            c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1", (st.session_state.user, k))
            i = c.fetchone()
            if i:
                st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i[0], k, k
                st.rerun()

# --- 💻 ANA EKRAN ---
st.markdown("## 🚀 TürkAI Ultimate v4.0")
st.markdown("<div class='kullanim-notu'>🎯 <b>YENİ:</b> Döviz, COVID verisi, ilginç bilgiler ve daha fazlası!</div>", unsafe_allow_html=True)

# HIZLI BİLGİ KARTLARI
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💰 Döviz", use_container_width=True):
        st.session_state.son_sorgu = "döviz"
        st.rerun()
with col2:
    if st.button("🌤️ Hava", use_container_width=True):
        st.session_state.son_sorgu = "İstanbul hava"
        st.rerun()
with col3:
    if st.button("🦠 COVID", use_container_width=True):
        st.session_state.son_sorgu = "covid"
        st.rerun()
with col4:
    if st.button("🎲 Bilgi", use_container_width=True):
        st.session_state.son_sorgu = "bilgi"
        st.rerun()

sorgu = st.chat_input("💭 TürkAI'ye sor...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    
    with st.spinner("🤖 Analiz ediliyor..."):
        bilgi, konu = tek_motor_analiz(sorgu)
        st.session_state.bilgi = bilgi
        st.session_state.konu = konu
        
        c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih, motor) VALUES (?,?,?,?,?)", 
                 (st.session_state.user, konu, bilgi[:1500], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Ultimate"))
        conn.commit()
        
        # İstatistik güncelle
        c.execute("SELECT sorgu_sayisi FROM istatistik WHERE kullanici=?", (st.session_state.user,))
        stat = c.fetchone()
        if stat:
            c.execute("UPDATE istatistik SET sorgu_sayisi=?, son_aktivite=? WHERE kullanici=?", 
                     (stat[0] + 1, datetime.datetime.now().strftime("%Y-%m-%d"), st.session_state.user))
        else:
            c.execute("INSERT INTO istatistik VALUES (?,?,?)", 
                     (st.session_state.user, 1, datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        
        st.rerun()

# --- 📊 SONUÇLAR ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>👤 {st.session_state.user}:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # PDF
    def pdf_yap():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="TurkAI Raporu", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        
        def temizle(t):
            d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
            for k,v in d.items(): t = t.replace(k, v)
            return t
        
        pdf.multi_cell(0, 10, txt=temizle(f"""
Kullanıcı: {st.session_state.user}
Tarih: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
Konu: {st.session_state.konu}
Sorgu: {st.session_state.son_sorgu}

{st.session_state.bilgi}
"""))
        return pdf.output(dest='S').encode('latin-1')
    
    st.download_button("📄 PDF İndir", pdf_yap(), f"TurkAI_{st.session_state.konu[:20]}.pdf", "application/pdf")

# --- 📱 FOOTER ---
st.markdown("---")
cols = st.columns(4)
with cols[0]:
    st.markdown(f"**Tema:** {'🌙 Karanlık' if st.session_state.dark_mode else '☀️ Aydınlık'}")
with cols[1]:
    st.markdown("**Versiyon:** 4.0 Ultimate")
with cols[2]:
    st.markdown(f"**Sorgu:** {sorgu_sayisi}")
with cols[3]:
    st.markdown("**Durum:** 🟢 Aktif")

st.markdown("""
<div style='text-align: center; color: #666; margin-top: 20px;'>
    🚀 <b>TürkAI Ultimate v4.0</b> | Döviz • COVID • Hava • Bilgi | 🇹🇷
</div>
""", unsafe_allow_html=True)
