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
import concurrent.futures

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 💾 SESSİON YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "tema" not in st.session_state: st.session_state.tema = "light"

# --- 🎨 GELİŞMİŞ CSS (KARANLIK MOD TAMİRİ) ---
def css_uygula():
    # Renk Paleti
    ana_renk = "#cc0000"
    if st.session_state.tema == "dark":
        bg_main = "#0e1117"     # Tam siyah arka plan
        bg_sec = "#262730"      # Sidebar arka planı
        text_c = "#ffffff"      # Beyaz yazı
        input_bg = "#333333"    # Kutucuk içi
        card_bg = "#1e1e1e"     # Kartlar
    else:
        bg_main = "#ffffff"
        bg_sec = "#f8f9fa"
        text_c = "#000000"
        input_bg = "#ffffff"
        card_bg = "#fffafa"

    st.markdown(f"""
        <style>
        /* GENEL SAYFA YAPISI */
        .stApp {{ background-color: {bg_main} !important; color: {text_c} !important; }}
        
        /* YAZILAR */
        h1, h2, h3, h4, h5, h6 {{ color: {ana_renk} !important; font-weight: 800 !important; }}
        p, span, label, div {{ color: {text_c}; }}
        
        /* GİRİŞ KUTULARI (Input) */
        .stTextInput input, .stTextArea textarea {{
            background-color: {input_bg} !important; 
            color: {text_c} !important; 
            border: 1px solid {ana_renk};
        }}
        
        /* SIDEBAR (Yan Panel) */
        [data-testid="stSidebar"] {{ background-color: {bg_sec} !important; border-right: 2px solid {ana_renk}; }}
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{ color: {text_c} !important; }}
        
        /* GİRİŞ KARTI */
        .giris-kapsayici {{
            background-color: {card_bg};
            border: 2px solid {ana_renk}; border-radius: 20px;
            padding: 30px; text-align: center;
            box-shadow: 0px 4px 15px rgba(204, 0, 0, 0.2);
        }}
        
        /* BUTONLAR */
        div.stButton > button {{
            background-color: {ana_renk} !important; color: white !important;
            border-radius: 8px !important; font-weight: bold !important;
            border: none;
        }}
        
        /* MESAJ KUTUSU */
        .ai-rapor-alani {{
            border-left: 5px solid {ana_renk}; padding: 20px;
            background-color: {card_bg}; border-radius: 0 10px 10px 0;
            color: {text_c} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

css_uygula()

# --- 💾 VERİTABANI ---
@st.cache_resource
def get_db():
    conn = sqlite3.connect('turkai_pro_v35.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    return conn
conn = get_db()
c = conn.cursor()

# --- 🛡️ FİLTRE MOTORU (İngilizce Engelleyici) ---
def cop_temizle(text):
    if not text: return ""
    # Yabancı emlak/reklam kelimeleri
    yasakli = ["Apartment", "Rent", "Bedroom", "Studio", "listings", "View detailed", "Search", "Sign In", "Login"]
    for y in yasakli:
        if y in text: return "" # Yasaklı kelime varsa o cümleyi direkt sil
    
    # Sadece Türkçe karakterleri ve temel noktalama işaretlerini tut
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/%@=]', '', str(text))

# --- 🔍 ARAMA MOTORLARI ---

def hizli_motor(sorgu):
    """DuckDuckGo ile Türkçe sitelerden özet çeker"""
    try:
        with DDGS() as ddgs:
            # "sorgu + nedir" diyerek sözlük/bilgi sitelerini hedefliyoruz
            results = list(ddgs.text(f"{sorgu} nedir bilgi", region='tr-tr', max_results=3))
            if not results: return "Türkçe kaynak bulunamadı."
            
            metin = ""
            for r in results:
                temiz_body = cop_temizle(r['body'])
                if len(temiz_body) > 20: # Kısa ve boş şeyleri alma
                    metin += f"📌 {r['title']}:\n{temiz_body}\n\n"
            return metin if metin else "İşe yarar Türkçe veri bulunamadı."
    except: return "Hızlı motor bağlantı hatası."

def siteyi_cek(url):
    """Derin motor için site okuyucu"""
    try:
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=h, timeout=4)
        if r.status_code != 200: return ""
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece p etiketlerini al, kısa olanları at
        paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
        return " ".join(paragraflar[:2]) # İlk 2 uzun paragrafı al
    except: return ""

def derin_motor(sorgu):
    """Hem Wiki hem Web'i aynı anda tarar"""
    try:
        havuz = []
        # 1. Wikipedia Özeti
        try:
            wiki_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
            w = requests.get(wiki_url, timeout=3).json()
            if 'extract' in w: havuz.append(f"📖 WIKIPEDIA:\n{w['extract']}")
        except: pass

        # 2. DuckDuckGo Linkleri (Sadece TR)
        linkler = []
        with DDGS() as ddgs:
            # "haber", "kimdir", "nedir" ekleyerek ticari sitelerden kaçıyoruz
            for r in ddgs.text(f"{sorgu} hakkında bilgi", region='tr-tr', max_results=6):
                if "sahibinden" not in r['href'] and "trendyol" not in r['href']: # Alışveriş sitelerini engelle
                    linkler.append(r['href'])

        # 3. Paralel Tarama (Aynı anda 6 siteye girer)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            sonuclar = list(executor.map(siteyi_cek, linkler))
        
        for s in sonuclar:
            temiz = cop_temizle(s)
            if len(temiz) > 50: havuz.append(f"🌍 WEB BİLGİSİ:\n{temiz}...")

        return "\n\n".join(havuz) if havuz else "Derin aramada veri çıkmadı."
    except Exception as e: return f"Sistem hatası: {str(e)}"

# --- 🔑 GİRİŞ / KAYIT ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>🇹🇷 TürkAI v3.5</h1></div>", unsafe_allow_html=True)
        st.write("")
        if st.button("🚀 Misafir Girişi", use_container_width=True):
            st.session_state.user = "Misafir"
            st.rerun()
            
        tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
        with tab1:
            u = st.text_input("Kullanıcı Adı", key="giris_u")
            p = st.text_input("Şifre", type="password", key="giris_p")
            if st.button("Giriş Yap"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                if c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp)).fetchone():
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı bilgi.")
        with tab2:
            nu = st.text_input("Yeni Ad", key="kayit_u")
            np = st.text_input("Yeni Şifre", type="password", key="kayit_p")
            if st.button("Kayıt Ol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Oldu! Şimdi giriş yap.")
                except: st.error("Bu isim alınmış.")
    st.stop()

# --- 🛸 ANA EKRAN ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    
    # Karanlık Mod Switch
    col_a, col_b = st.columns(2)
    if col_a.button("☀️"): st.session_state.tema = "light"; st.rerun()
    if col_b.button("🌙"): st.session_state.tema = "dark"; st.rerun()

    if st.button("Çıkış Yap"): st.session_state.clear(); st.rerun()
    st.divider()
    
    # 81 İl Hava Durumu
    st.markdown("### 🌦️ Hava Durumu")
    sehirler = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Sanliurfa", "Kocaeli", "Mersin", "Diyarbakir", "Hatay", "Manisa", "Kayseri", "Samsun", "Balikesir", "Kahramanmaras", "Van", "Aydin", "Tekirdag", "Sakarya", "Denizli", "Mugla", "Eskisehir", "Mardin", "Trabzon", "Malatya", "Erzurum", "Ordu"]
    sec_il = st.selectbox("İl Seçiniz:", sehirler)
    try:
        w = requests.get(f"https://wttr.in/{sec_il}?format=j1", timeout=2).json()['current_condition'][0]
        st.info(f"{sec_il}: {w['temp_C']}°C | {w['lang_tr'][0]['value']}")
    except: st.error("Hava verisi yok.")

    st.divider()
    st.write("📜 Geçmiş Aramalar")
    gecmis = c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", (st.session_state.user,)).fetchall()
    for idx, (k, i) in enumerate(gecmis):
        if st.button(f"🔎 {k[:15]}", key=f"hist_{idx}"):
            st.session_state.bilgi = i; st.session_state.konu = k; st.session_state.son_sorgu = k
            st.rerun()

# --- 💬 SOHBET ALANI ---
st.markdown("## 🇹🇷 TürkAI İstihbarat Masası")

# Arama Motoru Seçimi
motor = st.radio("Tarama Modu:", ["🏎️ Hızlı (Özet)", "🧠 Derin (Detaylı)"], horizontal=True)
sorgu = st.chat_input("Araştırma konusu girin...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.konu = sorgu.title()
    
    with st.spinner("🕵️‍♂️ TürkAI verileri analiz ediyor..."):
        if motor == "🏎️ Hızlı (Özet)":
            st.session_state.bilgi = hizli_motor(sorgu)
        else:
            st.session_state.bilgi = derin_motor(sorgu)
            
    # Kayıt
    if st.session_state.user != "Misafir":
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                  (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), motor))
        conn.commit()
    st.rerun()

# --- 📊 SONUÇ VE PDF ---
if st.session_state.bilgi:
    st.markdown(f"<div class='ai-rapor-alani'><h3>📌 {st.session_state.konu}</h3>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    # PDF OLUŞTURUCU (Tamir Edildi)
    def pdf_uret():
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Türkçe karakterleri İngilizce karşılıklarına çevir (PDF patlamasın diye)
            tr_map = {'İ':'I', 'ı':'i', 'Ş':'S', 'ş':'s', 'Ğ':'G', 'ğ':'g', 'Ü':'U', 'ü':'u', 'Ö':'O', 'ö':'o', 'Ç':'C', 'ç':'c'}
            
            baslik = st.session_state.konu
            icerik = st.session_state.bilgi
            
            for k, v in tr_map.items():
                baslik = baslik.replace(k, v)
                icerik = icerik.replace(k, v)
            
            # Desteklenmeyen tüm karakterleri temizle (Emoji vs.)
            baslik = re.sub(r'[^\x00-\x7F]+', '', baslik)
            icerik = re.sub(r'[^\x00-\x7F]+', '', icerik)
            
            pdf.cell(0, 10, txt=f"RAPOR: {baslik}", ln=True, align='C')
            pdf.ln(10)
            pdf.multi_cell(0, 10, txt=icerik)
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e:
            return f"Hata: {str(e)}".encode()

    with c1:
        st.download_button("📥 PDF İndir", data=pdf_uret(), file_name="Rapor.pdf", mime="application/pdf", use_container_width=True)
    
    with c2:
        if st.button("🔄 Beğenmedim, Tekrar Dene", use_container_width=True):
            st.session_state.bilgi = derin_motor(st.session_state.son_sorgu)
            st.rerun()

st.markdown("---")
st.markdown("<center>🚀 <b>Madara</b> tarafından kodlandı.</center>", unsafe_allow_html=True)
