import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ AYARLAR ---
st.set_page_config(page_title="TürkAI v91", page_icon="🇹🇷", layout="wide")

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_v91_master.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT)')
conn.commit()

# --- 📄 PDF SİSTEMİ ---
def pdf_olustur(baslik, metin, kaynak):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        b = baslik.encode('latin-1', 'ignore').decode('latin-1')
        m = metin.encode('latin-1', 'ignore').decode('latin-1')
        k = f"Kaynak: {kaynak}".encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, k, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- 🔑 HAFIZALI GİRİŞ SİSTEMİ ---
url_params = st.query_params
if "u" in url_params and "user" not in st.session_state:
    st.session_state.user = url_params["u"]

if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "kaynak_link" not in st.session_state: st.session_state.kaynak_link = ""

if not st.session_state.user:
    st.markdown("<h1 style='text-align: center; color: #b91c1c;'>🇹🇷 TürkAI Giriş</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sistemi Başlat", use_container_width=True):
            h_p = hashlib.sha256(p.encode()).hexdigest()
            c.execute("SELECT * FROM users WHERE username=?", (u,))
            user_data = c.fetchone()
            if user_data:
                if user_data[1] == h_p:
                    st.session_state.user = u
                    st.query_params["u"] = u
                    st.rerun()
                else: st.error("Hatalı şifre!")
            else:
                c.execute("INSERT INTO users VALUES (?,?)", (u, h_p))
                conn.commit()
                st.session_state.user = u
                st.query_params["u"] = u
                st.rerun()
    st.stop()

# --- 🚀 YAN PANEL ---
with st.sidebar:
    st.markdown(f"### 👤 **{st.session_state.user}**")
    if st.button("🔴 Çıkış Yap", use_container_width=True):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik, link FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, l in c.fetchall():
        if st.button(f"📌 {k[:20]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.kaynak_link = i, k, l
            st.rerun()

# --- 💻 ANA EKRAN ---
st.markdown("<h2 style='color: #b91c1c;'>TürkAI Araştırma Paneli</h2>", unsafe_allow_html=True)
st.info("💡 **Hesapla:** İşlemin başına 'hesapla' yazın. Örn: `hesapla (50*2)/4` | **Arat:** Sadece konuyu yazın.")

msg = st.chat_input("Mesajınızı buraya yazın...")

if msg:
    if msg.lower().startswith("hesapla"):
        try:
            islem = msg.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"🔢 İşlem: {islem}\n✅ Sonuç: {sonuc}"
            st.session_state.konu = "Hesaplama"
            st.session_state.kaynak_link = "TürkAI Matematik Modülü"
            st.rerun()
        except: st.error("Hesaplama yapılamadı. Formatı kontrol edin.")
    else:
        with st.spinner("Wikipedia taranıyor..."):
            try:
                # Kimlik kartı (User-Agent) ekleyerek engeli aşıyoruz
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                
                search_url = f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json"
                r = requests.get(search_url, headers=headers).json()
                
                if r.get('query', {}).get('search'):
                    baslik = r['query']['search'][0]['title']
                    wiki_link = f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}"
                    
                    page_res = requests.get(wiki_link, headers=headers)
                    soup = BeautifulSoup(page_res.text, 'html.parser')
                    
                    # Sayfa içeriğini temizle ve al
                    for script in soup(["script", "style"]): script.decompose()
                    txt_list = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 40]
                    txt = "\n\n".join(txt_list[:6])
                    
                    if not txt: txt = "Sayfa içeriği tam olarak çekilemedi, lütfen linke göz atın."

                    st.session_state.bilgi, st.session_state.konu = txt, baslik
                    st.session_state.kaynak_link = wiki_link
                    
                    # Geçmişe kaydet
                    c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now()), wiki_link))
                    conn.commit()
                    st.rerun()
                else: st.warning("Maalesef sonuç bulunamadı.")
            except Exception as e:
                st.error(f"Bağlantı Hatası: {e}. Lütfen internetinizi veya Wikipedia erişiminizi kontrol edin.")

# --- 📊 SONUÇ ---
if st.session_state.bilgi:
    st.write("---")
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi, st.session_state.kaynak_link)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"{st.session_state.konu}.pdf",
            mime="application/pdf"
        )
    
    st.subheader(f"🔍 {st.session_state.konu}")
    st.write(st.session_state.bilgi)
    if "http" in st.session_state.kaynak_link:
        st.markdown(f"📍 **Atıf:** Bu bilgiler [Wikipedia ({st.session_state.konu})]({st.session_state.kaynak_link}) üzerinden alınmıştır.")
    else:
        st.caption(f"📍 {st.session_state.kaynak_link}")
