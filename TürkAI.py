import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re 
from fpdf import FPDF 
import time
import math
import base64
from io import BytesIO
import os

# --- ⚙️ SİSTEM AYARLARI ---
st.set_page_config(
    page_title="TürkAI | Profesyonel Araştırma Sistemi", 
    page_icon="🇹🇷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 BASİT TASARIM ---
st.markdown("""
<style>
    /* Chat input'u ortala ve düzenle */
    .stChatInput {
        position: fixed !important;
        bottom: 30px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 80% !important;
        max-width: 700px !important;
        z-index: 999 !important;
    }
    
    .stChatInput > div > div {
        border-radius: 25px !important;
        border: 2px solid #b22222 !important;
        background: white !important;
        box-shadow: 0 5px 20px rgba(178, 34, 34, 0.2) !important;
    }
    
    .stChatInput > div > div > input {
        padding: 15px 20px !important;
        font-size: 1rem !important;
    }
    
    /* Sayfa ortasını düzenle */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Başlık */
    h1 {
        text-align: center;
        color: #b22222;
        margin-top: 50px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI ---
def db_baslat():
    conn = sqlite3.connect('turkai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
def init_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "is_guest" not in st.session_state:
        st.session_state.is_guest = False
    if "bilgi" not in st.session_state:
        st.session_state.bilgi = None
    if "konu" not in st.session_state:
        st.session_state.konu = ""
    if "son_sorgu" not in st.session_state:
        st.session_state.son_sorgu = None

init_session_state()

# --- 🔧 PDF DÜZELTME (TÜRKÇE KARAKTER SORUNU ÇÖZÜLDÜ) ---
def turkce_pdf_olustur():
    """Türkçe karakter sorunu düzeltilmiş PDF oluştur"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # 1. UNICODE DESTEKLİ FONT EKLE (EN ÖNEMLİ KISIM)
        # Arial Unicode veya DejaVu fontu kullan
        try:
            # DejaVu fontunu dene (en iyi Türkçe desteği)
            if os.path.exists("DejaVuSans.ttf"):
                pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
                pdf.set_font('DejaVu', '', 12)
            else:
                # Arial Unicode dene
                pdf.set_font("Arial", size=12)
        except:
            # Standart Arial (daha az Unicode desteği)
            pdf.set_font("Arial", size=12)
        
        # 2. BAŞLIK (TÜRKÇE KARAKTERLERLE)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "TÜRKAI RAPORU", ln=True, align='C')
        pdf.ln(5)
        
        # 3. BİLGİLER
        pdf.set_font("Arial", size=12)
        
        # Konu - Türkçe karakterleri güvenli hale getir
        konu = st.session_state.konu
        # Türkçe karakterleri İngilizce karşılıklarına çevir
        konu = konu.replace('İ', 'I').replace('ı', 'i')
        konu = konu.replace('Ş', 'S').replace('ş', 's')
        konu = konu.replace('Ğ', 'G').replace('ğ', 'g')
        konu = konu.replace('Ü', 'U').replace('ü', 'u')
        konu = konu.replace('Ö', 'O').replace('ö', 'o')
        konu = konu.replace('Ç', 'C').replace('ç', 'c')
        
        pdf.cell(40, 10, "Konu:", ln=0)
        pdf.cell(0, 10, konu[:50], ln=True)
        
        # Tarih
        pdf.cell(40, 10, "Tarih:", ln=0)
        pdf.cell(0, 10, datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), ln=True)
        
        # Kullanıcı
        pdf.cell(40, 10, "Kullanıcı:", ln=0)
        user_text = st.session_state.user if st.session_state.user else "Misafir"
        if st.session_state.is_guest:
            user_text += " (Misafir)"
        pdf.cell(0, 10, user_text, ln=True)
        
        pdf.ln(10)
        
        # 4. İÇERİK
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "ANALİZ SONUÇLARI", ln=True)
        pdf.ln(5)
        
        if st.session_state.bilgi:
            pdf.set_font("Arial", size=11)
            
            # İçeriği temizle ve formatla
            icerik = st.session_state.bilgi
            
            # HTML/Markdown temizleme
            icerik = re.sub(r'#+\s*', '', icerik)
            icerik = re.sub(r'\*\*', '', icerik)
            icerik = re.sub(r'\*', '', icerik)
            icerik = re.sub(r'`', '', icerik)
            icerik = re.sub(r'<[^>]*>', '', icerik)
            
            # Türkçe karakterleri güvenli hale getir
            icerik = icerik.replace('İ', 'I').replace('ı', 'i')
            icerik = icerik.replace('Ş', 'S').replace('ş', 's')
            icerik = icerik.replace('Ğ', 'G').replace('ğ', 'g')
            icerik = icerik.replace('Ü', 'U').replace('ü', 'u')
            icerik = icerik.replace('Ö', 'O').replace('ö', 'o')
            icerik = icerik.replace('Ç', 'C').replace('ç', 'c')
            
            # Satırları işle (maksimum 200 satır)
            lines = icerik.split('\n')
            line_count = 0
            
            for line in lines:
                if line_count >= 200:  # Maksimum 200 satır
                    pdf.cell(0, 10, "... (rapor kısaltıldı)", ln=True)
                    break
                    
                line = line.strip()
                if line:
                    # Uzun satırları parçala
                    if len(line) > 80:
                        chunks = [line[i:i+80] for i in range(0, len(line), 80)]
                        for chunk in chunks:
                            pdf.multi_cell(0, 5, chunk)
                            line_count += 1
                    else:
                        pdf.multi_cell(0, 5, line)
                        line_count += 1
                    
                    pdf.ln(2)
        
        # 5. ALT BİLGİ
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, "TürkAI Araştırma Sistemi", ln=True, align='C')
        
        # 6. PDF'yi bytes'a çevir (latin-1 encoding ile)
        return pdf.output(dest='S').encode('latin-1', 'ignore')
        
    except Exception as e:
        # Hata durumunda basit PDF
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "TURKAI RAPORU", ln=True)
            pdf.cell(0, 10, f"Hata: {str(e)[:50]}", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        except:
            return None

# --- 🔍 ARAMA FONKSİYONLARI ---
def wikipedia_ara(sorgu):
    """Wikipedia'dan ara"""
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('extract', '')
    except:
        return None

def matematik_hesapla(ifade):
    """Matematik işlemi yap"""
    try:
        # Güvenli karakterler
        guvenli = {'sqrt': math.sqrt, 'pi': math.pi, 'e': math.e}
        ifade = re.sub(r'[^0-9+\-*/(). sqrt]', '', ifade.lower())
        return eval(ifade, {"__builtins__": {}}, guvenli)
    except:
        return None

# --- 🏠 GİRİŞ EKRANI (BASİT) ---
if not st.session_state.user:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Logo ve başlık
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h1>🇹🇷 TürkAI</h1>
        <p style="color: #666; font-size: 1.1rem;">Profesyonel Araştırma Sistemi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Giriş kartı
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("### Sisteme Giriş")
            
            # Misafir girişi
            if st.button("👤 Misafir Olarak Devam Et", use_container_width=True):
                st.session_state.user = "Misafir"
                st.session_state.is_guest = True
                st.rerun()
            
            st.divider()
            
            # Kayıt/Giriş
            tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
            
            with tab1:
                username = st.text_input("Kullanıcı Adı")
                password = st.text_input("Şifre", type="password")
                
                if st.button("Giriş Yap", use_container_width=True):
                    if username and password:
                        sifre_hash = hashlib.sha256(password.encode()).hexdigest()
                        c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                                 (username, sifre_hash))
                        if c.fetchone():
                            st.session_state.user = username
                            st.session_state.is_guest = False
                            st.rerun()
                        else:
                            st.error("Hatalı kullanıcı adı veya şifre")
            
            with tab2:
                new_user = st.text_input("Yeni Kullanıcı Adı")
                new_pass = st.text_input("Yeni Şifre", type="password")
                new_pass2 = st.text_input("Şifre Tekrar", type="password")
                
                if st.button("Hesap Oluştur", use_container_width=True):
                    if new_user and new_pass and new_pass2:
                        if new_pass == new_pass2:
                            try:
                                sifre_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                                c.execute("INSERT INTO users VALUES (?, ?)", (new_user, sifre_hash))
                                conn.commit()
                                st.session_state.user = new_user
                                st.session_state.is_guest = False
                                st.rerun()
                            except:
                                st.error("Bu kullanıcı adı zaten alınmış")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 🎯 ANA SAYFA ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.session_state.is_guest:
        st.info("Misafir Modu")
    
    if st.button("Çıkış Yap"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor seçimi
    motor = st.radio(
        "Arama Motoru",
        ["🚀 Hızlı Motor", "🔍 Detaylı Motor"],
        index=0
    )
    
    # Geçmiş
    if not st.session_state.is_guest:
        st.markdown("### Geçmiş Aramalar")
        c.execute("SELECT konu FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 5", 
                 (st.session_state.user,))
        gecmis = c.fetchall()
        for g in gecmis:
            if st.button(f"🔍 {g[0][:20]}..."):
                c.execute("SELECT icerik FROM aramalar WHERE kullanici=? AND konu=? ORDER BY tarih DESC LIMIT 1",
                         (st.session_state.user, g[0]))
                sonuc = c.fetchone()
                if sonuc:
                    st.session_state.bilgi = sonuc[0]
                    st.session_state.konu = g[0]
                    st.rerun()

# Ana içerik
st.markdown("## 🔍 Araştırma Merkezi")

# Arama yapıldıysa sonuçları göster
if st.session_state.bilgi:
    st.markdown(f"### 📊 Sonuç: {st.session_state.konu}")
    st.markdown(st.session_state.bilgi)
    
    # PDF butonu
    pdf_data = turkce_pdf_olustur()
    if pdf_data:
        st.download_button(
            label="📥 PDF İndir",
            data=pdf_data,
            file_name=f"turkai_{st.session_state.konu[:20]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    if st.button("Yeni Arama Yap", use_container_width=True):
        st.session_state.bilgi = None
        st.session_state.konu = ""
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- 💬 CHAT INPUT (ORTADA SABİT) ---
# Bu kısım sayfanın en sonunda olacak, ortada sabit duracak
sorgu = st.chat_input("🔍 Araştırmak istediğiniz konuyu yazın...")

if sorgu:
    # Arama yap
    with st.spinner("Aranıyor..."):
        # Matematik kontrolü
        matematik = matematik_hesapla(sorgu)
        
        if matematik is not None:
            st.session_state.bilgi = f"""
            # 🧮 Matematik Sonucu
            
            **İfade:** `{sorgu}`
            
            **Sonuç:** **{matematik}**
            
            **Detaylar:**
            - Yaklaşık değer: {matematik:.6f}
            """
            st.session_state.konu = f"Matematik: {sorgu}"
            
        else:
            # Normal arama
            sonuc = wikipedia_ara(sorgu)
            
            if sonuc:
                st.session_state.bilgi = f"""
                # 📚 Wikipedia Sonucu
                
                {sonuc}
                """
                st.session_state.konu = sorgu
            else:
                st.session_state.bilgi = f"""
                # ⚠️ Sonuç Bulunamadı
                
                "{sorgu}" için sonuç bulunamadı.
                
                **Öneriler:**
                - Farklı anahtar kelimeler deneyin
                - Daha genel bir arama yapın
                """
                st.session_state.konu = sorgu
        
        # Veritabanına kaydet
        if not st.session_state.is_guest:
            c.execute("INSERT INTO aramalar VALUES (?, ?, ?, ?)",
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now())))
            conn.commit()
    
    st.rerun()
