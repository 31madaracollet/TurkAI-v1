import streamlit as st
from googlesearch import search
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="TürkAI v1 - Pro", layout="wide")
st.title("🛡️ TürkAI v1: Gelişmiş Veri Sızma Protokolü")

konu = st.text_input("Analiz edilecek kritik konuyu girin:")

if st.button("SİSTEMİ ÇALIŞTIR"):
    if konu:
        with st.spinner('Kalkanlar analiz ediliyor ve açıklar aranıyor...'):
            try:
                # Google kalkanını dolanarak sadece linkleri topluyoruz
                sonuclar = []
                for j in search(konu, num=3, stop=3, pause=2):
                    sonuclar.append(j)
                
                cols = st.columns(len(sonuclar))
                
                for i, link in enumerate(sonuclar):
                    with cols[i]:
                        st.info(f"Kaynak {i+1} taranıyor...")
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        res = requests.get(link, headers=headers, timeout=5)
                        
                        if res.status_code == 200:
                            soup = BeautifulSoup(res.text, 'html.parser')
                            # Sayfadaki paragrafları çekiyoruz
                            p_tags = soup.find_all('p')
                            metin = " ".join([p.text for p in p_tags[:3]]) # İlk 3 paragraf
                            if len(metin) > 20:
                                st.success(f"Veri Sızdırıldı!")
                                st.write(metin[:500] + "...")
                                st.caption(f"Kaynak: {link}")
                            else:
                                st.warning("İçerik şifreli veya boş.")
                        else:
                            st.error(f"Giriş reddedildi: {res.status_code}")
                            
            except Exception as e:
                st.error(f"Sistem hatası: {e}")
    else:
        st.warning("Konu girilmeden işlem başlatılamaz.")
