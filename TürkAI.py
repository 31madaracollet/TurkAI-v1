import streamlit as st
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz # Benzerlik algılayıcı
import random

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="TürkAI v60.0", layout="wide")

# --- HAFIZA (SESSION STATE) KURULUMU ---
if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = [] # Sohbet geçmişi
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- GELİŞMİŞ GÜVENLİK (KELİME BENZERLİĞİ) ---
KARA_LISTE = ["küfür1", "küfür2", "argo1"] # Burayı sen doldurursun kanka

def akilli_filtre(metin):
    kelimeler = metin.lower().split()
    for kelime in kelimeler:
        for yasak in KARA_LISTE:
            # Benzerlik oranı %80 üzerindeyse yakala
            if fuzz.ratio(kelime, yasak) > 80:
                return False
    return True

# --- GİRİŞ SİSTEMİ ---
if not st.session_state.logged_in:
    st.title("🔐 TürkAI Giriş")
    user_mail = st.text_input("E-posta:")
    if st.button("Sisteme Gir"):
        if "@" in user_mail:
            st.session_state.logged_in = True
            st.session_state.user = user_mail
            st.rerun()
    st.stop()

# --- ANA ARAYÜZ ---
st.sidebar.title("🕒 Sohbet Geçmişi")
for m in st.session_state.mesajlar:
    st.sidebar.write(f"🗨️ {m['soru'][:20]}...")

st.title("🇹🇷 TürkAI v60.0 - Akıllı Analiz Paneli")

# --- SOHBET AKIŞI ---
with st.container():
    for m in st.session_state.mesajlar:
        with st.chat_message("user"): st.write(m["soru"])
        with st.chat_message("assistant"): st.write(m["cevap"])

# --- GİRİŞ ALANI ---
prompt = st.chat_input("Bir konu yazın veya soru sorun...")

if prompt:
    if not akilli_filtre(prompt):
        st.error("⚠️ Hop! Kelime benzerliği üzerinden uygunsuz içerik tespit edildi. Lütfen üsluba dikkat.")
    else:
        # Wikipedia Analiz Motoru
        url = f"https://tr.wikipedia.org/wiki/{prompt.replace(' ', '_')}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                p = soup.find_all('p')
                cevap = p[1].text[:1000] if len(p) > 1 else "Üzgünüm, bu konuda detaylı veri bulamadım."
            else:
                cevap = "Aradığınız başlıkta bir kaynak bulunamadı."
        except:
            cevap = "Bağlantı hatası oluştu."

        # Hafızaya Kaydet
        st.session_state.mesajlar.append({"soru": prompt, "cevap": cevap})
        st.rerun() # Sayfayı yenileyip mesajı ekrana basar


