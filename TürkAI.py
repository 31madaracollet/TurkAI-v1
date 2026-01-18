import streamlit as st
import requests

st.set_page_config(page_title="TürkAI v1 - Akıllı Analiz", layout="wide")
st.title("⚡ TürkAI v1: Akıllı Veri Arama")

konu = st.text_input("Analiz edilecek konuyu girin:", placeholder="Örn: Tesla")

def akilli_ara(kelime):
    url = "https://tr.wikipedia.org/w/api.php"
    
    # Önce arama yapıp en yakın başlığı buluyoruz
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": kelime,
        "utf8": 1
    }
    
    try:
        s_res = requests.get(url, params=search_params).json()
        if s_res["query"]["search"]:
            en_yakin_baslik = s_res["query"]["search"][0]["title"]
            
            # Şimdi o başlığın içeriğini getiriyoruz
            prop_params = {
                "action": "query",
                "format": "json",
                "titles": en_yakin_baslik,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
            }
            p_res = requests.get(url, params=prop_params).json()
            page = next(iter(p_res["query"]["pages"].values()))
            return page.get("extract"), en_yakin_baslik
        return None, None
    except:
        return None, None

if st.button("ANALİZ ET"):
    if konu:
        with st.spinner('Veri tabanı taranıyor...'):
            sonuc, baslik = akilli_ara(konu)
            if sonuc:
                st.success(f"🎯 En Yakın Sonuç Bulundu: **{baslik}**")
                st.write(sonuc)
            else:
                st.warning("⚠️ Maalesef kütüphanede bu konuya dair net bir iz bulunamadı.")
    else:
        st.error("Lütfen bir kelime yaz kanka!")


