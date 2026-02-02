import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
from fpdf import FPDF
from duckduckgo_search import DDGS  # Derin arama için bu lazım

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 CANVA MODERN TEMASI (Dokunulmadı) ---
st.markdown("""
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
    /* Giriş Animasyonu */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(204, 0, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0); }
    }
    .stButton>button { animation: pulse 2s infinite; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
@st.cache_resource
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn

conn = db_baslat()
c = conn.cursor()

# --- 🛠️ FONKSİYONLAR ---
def agresif_temizle(text):
    """Sadece Latin harfleri, Rakamları ve Türkçe karakterleri tutar. Gerisini (Arapça, Korece vb.) siler."""
    # İzin verilenler: a-z, A-Z, 0-9, boşluk, noktalama ve Türkçe karakterler
    # Regex mantığı: İzin verilenlerin DIŞINDAKİ her şeyi sil.
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()çğıöşüÇĞİÖŞÜ\-\+*/]', '', str(text))

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
        t1, t2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        with t1:
            u_in = st.text_input("Kullanıcı Adı", key="l_u")
            p_in = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Giriş Yap"):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone(): st.session_state.user = u_in; st.rerun()
                else: st.error("Hatalı bilgi.")
        with t2:
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydol"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit(); st.success("Kaydoldun, giriş yap!")
                except: st.error("Bu isim dolu.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("### 🗄️ Son Aramalar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:18]}...", key=f"h_{hash(k+i)}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()

# --- 💻 AKILLI TERMİNAL ---
st.markdown("## TürkAI Akıllı Analiz Merkezi")
st.info("💡 **Otomatik Mod Devrede:** Matematik, Altın, Hava Durumu veya Derin Araştırma... Sen sadece yaz, motor anlar.")

sorgu = st.chat_input("Emret kanka, neye bakalım?")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.bilgi = "Analiz ediliyor..." # Geçici
    motor_tipi = "Genel"
    
    # --- 🧠 YAPAY ZEKA YÖNLENDİRİCİSİ (HEPSİ BİR ARADA) ---
    
    # 1. HAVA DURUMU SENSÖRÜ
    if "hava" in sorgu.lower() or "sıcaklık" in sorgu.lower() or "derece" in sorgu.lower():
        try:
            sehir = sorgu.lower().replace("hava", "").replace("durumu", "").replace("nasıl", "").replace("sıcaklık", "").strip()
            if not sehir: sehir = "Istanbul"
            r = requests.get(f"https://wttr.in/{sehir}?format=j1").json()
            curr = r['current_condition'][0]
            st.session_state.bilgi = f"📍 **{sehir.title()} Hava Raporu:**\n\n🌡️ Sıcaklık: {curr['temp_C']}°C\n💧 Nem: %{curr['humidity']}\n🌬️ Rüzgar: {curr['windspeedKmph']} km/h\n☁️ Durum: {curr['lang_tr'][0]['value']}"
            st.session_state.konu = f"{sehir.title()} Hava Durumu"
            motor_tipi = "Hava"
        except:
            st.session_state.bilgi = "Hava durumu servisine ulaşılamadı."

    # 2. MATEMATİK SENSÖRÜ (Sadece sayı ve işlem varsa)
    elif re.match(r"^[\d\+\-\*/\.\(\)\s,x]+$", sorgu.replace("x", "*")):
        try:
            # Güvenli temizlik: x yerine *, virgül yerine nokta
            islem = sorgu.replace("x", "*").replace(",", ".")
            res = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"🧮 **İşlem Sonucu:**\n\n`{sorgu}`\n# = **{res}**"
            st.session_state.konu = "Matematik İşlemi"
            motor_tipi = "Matematik"
        except:
            st.session_state.bilgi = "Hesaplama hatası. İşlemi kontrol et."

    # 3. FİNANS/ALTIN SENSÖRÜ (DuckDuckGo Anlık Bilgi)
    elif any(x in sorgu.lower() for x in ["altın", "dolar", "euro", "borsa", "fiyat"]):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{sorgu} fiyatı son dakika", region='tr-tr', max_results=3))
                ozet = "\n\n".join([f"💰 {r['title']}:\n{r['body']}" for r in results])
                st.session_state.bilgi = f"📉 **Piyasa Özeti:**\n\n{ozet}"
                st.session_state.konu = "Finans Verisi"
                motor_tipi = "Finans"
        except Exception as e:
            st.session_state.bilgi = "Piyasa verisi çekilemedi."

    # 4. DERİN ARAŞTIRMA (Wikipedia + Web)
    else:
        ozet_bilgi = ""
        # Önce DuckDuckGo (Global Web)
        try:
            with DDGS() as ddgs:
                web_res = list(ddgs.text(sorgu, region='tr-tr', max_results=3))
                ozet_bilgi += "🌐 **Web Sonuçları:**\n"
                for r in web_res:
                    ozet_bilgi += f"- **{r['title']}**: {r['body']}\n"
        except: pass
        
        # Sonra Wikipedia (Ansiklopedik)
        try:
            wiki_res = requests.get(f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}").json()
            if 'extract' in wiki_res:
                ozet_bilgi += f"\n📖 **Ansiklopedik Bilgi:**\n{wiki_res['extract']}"
        except: pass
        
        if ozet_bilgi:
            st.session_state.bilgi = ozet_bilgi
            st.session_state.konu = sorgu.title()
            motor_tipi = "Derin Araştırma"
        else:
            st.session_state.bilgi = "Kanka bu konuda internette bile bişey bulamadım."

    # Kayıt
    if st.session_state.bilgi:
        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, st.session_state.konu, st.session_state.bilgi, str(datetime.datetime.now()), motor_tipi))
        conn.commit(); st.rerun()

# --- 📊 GÖRÜNÜM ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"### 🇹🇷 Analiz: {st.session_state.konu}")
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # --- 📄 PDF SİSTEMİ (GÜÇLENDİRİLMİŞ FİLTRE) ---
    def pdf_yap():
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="TurkAI Ozel Rapor", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            
            # UTF-8 Bozukluğunu Önleyen Mapping
            def tr_cevir(t):
                # Önce Türkçe karakterleri düzelt
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): t = t.replace(k,v)
                # Sonra agresif temizlik (Sadece Latin + Rakam + Noktalama)
                return re.sub(r'[^\x00-\x7F]+', '', t) 

            temiz_konu = tr_cevir(st.session_state.konu)
            temiz_icerik = tr_cevir(st.session_state.bilgi)
            temiz_user = tr_cevir(st.session_state.user)

            metin = f"Konu: {temiz_konu}\n\nTarih: {str(datetime.datetime.now())[:16]}\n\nRapor:\n{temiz_icerik}\n\nKullanici: {temiz_user}"
            pdf.multi_cell(0, 10, txt=metin.encode('latin-1', 'ignore').decode('latin-1'))
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e:
            return f"PDF Hatasi: {str(e)}".encode('utf-8')

    st.download_button("📄 PDF İndir (Temizlenmiş)", data=pdf_yap(), file_name="TurkAI_Rapor.pdf", mime="application/pdf")
