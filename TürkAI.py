import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

# Sayfa Ayarları
st.set_page_config(page_title="TürkAI Pro - Analiz Sistemi", layout="wide")
st.title("🛡️ TürkAI v1: Çok Kanallı Veri Analiz Motoru")
st.markdown("---")

# Kullanıcı Girişi
konu = st.text_input("Analiz Edilecek Stratejik Konuyu Giriniz:", placeholder="Örn: Kuantum Bilgisayarlar")

def veri_cek(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.text
        return None
    except:
        return None

if st.button("DERİN ANALİZİ BAŞLAT"):
    if konu:
        cols = st.columns(3)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
        
        # --- 1. KAPI: GOOGLE STRATEJİK TARAMA ---
        with cols[0]:
            st.subheader("🌐 Google Kaynakları")
            with st.spinner("Google kalkanı zorlanıyor..."):
                g_url = f"https://www.google.com/search?q={konu}+nedir+hakkında+bilgi"
                g_data = veri_cek(g_url, headers)
                if g_data:
                    soup = BeautifulSoup(g_data, 'html.parser')
                    texts = [s.text for s in soup.find_all('span') if len(s.text) > 40]
                    if texts:
                        st.success("Veri çekildi.")
                        st.write(texts[0])
                    else:
                        st.error("Google erişimi kısıtladı.")
                else:
                    st.error("Bağlantı başarısız.")

        # --- 2. KAPI: DUCKDUCKGO (GİZLİ GEÇİT) ---
        with cols[1]:
            st.subheader("🦆 DuckDuckGo Analizi")
            with st.spinner("Alternatif yollar taranıyor..."):
                d_url = f"https://duckduckgo.com/html/?q={konu}"
                d_data = veri_cek(d_url, headers)
                if d_data:
                    soup = BeautifulSoup(d_data, 'html.parser')
                    links = soup.find_all('a', class_='result__a')
                    if links:
                        st.success("Alternatif veri bulundu.")
                        st.write(links[0].text)
                    else:
                        st.warning("Sonuç bulunamadı.")
                else:
                    st.error("Erişim engellendi.")

        # --- 3. KAPI: WIKIPEDIA (AKADEMİK DOĞRULAMA) ---
        with cols[2]:
            st.subheader("📚 Akademik Kayıtlar")
            with st.spinner("Arşivler inceleniyor..."):
                w_url = f"https://tr.wikipedia.org/wiki/{konu.replace(' ', '_')}"
                w_data = veri_cek(w_url, headers)
                if w_data:
                    soup = BeautifulSoup(w_data, 'html.parser')
                    p = soup.find_all('p')
                    if len(p) > 1:
                        st.success("Resmi kayıtlar eşleşti.")
                        st.write(p[1].text[:500] + "...")
                    else:
                        st.warning("Wikipedia kaydı bulunamadı.")
                else:
                    st.error("Arşiv bağlantısı koptu.")
    else:
        st.warning("Lütfen bir analiz konusu giriniz.")

st.markdown("---")
st.caption("TürkAI v1 - Güvenli ve Çok Kanallı Veri Çekme Protokolü")
