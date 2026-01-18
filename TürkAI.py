import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import hashlib

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Pro v45.2", page_icon="🇹🇷", layout="wide")

# --- 🛡️ GELİŞMİŞ GÜVENLİK VE FİLTRE MOTORU ---
KARA_LISTE = [
    "amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak",
    "ibne", "kahpe", "yavsak", "gerizekali", "salak", "aptal",
    "serefsiz", "namussuz", "pezevenk", "fahise", "oros"
]

def kalkan(metin):
    """Filtre delme taktiklerini (s.i.k, s1k, şik) engeller."""
    # Küçük harfe çevir
    t = metin.lower()
    # Türkçe karakterleri İngilizce karşılıklarına çevir (Filtreleme kolaylığı için)
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    # Harf yerine kullanılan sayıları temizle (0=o, 1=i, 3=e, 4=a, 7=t)
    num_map = str.maketrans("01347", "oiEat")
    t = t.translate(num_map)
    # Harf dışındaki tüm karakterleri (nokta, boşluk, virgül) kaldır
    t = re.sub(r'[^a-z]', '', t)
    
    for kelime in KARA_LISTE:
        if kelime in t:
            return False
    return True

# --- 💾 VERİTABANI VE DİĞER FONKSİYONLAR ---
def get_db():
    return sqlite3.connect('turkai_v45_2.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr_pdf(m): # PDF için Türkçe karakter temizliği
        map = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in map.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, tr_pdf(konu), ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, tr_pdf(re.sub('<[^<]+?>', '', icerik)))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 SESSION & F5 KORUMASI ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 ARAYÜZ ---
st.markdown("<style>.stApp{background:#fff;} .turkai-header{color:#b91c1c; text-align:center; border-bottom:2px solid #b91c1c;}</style>", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='turkai-header'>🇹🇷 TÜRKAI v45.2 - GÜVENLİ WEB</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("🤖 Adınız nedir?")
        p = st.text_input("Şifreniz", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("⚠️ Uygunsuz isim veya hatalı giriş!")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş Aramalar**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:15]}...", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = k, i
            st.rerun()

st.title("TürkAI Bilgi Merkezi")

# --- SONUÇ GÖSTERİMİ ---
if st.session_state.analiz_sonucu:
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f'<div style="background:#f8fafc; padding:20px; border-radius:10px; border:1px solid #ddd;">'
                    f'<h3>{st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        pdf_v = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_v, file_name=f"{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- 📥 ARAMA & HESAPLAMA ---
msg = st.chat_input("Konu yazın veya hesaplama yapın...")

if msg:
    if not kalkan(msg):
        st.error("🚨 TürkAI: Uygunsuz içerik veya filtre delme girişimi tespit edildi!")
    else:
        # 1. HESAPLAMA
        math_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
        if math_match:
            try:
                islem = math_match.group(0)
                cevap = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematiksel Sonuç\n\nİşlem: {islem}\n✅ Cevap: {cevap}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
                st.rerun()
            except: pass

        # 2. WIKIPEDIA (GÜÇLENDİRİLMİŞ ARAMA)
        with st.spinner("🔎 Bilgiler analiz ediliyor..."):
            search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
            search_res = requests.get(search_url).json()
            if search_res.get('query', {}).get('search'):
                baslik = search_res['query']['search'][0]['title']
                r = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}")
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for j in soup(["sup", "table", "style", "script"]): j.decompose()
                    paragraf = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    if paragraf:
                        bilgi = "\n\n".join(paragraf[:6])
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, datetime.datetime.now()))
                        conn.commit()
                        st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                        st.rerun()
            st.warning("Bu konuda sonuç bulunamadı.")
    
