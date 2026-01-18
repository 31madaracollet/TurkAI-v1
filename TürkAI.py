import streamlit as st
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# --- GELİŞMİŞ GÜVENLİK VE FİLTRE MOTORU ---
def icerik_denetimi(metin):
    # Harf oyunlarını ve boşlukları bozmak için metni tamamen temizliyoruz
    # (Örn: "a.m.k" veya "am k" -> "amk" olur)
    temiz_metin = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    
    # Engellenecek kök kelimeler (Küçük harf ve boşluksuz yazılmalıdır)
    yasakli_kokler = [
        "siktir", "sik", "pic", "aminakoyayim", "orospucocugu", 
        "göt", "amk", "aq", "yavsak", "pic"
    ] 
    
    for kok in yasakli_kokler:
        if kok in temiz_metin:
            return False
            
    return True

# --- SAYFA YAPISI ---
st.set_page_config(page_title="TürkAI v1.0 Profesyonel", page_icon="🇹🇷")

if 'hafiza' not in st.session_state:
    st.session_state.hafiza = []
if 'kullanici' not in st.session_state:
    st.session_state.kullanici = ""

# --- KURUMSAL BANNER ---
st.title("🇹🇷 TürkAI - v1.0 Milli Analiz Sistemi")
st.markdown("---")

# --- KULLANICI GİRİŞİ ---
if not st.session_state.kullanici:
    st.info("Sistemi kullanmak için kurumsal etik kurallara uygun bir kullanıcı adı giriniz.")
    isim_giris = st.text_input("Sistem Kullanıcı Adı:")
    if st.button("Sisteme Giriş Yap"):
        if icerik_denetimi(isim_giris) and len(isim_giris.strip()) > 0:
            st.session_state.kullanici = isim_giris
            st.rerun()
        else:
            st.error("Hata: Kullanıcı adı uygunsuz içerik barındırmaktadır veya boştur.")
else:
    st.sidebar.success(f"Yetkili: {st.session_state.kullanici}")
    st.error("""
    **SİSTEM TALİMATI:**
    1. Bilgi edinmek istediğiniz konuyu yazıp 'Veriyi İşle' butonuna basınız.
    2. Veri yüklendiğinde, sorunuzun sonuna **'?'** işareti ekleyerek sorgulama yapınız.
    3. Matematiksel işlemler için başına **'hesapla'** yazınız.
    """)

    # --- HESAPLAMA MOTORU ---
    def hesap_birimi(girdi):
        # İşlem kısmını ayıklıyoruz
        islem_metni = girdi.lower().replace("hesapla", "").replace(" ", "")
        islem = re.findall(r"(\d+[\+\-\*\/\%]\d+)", islem_metni)
        if islem:
            try:
                sonuc = eval(islem[0])
                return f"🔢 Analiz Sonucu: {islem[0]} = {sonuc}"
            except:
                return "⚠️ Hata: Matematiksel işlem gerçekleştirilemedi."
        return "⚠️ Hata: Lütfen 'hesapla 10*5' formatında giriş yapınız."

    # --- ANA İŞLEM ---
    girdi = st.text_input("Sistem Giriş Alanı (Konu veya Soru?):")

    if st.button("Veriyi İşle"):
        # Güvenlik Kontrolü
        if not icerik_denetimi(girdi):
            st.error("🚨 Sistem Uyarısı: Giriş yapılan metin etik kurallara aykırıdır. İşlem durduruldu.")
        
        # Hesaplama Modu
        elif girdi.lower().startswith("hesapla"):
            st.subheader(hesap_birimi(girdi))
            
        # Soru-Cevap Modu
        elif girdi.endswith("?"):
            if not st.session_state.hafiza:
                st.warning("Analiz hatası: Lütfen önce bir konu başlığı girerek veriyi sisteme yükleyiniz.")
            else:
                try:
                    vectorizer = TfidfVectorizer()
                    matris = vectorizer.fit_transform(st.session_state.hafiza + [girdi])
                    sim = cosine_similarity(matris[-1], matris[:-1])
                    idx = sim[0].argsort()[-3:][::-1]
                    
                    st.write("### 🤖 Analiz Sonuçları:")
                    bulunan = False
                    for i in idx:
                        if sim[0][i] > 0.05:
                            bulunan = True
                            with st.expander(f"Veri Kaynağı {idx.tolist().index(i)+1}"):
                                st.write(st.session_state.hafiza[i])
                    
                    if not bulunan:
                        st.warning("Sorgunuza uygun spesifik bir bilgi eşleşmesi bulunamadı.")
                    else:
                        st.write("**Sayın kullanıcı, analiz edilen veriler yeterli mi?**")
                except:
                    st.error("Sorgu işlenirken bir algoritma hatası oluştu.")
        
        # Araştırma Modu
        else:
            with st.spinner("Dijital kaynaklar taranıyor..."):
                try:
                    # Wikipedia Türkiye üzerinden veri çekme
                    r = requests.get(f"https://tr.wikipedia.org/w/index.php?search={girdi}", timeout=10)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    veriler = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if veriler:
                        st.session_state.hafiza = veriler
                        st.success(f"✅ '{girdi}' konulu veri seti başarıyla analiz edildi ve sisteme yüklendi.")
                    else:
                        st.warning("Girilen konu hakkında yeterli dijital veri kaynağı bulunamadı.")
                except:
                    st.error("Bağlantı Hatası: Veri sunucularına erişilemiyor.")

# --- FOOTER ---
st.markdown("---")
st.caption("TürkAI v1.0 | Kurumsal Yapay Zeka Analiz Sistemi | Yerli Yazılım")