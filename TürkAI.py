import streamlit as st
import random
import re
import requests
from bs4 import BeautifulSoup

# --- GÜVENLİK VE FİLTRE ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"]

def temiz_mi(metin):
    for kelime in KARA_LISTE:
        if kelime in metin.lower(): return False
    return True

# --- OTURUM YÖNETİMİ ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

# --- WEB ARAYÜZÜ ---
st.set_page_config(page_title="TürkAI v50.0 - Güvenli Giriş", page_icon="🇹🇷")

# --- HESAP / GİRİŞ SİSTEMİ ---
if not st.session_state.logged_in:
    st.title("🔐 TürkAI Güvenli Giriş")
    
    email = st.text_input("E-posta Adresiniz:", placeholder="ornek@mail.com")
    
    if not st.session_state.otp_sent:
        if st.button("Doğrulama Kodu Gönder"):
            if email and "@" in email:
                # Gerçek sistemde burada mail gönderilir. Şimdilik simüle ediyoruz.
                st.session_state.generated_otp = str(random.randint(100000, 999999))
                st.session_state.otp_sent = True
                st.success(f"✅ Kod gönderildi! (Test için kodunuz: {st.session_state.generated_otp})")
                # NOT: Gerçekten mail gitmesini istersen smtplib kütüphanesi eklenir.
            else:
                st.error("Lütfen geçerli bir e-posta girin.")
    else:
        otp_input = st.text_input("E-postanıza gelen 6 haneli kodu girin:", type="password")
        if st.button("Giriş Yap"):
            if otp_input == st.session_state.generated_otp:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("❌ Hatalı kod girdiniz!")
        if st.button("Geri Dön"):
            st.session_state.otp_sent = False
            st.rerun()
    st.stop() # Giriş yapılmadan ana sayfayı gösterme

# --- ANA PROGRAM (Giriş Yapıldıktan Sonra) ---
st.sidebar.success(f"Hoş geldin, {st.session_state.user_email}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.logged_in = False
    st.rerun()

st.title("🇹🇷 TürkAI v50.0 - Ana Kontrol Merkezi")

konu = st.text_input("Araştırmak istediğiniz konuyu giriniz:")

if st.button("Analizi Başlat"):
    if konu and temiz_mi(konu):
        with st.spinner("Bilgi süzülüyor..."):
            # Analiz kodları buraya (Wikipedia API vb.)
            url = f"https://tr.wikipedia.org/wiki/{konu.replace(' ', '_')}"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    p = soup.find_all('p')
                    st.info(p[1].text[:800] if len(p) > 1 else "Veri bulunamadı.")
                else: st.error("Konu bulunamadı.")
            except: st.error("Bağlantı hatası.")
    elif not temiz_mi(konu):
        st.error("⚠️ Uygunsuz üslup tespit edildi.")
