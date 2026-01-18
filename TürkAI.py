import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GÜVENLİK & ŞİFRELEME ---
def sifrele(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros"]

def karakter_sigortasi(metin):
    if not metin: return ""
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = "".join(ch for ch in metin if ch.isprintable())
    return re.sub(r'\s+', ' ', metin).strip()

# --- 💾 VERİTABANI ---
def get_db():
    return sqlite3.connect('turkai_master_v2.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 🔑 SESSION YÖNETİMİ ---
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "user" not in st.session_state: st.session_state.user = ""
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""
if "su_anki_kaynak" not in st.session_state: st.session_state.su_anki_kaynak = ""

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.4rem; font-weight:bold; margin-bottom:15px; }
    .kaynak-label { font-size:0.9rem; color:#2563eb; font-weight:bold; text-decoration:none; }
    .footer-note { text-align:center; color:#64748b; font-size:0.85rem; margin-top:20px; font-style: italic; }
    .footer-uyari { text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:40px; border-top:1px solid #f1f5f9; padding-top:10px; }
    </style>
""", unsafe_allow_html=True)

# --- 🔑 GİRİŞ VE KAYIT ---
if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v61.0</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t2:
        y_u = st.text_input("Kullanıcı Adı", key="reg_u")
        y_p = st.text_input("Şifre", type="password", key="reg_p")
        if st.button("Kaydol"):
            if y_u and y_p:
                conn = get_db(); c = conn.cursor()
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (y_u, sifrele(y_p)))
                    conn.commit(); st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                except: st.error("Bu kullanıcı zaten var!")
                conn.close()
    with t1:
        u = st.text_input("Kullanıcı Adı", key="log_u")
        p = st.text_input("Şifre", type="password", key="log_p")
        if st.button("Giriş"):
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sifrele(p)))
            if c.fetchone():
                st.session_state.giris_yapildi, st.session_state.user = True, u
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
    if st.button("🔴 Çıkış Yap"): st.session_state.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih, kaynak FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i, t, l in c.fetchall():
        if st.button(f"📌 {k[:18]}", key=f"b_{t}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.su_anki_kaynak = k, i, l
            st.rerun()
    conn.close()

# --- 🖥️ ANA EKRAN ---
st.markdown("<h2 class='header'>TürkAI Bilgi ve Analiz</h2>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="sonuc-karti">
                <h3>🔍 {st.session_state.su_anki_konu}</h3>
                {st.session_state.analiz_sonucu.replace(chr(10), "<br>")}
                {f'<br><br><hr><b>🔗 Kaynak:</b> <a href="{st.session_state.su_anki_kaynak}" class="kaynak-label" target="_blank">Wikipedia</a>' if st.session_state.su_anki_kaynak else ""}
            </div>
        ''', unsafe_allow_html=True)

# --- 📥 AKILLI GİRİŞ ---
msg = st.chat_input("Mesajınızı yazın...")
st.markdown("<div class='footer-note'>💡 Not: Çarpma işlemi için lütfen (*) işaretini kullanınız. (Örn: 5*4)</div>", unsafe_allow_html=True)

if msg:
    # 1. AKILLI HESAPLAMA (x harfini * ile otomatik düzeltme özelliği eklendi)
    math_msg = msg.lower().replace('x', '*') 
    islem_bulucu = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", math_msg)
    
    if islem_bulucu:
        try:
            temiz_islem = islem_bulucu.group(0)
            cevap = eval(temiz_islem, {"__builtins__": {}}, {})
            st.session_state.analiz_sonucu = f"🔢 Matematiksel Sonuç\n\nSoru: {msg}\n✅ Cevap: {cevap}"
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
                    bilgi = karakter_sigortasi("\n\n".join(txt[:6]))
                    su_an = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, su_an, link))
                    conn.commit(); conn.close()
                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = bilgi, baslik, link
                    st.rerun()
            st.warning("Bilgi bulunamadı.")
        except: st.error("🚨 Sunucu hatası!")

st.markdown("<div class='footer-uyari'>⚠️ TürkAI hata yapabilir. Bilgileri doğrulamayı unutmayın.</div>", unsafe_allow_html=True)
