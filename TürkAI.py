import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
import socket
from PyPDF2 import PdfReader # PDF okuyucu eklendi

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GÜVENLİK & KİMLİK ---
def sifrele(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

def get_device_id():
    return hashlib.md5(socket.gethostname().encode()).hexdigest()

# --- 💾 VERİTABANI (MASTER) ---
def get_db(): 
    return sqlite3.connect('turkai_master_v67.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, device_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 🔑 OTURUM SABİTLEYİCİ ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
    st.session_state.user = ""
    did = get_device_id()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT username FROM users WHERE device_id=?", (did,))
    row = c.fetchone()
    if row:
        st.session_state.user = row[0]
        st.session_state.giris_yapildi = True
    conn.close()

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.8rem; font-weight:bold; }
    .not-kutusu { background:#fff9db; padding:12px; border-radius:10px; border:1px solid #fab005; color:#862e00; font-size:0.9rem; text-align:center; margin-bottom:15px; font-weight:bold; }
    .pdf-bilgi { background:#e2e8f0; padding:15px; border-radius:10px; border-left:5px solid #64748b; margin-bottom:10px; }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v76.0</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol ve Bu Cihazda Hatırla"):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (y_u, sifrele(y_p), get_device_id()))
                    conn.commit(); st.success("Kayıt başarılı!")
                except: st.error("Bu isim alınmış!")
                conn.close()
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sistemi Aç"):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                c.execute("UPDATE users SET device_id=? WHERE username=?", (get_device_id(), u))
                conn.commit()
                st.session_state.giris_yapildi, st.session_state.user = True, u
                st.rerun()
            else: st.error("Hatalı!")
            conn.close()
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    
    # 📄 PDF YÜKLEME ALANI
    st.divider()
    st.markdown("### 📄 PDF Analiz Motoru")
    pdf_dosya = st.file_uploader("Bir PDF dosyası yükle", type="pdf")
    
    if pdf_dosya:
        with st.spinner("PDF okunuyor..."):
            reader = PdfReader(pdf_dosya)
            pdf_metni = ""
            for page in reader.pages:
                pdf_metni += page.extract_text()
            st.session_state.analiz_sonucu = pdf_metni
            st.session_state.su_anki_konu = f"Dosya: {pdf_dosya.name}"
            st.session_state.su_anki_kaynak = "Yüklenen PDF"
            st.success("PDF Başarıyla Okundu!")

    st.divider()
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.rerun()
    if st.button("🔴 Oturumu Tamamen Kapat", use_container_width=True):
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE users SET device_id=NULL WHERE username=?", (st.session_state.user,))
        conn.commit(); conn.close()
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.markdown("📂 **Eski Kayıtların**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih, kaynak FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i, t, l in c.fetchall():
        if st.button(f"📌 {k[:18]}", key=f"h_{t}", use_container_width=True):
            st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = i, k, l
            st.rerun()
    conn.close()

st.markdown("<h2 class='header'>TürkAI Akıllı Analiz Sistemi</h2>", unsafe_allow_html=True)

# --- 📟 ÇIKTI ALANI ---
if st.session_state.get("analiz_sonucu"):
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        # Eğer içerik PDF'den geliyorsa özel kutu kullan
        st.markdown(f'''
            <div class="sonuc-karti">
                <h3>🔍 {st.session_state.su_anki_konu}</h3>
                {st.session_state.analiz_sonucu.replace(chr(10), "<br>")}
                <br><br><hr>
                <b>🔗 Kaynak:</b> {st.session_state.su_anki_kaynak}
            </div>
        ''', unsafe_allow_html=True)

# --- 📥 GİRİŞ ---
st.markdown("<div class='not-kutusu'>💡 İşlem yapacaksanız başına hesapla koyunuz ve çarpma için (*) veya (x) kullanın. Sorucağınız şeyin sonuna noktalama işareti koymayınız.</div>", unsafe_allow_html=True)
msg = st.chat_input("Buraya yazın...")

if msg:
    # 1. HESAPLAMA
    math_msg = msg.lower().replace('x', '*')
    islem_ara = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", math_msg)
    if islem_ara:
        try:
            islem = islem_ara.group(0)
            st.session_state.analiz_sonucu = f"🔢 Matematik Sonucu\n\n✅ {islem} = {eval(islem, {'__builtins__': {}}, {})}"
            st.session_state.su_anki_konu = "Hesaplama"
            st.rerun()
        except: pass

    # 2. ARAŞTIRMA
    with st.spinner("🔎 Araştırılıyor..."):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json", headers=h).json()
            if res.get('query', {}).get('search'):
                baslik = res['query']['search'][0]['title']
                link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                wiki = requests.get(link, headers=h, timeout=10)
                soup = BeautifulSoup(wiki.text, 'html.parser')
                for j in soup(["sup", "table", "style", "script"]): j.decompose()
                txt = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if txt:
                    bilgi = "".join(ch for ch in "\n\n".join(txt[:6]) if ch.isprintable())
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, str(datetime.datetime.now()), link))
                    conn.commit(); conn.close()
                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = bilgi, baslik, link
                    st.rerun()
            st.warning("Sonuç bulunamadı.")
        except: st.error("Sunucu hatası!")
