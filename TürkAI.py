import streamlit as st
import requests
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

# --- ⚙️ TEMEL AYARLAR ---
if "log" not in st.session_state: st.session_state.log = False
if "chat" not in st.session_state: st.session_state.chat = []
if "username" not in st.session_state: st.session_state.username = ""

# --- 🛡️ KÜFÜR FİLTRESİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"] 

def akilli_filtre(metin):
    if not metin: return True
    kelimeler = metin.lower().split()
    for k in kelimeler:
        for y in KARA_LISTE:
            if fuzz.ratio(k, y) > 80: return False
    return True

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.log:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="👋")
    st.title("🇹🇷 TürkAI Analiz Merkezi")
    
    isim = st.text_input("İsminiz nedir?", placeholder="Örn: Kaptan")
    if st.button("Sisteme Gir"):
        if len(isim) > 1:
            st.session_state.username = isim
            st.session_state.log = True
            st.rerun()
        else:
            st.error("Lütfen geçerli bir isim girin!")
    st.stop()

# --- 🚀 ANA PANEL ---
st.set_page_config(page_title="TürkAI v99.0", layout="wide")

# 👈 YAN PANEL
st.sidebar.title("🕒 Geçmiş")
st.sidebar.info(f"👤 Kullanıcı: {st.session_state.username}")
if st.sidebar.button("Sohbeti Temizle"):
    st.session_state.chat = []
    st.rerun()

st.sidebar.divider()
for i, m in enumerate(st.session_state.chat):
    st.sidebar.write(f"{i+1}. {m['q'][:15]}...")

# ANA EKRAN
st.title("🇹🇷 TürkAI Analiz")

# MESAJLAR
for m in st.session_state.chat:
    with st.chat_message("user"): st.write(m["q"])
    with st.chat_message("assistant"): st.info(m["a"])

# SORU GİRİŞİ
soru = st.chat_input("Neyi merak ediyorsun?")

if soru:
    if not akilli_filtre(soru):
        st.error("⚠️ Lütfen uygun bir üslup kullanın.")
    else:
        with st.spinner("Bilgi çekiliyor..."):
            arama = soru.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{arama}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    p_tags = soup.find_all('p')
                    res_text = ""
                    for p in p_tags:
                        if len(p.text) > 100:
                            res_text = p.text[:1200]
                            break
                    if not res_text: res_text = "İçerik çekilemedi."
                else:
                    res_text = f"'{soru}' hakkında bilgi bulunamadı."
                
                st.session_state.chat.append({"q": soru, "a": res_text})
                st.rerun()
            except:
                st.error("Bağlantı hatası!")


