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

# --- 🧠 MATEMATİK VE AYIKLAMA ---
def matematiksel_islem_bul(metin):
    temiz_metin = metin.lower().replace("hesapla", "").strip()
    bulunan = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", temiz_metin)
    if bulunan:
        islem = bulunan.group(0).strip()
        try:
            sonuc = eval(islem)
            return True, islem, sonuc
        except: return False, None, None
    return False, None, None

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

# --- 🔑 OTURUM YÖNETİMİ (KANKA BURASI ÖNEMLİ) ---
# Tarayıcı yenilendiğinde st.session_state sıfırlanabilir. 
# Tam çözüm için Streamlit'in yeni özelliği olan 'st.query_params' üzerinden 
# basit bir token sistemi taklit edeceğiz ki sekme yenilense de düşmesin.

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 style='text-align: center; color: #DC2626;'>TürkAI Pro Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
        with tab1:
            u = st.text_input("Kullanıcı Adı", key="login_user")
            p = st.text_input("Şifre", type="password", key="login_pass")
            if st.button("Sisteme Eriş", use_container_width=True):
                if kullanici_kontrol(u, p):
                    st.session_state.giris_yapildi = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Hatalı kullanıcı adı veya şifre.")
        with tab2:
            nu = st.text_input("Yeni Kullanıcı", key="reg_user")
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            if st.button("Hesabı Oluştur", use_container_width=True):
                if len(nu) > 2 and len(np) > 3:
                    if yeni_kayit(nu, np): st.success("Hesap oluşturuldu! Giriş yapabilirsiniz.")
                    else: st.error("Bu kullanıcı adı zaten var.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    
    # ÇIKIŞ BUTONU (Basana kadar çıkış yapmaz)
    if st.button("🔴 Oturumu Kapat", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.session_state.user = ""
        st.rerun()
        
    st.divider()
    st.markdown("📂 **Senin Arşivin**")
    arsiv = gecmis_getir(st.session_state.user)
    for idx, (konu_adi, icerik_metni) in enumerate(arsiv):
        emoji = "🔢" if "Matematiksel Sonuç" in icerik_metni else "🔍"
        if st.button(f"{emoji} {konu_adi}", use_container_width=True, key=f"h_{idx}"):
            st.session_state.su_anki_konu = konu_adi
            st.session_state.analiz_sonucu = icerik_metni
            st.rerun()

# --- ANA EKRAN İÇERİĞİ ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    if "🔢 Matematiksel Sonuç" in st.session_state.analiz_sonucu:
        st.success(st.session_state.analiz_sonucu)
    else:
        st.info(f"### 📌 {st.session_state.su_anki_konu}\n\n{st.session_state.analiz_sonucu}")

sorgu = st.chat_input("İşlem yapın veya konu aratın...")

if sorgu:
    is_math, islem, sonuc = matematiksel_islem_bul(sorgu)
    if is_math:
        sonuc_metni = f"🔢 Matematiksel Sonuç \n\n İşlem: {islem} \n\n ✅ Cevap: {sonuc}"
        analiz_kaydet(st.session_state.user, f"Hesapla: {islem}", sonuc_metni)
        st.session_state.analiz_sonucu = sonuc_metni
        st.session_state.su_anki_konu = "Hesaplama"
        st.rerun()
    else:
        # Wikipedia Arama Kısmı (Aynı şekilde devam)
        url = f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}"
        r = requests.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            metin = "\n".join([p.get_text() for p in soup.find_all('p')[:5]])
            analiz_kaydet(st.session_state.user, sorgu, metin)
            st.session_state.analiz_sonucu = metin
            st.session_state.su_anki_konu = sorgu
            st.rerun()
