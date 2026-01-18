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

# --- 🛡️ KARAKTER VE KÜFÜR FİLTRE MOTORU ---
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros", "ananı"]

def metni_temizle(metin):
    """Okunmayan garip karakterleri, Unicode hatalarını ve Wikipedia artıklarını temizler."""
    if not metin: return ""
    # Gizli karakterler ve Unicode bozuklukları
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    # Wikipedia kaynak numaraları [1], [12] vb.
    metin = re.sub(r'\[\d+\]', '', metin)
    # Sadece okunabilir karakterler (Harf, rakam ve temel noktalama)
    metin = re.sub(r'[^\w\s\.\,\!\?\-\:\(\)\"\']+', ' ', metin)
    # Çift boşlukları temizle
    return re.sub(r'\s+', ' ', metin).strip()

def kalkan(metin):
    """Gelişmiş Filtre Kalkanı: Harf oyunlarını (s.i.k, s1k) engeller."""
    t = metin.lower()
    # Türkçe -> İngilizce (Filtre delemesinler diye)
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    # Sayıları harfe çevir (3=e, 0=o vb)
    t = t.translate(str.maketrans("01347", "oiEat"))
    # Noktalama ve boşlukları sil
    t = re.sub(r'[^a-z]', '', t)
    return not any(kelime in t for kelime in KARA_LISTE)

# --- 💾 VERİTABANI MOTORU ---
def get_db():
    return sqlite3.connect('turkai_pro.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF OLUŞTURUCU (GÜVENLİ) ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr_pdf(m):
        m = metni_temizle(m)
        map = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in map.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, tr_pdf(konu), ln=1, align="C"); pdf.ln(10)
    pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, tr_pdf(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 SESSION & GİRİŞ ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 ARAYÜZ TASARIMI ---
st.markdown("""
    <style>
    .stApp { background: #ffffff; }
    .turkai-header { color: #b91c1c; text-align: center; border-bottom: 2px solid #b91c1c; padding: 10px; }
    .sonuc-karti { background: #f8fafc; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; line-height: 1.7; }
    .math-karti { background: #f0fdf4; padding: 20px; border-radius: 12px; border: 2px solid #22c55e; text-align: center; color: #166534; font-size: 1.3rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='turkai-header'>🇹🇷 TÜRKAI v45.5</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("🤖 Adınız nedir?")
        p = st.text_input("Şifreniz", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user = u
                st.session_state.giris_yapildi = True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("⚠️ Uygunsuz isim veya geçersiz giriş!")
    st.stop()

# --- 🚀 ANA EKRAN ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Geçmiş**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 12", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:15]}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = k, i
            st.rerun()

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
        st.download_button("📄 PDF İndir", data=pdf_v, file_name=f"{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- 📥 ARAMA & HESAPLAMA MOTORU ---
msg = st.chat_input("Konu yazın veya hesaplama yapın (Örn: 15*8)...")

if msg:
    if not kalkan(msg):
        st.error("🚨 TürkAI: Uygunsuz içerik tespit edildi!")
    else:
        # 1. HESAPLAMA SİGORTASI
        math_match = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
        if math_match:
            try:
                islem = math_match.group(0)
                cevap = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematiksel Sonuç\n\nİşlem: {islem}\n✅ Cevap: {cevap}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
                st.rerun()
            except: pass

        # 2. GÜVENLİ WIKIPEDIA ARAMA (JSON HATASI KORUMALI)
        with st.spinner("🔎 Analiz ediliyor..."):
            try:
                search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                resp = requests.get(search_url, timeout=10)
                
                if resp.status_code == 200:
                    try:
                        search_data = resp.json()
                        if search_data.get('query', {}).get('search'):
                            baslik = search_data['query']['search'][0]['title']
                            wiki_r = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", timeout=10)
                            if wiki_r.status_code == 200:
                                soup = BeautifulSoup(wiki_r.text, 'html.parser')
                                for j in soup(["sup", "table", "style", "script"]): j.decompose()
                                paragraf = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                                if paragraf:
                                    bilgi = metni_temizle("\n\n".join(paragraf[:6]))
                                    conn = get_db(); c = conn.cursor()
                                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, datetime.datetime.now()))
                                    conn.commit()
                                    st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                                    st.rerun()
                        else: st.warning("😔 Sonuç bulunamadı.")
                    except ValueError: st.error("❌ Veri okuma hatası.")
                else: st.error("🌐 Sunucuya ulaşılamıyor.")
            except Exception as e: st.error(f"🚨 Hata: {str(e)}")
    

