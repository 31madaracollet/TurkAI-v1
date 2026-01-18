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

# --- 💾 VERİTABANI MOTORU (ADLİ SİCİL EKLENDİ) ---
def db_baslat():
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    # ihlal_sayisi ve ban_bitis eklendi
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, ihlal_sayisi INTEGER DEFAULT 0, ban_bitis TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def kullanici_verisi_getir(user):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    c.execute("SELECT ihlal_sayisi, ban_bitis FROM users WHERE username=?", (user,))
    data = c.fetchone()
    conn.close()
    return data

def ihlal_arttir(user):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    c.execute("UPDATE users SET ihlal_sayisi = ihlal_sayisi + 1 WHERE username=?", (user,))
    # İhlal sayısını al
    c.execute("SELECT ihlal_sayisi FROM users WHERE username=?", (user,))
    sayi = c.fetchone()[0]
    
    msg = ""
    if sayi == 3:
        msg = "⚠️ UYARI: 3. ihlalini yaptın. Kurallara uymazsan banlanacaksın!"
    elif sayi == 7:
        ban_vakti = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET ban_bitis = ? WHERE username=?", (ban_vakti, user))
        msg = "🚫 BAN: 7. ihlal! Hesabın 24 saatliğine askıya alındı."
    elif sayi >= 10:
        c.execute("DELETE FROM users WHERE username=?", (user))
        c.execute("DELETE FROM aramalar WHERE kullanici=?", (user))
        msg = "💀 HESAP SİLİNDİ: 10 ihlal sınırı aşıldı. Hesabınız kalıcı olarak imha edildi."
    
    conn.commit()
    conn.close()
    return sayi, msg

# Diğer DB fonksiyonları (Giriş, Kayıt, Analiz Kaydet vb.)
def kullanici_kontrol(user, pwd):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, sifre_hashle(pwd)))
    data = c.fetchone()
    conn.close()
    return data

def yeni_kayit(user, pwd):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, ihlal_sayisi) VALUES (?,?,0)", (user, sifre_hashle(pwd)))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def analiz_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def gecmis_getir(user):
    conn = sqlite3.connect('turkai_v48.db')
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

db_baslat()

# --- 🛡️ GENİŞLETİLMİŞ ARGO FİLTRESİ (BAĞDAŞTIRMALI) ---
KARA_LISTE = [
    "amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "serefsiz", 
    "orospu", "gay", "lez", "pust", "dalyarak", "amcik", "gavat", "yavsak", "it"
]

def guvenli_mi(metin):
    # Türkçe karakterleri İngilizce benzerlerine çevir ve temizle
    temiz = metin.lower().replace('ı','i').replace('ş','s').replace('ç','c').replace('ğ','g').replace('ü','u').replace('ö','o')
    temiz = re.sub(r'[^a-z]', '', temiz) # Sadece harfleri bırak
    
    for kelime in KARA_LISTE:
        if kelime in temiz: # Kelime bağdaştırma (kelimenin içinde geçiyor mu?)
            return False
    return True

# --- 🎨 ARAYÜZ ---
st.markdown("""<style>
    .stApp { background-color: #FFFFFF; color: #1F2937; }
    .sonuc-karti { background-color: #F9FAFB; padding: 25px; border-radius: 12px; border: 1px solid #E5E7EB; margin-bottom: 20px; }
    h1 { color: #DC2626; text-align: center; }
</style>""", unsafe_allow_html=True)

# --- 🧠 SESSION STATE ---
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🚪 GİRİŞ SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1>TürkAI Güvenlik Merkezi</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t1, t2 = st.tabs(["🔑 Giriş", "📝 Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Giriş"):
                res = kullanici_kontrol(u, p)
                if res:
                    # Ban kontrolü
                    ihlal, ban_vakti = res[2], res[3]
                    if ban_vakti and datetime.datetime.strptime(ban_vakti, "%Y-%m-%d %H:%M:%S") > datetime.datetime.now():
                        st.error(f"Hesabınız banlanmıştır. Bitiş: {ban_vakti}")
                    else:
                        st.session_state.giris_yapildi = True
                        st.session_state.user = u
                        st.rerun()
                else: st.error("Hatalı bilgiler.")
        with t2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Hesap Oluştur"):
                if yeni_kayit(nu, np): st.success("Başarılı!")
                else: st.error("Kullanıcı adı alınmış.")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    ihlal_bilgisi = kullanici_verisi_getir(st.session_state.user)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"🚩 **İhlal Puanı: {ihlal_bilgisi[0]} / 10**")
    st.divider()
    
    arsiv = gecmis_getir(st.session_state.user)
    for k, i in arsiv:
        if st.button(f"🔍 {k}", use_container_width=True, key=f"h_{k}"):
            st.session_state.su_anki_konu = k
            st.session_state.analiz_sonucu = i
    
    if st.button("Çıkış Yap"):
        st.session_state.giris_yapildi = False
        st.rerun()

st.title("TürkAI Araştırma Portalı")

if st.session_state.analiz_sonucu:
    st.markdown(f'<div class="sonuc-karti"><h3>📌 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

# --- SORGULAMA ---
sorgu = st.chat_input("Konu yazın...")

if sorgu:
    if not guvenli_mi(sorgu):
        sayi, mesaj = ihlal_arttir(st.session_state.user)
        st.error(mesaj)
        if sayi >= 10:
            st.session_state.giris_yapildi = False
            st.rerun()
    else:
        # Wikipedia analizi ve kayıt işlemleri...
        with st.spinner("Analiz ediliyor..."):
            url = f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                metinler = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if metinler:
                    ozet = "\n\n".join(metinler[:7])
                    analiz_kaydet(st.session_state.user, sorgu, ozet)
                    st.session_state.analiz_sonucu = ozet
                    st.session_state.su_anki_konu = sorgu
                    st.rerun()
            else: st.error("Bulunamadı.")
    


