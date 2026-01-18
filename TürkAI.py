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

def analiz_kaydet(user, konu, icerik):
    conn = sqlite3.connect('turkai_pro_data.db', check_same_thread=False)
    c = conn.cursor()
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (user, konu, icerik, zaman))
    conn.commit()
    conn.close()

def gecmis_getir(user):
    conn = sqlite3.connect('turkai_pro_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC", (user,))
    data = c.fetchall()
    conn.close()
    return data

# --- 📄 PDF OLUŞTURUCU ---
def pdf_olustur(baslik, icerik):
    pdf = FPDF()
    pdf.add_page()
    # PDF için karakter temizliği (Hata vermemesi için)
    t_baslik = baslik.replace('İ','I').replace('ı','i').replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
    t_icerik = icerik.replace('İ','I').replace('ı','i').replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ç','c')
    t_icerik = re.sub('<[^<]+?>', '', t_icerik) # HTML temizle

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=t_baslik, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=t_icerik)
    return pdf.output(dest='S').encode('latin-1')

# --- 🧠 METİN SADELEŞTİRME ---
def metni_temizle(metin):
    # Akademik terimleri sadeleştir
    sozluk = {"uygulayım bilimi": "teknoloji", "betimleme": "tanımlama", "gereksinim": "ihtiyaç"}
    for eski, yeni in sozluk.items():
        metin = metin.replace(eski, yeni).replace(eski.capitalize(), yeni.capitalize())
    # [1], [20] gibi atıfları sil
    metin = re.sub(r"\[\d+\]", "", metin)
    return metin

db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" in st.query_params and "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = True
    st.session_state.user = st.query_params["user"]

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 TASARIM ---
st.markdown("""
    <style>
    .sonuc-karti { background-color: #F9FAFB; padding: 25px; border-radius: 15px; border: 1px solid #E5E7EB; color: #111827; line-height: 1.7; }
    .kaynakca { background-color: #F3F4F6; padding: 10px; border-radius: 5px; margin-top: 15px; font-size: 0.8rem; border-left: 4px solid #DC2626; }
    </style>
""", unsafe_allow_html=True)

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.title("🇹🇷 TürkAI Pro Giriş")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            conn = sqlite3.connect('turkai_pro_data.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifre_hashle(p)))
            if c.fetchone():
                st.session_state.giris_yapildi, st.session_state.user = True, u
                st.query_params["user"] = u
                st.rerun()
            else: st.error("Hatalı bilgiler!")
        
        st.divider()
        if st.button("Yeni Hesap Oluştur"):
            try:
                conn = sqlite3.connect('turkai_pro_data.db')
                c = conn.cursor()
                c.execute("INSERT INTO users VALUES (?,?)", (u, sifre_hashle(p)))
                conn.commit()
                st.success("Kayıt başarılı! Şimdi giriş yapabilirsin.")
            except: st.error("Bu kullanıcı adı zaten var.")
    st.stop()

# --- 🚀 ANA PANEL (ARŞİV) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Oturumu Kapat", use_container_width=True):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    
    st.divider()
    st.markdown("📂 **Senin Arşivin**")
    arsiv = gecmis_getir(st.session_state.user)
    for idx, (konu_adi, icerik_metni) in enumerate(arsiv):
        if st.button(f"📌 {konu_adi[:20]}", use_container_width=True, key=f"h_{idx}"):
            st.session_state.su_anki_konu = konu_adi
            st.session_state.analiz_sonucu = icerik_metni
            st.rerun()

# --- ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    c_ana, c_pdf = st.columns([4, 1])
    with c_ana:
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c_pdf:
        pdf_data = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_data, file_name=f"{st.session_state.su_anki_konu}.pdf", mime="application/pdf")

# --- 📥 AKILLI SORGULAMA ---
sorgu = st.chat_input("Neyi hesaplamak veya araştırmak istersiniz?")

if sorgu:
    # 1. HESAPLAMA MI?
    is_math = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", sorgu)
    if is_math:
        try:
            islem = is_math.group(0)
            cevap = eval(islem)
            res = f"🔢 Matematiksel Sonuç \n\nİşlem: {islem} \n✅ Cevap: {cevap}"
            analiz_kaydet(st.session_state.user, f"Hesapla: {islem}", res)
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
            st.rerun()
        except: pass

    # 2. ARAMA MI?
    with st.spinner("Bilgi taranıyor..."):
        r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            metinler = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
            if metinler:
                ozet = metni_temizle("\n\n".join(metinler[:7]))
                ozet += f"\n\n<div class='kaynakca'><b>📚 Kaynaklar:</b><br>1. Wikipedia - {sorgu.capitalize()}</div>"
                analiz_kaydet(st.session_state.user, sorgu, ozet)
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = ozet, sorgu
                st.rerun()
        else: st.error("Üzgünüm, bu başlıkta bir sonuç bulamadım.")
