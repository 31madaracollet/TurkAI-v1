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
    conn = sqlite3.connect('turkai_pro_data.db', check_same_thread=False)
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

# --- 🔑 AKILLI OTURUM YÖNETİMİ (WEB İÇİN) ---
# Eğer URL'de 'user' parametresi varsa otomatik giriş yap
query_params = st.query_params
if "user" in query_params and "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = True
    st.session_state.user = query_params["user"]

# Değişkenleri başlat (Hata almamak için)
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🧠 MATEMATİKSEL MOTOR ---
def matematiksel_islem_bul(metin):
    temiz = metin.lower().replace("hesapla", "").strip()
    bulunan = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", temiz)
    if bulunan:
        islem = bulunan.group(0).strip()
        try: return True, islem, eval(islem)
        except: return False, None, None
    return False, None, None

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 style='text-align: center; color: #DC2626;'>TürkAI Web Portal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
        with t1:
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("Sisteme Eriş", use_container_width=True):
                if kullanici_kontrol(u, p):
                    st.session_state.giris_yapildi = True
                    st.session_state.user = u
                    st.query_params["user"] = u # URL'ye kazı (Sayfa yenilense de gitmez)
                    st.rerun()
                else: st.error("Hatalı bilgiler.")
        with t2:
            nu = st.text_input("Yeni Kullanıcı", key="r_u")
            np = st.text_input("Yeni Şifre", type="password", key="r_p")
            if st.button("Kayıt Ol", use_container_width=True):
                if yeni_kayit(nu, np): st.success("Hesap hazır!")
                else: st.error("Kullanıcı adı alınmış.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Oturumu Kapat", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.query_params.clear() # URL'den temizle
        st.rerun()
    
    st.divider()
    st.markdown("📂 **Arşivin**")
    arsiv = gecmis_getir(st.session_state.user)
    for idx, (konu_adi, icerik_metni) in enumerate(arsiv):
        emoji = "🔢" if "Matematiksel Sonuç" in icerik_metni else "🔍"
        if st.button(f"{emoji} {konu_adi}", use_container_width=True, key=f"h_{idx}"):
            st.session_state.su_anki_konu = konu_adi
            st.session_state.analiz_sonucu = icerik_metni
            st.rerun()

# --- ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    if "🔢 Matematiksel Sonuç" in st.session_state.analiz_sonucu:
        st.success(st.session_state.analiz_sonucu)
    else:
        st.info(f"### 📌 {st.session_state.su_anki_konu}\n\n{st.session_state.analiz_sonucu}")

sorgu = st.chat_input("İşlem yapın (Örn: hesapla 5*5) veya konu aratın...")

if sorgu:
    is_math, islem, sonuc = matematiksel_islem_bul(sorgu)
    if is_math:
        res = f"🔢 Matematiksel Sonuç \n\n İşlem: {islem} \n\n ✅ Cevap: {sonuc}"
        analiz_kaydet(st.session_state.user, f"Hesapla: {islem}", res)
        st.session_state.analiz_sonucu = res
        st.session_state.su_anki_konu = "Hesaplama"
        st.rerun()
    else:
        with st.spinner("Bilgi taranıyor..."):
            r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                metin = "\n".join([p.get_text() for p in soup.find_all('p')[:5] if len(p.get_text()) > 30])
                if metin:
                    analiz_kaydet(st.session_state.user, sorgu, metin)
                    st.session_state.analiz_sonucu = metin
                    st.session_state.su_anki_konu = sorgu
                    st.rerun()
            else: st.error("Sonuç bulunamadı.")
