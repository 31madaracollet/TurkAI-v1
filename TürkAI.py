import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GÜVENLİK & KARAKTER SİGORTASI (EN İYİ HALİ) ---
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

# --- 💾 VERİTABANI MOTORU (OTOMATİK ONARICI) ---
def get_db():
    return sqlite3.connect('turkai_v54.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, kaynak TEXT)')
    # Eğer eski tablodan geliyorsa ve 'kaynak' sütunu yoksa ekle (Hata almamak için)
    try:
        c.execute('ALTER TABLE aramalar ADD COLUMN kaynak TEXT')
    except: pass 
    conn.commit(); conn.close()

db_baslat()

# --- 🔑 SESSION ---
if "user" not in st.session_state: st.session_state.user = "Misafir"
if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""
if "su_anki_kaynak" not in st.session_state: st.session_state.su_anki_kaynak = ""

# --- 🎨 ARAYÜZ TASARIMI ---
st.markdown("""
    <style>
    .stApp { background:#fff; }
    .header { color:#b91c1c; text-align:center; border-bottom:3px solid #b91c1c; padding:10px; font-weight:bold; }
    .sonuc-karti { background:#f8fafc; padding:25px; border-radius:15px; border:1px solid #e2e8f0; line-height:1.7; position: relative; }
    .math-karti { background:#f0fdf4; padding:20px; border-radius:12px; border:2px solid #22c55e; text-align:center; color:#166534; font-size:1.4rem; font-weight:bold; margin-bottom: 20px; }
    .kaynak-label { font-size:0.85rem; color:#64748b; margin-top:20px; padding-top:10px; border-top:1px dashed #cbd5e1; }
    .footer-uyari { text-align:center; color:#94a3b8; font-size:0.85rem; margin-top:50px; padding:20px; border-top:1px solid #f1f5f9; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='header'>🇹🇷 TÜRKAI v54.0</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("🤖 Adınız nedir?")
        if st.button("Sistemi Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.rerun()
            else: st.error("⚠️ Uygunsuz isim!")
    st.stop()

# --- 🚀 YAN PANEL (YENİ SOHBET & GEÇMİŞ) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("➕ Yeni Sohbet Oluştur", use_container_width=True):
        st.session_state.analiz_sonucu = None
        st.session_state.su_anki_konu = ""
        st.session_state.su_anki_kaynak = ""
        st.rerun()
    st.divider()
    st.markdown("📂 **Sohbet Geçmişi**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik, tarih, kaynak FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for konu, icerik, tarih, kaynak in c.fetchall():
        if st.button(f"📌 {konu[:16]}", key=f"h_{tarih}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = konu, icerik
            st.session_state.su_anki_kaynak = kaynak if kaynak else "Kaynak belirtilmemiş"
            st.rerun()

st.markdown("<h2 class='header'>TürkAI Akıllı Analiz Sistemi</h2>", unsafe_allow_html=True)

# --- 🖥️ ANA EKRAN GÖSTERİMİ ---
if st.session_state.analiz_sonucu:
    if "🔢" in st.session_state.analiz_sonucu:
        st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
            <div class="sonuc-karti">
                <h3>🔍 {st.session_state.su_anki_konu}</h3>
                {st.session_state.analiz_sonucu.replace(chr(10), "<br>")}
                <div class="kaynak-label">
                    <b>🔗 Kaynaklar:</b><br>
                    <a href="{st.session_state.su_anki_kaynak}" target="_blank">{st.session_state.su_anki_kaynak}</a>
                </div>
            </div>
        ''', unsafe_allow_html=True)

# --- 📥 GİRİŞ (HESAP MAKİNESİ + ARAŞTIRMA) ---
msg = st.chat_input("Bir konu yazın veya hesap yapın (Örn: 25*4)...")

if msg:
    if not kalkan(msg):
        st.error("🚨 Uygunsuz içerik engellendi!")
    else:
        # 1. HESAP MAKİNESİ (ÖNCELİKLİ)
        if re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg):
            try:
                sonuc = eval(msg, {"__builtins__": {}}, {})
                res = f"🔢 Matematiksel Sonuç\n\nİşlem: {msg}\n✅ Cevap: {sonuc}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
                st.rerun()
            except: pass

        # 2. ARAŞTIRMA MOTORU
        with st.spinner("🔎 Bilgiler analiz ediliyor..."):
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
                        
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, bilgi, su_an, link))
                        conn.commit()
                        
                        st.session_state.analiz_sonucu, st.session_state.su_anki_konu, st.session_state.su_anki_kaynak = bilgi, baslik, link
                        st.rerun()
                st.warning("😔 Üzgünüm, bu konuda bilgi bulamadım.")
            except:
                st.error("🚨 Sunucu ile bağlantı kurulamadı. Lütfen tekrar deneyin.")

# --- ⚠️ ALT BİLGİ UYARISI ---
st.markdown("<div class='footer-uyari'>⚠️ TürkAI hata yapabilir. Önemli bilgileri kontrol etmenizi öneririz.</div>", unsafe_allow_html=True)
