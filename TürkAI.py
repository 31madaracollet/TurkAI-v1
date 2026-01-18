import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI MOTORU ---
def db_baslat():
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def kullanici_kontrol(user, pwd):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, sifre_hashle(pwd)))
    data = c.fetchone()
    conn.close()
    return data

def yeni_kayit(user, pwd):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?)", (user, sifre_hashle(pwd)))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def analiz_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def gecmis_getir(user):
    conn = sqlite3.connect('turkai_pro_data.db')
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

db_baslat()

# --- 🧠 SESSION STATE ---
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🛡️ GÜVENLİK FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt"]
def guvenli_mi(metin):
    temiz = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    return not any(k in temiz for k in KARA_LISTE)

# --- 🎨 AYDINLIK VE CİDDİ ARAYÜZ (CSS) ---
st.markdown("""
    <style>
    /* Aydınlık Mod Temelleri */
    .stApp { background-color: #FFFFFF; color: #1F2937; }
    
    /* İçerik Kartı */
    .sonuc-karti {
        background-color: #F9FAFB;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        color: #111827;
        line-height: 1.8;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Orta Alan Genişliği */
    .main .block-container { max-width: 900px; padding-bottom: 10rem; }
    
    /* Başlıklar */
    h1 { color: #DC2626; text-align: center; font-weight: 800; }
    
    /* Giriş Paneli */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 🚪 GİRİŞ & KAYIT SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1>TürkAI Bilgi Portalı</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
        with tab1:
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sisteme Giriş", use_container_width=True):
                if kullanici_kontrol(u, p):
                    st.session_state.giris_yapildi = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Hatalı kimlik bilgileri.")
        with tab2:
            new_u = st.text_input("Yeni Kullanıcı Adı", key="r_u")
            new_p = st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Hesabı Oluştur", use_container_width=True):
                if len(new_u) > 2 and len(new_p) > 3:
                    if yeni_kayit(new_u, new_p): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                    else: st.error("Bu kullanıcı adı sistemde mevcut.")
                else: st.warning("Bilgiler çok kısa.")
    st.stop()

# --- 🚀 ANA PANEL ---

# YAN PANEL (KİŞİSEL ARŞİV)
with st.sidebar:
    st.markdown(f"### 🛡️ Kullanıcı: **{st.session_state.user}**")
    st.divider()
    st.markdown("📂 **Kişisel Analiz Geçmişi**")
    
    arsiv = gecmis_getir(st.session_state.user)
    if arsiv:
        for konu_adi, icerik_metni in arsiv:
            # Tıklanabilir geçmiş butonu
            if st.button(f"🔍 {konu_adi}", use_container_width=True, key=f"hist_{konu_adi}"):
                st.session_state.su_anki_konu = konu_adi
                st.session_state.analiz_sonucu = icerik_metni
    else:
        st.caption("Henüz kayıtlı analiziniz yok.")

    st.divider()
    if st.button("Çıkış Yap", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

# ANA SAYFA
st.markdown("<h1>TürkAI Araştırma Merkezi</h1>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    st.markdown(f"""
    <div class="sonuc-karti">
        <h3 style="color: #DC2626;">📌 Konu: {st.session_state.su_anki_konu}</h3>
        {st.session_state.analiz_sonucu.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    # PDF RAPORU
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
    safe_text = st.session_state.analiz_sonucu.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    st.download_button("📄 Analiz Raporunu İndir (PDF)", pdf.output(dest='S').encode('latin-1'), f"{st.session_state.su_anki_konu}.pdf", "application/pdf")
else:
    st.markdown("<p style='text-align: center; opacity: 0.6;'>Hoş geldin kanka. Analizini başlatmak için aşağıya bir konu yazabilir veya geçmişten bir kayıt seçebilirsin.</p>", unsafe_allow_html=True)

# ALT SORGULAMA BARI (SABİT)
sorgu = st.chat_input("Analiz edilecek konu başlığını giriniz...")

if sorgu:
    if guvenli_mi(sorgu):
        with st.spinner("Bilgi havuzu taranıyor..."):
            wiki_url = f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}"
            res = requests.get(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                metinler = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if metinler:
                    ozet = "\n\n".join(metinler[:7])
                    # Veritabanına kaydet (Kişiye özel)
                    analiz_kaydet(st.session_state.user, sorgu, ozet)
                    st.session_state.analiz_sonucu = ozet
                    st.session_state.su_anki_konu = sorgu
                    st.rerun()
                else: st.warning("Yeterli içerik bulunamadı.")
            else: st.error("Konu başlığı Wikipedia'da bulunamadı.")
    else: st.error("⚠️ Uygunsuz içerik algılandı!")
    

