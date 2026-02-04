import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
from duckduckgo_search import DDGS
import concurrent.futures # Aynı anda 25 siteye saldırmak için

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 💾 SESSİON (HAFIZA) AYARLARI ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "tema" not in st.session_state: st.session_state.tema = "light" # Varsayılan Aydınlık

# --- 🎨 DİNAMİK CSS (DARK/LIGHT MOD) ---
def css_yukle():
    ana_renk = "#cc0000"
    if st.session_state.tema == "dark":
        bg_color = "#121212"
        text_color = "#ffffff"
        card_bg = "#1e1e1e"
        input_bg = "#2d2d2d"
    else:
        bg_color = "#ffffff"
        text_color = "#000000"
        card_bg = "#fffafa"
        input_bg = "#ffffff"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        h1, h2, h3, h4 {{ color: {ana_renk} !important; font-weight: 800 !important; }}
        p, label, .stMarkdown {{ color: {text_color} !important; }}
        
        /* Giriş Kutusu */
        .giris-kapsayici {{
            background-color: {card_bg};
            border: 2px solid {ana_renk}; border-radius: 20px;
            padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.1);
        }}
        
        /* Mesaj Kutuları */
        .user-msg {{
            background: linear-gradient(135deg, #cc0000 0%, #ff4d4d 100%);
            color: white !important; padding: 12px 18px; 
            border-radius: 15px 15px 0px 15px; margin-bottom: 20px; 
            width: fit-content; max-width: 70%; margin-left: auto;
        }}
        .user-msg b {{ color: white !important; }}
        
        .ai-rapor-alani {{
            border-left: 6px solid {ana_renk}; padding: 20px 25px;
            background-color: {card_bg}; margin-bottom: 25px;
            border-radius: 0px 15px 15px 0px; color: {text_color};
        }}

        /* Sidebar ve Butonlar */
        [data-testid="stSidebar"] {{ background-color: {card_bg}; border-right: 3px solid {ana_renk}; }}
        div.stButton > button {{
            background-color: {ana_renk} !important; color: white !important;
            border-radius: 10px !important; font-weight: bold !important;
            border: none;
        }}
        
        /* Hava Durumu Kartı */
        .hava-kart {{
            background-color: {input_bg}; border: 1px solid {ana_renk};
            border-radius: 10px; padding: 10px; text-align: center;
            margin-bottom: 20px; font-size: 0.9rem;
        }}
        </style>
    """, unsafe_allow_html=True)

css_yukle()

# --- 💾 VERİTABANI ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect('turkai_v30.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    return conn

conn = get_db()
c = conn.cursor()

# --- 🛡️ TEMİZLİK ROBOTU ---
def temizle(text):
    if not text: return ""
    # İngilizce reklamları temizle
    copler = ["Sign In", "Login", "Subscribe", "Cookies", "Password", "Username"]
    for cop in copler: text = text.replace(cop, "")
    # Türkçe harfleri koru, gerisini sil
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/%@=]', '', str(text))

# --- 🔍 MOTOR 1: HIZLI MOTOR (TURBO) ---
def hizli_motor(sorgu):
    try:
        with DDGS() as ddgs:
            # 5 saniye limitli, az sonuç
            results = list(ddgs.text(f"{sorgu} nedir özet", region='tr-tr', max_results=2))
            metin = "\n".join([f"🚀 {r['body']}" for r in results])
            return metin if metin else "Hızlı arama sonuç vermedi."
    except: return "Hızlı motor bağlantı hatası."

# --- 🧠 MOTOR 2: DERİN DÜŞÜNEN (DEEP THINK) ---
def siteyi_oku(url):
    try:
        # 7 Saniye süre veriyoruz her siteye
        h = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=h, timeout=7)
        soup = BeautifulSoup(r.text, 'html.parser')
        p_ler = soup.find_all('p')
        # Sadece dolu paragrafları al
        return " ".join([p.get_text() for p in p_ler if len(p.get_text()) > 50][:3])
    except:
        return ""

def derin_motor(sorgu):
    try:
        bilgi_havuzu = []
        # Önce Wikipedia
        url_wiki = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        try:
            r = requests.get(url_wiki, timeout=5).json()
            if 'extract' in r: bilgi_havuzu.append(f"📖 WIKIPEDIA: {r['extract']}")
        except: pass

        # Sonra DuckDuckGo'dan 10 link alıp içine giriyoruz
        with DDGS() as ddgs:
            linkler = [r['href'] for r in ddgs.text(f"{sorgu} detaylı bilgi", region='tr-tr', max_results=8)]
        
        # AYNI ANDA (Paralel) sitelere saldırıyoruz
        with concurrent.futures.ThreadPoolExecutor() as executor:
            icerikler = list(executor.map(siteyi_oku, linkler))
        
        for icerik in icerikler:
            if icerik: bilgi_havuzu.append(f"🔹 {temizle(icerik[:300])}...")
            
        return "\n\n".join(bilgi_havuzu) if bilgi_havuzu else "Derin aramada veri bulunamadı."
    except Exception as e: return f"Derin motor hatası: {str(e)}"

# --- 🔑 GİRİŞ EKRANI ---
if not st.session_state.user:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI v3.0</h1></div>", unsafe_allow_html=True)
        
        misafir = st.button("👤 Misafir Olarak Gir (Kayıtsız)", use_container_width=True)
        if misafir:
            st.session_state.user = "Misafir"
            st.rerun()
            
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u, p = st.text_input("Kullanıcı Adı", key="li_u"), st.text_input("Şifre", type="password", key="li_p")
            if st.button("Giriş Yap", key="btn_giris"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                if c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone():
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı!")
        with t2:
            nu, np = st.text_input("Yeni Ad", key="re_u"), st.text_input("Yeni Şifre", type="password", key="re_p")
            if st.button("Kaydol", key="btn_kayit"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Tamamdır!")
                except: st.error("İsim dolu.")
    st.stop()

# --- 🚀 PANEL VE SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    
    # 🌗 Tema Değiştirici
    c1, c2 = st.columns(2)
    with c1:
        if st.button("☀️"): st.session_state.tema = "light"; st.rerun()
    with c2:
        if st.button("🌙"): st.session_state.tema = "dark"; st.rerun()
        
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    
    st.divider()
    
    # 🌦️ 81 İL HAVA DURUMU
    st.markdown("### 🌦️ Hava Durumu")
    iller = ["Adana", "Adiyaman", "Afyon", "Agri", "Amasya", "Ankara", "Antalya", "Artvin", "Aydin", "Balikesir", "Bilecik", "Bingol", "Bitlis", "Bolu", "Burdur", "Bursa", "Canakkale", "Cankiri", "Corum", "Denizli", "Diyarbakir", "Edirne", "Elazig", "Erzincan", "Erzurum", "Eskisehir", "Gaziantep", "Giresun", "Gumushane", "Hakkari", "Hatay", "Isparta", "Mersin", "Istanbul", "Izmir", "Kars", "Kastamonu", "Kayseri", "Kirklareli", "Kirsehir", "Kocaeli", "Konya", "Kutahya", "Malatya", "Manisa", "Kahramanmaras", "Mardin", "Mugla", "Mus", "Nevsehir", "Nigde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdag", "Tokat", "Trabzon", "Tunceli", "Sanliurfa", "Usak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kirikkale", "Batman", "Sirnak", "Bartin", "Ardahan", "Igdir", "Yalova", "Karabuk", "Kilis", "Osmaniye", "Duzce"]
    secilen_il = st.selectbox("İl Seç:", iller)
    
    try:
        # Hava durumu için minik API
        w = requests.get(f"https://wttr.in/{secilen_il}?format=j1", timeout=3).json()['current_condition'][0]
        st.markdown(f"""
        <div class='hava-kart'>
            <b>📍 {secilen_il}</b><br>
            🌡️ {w['temp_C']}°C | 💧 %{w['humidity']}<br>
            ☁️ {w['lang_tr'][0]['value']}
        </div>
        """, unsafe_allow_html=True)
    except: st.write("Hava verisi alınamadı.")

    st.divider()
    st.markdown("### 📌 Geçmiş")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,)).fetchall()
    for idx, (k, i) in enumerate(gecmis):
        if st.button(f"📄 {k[:15]}", key=f"hist_{idx}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 ÇALIŞMA ALANI ---
st.markdown("## 🇹🇷 TürkAI İstihbarat Terminali")

# Motor Seçimi
motor_tipi = st.radio("Motor Gücü:", ["🏎️ Hızlı Motor (5sn)", "🧠 Derin Düşünen (Detaylı)"], horizontal=True)

sorgu = st.chat_input("Hedef konuyu gir komutanım...")

# Fonksiyon: Analizi Başlat
def analizi_yap(gelen_sorgu, motor):
    with st.spinner('🚀 TürkAI Veri Akışını Tarıyor...'):
        if motor == "🏎️ Hızlı Motor (5sn)":
            sonuc = hizli_motor(gelen_sorgu)
        else:
            sonuc = derin_motor(gelen_sorgu)
        return sonuc

# Eğer yeni sorgu varsa veya "Yeniden Yap" butonuna basıldıysa
if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.konu = sorgu.title()
    st.session_state.bilgi = analizi_yap(sorgu, motor_tipi)
    
    # Kaydet
    if st.session_state.user != "Misafir":
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                  (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), motor_tipi))
        conn.commit()

# --- 📊 SONUÇ EKRANI ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz Raporu: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        # PDF İndir
        def pdf_yap():
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", size=11)
            def tr_font(x):
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): x = x.replace(k,v)
                return re.sub(r'[^\x00-\x7F]+', '', x)
            pdf.multi_cell(0, 10, txt=tr_font(f"RAPOR: {st.session_state.konu}\n\n{st.session_state.bilgi}").encode('latin-1','ignore').decode('latin-1'))
            return pdf.output(dest='S').encode('latin-1')
        st.download_button("📄 PDF İndir", data=pdf_yap(), file_name="Rapor.pdf", use_container_width=True)
    
    with c2:
        # Beğenmedim Butonu (Regenerate)
        if st.button("🔄 Beğenmedim, Derin Analiz Yap", use_container_width=True):
            st.session_state.bilgi = analizi_yap(st.session_state.son_sorgu, "🧠 Derin Düşünen (Detaylı)")
            st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; opacity: 0.5;'>🚀 Powered by Madara | v3.0 Ultimate</p>", unsafe_allow_html=True)
