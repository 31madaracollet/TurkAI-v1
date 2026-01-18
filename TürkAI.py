import streamlit as st
import requests

st.set_page_config(page_title="TürkAI v1 - Hızlı Analiz", layout="wide")
st.title("⚡ TürkAI v1: Kesintisiz Bilgi Akışı")

konu = st.text_input("Analiz edilecek konuyu girin:", placeholder="Örn: Yapay Zeka")

def vikipedi_getir(kelime):
    # Vikipedi'nin resmi API'sini kullanıyoruz (Engellenmez)
    url = "https://tr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": kelime,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        page = next(iter(data["query"]["pages"].values()))
        if "extract" in page:
            return page["extract"]
        return None
    except:
        return None

if st.button("HIZLI ANALİZ"):
    if konu:
        with st.spinner('Bilgi tüneli açılıyor...'):
            sonuc = vikipedi_getir(konu)
            if sonuc:
                st.success(f"✅ '{konu}' Hakkında Doğrulanmış Bilgi:")
                st.info(sonuc)
            else:
                st.warning("⚠️ Bu konuda doğrudan bir kayıt bulunamadı. Lütfen kelimeyi kontrol edin.")
    else:
        st.error("Lütfen bir konu yazın!")

