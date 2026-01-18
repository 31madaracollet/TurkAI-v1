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

# --- 🛡️ GELİŞMİŞ TEMİZLİK VE FİLTRE MOTORU ---
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros", "ananı"]

def metni_temizle(metin):
    """Bozuk karakterleri siler ama Yunanca (τέχνη) gibi dilleri korur."""
    if not metin: return ""
    
    # 1. Gizli sistem karakterlerini ve Unicode bozukluklarını temizle
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    
    # 2. Wikipedia kaynak numaralarını [1] temizle
    metin = re.sub(r'\[\d+\]', '', metin)
    
    # 3. SADECE GERÇEKTEN BOZUK (Görünmeyen) karakterleri sil. 
    # Yunanca, Kiril ve Latin harflerini serbest bırakıyoruz.
    # Bu regex; kontrol karakterlerini ve bazı anlamsız sembolleri hedefler.
    metin = "".join(ch for ch in metin if ch.isprintable())
    
    # 4. Gereksiz çift boşlukları temizle
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin

def kalkan(metin):
    """Küfür kalkanı: Hileli yazımları (s.i.k, s1k) yakalar."""
    t = metin.lower()
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    t = t.translate(str.maketrans("01347", "oiEat"))
    t = re.sub(r'[^a-z]', '', t)
    return not any(kelime in t for kelime in KARA_LISTE)

# --- 💾 VERİTABANI ---
def get_db():
    return sqlite3.connect('turkai_v46.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF SİSTEMİ (UNİCODE DESTEKLİ) ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr_icin_guvenli(m):
        m = metni_temizle(m)
        # PDF Arial fontu Yunanca karakterleri direkt desteklemeyebilir, 
        # bu yüzden PDF'de bozulma olmaması için sembolleri koruyup formatı düzeltiyoruz.
        map = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in map.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, tr_icin_guvenli(konu), ln=1, align="C"); pdf.ln(10)
    pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, tr_icin_guvenli(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 GİRİŞ VE SESSION ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 ARAYÜZ ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .turkai-header { color: #b91c1c; text-align: center; border-bottom: 3px solid #b91c1c; padding: 10px; font-weight: bold; }
    .sonuc-karti { background: #f8fafc; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; line-height: 1.8; color: #1e293b; }
    .math-karti { background: #f0fdf4; padding: 20px; border-radius: 12px; border: 2px solid #22c55e; text-align: center; color: #166534; font-size: 1.4rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='turkai-header'>🇹🇷 TÜRKAI v46.0 - EVRENSEL DESTEK</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("🤖 Adınız nedir?")
        p = st.text_input("Şifreniz", type="password")
        if st.button("Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user, st.session_state.giris_yapildi = u, True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("⚠️ Uygunsuz veya boş isim!")
    st.stop()

# --- 🚀 ANA PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:18]}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = k, i
            st.rerun()

st.markdown("<h2 class='turkai-header'>TürkAI Bilgi Merkezi</h2>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        pdf_data = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_data, file_name=f"TurkAI_{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- 📥 GİRİŞ MOTORU ---
msg = st.chat_input("Bir konu yazın veya hesaplama yapın...")

if msg:
    if not kalkan(msg):
        st.error("🚨 TürkAI: Uygunsuz içerik engellendi!")
    else:
        # HESAPLAMA
        math_check = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
        if math_check:
            try:
                islem = math_check.group(0); cevap = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematik Sonucu\n\nİşlem: {islem}\n✅ Cevap: {cevap}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"; st.rerun()
            except: pass

        # ARŞİV ARAMA (WIKIPEDIA)
        with st.spinner("🔎 Bilgiler analiz ediliyor..."):
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                s_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                r = requests.get(s_url, headers=headers, timeout=10).json()
                
                if r.get('query', {}).get('search'):
                    baslik = r['query']['search'][0]['title']
                    wiki = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", headers=headers, timeout=10)
                    if wiki.status_code == 200:
                        soup = BeautifulSoup(wiki.text, 'html.parser')
                        for j in soup(["sup", "table", "style", "script"]): j.decompose()
                        paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                        if paragraflar:
                            bilgi = metni_temizle("\n\n".join(paragraflar[:7]))
                            conn = get_db(); c = conn.cursor()
                            c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, datetime.datetime.now()))
                            conn.commit()
                            st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                            st.rerun()
                st.warning("Sonuç bulunamadı.")
            except Exception as e: st.error("🚨 Bağlantı hatası oluştu.")
