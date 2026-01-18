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
KARA_LISTE = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros", "ananı"]

def metni_pırıl_pırıl_yap(metin):
    """Gereksiz sembolleri, Unicode hatalarını ve Wikipedia artıklarını temizler."""
    if not metin: return ""
    # Gizli karakterler ve Unicode bozuklukları temizliği
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    # Wikipedia kaynak numaraları [1], [12] vb. temizliği
    metin = re.sub(r'\[\d+\]', '', metin)
    # Sadece okunabilir temel karakterleri tut (Harf, rakam, temel noktalama)
    metin = re.sub(r'[^\w\s\.\,\!\?\-\:\(\)\"\']+', ' ', metin)
    # Çift boşlukları ve satır başlarını düzenle
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin

def kalkan(metin):
    """Gelişmiş Filtre Kalkanı: Küfürleri ve filtre delme taktiklerini engeller."""
    t = metin.lower()
    # Türkçe -> İngilizce karakter eşleme
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    # Sayıları harfe çevir (s1k -> sik gibi)
    t = t.translate(str.maketrans("01347", "oiEat"))
    # Noktalama ve boşlukları silerek bitişik kontrol et
    t = re.sub(r'[^a-z]', '', t)
    return not any(kelime in t for kelime in KARA_LISTE)

# --- 💾 VERİTABANI YÖNETİMİ ---
def get_db():
    return sqlite3.connect('turkai_final_data.db', check_same_thread=False)

def db_baslat():
    conn = get_db(); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit(); conn.close()

db_baslat()

# --- 📄 PDF SİSTEMİ (HATASIZ TÜRKÇE) ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr_duzelt(m):
        m = metni_pırıl_pırıl_yap(m)
        mapping = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in mapping.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, tr_duzelt(konu), ln=1, align="C"); pdf.ln(10)
    pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, tr_duzelt(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 🔑 GİRİŞ VE SESSION YÖNETİMİ ---
if "u" in st.query_params and "user" not in st.session_state:
    st.session_state.user = st.query_params["u"]
    st.session_state.giris_yapildi = True

if "giris_yapildi" not in st.session_state: st.session_state.giris_yapildi = False
if "analiz_sonucu" not in st.session_state: st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state: st.session_state.su_anki_konu = ""

# --- 🎨 ARAYÜZ (KOYU KIRMIZI & BEYAZ) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .turkai-header { color: #b91c1c; text-align: center; border-bottom: 3px solid #b91c1c; padding: 15px; font-weight: bold; }
    .sonuc-karti { background: #f8fafc; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; line-height: 1.8; color: #1e293b; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .math-karti { background: #f0fdf4; padding: 20px; border-radius: 12px; border: 2px solid #22c55e; text-align: center; color: #166534; font-size: 1.4rem; font-weight: bold; }
    .sidebar-text { font-size: 0.9rem; color: #64748b; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.giris_yapildi:
    st.markdown("<h1 class='turkai-header'>🇹🇷 TÜRKAI v45.8 - GÜVENLİ ERİŞİM</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("🤖 Kullanıcı Adınız?")
        p = st.text_input("Şifreniz", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            if kalkan(u) and len(u) > 1:
                st.session_state.user = u
                st.session_state.giris_yapildi = True
                st.query_params["u"] = u
                st.rerun()
            else: st.error("⚠️ Geçersiz veya uygunsuz kullanıcı adı!")
    st.stop()

# --- 🚀 YAN PANEL (GEÇMİŞ) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔴 Çıkış Yap", use_container_width=True):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    st.markdown("📂 **Analiz Geçmişi**")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 15", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:18]}", use_container_width=True):
            st.session_state.su_anki_konu, st.session_state.analiz_sonucu = k, i
            st.rerun()

# --- 🖥️ ANA EKRAN ---
st.markdown("<h2 class='turkai-header'>TürkAI Bilgi ve Araştırma Merkezi</h2>", unsafe_allow_html=True)

if st.session_state.analiz_sonucu:
    c1, c2 = st.columns([4, 1])
    with c1:
        if "🔢" in st.session_state.analiz_sonucu:
            st.markdown(f'<div class="math-karti">{st.session_state.analiz_sonucu}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sonuc-karti"><h3>🔍 {st.session_state.su_anki_konu}</h3>{st.session_state.analiz_sonucu.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with c2:
        pdf_data = pdf_yap(st.session_state.su_anki_konu, st.session_state.analiz_sonucu)
        st.download_button("📄 PDF İndir", data=pdf_data, file_name=f"TurkAI_{st.session_state.su_anki_konu}.pdf", use_container_width=True)

# --- 📥 AKILLI GİRİŞ (HESAPLAMA VE ARAMA) ---
msg = st.chat_input("Bir konu yazın veya hesaplama yapın (Örn: 1024/8)...")

if msg:
    if not kalkan(msg):
        st.error("🚨 TürkAI: Uygunsuz içerik veya filtre delme girişimi engellendi!")
    else:
        # 1. HESAPLAMA MODÜLÜ
        math_check = re.search(r"(\d+[\s\+\-\*\/\(\)\.]+\d+)", msg)
        if math_check:
            try:
                islem = math_check.group(0)
                cevap = eval(islem, {"__builtins__": {}}, {})
                res = f"🔢 Matematiksel Sonuç\n\nİşlem: {islem}\n✅ Cevap: {cevap}"
                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = res, "Hesaplama"
                st.rerun()
            except: pass

        # 2. GELİŞMİŞ WIKIPEDIA MOTORU (USER-AGENT VE HATA KORUMALI)
        with st.spinner("🔎 Bilgi havuzu taranıyor..."):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                # API Arama
                search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                resp = requests.get(search_url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('query', {}).get('search'):
                        baslik = data['query']['search'][0]['title']
                        # Sayfa Çekme
                        wiki_r = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}", headers=headers, timeout=10)
                        if wiki_r.status_code == 200:
                            soup = BeautifulSoup(wiki_r.text, 'html.parser')
                            # Çöp temizleme
                            for j in soup(["sup", "table", "style", "script", "link"]): j.decompose()
                            paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                            
                            if paragraflar:
                                bilgi = metni_pırıl_pırıl_yap("\n\n".join(paragraflar[:7]))
                                # Veritabanı Kayıt
                                conn = get_db(); c = conn.cursor()
                                c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, bilgi, datetime.datetime.now()))
                                conn.commit()
                                st.session_state.analiz_sonucu, st.session_state.su_anki_konu = bilgi, baslik
                                st.rerun()
                        else: st.error("🌐 Sayfa içeriği çekilemedi.")
                    else: st.warning("😔 Wikipedia'da bu konuda sonuç bulunamadı.")
                else: st.error(f"🌐 Sunucu Hatası: {resp.status_code}")
            except Exception as e:
                st.error(f"🚨 Bağlantı kesildi veya hata oluştu. Lütfen tekrar deneyin.")


