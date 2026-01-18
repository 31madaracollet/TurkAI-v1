import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ AYARLAR ---
st.set_page_config(page_title="TürkAI v85", page_icon="🇹🇷")

# --- 💾 VERİTABANI ---
def get_db(): 
    return sqlite3.connect('turkai_v85.db', check_same_thread=False)

conn = get_db(); c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
conn.commit()

# --- 📄 PDF SİSTEMİ ---
def pdf_olustur(baslik, metin):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        # Karakter temizleme (Hata vermemesi için)
        b = baslik.encode('latin-1', 'ignore').decode('latin-1')
        m = metin.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 10, b, ln=True)
        pdf.ln(5)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, m)
        return pdf.output()
    except: return None

# --- 🔑 GİRİŞ SİSTEMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""

if not st.session_state.user:
    st.title("🇹🇷 TürkAI Giriş")
    u = st.text_input("Kullanıcı Adı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap / Kaydol"):
        h_p = hashlib.sha256(p.encode()).hexdigest()
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        data = c.fetchone()
        if data:
            if data[1] == h_p: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı şifre!")
        else:
            c.execute("INSERT INTO users VALUES (?,?)", (u, h_p))
            conn.commit(); st.session_state.user = u; st.rerun()
    st.stop()

# --- 🚀 YAN PANEL (GEÇMİŞ) ---
with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    if st.button("🔴 Çıkış"): st.session_state.user = None; st.rerun()
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📌 {k[:20]}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu = i, k
            st.rerun()

# --- 💻 ANA EKRAN ---
st.title("TürkAI Araştırma & Hesaplama")
st.info("💡 **Not:** Çarpma işareti `*` budur. İşlem yapmak için başına **'hesapla'** yazınız (Örn: hesapla 5*5)")

msg = st.chat_input("Bir şey yazın...")

if msg:
    # 1. HESAP MAKİNESİ KONTROLÜ
    if msg.lower().startswith("hesapla"):
        try:
            islem = msg.lower().replace("hesapla", "").strip()
            sonuc = eval(islem, {"__builtins__": {}}, {})
            st.session_state.bilgi = f"🔢 İşlem: {islem}\n✅ Sonuç: {sonuc}"
            st.session_state.konu = "Hesaplama"
            st.rerun()
        except: st.error("Hesaplama hatası! Lütfen rakam ve işlem kullanın.")
    
    # 2. ARAŞTIRMA KONTROLÜ
    else:
        with st.spinner("Wikipedia taranıyor..."):
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={msg}&format=json").json()
                if r['query']['search']:
                    baslik = r['query']['search'][0]['title']
                    w = requests.get(f"https://tr.wikipedia.org/wiki/{baslik.replace(' ', '_')}")
                    soup = BeautifulSoup(w.text, 'html.parser')
                    txt = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50][:5])
                    st.session_state.bilgi, st.session_state.konu = txt, baslik
                    
                    # Geçmişe kaydet (Aynı konu yoksa kaydet bug önleyici)
                    c.execute("SELECT * FROM aramalar WHERE kullanici=? AND konu=?", (st.session_state.user, baslik))
                    if not c.fetchone():
                        c.execute("INSERT INTO aramalar VALUES (?,?,?,?)", (st.session_state.user, baslik, txt, str(datetime.datetime.now())))
                        conn.commit()
                    st.rerun()
                else: st.warning("Sonuç bulunamadı.")
            except: st.error("Bağlantı hatası!")

# --- 📊 ÇIKTI VE PDF ---
if st.session_state.bilgi:
    st.write("---")
    # PDF Butonu
    pdf_byt = pdf_olustur(st.session_state.konu, st.session_state.bilgi)
    if pdf_byt:
        st.download_button(
            label="📥 Bu bilgiyi pdf olarak indir(pdfyi düzenlemeyi unutmayın)",
            data=bytes(pdf_byt),
            file_name=f"{st.session_state.konu}.pdf",
            mime="application/pdf"
        )
    
    st.subheader(st.session_state.konu)
    st.write(st.session_state.bilgi)
