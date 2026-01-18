import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GÜVENLİK ---
def sifrele(sifre): return hashlib.sha256(str.encode(sifre)).hexdigest()

def karakter_sigortasi(metin):
    if not metin: return ""
    metin = metin.replace('\xa0', ' ').replace('\u200b', '')
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = "".join(ch for ch in metin if ch.isprintable())
    return re.sub(r'\s+', ' ', metin).strip()

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_master_v65.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 🔑 OTURUM YÖNETİMİ (YENİLENİNCE GİTMEMESİ İÇİN) ---
# Streamlit'in yenilenince session'ı silmesini engellemek için geçici bir 'cache' yöntemi
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "user" not in st.session_state:
    st.session_state.user = ""

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.8rem; font-weight:bold; }
    .not-alani { background:#fff9db; padding:10px; border-radius:8px; border:1px solid #fab005; color:#862e00; font-size:0.85rem; text-align:center; margin-bottom:10px; }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 GİRİŞ / KAYIT SİSTEMİ ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v65.0</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with t2:
        y_u = st.text_input("Kullanıcı Adı Seçin", key="reg_u")
        y_p = st.text_input("Şifre Belirleyin", type="password", key="reg_p")
        if st.button("Kaydol"):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt başarılı! Giriş sekmesine geçebilirsiniz.")
                except: st.error("Kullanıcı adı mevcut.")
                conn.close()
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Sisteme Gir"):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                st.session_state.giris_yapildi = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Hatalı giriş!")
            conn.close()
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""; st.session_state.su_anki_kaynak = ""
        st.rerun()
    if st.button("🔴 Çıkışı Kapat"): 
        st.session_state.giris_yapildi = False
        st.rerun()
    st.divider()
    st.markdown("📂 **Sohbet Geçmişi**")
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih, kaynak FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i, t, l in c.fetchall():
        if st.button(f"📌 {k[:18]}", key=f"b_{t}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.su_anki_kaynak = k, i, l
            st.rerun()
    conn.close()

st.markdown("<h2 class='header'>TürkAI Akıllı Analiz Merkezi</h2>", unsafe_allow_html=True)

# --- 🖥️ ANA EKRAN ---
if st.session_state.get("analiz_sonucu"):
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="sonuc-karti">
                <h3>🔍 {st.session_state.su_anki_konu}</h3>
                {st.session_state.analiz_sonucu.replace(chr(10), "<br>")}
                {f'<br><br><hr><b>🔗 Kaynak:</b> <a href="{st.session_state.su_anki_kaynak}" target="_blank">Wikipedia</a>' if st.session_state.su_anki_kaynak else ""}
            </div>
        ''', unsafe_allow_html=True)

# --- 📥 GİRİŞ (NOT VE İŞLEM ÖNCELİĞİ) ---
st.markdown("<div class='not-alani'>💡 Not: Çarpma işlemi için lütfen (*) veya (x) kullanınız.</div>", unsafe_allow_html=True)
msg = st.chat_input("Bir şey yazın...")

if msg:
    # 1. ÖNCELİKLİ HESAPLAMA
    math_text = msg.lower().replace('x', '*')
    islem_bulucu = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", math_text)
    
    if islem_bulucu:
        try:
            islem = islem_bulucu.group(0)
            cevap = eval(islem, {"__builtins__": {}}, {})
            st.session_state.analiz_sonucu = f"🔢 Matematik Sonucu\n\n✅ {islem} = {cevap}"
            st.session_state.su_anki_konu = "Hesaplama"
            st.rerun()
        except: pass

    # 2. ARAŞTIRMA
    with st.spinner("🔍 İnceleniyor..."):
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
                    bilgi = karakter_sigortasi("\n\n".join(txt[:6]))
                    su_an = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, su_an, link))
                    conn.commit(); conn.close()
                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = bilgi, baslik, link
                    st.rerun()
            st.warning("Bilgi bulunamadı.")
        except: st.error("🚨 Sunucu hatası!")

st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:50px;'>⚠️ TürkAI hata yapabilir. Bilgileri kontrol etmeniz önerilir.</p>", unsafe_allow_html=True)
