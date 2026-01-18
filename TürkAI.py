import streamlit as st
import requests
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

# --- 🛡️ AKILLI GÜVENLİK DUVARI ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt", "yavşak"] 

def akilli_filtre(metin):
    if not metin: return True
    kelimeler = metin.lower().split()
    for k in kelimeler:
        for y in KARA_LISTE:
            if fuzz.ratio(k, y) > 80:
                return False
    return True

# --- 🧠 SİSTEM HAFIZASI ---
if "log" not in st.session_state: st.session_state.log = False
if "chat" not in st.session_state: st.session_state.chat = []
if "username" not in st.session_state: st.session_state.username = ""

# --- 🚪 BASİT GİRİŞ EKRANI ---
if not st.session_state.log:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="👋")
    st.title("🇹🇷 TürkAI Analiz Merkezi")
    st.markdown("---")
    
    name = st.text_input("Kanka ismini veya lakabını yaz:", placeholder="Örn: Kaptan")
    if st.button("Tıra Bin ve Başla"):
        if len(name) > 1:
            st.session_state.username = name
            st.session_state.log = True
            st.rerun()
        else:
            st.error("Lütfen bir isim yaz kanka!")
    st.stop()

# --- 🚀 ANA ANALİZ PANELİ ---
st.set_page_config(page_title="TürkAI v90.0", layout="wide")

# SOL PANEL (Sohbet Geçmişi)
st.sidebar.title("🕒 Sohbet Geçmişi")
st.sidebar.info(f"👤 Kaptan: {st.session_state.username}")
if st.sidebar.button("Sohbeti Sıfırla"):
    st.session_state.chat = []
    st.rerun()

st.sidebar.divider()
for i, m in enumerate(st.session_state.chat):
    st.sidebar.write(f"{i+1}. {m['q'][:15]}...")

# ANA EKRAN
st.title("🇹🇷 TürkAI v90.0 - Akıllı Analiz")
st.caption("E-posta derdi bitti, doğrudan bilgiye odaklan!")

# MESAJLARI GÖSTER
for m in st.session_state.chat:
    with st.chat_message("user"): st.write(m["q"])
    with st.chat_message("assistant"): st.info(m["a"])

# YENİ SORU GİRİŞİ
soru = st.chat_input("Neyi merak ediyorsun kanka?")

if soru:
    if not akilli_filtre(soru):
        st.error("⚠️ Filtre: Üslubunu bozma kanka!")
    else:
        with st.spinner("Wikipedia taranıyor..."):
            url = f"https://tr.wikipedia.org/wiki/{soru.replace(' ', '_')}"
            try:
                r = requests.get(url, timeout=7)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    p_tags = soup.find_all('p')
                    res_text = ""
                    for p in p_tags:
                        if len(p.text) > 100:
                            res_text = p.text[:1200]
                            break
                    if not res_text: res_text = "Bu konuda tam bir bilgi bulamadım."
                else:
                    res_text = "Maalesef sonuç bulunamadı."
                
                st.session_state.chat.append({"q": soru, "a": res_text})
                st.rerun()
            except:
                st.error("Bağlantı hatası!")


