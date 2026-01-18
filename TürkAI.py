import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
from fpdf import FPDF

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI Analiz Merkezi", page_icon="🇹🇷", layout="wide")

# --- 🎨 CHAT VE KIRMIZI TEMA TASARIMI ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { color: #cc0000 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 3px solid #cc0000; }
    
    .user-msg {
        background-color: #cc0000;
        color: white;
        padding: 12px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 15px;
        width: fit-content;
        max-width: 70%;
        margin-left: auto;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    .ai-msg {
        background-color: #f0f2f6;
        color: #333;
        padding: 15px;
        border-radius: 15px 15px 15px 0px;
        margin-bottom: 20px;
        width: fit-content;
        max-width: 85%;
        border-left: 5px solid #cc0000;
    }
    
    div.stButton > button {
        background-color: #cc0000 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai_v121_chat.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, link TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 GİRİŞ ---
if "u" in st.query_params: st.session_state.user = st.query_params["u"]
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None

if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, col2, c3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🇹🇷 TürkAI</h1>", unsafe_allow_html=True)
        mod = st.radio("Seçim:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
        u_in = st.text_input("Kullanıcı")
        p_in = st.text_input("Şifre", type="password")
        if st.button("Başlat"):
            h_p = hashlib.sha256(p_in.encode()).hexdigest()
            if mod == "Giriş Yap":
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in; st.query_params["u"] = u_in; st.rerun()
                else: st.warning("Bilgiler uyuşmadı.")
            else:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (u_in, h_p)); conn.commit()
                    st.session_state.user = u_in; st.query_params["u"] = u_in; st.rerun()
                except: st.warning("Bu kullanıcı zaten kayıtlı.")
    st.stop()

# --- 🚀 PANEL ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    if st.button("🔴 Çıkış"):
        st.session_state.clear(); st.query_params.clear(); st.rerun()
    st.divider()
    m_secim = st.radio("Motor:", ["V1 (Wikipedia)", "V2 (Sözlük/Teknik)", "V3 (Hesap Makinesi)"])
    
    if m_secim == "V3 (Hesap Makinesi)":
        st.warning("⚠️ Not: Çarpma işareti (*) sembolüdür.")
    
    st.divider()
    st.subheader("📂 Geçmiş")
    c.execute("SELECT konu, icerik, motor FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 10", (st.session_state.user,))
    for k, i, m in c.fetchall():
        if st.button(f"📌 [{m}] {k[:15]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.son_sorgu = i, k
            st.rerun()

# --- 💬 CHAT EKRANI ---
st.markdown("<h2 style='border-bottom: 2px solid #cc0000;'>TürkAI Analiz Terminali</h2>", unsafe_allow_html=True)

sorgu = st.chat_input("Mesajınızı yazın...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # --- V3 HESAP MAKİNESİ ---
    if m_secim == "V3 (Hesap Makinesi)":
        try:
            # Güvenli matematik temizliği
            temiz_islem = "".join(char for char in sorgu if char in "0123456789+-*/(). ")
            res = eval(temiz_islem, {"__builtins__": {}}, {})
            info, head = f"🔢 Hesaplama Sonucu: {res}", "Matematik"
            c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih, motor) VALUES (?,?,?,?,?)", (st.session_state.user, head, info, str(datetime.datetime.now()), "V3"))
            conn.commit(); st.session_state.bilgi = info; st.rerun()
        except:
            st.session_state.bilgi = "⚠️ İşlem anlaşılamadı. Lütfen sadece sayı ve matematiksel işaretler kullanın."

    # --- V1 WIKIPEDIA ---
    elif m_secim == "V1 (Wikipedia)":
        try:
            r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
            if r['query']['search']:
                head = r['query']['search'][0]['title']
                link = f"https://tr.wikipedia.org/wiki/{head.replace(' ', '_')}"
                soup = BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser')
                info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
                c.execute("INSERT INTO aramalar (kullanici, konu, icerik, tarih, motor, link) VALUES (?,?,?,?,?,?)", (st.session_state.user, head, info, str(datetime.datetime.now()), "V1", link))
                conn.commit(); st.session_state.bilgi = info; st.rerun()
            else:
                st.session_state.bilgi = "🔍 Üzgünüm, bu konuyla ilgili bir kayıt bulamadım."
        except:
            st.session_state.bilgi = "🌐 Bilgiye erişirken bir sorun oluştu, lütfen tekrar deneyin."

# --- 📊 MESAJ GÖRÜNÜMÜ ---
if st.session_state.son_sorgu:
    st.markdown(f"<div class='user-msg'><b>Siz:</b><br>{st.session_state.son_sorgu}</div>", unsafe_allow_html=True)

if st.session_state.bilgi:
    st.markdown(f"<div class='ai-msg'><b>🇹🇷 TürkAI:</b><br>{st.session_state.bilgi.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
