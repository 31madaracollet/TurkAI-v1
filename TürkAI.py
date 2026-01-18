import streamlit as st
import requests
import random
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

# --- 🔑 ANAHTARLARIN ---
SERVICE_ID = "service_t94tzf3"
TEMPLATE_ID = "template_icpc1mx"
PUBLIC_KEY = "WSbTebVBao1cHy4dT" # <--- Kendi anahtarını buraya yaz kanka!

# --- ✉️ EMAILJS MOTORU (Hata Almamak İçin En Üste Aldık) ---
def kod_gonder(email, code):
    url = "https://api.emailjs.com/api/v1.0/email/send"
    data = {
        'service_id': SERVICE_ID,
        'template_id': TEMPLATE_ID,
        'user_id': PUBLIC_KEY,
        'template_params': {
            'to_email': email,
            'otp_code': code
        }
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        return res.status_code == 200
    except:
        return False

# --- 🛡️ AKILLI GÜVENLİK DUVARI ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt"] 

def akilli_filtre(metin):
    if not metin: return True
    kelimeler = metin.lower().split()
    for k in kelimeler:
        for y in KARA_LISTE:
            if fuzz.ratio(k, y) > 80:
                return False
    return True

# --- 🧠 SİSTEM HAFIZASI ---
if "log" not in st.session_state: st.session_state.log = False
if "otp" not in st.session_state: st.session_state.otp = None
if "chat" not in st.session_state: st.session_state.chat = []
if "email" not in st.session_state: st.session_state.email = ""
if "kayitli_kullanicilar" not in st.session_state:
    st.session_state.kayitli_kullanicilar = []

# --- 🚪 GİRİŞ VE KAYIT ARAYÜZÜ ---
if not st.session_state.log:
    st.set_page_config(page_title="TürkAI v85.0 - Giriş", page_icon="🔐")
    st.title("🇹🇷 TürkAI Güvenlik Hattı")
    
    secenek = st.radio("Yapmak istediğiniz işlemi seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)

    if secenek == "Kayıt Ol":
        st.subheader("📝 Yeni Hesap Oluştur")
        email_reg = st.text_input("Kayıt için E-posta:", key="reg_input")
        if st.button("Kodu Gönder ve Kaydı Başlat"):
            if email_reg in st.session_state.kayitli_kullanicilar:
                st.warning("Bu e-posta zaten kayıtlı.")
            elif "@" in email_reg:
                st.session_state.otp = str(random.randint(100000, 999999))
                if kod_gonder(email_reg, st.session_state.otp):
                    st.session_state.kayitli_kullanicilar.append(email_reg)
                    st.success(f"✅ Kod {email_reg} adresine gönderildi!")
                else: st.error("Mail gönderilemedi. API anahtarlarını kontrol et.")
            else: st.error("Geçerli bir mail girin.")

    else:
        st.subheader("🔐 Üye Girişi")
        email_log = st.text_input("Kayıtlı E-posta:", key="log_input")
        otp_input = st.text_input("Doğrulama Kodu:", type="password")
        
        if st.button("Sisteme Giriş"):
            if email_log not in st.session_state.kayitli_kullanicilar:
                st.error("Bu e-posta kayıtlı değil.")
            elif st.session_state.otp and otp_input == st.session_state.otp:
                st.session_state.log = True
                st.session_state.email = email_log
                st.rerun()
            else: st.error("❌ Hatalı kod!")
    st.stop()

# --- 🚀 ANA ANALİZ PANELİ (Giriş Başarılıysa) ---
st.set_page_config(page_title="TürkAI v85.0", layout="wide")
st.sidebar.title("🕒 Sohbet Geçmişi")
st.sidebar.info(f"👤 {st.session_state.email}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.log = False
    st.rerun()

st.title("🇹🇷 TürkAI v85.0 - Ana Panel")
for m in st.session_state.chat:
    with st.chat_message("user"): st.write(m["q"])
    with st.chat_message("assistant"): st.info(m["a"])

soru = st.chat_input("Neyi merak ediyorsun?")
if soru:
    if not akilli_filtre(soru):
        st.error("⚠️ Filtre: Uygunsuz üslup!")
    else:
        url = f"https://tr.wikipedia.org/wiki/{soru.replace(' ', '_')}"
        try:
            r = requests.get(url, timeout=7)
            soup = BeautifulSoup(r.text, 'html.parser')
            p_tags = soup.find_all('p')
            res_text = p_tags[1].get_text()[:1200] if len(p_tags) > 1 else "Bilgi bulunamadı."
            st.session_state.chat.append({"q": soru, "a": res_text})
            st.rerun()
        except: st.error("Hata oluştu.")
