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
                # Yeni sürümde sadece 'term' ve 'num_results' (veya sadece döngü) kullanılır.
                # En güvenli yol doğrudan döngüye sokmaktır.
                sonuclar = []
                # İlk 3 linki çekiyoruz
                for j in search(konu, lang="tr", num_results=3):
                    sonuclar.append(j)
                
                if not sonuclar:
                    st.warning("Hiçbir kaynak bulunamadı.")
                else:
                    cols = st.columns(len(sonuclar))
                    for i, link in enumerate(sonuclar):
                        with cols[i]:
                            st.info(f"Kaynak {i+1} taranıyor...")
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
                            try:
                                res = requests.get(link, headers=headers, timeout=7)
                                if res.status_code == 200:
                                    soup = BeautifulSoup(res.text, 'html.parser')
                                    p_tags = soup.find_all('p')
                                    metin = " ".join([p.text for p in p_tags[:3]]) 
                                    if len(metin) > 30:
                                        st.success(f"Veri Sızdırıldı!")
                                        st.write(metin[:600] + "...")
                                        st.caption(f"Kaynak: {link}")
                                    else:
                                        st.warning("İçerik boş veya korumalı.")
                                else:
                                    st.error(f"Erişim reddedildi: {res.status_code}")
                            except:
                                st.error("Bu kaynağa bağlanılamadı.")
                                
            except Exception as e:
                st.error(f"Sistem hatası: {e}")
    else:
        st.warning("Konu girilmeden işlem başlatılamaz.")
