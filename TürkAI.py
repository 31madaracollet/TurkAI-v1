import streamlit as st
import requests
import random
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

# --- 🔑 ANAHTARLARIN ---
SERVICE_ID = "service_t94tzf3"
TEMPLATE_ID = "template_icpc1mx"
PUBLIC_KEY = "WSbTebVBao1cHy4dT"

# --- 🧠 KAYITLI KULLANICI KASASI (DATABASE SİMÜLASYONU) ---
# Gerçek bir veritabanı bağlayana kadar bu liste tarayıcı açık kaldığı sürece tutar.
if "kayitli_kullanicilar" not in st.session_state:
    st.session_state.kayitli_kullanicilar = [] # Burası bizim "Müşteri Defteri"

# --- 🚪 GİRİŞ VE KAYIT ARAYÜZÜ ---
if "log" not in st.session_state: st.session_state.log = False

if not st.session_state.log:
    st.set_page_config(page_title="TürkAI v80.0 - Giriş", page_icon="🔐")
    st.title("🇹🇷 TürkAI Güvenlik Hattı")
    
    # Giriş mi Kayıt mı seçeneği
    secenek = st.radio("Yapmak istediğiniz işlemi seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)

    if secenek == "Kayıt Ol":
        st.subheader("📝 Yeni Hesap Oluştur")
        email = st.text_input("Kayıt için E-posta:")
        if st.button("Kodu Gönder ve Kaydı Tamamla"):
            if email in st.session_state.kayitli_kullanicilar:
                st.warning("Bu e-posta zaten kayıtlı, Giriş Yap sekmesine gidin.")
            elif "@" in email:
                st.session_state.otp = str(random.randint(100000, 999999))
                if kod_gonder(email, st.session_state.otp):
                    st.session_state.kayitli_kullanicilar.append(email) # Deftere yazdık!
                    st.success(f"✅ Kayıt kodu {email} adresine gönderildi!")
                else: st.error("Mail gönderilemedi.")
            else: st.error("Geçerli bir mail girin.")

    else:
        st.subheader("🔐 Üye Girişi")
        email = st.text_input("Kayıtlı E-posta:")
        otp_input = st.text_input("Doğrulama Kodu:", type="password")
        
        if st.button("Sisteme Giriş"):
            if email not in st.session_state.kayitli_kullanicilar:
                st.error("Bu e-posta kayıtlı değil. Önce kayıt olun.")
            elif st.session_state.otp and otp_input == st.session_state.otp:
                st.session_state.log = True
                st.session_state.email = email
                st.rerun()
            else: st.error("❌ Hatalı kod!")
    st.stop()

