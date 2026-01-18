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
    # Karakter temizliği (PDF çökmemesi için)
    t_baslik = baslik.encode('latin-1', 'ignore').decode('latin-1')
    t_icerik = icerik.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"TurkAI: {t_baslik}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=t_icerik)
    return pdf.output(dest='S').encode('latin-1')

db_baslat()

# --- 🔑 F5 KORUMASI (QUERY PARAMS) ---
# Eğer URL'de 'u' parametresi varsa session'ı canlandır
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 TASARIM ---
st.markdown("""
    <style>
    .sonuc-karti { background-color: #F9FAFB; padding: 25px; border-radius: 12px; border: 1px solid #E5E7EB; line-height: 1.7; }
    .kaynak-box { background-color: #F3F4F6; padding: 10px; border-radius: 5px; margin-top: 15px; border-left: 5px solid #DC2626; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 style='text-align: center; color: #DC2626;'>TürkAI Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Giriş Yap", use_container_width=True):
                conn = sqlite3.connect('turkai_pro_data.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifre_hashle(p)))
                if c.fetchone():
                    st.session_state.user = u
                    st.session_state.giris_yapildi = True
                    st.query_params["u"] = u # URL'ye ismi yaz
                    st.rerun()
                else: st.error("Hatalı giriş!")
        with c2:
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    conn = sqlite3.connect('turkai_pro_data.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users VALUES (?,?)", (u, sifre_hashle(p)))
                    conn.commit()
                    st.success("Kaydolun! Giriş yapabilirsin.")
                except: st.error("Bu kullanıcı zaten var.")
    st.stop()

# --- 🚀 YAN PANEL (ARŞİV) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    st.markdown("📂 **Senin Arşivin**")
    for konu, icerik in gecmis_getir(st.session_state.user):
        if st.button(f"📌 {konu[:20]}", use_container_width=True):
            st.session_state.analiz_sonucu = icerik
            st.session_state.su_anki_konu = konu
            st.rerun()

# --- ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    c_metin, c_islem = st.columns([4, 1])
    with c_metin:
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c_islem:
        # 📄 PDF OLUŞTURMA
        pdf_file = pdf_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_file, file_name=f"{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- ARAMA MOTORU ---
sorgu = st.chat_input("Bir şeyler sor veya hesapla...")

if sorgu:
    # 1. MATEMATİKSEL KONTROL
    temiz_sorgu = sorgu.lower().replace("hesapla", "").strip()
    is_math = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", temiz_sorgu)
    
    if is_math:
        try:
            islem = is_math.group(0)
            cevap = eval(islem)
            sonuc = f"🔢 Matematiksel Sonuç \n\n İşlem: {islem} \n ✅ Cevap: {cevap}"
            analiz_kaydet(st.session_state.user, f"Hesapla: {islem}", sonuc)
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = sonuc, "Hesaplama"
            st.rerun()
        except: pass

    # 2. WIKIPEDIA ARAMASI
    with st.spinner("Bilgi taranıyor..."):
        r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Gereksiz [1], [2] gibi atıfları sil
            for cite in soup.find_all(["sup", "span"], class_=["reference", "mw-editsection"]): cite.decompose()
            
            paragraflar = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50]
            if paragraflar:
                ozet = "\n\n".join(paragraflar[:7])
                # Akademik kelimeleri sadeleştirme (Opsiyonel)
                ozet = ozet.replace("uygulayım bilimi", "teknoloji")
                ozet += f"\n\n<div class='kaynak-box'><b>📚 Kaynak:</b> Wikipedia - {sorgu.capitalize()}</div>"
                
                analiz_kaydet(st.session_state.user, sorgu, ozet)
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = ozet, sorgu
                st.rerun()
        else: st.error("Konu bulunamadı.")
