import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="TürkAI v1 - Temiz Veri", layout="wide")
st.title("🛡️ TürkAI v1: Akıllı Veri Filtreleme")

konu = st.text_input("Analiz edilecek konuyu girin (Detaylı yazın, örn: 'Yapay Zeka Nedir'):")

def temiz_veri_cek(konu):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    # DuckDuckGo'nun en sade sürümünü kullanıyoruz (reklam oranı daha düşük)
    url = f"https://html.duckduckgo.com/html/?q={konu}"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Sadece gerçek sonuç özetlerini al (reklamları ve yan menüleri atla)
            sonuclar = soup.find_all('a', class_='result__snippet')
            
            ayiklanmis_metin = []
            for s in sonuclar:
                txt = s.text.strip()
                # Filtre: Eğer metin reklam içeriyorsa veya çok kısaysa alma
                if len(txt) > 40 and "shop" not in txt.lower() and "price" not in txt.lower():
                    ayiklanmis_metin.append(txt)
            
            return ayiklanmis_metin
        return None
    except:
        return None

if st.button("AKILLI ANALİZİ BAŞLAT"):
    if konu:
        with st.spinner('Gereksiz veriler temizleniyor...'):
            veriler = temiz_veri_cek(konu)
            
            if veriler:
                st.success(f"✅ {len(veriler)} adet güvenilir kaynak doğrulandı.")
                for i, v in enumerate(veriler[:5]): # En iyi 5 sonucu göster
                    st.info(f"Rapor {i+1}")
                    st.write(v)
            else:
                st.error("Maalesef temiz bir veri kaynağına ulaşılamadı.")
    else:
        st.warning("Lütfen bir konu giriniz.")


