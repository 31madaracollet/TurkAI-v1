import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="TürkAI v1 - Pro", layout="wide")
st.title("🛡️ TürkAI v1: Çok Kanallı Kuşatma Protokolü")

konu = st.text_input("Analiz edilecek konuyu girin (Örn: Mars Yolculuğu):")

def kaynak_ara(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.text if res.status_code == 200 else None
    except:
        return None

if st.button("ANALİZİ BAŞLAT"):
    if konu:
        with st.spinner('Kalkanlar etrafından dolanılıyor...'):
            cols = st.columns(2)
            
            # --- 1. KANAL: WIKIPEDIA (DOĞRUDAN BİLGİ) ---
            with cols[0]:
                st.subheader("📚 Ansiklopedik Veri")
                wiki_url = f"https://tr.wikipedia.org/wiki/{konu.replace(' ', '_')}"
                wiki_html = kaynak_ara(wiki_url)
                if wiki_html:
                    soup = BeautifulSoup(wiki_html, 'html.parser')
                    paragraflar = soup.find_all('p')
                    if len(paragraflar) > 1:
                        st.success("Wikipedia verisi sızdırıldı.")
                        st.write(paragraflar[1].text[:800] + "...")
                    else:
                        st.warning("Wikipedia'da bu başlık henüz yok.")
                else:
                    st.error("Wikipedia kalkanı geçilemedi.")

            # --- 2. KANAL: DUCKDUCKGO (ARAMA MOTORU) ---
            with cols[1]:
                st.subheader("🦆 Özgür Kaynak Taraması")
                # DuckDuckGo'nun HTML sürümü botlara karşı daha esnektir
                ddg_url = f"https://html.duckduckgo.com/html/?q={konu}"
                ddg_html = kaynak_ara(ddg_url)
                if ddg_html:
                    soup = BeautifulSoup(ddg_html, 'html.parser')
                    sonuclar = soup.find_all('a', class_='result__snippet')
                    if sonuclar:
                        st.success("Alternatif kaynaklar bulundu.")
                        for s in sonuclar[:3]: # İlk 3 özeti göster
                            st.write(f"• {s.text}")
                    else:
                        st.warning("Alternatif kaynaklarda veri bulunamadı.")
                else:
                    st.error("DuckDuckGo bağlantısı reddedildi.")
    else:
        st.warning("Lütfen bir konu giriniz.")
