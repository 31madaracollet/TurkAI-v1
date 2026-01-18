import streamlit as st
import requests
from bs4 import BeautifulSoup
import random

# --- 🧠 HAFIZA VE GİRİŞ AYARLARI (KODUNU BOZMADAN EKLEDİK) ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""

# --- 🚪 GİRİŞ EKRANI ---
if not st.session_state.giris_yapildi:
    st.set_page_config(page_title="TürkAI Giriş", page_icon="🇹🇷")
    st.title("🇹🇷 TürkAI Analiz Merkezi")
    st.write("---")
    isim_girisi = st.text_input("Kanka, adın veya lakabın nedir?", placeholder="Örn: Kaptan")
    if st.button("Sisteme Giriş Yap"):
        if len(isim_girisi) >= 2:
            st.session_state.kullanici_adi = isim_girisi
            st.session_state.giris_yapildi = True
            st.rerun()
        else:
            st.error("Lütfen geçerli bir isim gir kanka!")
    st.stop()

# --- 🚀 ANA PANEL (SENİN KODUNUN BAŞLADIĞI YER) ---
st.set_page_config(page_title="TürkAI v45.0 - Pro", page_icon="🇹🇷", layout="wide")

# 👈 YAN PANEL (SIDEBAR) EKLEMESİ
st.sidebar.title("🕒 TürkAI Kontrol")
st.sidebar.info(f"👤 Aktif Kullanıcı: {st.session_state.kullanici_adi}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.giris_yapildi = False
    st.rerun()

st.sidebar.divider()
st.sidebar.write("Bu panelden kullanıcı bilgilerini görebilir ve oturumu yönetebilirsin kanka.")

# --- SENİN ORİJİNAL KODLARIN (DOKUNULMADI) ---

st.title(f"🇹🇷 TürkAI v45.0 - Hoş geldin, {st.session_state.kullanici_adi}!")

# GÜVENLİK PROTOKOLÜ
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
            st.error("⚠️ TürkAI: Uygunsuz içerik veya üslup tespit edildi. Analiz iptal edildi.")
        else:
            with st.spinner(f"🔎 {hitap}, kaynaklar taranıyor..."):
                url = f"https://tr.wikipedia.org/wiki/{konu.replace(' ', '_')}"
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        paragraflar = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                        
                        if paragraflar:
                            st.success(f"✅ {hitap}, veriler başarıyla analiz edildi.")
                            st.write("### 📖 Analiz Sonucu:")
                            st.info(paragraflar[0]) # İlk paragrafı göster
                            if len(paragraflar) > 1:
                                with st.expander("Detaylı Bilgiyi Gör"):
                                    st.write(" ".join(paragraflar[1:4]))
                        else:
                            st.warning("⚠️ Bu konuda yeterli açıklama bulunamadı.")
                    else:
                        st.error("⚠️ Aranan konu bulunamadı. Lütfen kelimeyi kontrol edin.")
                except:
                    st.error("❌ Bağlantı hatası: Sunucuya ulaşılamıyor.")
    else:
        st.warning("Lütfen bir konu başlığı giriniz.")

st.divider()
st.caption(f"TürkAI v45.0 | Kullanıcı: {st.session_state.kullanici_adi} | Güvenli ve Filtreli Yapay Zeka Arayüzü")
