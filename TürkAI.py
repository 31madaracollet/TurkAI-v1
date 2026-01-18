import streamlit as st
import requests
from bs4 import BeautifulSoup
import random

# --- 🧠 GÜVENLİ HAFIZA BAŞLATMA ---
# Loglardaki "KeyError" ve "AttributeError" hatalarını bu blok kökten çözer.
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "gecmis" not in st.session_state:
    st.session_state.gecmis = []

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    st.title("🇹🇷 TürkAI Analiz Sistemi")
    st.write("---")
    isim = st.text_input("Kanka, adın veya lakabın nedir?", placeholder="Örn: Kaptan")
    if st.button("Sistemi Başlat"):
        if len(isim) >= 2:
            st.session_state.kullanici_adi = isim
            st.session_state.giris_yapildi = True
            st.rerun()
        else:
            st.error("Lütfen en az 2 harfli bir isim yaz kanka!")
    st.stop()

# --- 🚀 ANA PANEL (SENİN ORİJİNAL KODUNUN GÜNCELLENMİŞ HALİ) ---
st.set_page_config(page_title="TürkAI v45.0 - Pro", page_icon="🇹🇷", layout="wide")

# 👈 YAN PANEL (SIDEBAR)
st.sidebar.title("🕒 TürkAI Panel")
st.sidebar.success(f"👤 Aktif: {st.session_state.kullanici_adi}")
if st.sidebar.button("Oturumu Kapat"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.sidebar.divider()
st.sidebar.write("**Son Aramalar:**")
for g in st.session_state.gecmis[-5:]: # Son 5 aramayı göster
    st.sidebar.caption(f"• {g}")

# --- ANALİZ MOTORU ---
st.title(f"🇹🇷 TürkAI v45.0 - Hoş geldin, {st.session_state.kullanici_adi}!")

# GÜVENLİK PROTOKOLÜ (Senin Orijinal Listen)
KARA_LISTE = [
    "amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt", "meme", "daşşak",
    "ibne", "kahpe", "yavşak", "gerizekalı", "salak", "aptal", "it", "köpek",
    "şerefsiz", "namussuz", "pezevenk", "fahişe", "mal", "oros", "ananı"
]

def temiz_mi(metin):
    metin_kucuk = metin.lower()
    for kelime in KARA_LISTE:
        if kelime in metin_kucuk:
            return False
    return True

hitaplar = ["Değerli Dostum", "Sayın Kullanıcı", "Kıymetli Arkadaşım"]
hitap = random.choice(hitaplar)

konu = st.text_input("Araştırmak istediğiniz konuyu giriniz:", placeholder="Örn: Uzay Teknolojileri")

if st.button("Analizi Başlat"):
    if konu:
        if not temiz_mi(konu):
            st.error("⚠️ TürkAI: Uygunsuz içerik veya üslup tespit edildi.")
        else:
            with st.spinner(f"🔎 {hitap}, kaynaklar taranıyor..."):
                # Wikipedia Arama
                arama = konu.strip().capitalize().replace(' ', '_')
                url = f"https://tr.wikipedia.org/wiki/{arama}"
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                        
                        if paragraflar:
                            if konu not in st.session_state.gecmis:
                                st.session_state.gecmis.append(konu)
                            
                            st.success(f"✅ {hitap}, veriler başarıyla analiz edildi.")
                            st.write("### 📖 Analiz Sonucu:")
                            st.info(paragraflar[0]) 
                            if len(paragraflar) > 1:
                                with st.expander("Detaylı Bilgiyi Gör"):
                                    st.write(" ".join(paragraflar[1:4]))
                        else:
                            st.warning("⚠️ Bu konuda yeterli açıklama bulunamadı.")
                    else:
                        st.error("⚠️ Aranan konu bulunamadı. Yazımı kontrol et kanka.")
                except:
                    st.error("❌ Bağlantı hatası: Sunucuya ulaşılamıyor.")
    else:
        st.warning("Lütfen bir konu başlığı giriniz.")

st.divider()
st.caption(f"TürkAI v45.0 | Kullanıcı: {st.session_state.kullanici_adi}")

