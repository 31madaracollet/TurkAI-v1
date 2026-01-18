import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GÜVENLİK & KARAKTER SİGORTASI (BOZULMADI) ---
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros"]

def karakter_sigortasi(metin):
    if not metin: return ""
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = "".join(ch for ch in metin if ch.isprintable())
    return re.sub(r'\s+', ' ', metin).strip()

def kalkan(metin):
    t = metin.lower()
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    t = t.translate(str.maketrans("01347", "oiEat"))
    t = re.sub(r'[^a-z]', '', t)
    return not any(kelime in t for kelime in KARA_LISTE)

# --- 💾 VERİTABANI ---
def get_db():
    return sqlite3.connect('turkai_v53.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 🔑 SESSION ---
if "user" not in st.session_state: st.session_state.user = "Misafir"
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""
if "su_anki_kaynak" not in st.session_state: st.session_state.su_anki_kaynak = ""

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.4rem; font-weight:bold; }
    .kaynak-text { font-size:0.85rem; color:#64748b; margin-top:20px; padding-top:10px; border-top:1px solid #e2e8f0; }
    .footer { text-align:center; color:#94a3b8; font-size:0.8rem; padding:20px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v53.0</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("🤖 Adınız nedir?")
        if st.button("Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.rerun()
            else: st.error("⚠️ Uygunsuz isim!")
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""; st.session_state.su_anki_kaynak = ""
        st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih, kaynak FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for konu, icerik, tarih, kaynak in c.fetchall():
        if st.button(f"📌 {konu[:15]}", key=f"h_{tarih}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = konu, icerik
            st.session_state.su_anki_kaynak = kaynak
            st.rerun()

st.markdown("<h2 class='header'>TürkAI Araştırma Merkezi</h2>", unsafe_allow_html=True)

# --- 🖥️ EKRAN GÖSTERİMİ ---
if st.session_state.analiz_sonucu:
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}'
                    f'<div class="kaynak-text"><b>🔗 Kaynaklar:</b><br>{st.session_state.su_anki_kaynak}</div></div>', unsafe_allow_html=True)

# --- 📥 GİRİŞ (HESAP MAKİNESİ + ARAŞTIRMA) ---
msg = st.chat_input("Bir konu yazın veya hesap yapın...")

if msg:
    if not kalkan(msg): st.error("🚨 Uygunsuz!")
    else:
        # 1. HESAP MAKİNESİ (SABİT VE BOZULMADI)
        math_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
        if math_match:
            try:
                islem = math_match.group(0); sonuc = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematik Sonucu\n\nİşlem: {islem}\n✅ Cevap: {sonuc}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"; st.rerun()
            except: pass

        # 2. ARAŞTIRMA MOTORU
        with st.spinner("🔎 Analiz ediliyor..."):
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                s_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                r = requests.get(s_url, headers=h, timeout=10).json()
                if r.get('query', {}).get('search'):
                    baslik = r['query']['search'][0]['title']
                    link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    wiki = requests.get(link, headers=h, timeout=10)
                    soup = BeautifulSoup(wiki.text, 'html.parser')
                    for j in soup(["sup", "table", "style", "script"]): j.decompose()
                    txt = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    if txt:
                        bilgi = karakter_sigortasi("\n\n".join(txt[:6]))
                        su_an = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        # Veritabanına kaynağıyla kaydet
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, su_an, link))
                        conn.commit()
                        st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = bilgi, baslik, link
                        st.rerun()
                st.warning("Sonuç bulunamadı.")
            except: st.error("🚨 Sunucu hatası!")

# --- ⚠️ HATA UYARISI (EN ALTA) ---
st.markdown("<div class='footer'>⚠️ TürkAI hata yapabilir. Önemli bilgileri kontrol etmenizi öneririz.</div>", unsafe_allow_html=True)
