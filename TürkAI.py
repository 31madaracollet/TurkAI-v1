import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="TürkAI v1 - Pro", layout="wide")
st.title("🛡️ TürkAI v1: Kalkan Delen Son Protokol")

konu = st.text_input("Analiz edilecek konuyu girin:")

def kalkan_del(url):
    # Google ve diğerlerini kandırmak için çok daha detaylı bir kimlik
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.google.com/',
        'DNT': '1'
    }
    try:
        # Verify=False yaparak SSL sertifika kalkanlarını da es geçiyoruz
        res = requests.get(url, headers=headers, timeout=15, verify=True)
        return res.text if res.status_code == 200 else None
    except Exception as e:
        return str(e)

if st.button("SİSTEMİ TETİKLE"):
    if konu:
        with st.spinner('Kalkanlar Bypass ediliyor...'):
            # Google'ın "Özet" kısmına değil, doğrudan arama sonuçlarına odaklanıyoruz
            search_url = f"https://www.google.com/search?q={konu}+bilgi+nedir&hl=tr"
            html = kalkan_del(search_url)
            
            if html and "<!doctype html>" in html.lower():
                soup = BeautifulSoup(html, 'html.parser')
                # Google sonuçlarındaki ana metin bloklarını (Snippet) yakalıyoruz
                snippets = soup.find_all(['span', 'div'], attrs={'class': ['VwiC3b', 'yWG44c', 'MUFuzb']})
                
                if snippets:
                    st.success("🎯 Kalkan Delindi! Veri Sızdırıldı.")
                    for i, s in enumerate(snippets[:5]):
                        if len(s.text) > 30:
                            st.info(f"Bulgu {i+1}:")
                            st.write(s.text)
                else:
                    # Eğer Google hala vermiyorsa DuckDuckGo Lite sürümünü (bot dostu) dene
                    st.warning("Google hala direniyor, alternatif tünel (DuckDuckGo Lite) açılıyor...")
                    ddg_url = f"https://duckduckgo.com/lite/?q={konu}"
                    ddg_html = kalkan_del(ddg_url)
                    if ddg_html:
                        soup_ddg = BeautifulSoup(ddg_html, 'html.parser')
                        results = soup_ddg.find_all('td', class_='result-snippet')
                        for r in results[:3]:
                            st.write(f"• {r.text.strip()}")
                    else:
                        st.error("Tüm yollar kapalı. Sunucu IP adresi tamamen bloklanmış olabilir.")
            else:
                st.error("Kritik Hata: Sunucu kimliği tespit edildi ve kapılar kapatıldı.")
    else:
        st.warning("Konu girmeden motoru çalıştıramazsın kanka.")

