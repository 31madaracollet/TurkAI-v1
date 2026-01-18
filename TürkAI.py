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

# --- 🛡️ GÜVENLİK VE TEMİZLİK MOTORU ---
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros"]

def karakter_sigortasi(metin):
    """Metni hem temizler hem de PDF/Ekran için güvenli hale getirir."""
    if not metin: return ""
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = "".join(ch for ch in metin if ch.isprintable())
    return re.sub(r'\s+', ' ', metin).strip()

def kalkan(metin):
    """Küfür kalkanı."""
    t = metin.lower()
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    t = t.translate(str.maketrans("01347", "oiEat"))
    t = re.sub(r'[^a-z]', '', t)
    return not any(kelime in t for kelime in KARA_LISTE)

# --- 💾 VERİTABANI ---
def get_db():
    return sqlite3.connect('turkai_v48.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF SİSTEMİ ---
def pdf_yap(konu, icerik):
    try:
        pdf = FPDF()
        pdf.add_page()
        def pdf_temiz(m):
            m = karakter_sigortasi(m)
            tr = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
            for k, v in tr.items(): m = m.replace(k, v)
            return m.encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, pdf_temiz(konu), ln=1, align="C"); pdf.ln(10)
        pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, pdf_temiz(icerik))
        return pdf.output(dest='S').encode('latin-1')
    except: return b"Error"

# --- 🔑 SESSION ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user, st.session_state.giris_yapildi = st.query_params["u"], True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 ARAYÜZ ---
st.markdown("<style>.stApp{background:#fff;} .header{color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px;}</style>", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v48.0</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("🤖 Adınız?")
        if st.button("Sistemi Aç", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("⚠️ Geçersiz isim!")
    st.stop()

# --- 🚀 YAN PANEL (HATA ÇÖZÜLDÜ) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor()
    # Tarih bilgisini de çekiyoruz
    c.execute("SELECT konu, icerik, tarih FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for konu, icerik, tarih in c.fetchall():
        # ÇÖZÜM: Her butona 'tarih' bilgisini içeren benzersiz bir key veriyoruz
        if st.button(f"📌 {konu[:18]}", key=f"btn_{tarih}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = konu, icerik
            st.rerun()

st.markdown("<h2 class='header'>TürkAI Bilgi Merkezi</h2>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(f'<div style="background:#f8fafc; padding:20px; border-radius:10px; border:1px solid #ddd;">'
                    f'<h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with col_b:
        data = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF", data=data, file_name="TurkAI.pdf", use_container_width=True)

# --- 📥 ARAMA MOTORU ---
msg = st.chat_input("Bir konu yazın...")
if msg:
    if not kalkan(msg): st.error("🚨 Uygunsuz!")
    else:
        with st.spinner("🔎 Araştırılıyor..."):
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                s_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                r = requests.get(s_url, headers=h, timeout=10).json()
                if r.get('query', {}).get('search'):
                    baslik = r['query']['search'][0]['title']
                    wiki = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", headers=h, timeout=10)
                    soup = BeautifulSoup(wiki.text, 'html.parser')
                    for j in soup(["sup", "table", "style", "script"]): j.decompose()
                    txt = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    if txt:
                        bilgi = karakter_sigortasi("\n\n".join(txt[:6]))
                        # Kaydederken tam zamanı milisaniyesine kadar alıyoruz (Benzersiz ID için)
                        su_an = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, su_an))
                        conn.commit()
                        st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                        st.rerun()
                st.warning("Bulunamadı.")
            except: st.error("🚨 Hata!")
