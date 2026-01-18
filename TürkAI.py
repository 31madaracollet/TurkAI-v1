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
def get_db():
    return sqlite3.connect('turkai_pro_data.db', check_same_thread=False)

def db_baslat():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    conn.close()

def sifre_hashle(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

db_baslat()

# --- 🛡️ KÜFÜR KALKANI ---
KARA_LISTE = ["amk", "aq", "sik", "piç", "yarrak", "göt", "oç", "ibne", "kahpe"] # Listeyi genişletebilirsin

def guvenli_mi(metin):
    temiz = metin.lower().strip()
    for kelime in KARA_LISTE:
        if kelime in temiz:
            return False
    return True

# --- 📄 PDF OLUŞTURUCU ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr(m):
        mapping = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in mapping.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, tr(konu), ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, tr(re.sub('<[^<]+?>', '', icerik)))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 GİRİŞ VE F5 KORUMASI ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🚪 GİRİŞ EKRANI (SADE) ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 style='text-align:center; color:#b91c1c;'>TürkAI Giriş</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Bağlan", use_container_width=True):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifre_hashle(p)))
            if c.fetchone():
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("Hatalı Giriş!")
    st.stop()

# --- 🚀 YAN PANEL (GEÇMİŞ) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş Aramalar**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:15]}...", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = k, i
            st.rerun()

# --- 🖥️ ANA EKRAN ---
st.title("TürkAI Bilgi & Hesap Merkezi")

if st.session_state.analiz_sonucu:
    c1, c2 = st.columns([4, 1])
    with c1:
        color = "#f0fdf4" if "🔢" in st.session_state.analiz_sonucu else "#f8fafc"
        st.markdown(f'<div style="background:{color}; padding:20px; border-radius:10px; border:1px solid #ddd;">'
                    f'<h3>{st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        pdf_v = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_v, file_name="TurkAI_Cikti.pdf", use_container_width=True)

# --- 📥 GİRİŞ ALANI ---
sorgu = st.chat_input("Bir şey aratın veya hesaplama yapın (Örn: 15*8)...")

if sorgu:
    # 1. KÜFÜR KONTROLÜ
    if not guvenli_mi(sorgu):
        st.error("🚨 Uyarı: Lütfen saygılı ve profesyonel bir dil kullanın!")
    else:
        # 2. HESAP MAKİNESİ
        # Sadece rakam ve matematik sembollerini içeren bir kalıp arar
        math_pattern = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", sorgu)
        if math_pattern:
            try:
                islem = math_pattern.group(0)
                cevap = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematiksel Sonuç\n\nİşlem: {islem}\n✅ Cevap: {cevap}"
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, "Hesaplama", res, datetime.datetime.now()))
                conn.commit(); st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"; st.rerun()
            except: pass

        # 3. WIKIPEDIA ARAMA
        with st.spinner("Bilgi taranıyor..."):
            r = requests.get(f"https://tr.wikipedia.org/wiki/{sorgu.strip().capitalize().replace(' ', '_')}")
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for junk in soup(["sup", "span", "table", "style", "script"]): junk.decompose()
                paragraf = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 50]
                if paragraf:
                    bilgi = "\n\n".join(paragraf[:6])
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, sorgu, bilgi, datetime.datetime.now()))
                    conn.commit(); st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, sorgu; st.rerun()
            st.warning("Bu konuda net bir bilgi bulunamadı. Lütfen kelimeyi kontrol edin.")
