import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM VE TASARIM ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .sonuc-karti {
        background: #f8fafc; padding: 25px; border-radius: 15px;
        border: 1px solid #e2e8f0; line-height: 1.7; color: #1e293b;
    }
    .math-karti {
        background: #f0fdf4; padding: 20px; border-radius: 12px;
        border: 2px solid #22c55e; text-align: center; font-size: 1.5rem;
        font-weight: bold; color: #166534;
    }
    h1 { color: #b91c1c !important; text-align: center; }
    .stSidebar { background-color: #f1f5f9 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI MOTORU (THREAD KORUMALI) ---
def get_db():
    conn = sqlite3.connect('turkai_pro_data.db', check_same_thread=False)
    return conn

def db_baslat():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

db_baslat()

# --- 📄 PDF OLUŞTURUCU (GÜVENLİ MOD) ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    
    # PDF çökmesini önlemek için Türkçe karakterleri çevirir
    def tr_duzelt(metin):
        sozluk = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in sozluk.items(): metin = metin.replace(k, v)
        return metin.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, tr_duzelt(konu), ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    # HTML ve gereksiz boşlukları temizle
    temiz_icerik = re.sub('<[^<]+?>', '', icerik)
    pdf.multi_cell(0, 8, tr_duzelt(temiz_icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 SESSION & F5 KORUMASI ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1>TürkAI Bilgi Portalı</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        t1, t2 = st.tabs(["🔑 Giriş", "📝 Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir", use_container_width=True):
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifre_hashle(p)))
                if c.fetchone():
                    st.session_state.user, st.session_state.giris_yapildi = u, True
                    st.query_params["u"] = u
                    st.rerun()
                else: st.error("Hatalı bilgiler!")
        with t2:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, sifre_hashle(np)))
                    conn.commit(); st.success("Hesap açıldı!")
                except: st.error("Bu kullanıcı adı alınmış.")
    st.stop()

# --- 🚀 YAN PANEL (GEÇMİŞ) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış Yap", use_container_width=True):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Senin Arşivin**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for konu_adi, icerik_metni in c.fetchall():
        if st.button(f"📌 {konu_adi[:20]}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = konu_adi, icerik_metni
            st.rerun()

# --- 🖥️ ANA EKRAN ---
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    c1, c2 = st.columns([4, 1])
    with c1:
        if "🔢" in st.session_state.analiz_sonucu:
            st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        pdf_v = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_v, file_name=f"TurkAI_{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- 📥 AKILLI ARAMA & HESAPLAMA ---
sorgu = st.chat_input("Bir şeyler sor veya hesapla (Örn: 25*4)...")

if sorgu:
    # 1. HESAPLAMA KONTROLÜ
    temiz_s = sorgu.lower().replace("hesapla", "").strip()
    is_math = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", temiz_s)
    
    if is_math:
        try:
            islem = is_math.group(0)
            cevap = eval(islem, {"__builtins__": {}}, {})
            res = f"🔢 Matematiksel Sonuç \n\nİşlem: {islem} \n✅ Cevap: {cevap}"
            # DB KAYDET
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, "Hesaplama", res, datetime.datetime.now()))
            conn.commit()
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
            st.rerun()
        except: pass

    # 2. WIKIPEDIA (TEMİZLENMİŞ)
    with st.spinner("Bilgiler filtreleniyor..."):
        r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Abuk subuk şeyleri (atıfları, düzenleme linklerini) temizle
            for junk in soup(["sup", "span", "table", "style", "script"]): junk.decompose()
            
            paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
            if paragraflar:
                # Akademik kelime filtresi
                bilgi = "\n\n".join(paragraflar[:7])
                bilgi = bilgi.replace("uygulayım bilimi", "teknoloji").replace("gereksinim", "ihtiyaç")
                
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, sorgu, bilgi, datetime.datetime.now()))
                conn.commit()
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, sorgu
                st.rerun()
        else: st.error("Sonuç bulunamadı.")
