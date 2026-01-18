import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import pandas as pd

# --- ⚙️ SİSTEM BAŞLANGIÇ AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI BAĞLANTISI (SQLITE) ---
def db_baslat():
    conn = sqlite3.connect('turkai_kayitlar.db')
    c = conn.cursor()
    # Eğer tablo yoksa oluştur (Kullanıcı, Aranan Konu, Tarih)
    c.execute('''CREATE TABLE IF NOT EXISTS aramalar
                 (kullanici TEXT, konu TEXT, tarih TEXT)''')
    conn.commit()
    conn.close()

def kayit_ekle(kullanici, konu):
    conn = sqlite3.connect('turkai_kayitlar.db')
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO aramalar VALUES (?, ?, ?)", (kullanici, konu, zaman))
    conn.commit()
    conn.close()

def kayitlari_getir():
    conn = sqlite3.connect('turkai_kayitlar.db')
    # Son 10 aramayı getir
    df = pd.read_sql_query("SELECT * FROM aramalar ORDER BY tarih DESC LIMIT 10", conn)
    conn.close()
    return df

# Uygulama açılırken veritabanını kontrol et
db_baslat()

# --- SESSION STATE ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "analiz_sonucu" not in st.session_state:
    st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state:
    st.session_state.su_anki_konu = ""

# --- 🛡️ GÜVENLİK ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt", "meme", "daşşak", "ibne", "kahpe"]

def guvenlik_tarama(metin):
    if not metin: return True
    temiz_metin = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    for kelime in KARA_LISTE:
        if kelime in temiz_metin: return False
    return True

# --- 🧹 TEMİZLİK ---
def metin_optimizasyonu(metin):
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    metin = metin.replace('\xa0', ' ').strip()
    return metin

# --- 📄 PDF RAPOR ---
def rapor_olustur(baslik, icerik, yazar):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "TURKAI ANALIZ RAPORU", ln=True, align='C')
    pdf.line(10, 25, 200, 25)
    pdf.ln(15)
    
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    def safe(s): return s.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 8, txt=safe(f"Konu: {baslik}"), ln=True)
    pdf.cell(0, 8, txt=safe(f"Hazirlayan: {yazar}"), ln=True)
    pdf.cell(0, 8, txt=safe(f"Islem Tarihi: {zaman}"), ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, txt=safe(icerik))
    
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "TurkAI Kurumsal Veri Analiz Sistemi", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 CSS ---
def stil_enjekte_et():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 8rem; }
        
        .sonuc-karti {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1.5rem;
        }
        @media (prefers-color-scheme: dark) {
            .sonuc-karti { background-color: #1e1f20; border: 1px solid #333; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); }
            h1, h2, h3, p { color: #e2e8f0; }
        }
        h1 {
            font-weight: 700;
            text-align: center;
            background: -webkit-linear-gradient(45deg, #e63946, #457b9d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .stChatInputContainer { padding-bottom: 2rem; }
        section[data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.1); }
        </style>
    """, unsafe_allow_html=True)

stil_enjekte_et()

# --- 🚪 GİRİŞ ---
if not st.session_state.giris_yapildi:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>TürkAI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Kurumsal Araştırma & Kayıt Sistemi</p>", unsafe_allow_html=True)
        kullanici = st.text_input("Kimlik Doğrulama", placeholder="Adınızı giriniz...")
        if st.button("Platforma Giriş Yap", use_container_width=True):
            if len(kullanici) >= 2:
                st.session_state.kullanici_adi = kullanici
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.warning("Geçerli bir isim giriniz.")
    st.stop()

# --- 🚀 ANA PLATFORM ---

# YAN PANEL (KAYITLARI GÖSTERİR)
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.kullanici_adi}")
    st.caption("Veritabanı: Bağlı 🟢")
    st.divider()
    
    st.markdown("**📂 Son Kaydedilen Aramalar**")
    try:
        df_kayitlar = kayitlari_getir()
        if not df_kayitlar.empty:
            st.dataframe(df_kayitlar, hide_index=True, use_container_width=True)
        else:
            st.info("Henüz kayıt bulunmuyor.")
    except:
        st.error("Veritabanı okunamadı.")
        
    st.divider()
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

# İÇERİK
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    st.markdown(f"""
    <div class="sonuc-karti">
        <h3 style="color: #e63946; margin-top:0;">📌 Analiz: {st.session_state.su_anki_konu}</h3>
        <p style="line-height: 1.8; font-size: 1.05rem;">
            {st.session_state.analiz_sonucu.replace(chr(10), '<br><br>')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_pdf, col_bos = st.columns([1, 3])
    with col_pdf:
        pdf_data = rapor_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.kullanici_adi)
        st.download_button("📄 Raporu PDF Olarak İndir", pdf_data, f"Rapor_{st.session_state.su_anki_konu}.pdf", "application/pdf", use_container_width=True)

else:
    st.markdown("""
    <div style="text-align: center; padding: 3rem; opacity: 0.6;">
        <h3>Sistem Hazır</h3>
        <p>Yapılan tüm aramalar artık 'turkai_kayitlar.db' dosyasında saklanmaktadır.<br>
        Geçmiş kayıtları yan panelden inceleyebilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)

# SORGULAMA
sorgu = st.chat_input("Araştırma konusunu giriniz...")

if sorgu:
    if not guvenlik_tarama(sorgu):
        st.error("⛔ Güvenlik Protokolü: Uygunsuz içerik.")
    else:
        with st.spinner("Veriler işleniyor ve kaydediliyor..."):
            konu_linki = sorgu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{konu_linki}"
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metin_optimizasyonu(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        # 💾 VERİYİ KALICI OLARAK KAYDET
                        kayit_ekle(st.session_state.kullanici_adi, sorgu)
                        
                        st.session_state.analiz_sonucu = "\n".join(paragraflar[:8])
                        st.session_state.su_anki_konu = sorgu
                        st.rerun()
                    else:
                        st.warning("⚠️ Yeterli veri bulunamadı.")
                else:
                    st.error("❌ Konu bulunamadı.")
            except:
                st.error("⚠️ Bağlantı hatası.")

