import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime

# --- ⚙️ SİSTEM BAŞLANGIÇ AYARLARI ---
st.set_page_config(page_title="TürkAI Pro", page_icon="🇹🇷", layout="wide")

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "kullanici_adi" not in st.session_state:
    st.session_state.kullanici_adi = ""
if "analiz_sonucu" not in st.session_state:
    st.session_state.analiz_sonucu = None
if "su_anki_konu" not in st.session_state:
    st.session_state.su_anki_konu = ""
if "gecmis" not in st.session_state:
    st.session_state.gecmis = []

# --- 🛡️ GÜVENLİK VE FİLTRE PROTOKOLLERİ ---
KARA_LISTE = ["amk", "aq", "piç", "oç", "sik", "yarrak", "göt", "meme", "daşşak", "ibne", "kahpe"]

def guvenlik_tarama(metin):
    if not metin: return True
    temiz_metin = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', metin.lower())
    for kelime in KARA_LISTE:
        if kelime in temiz_metin:
            return False
    return True

# --- 🧹 VERİ TEMİZLEME MOTORU ---
def metin_optimizasyonu(metin):
    # Kaynakçaları [1] ve bozuk karakterleri temizle
    metin = re.sub(r'\[\d+\]', '', metin)
    metin = re.sub(r'[^\x00-\x7f\x80-\xff]', '', metin)
    metin = metin.replace('\xa0', ' ').strip()
    return metin

# --- 📄 KURUMSAL RAPORLAMA (PDF) ---
def rapor_olustur(baslik, icerik, yazar):
    pdf = FPDF()
    pdf.add_page()
    
    # Başlık Alanı
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "TURKAI ANALIZ RAPORU", ln=True, align='C')
    pdf.line(10, 25, 200, 25) # Çizgi çek
    
    # Meta Veriler
    pdf.ln(15)
    pdf.set_font("Arial", "I", 10)
    zaman = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    
    def safe(s): return s.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.cell(0, 8, txt=safe(f"Konu: {baslik}"), ln=True)
    pdf.cell(0, 8, txt=safe(f"Hazirlayan: {yazar}"), ln=True)
    pdf.cell(0, 8, txt=safe(f"Tarih: {zaman}"), ln=True)
    pdf.ln(10)
    
    # İçerik
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, txt=safe(icerik))
    
    # Alt Bilgi
    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Bu rapor TurkAI Yapay Zeka Sistemleri tarafindan olusturulmustur.", 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 🎨 PROFESYONEL ARAYÜZ TASARIMI (CSS) ---
def stil_enjekte_et():
    st.markdown("""
        <style>
        /* Genel Tipografi ve Renkler */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Ana Konteyner Düzeni */
        .main .block-container {
            max-width: 900px;
            padding-top: 2rem;
            padding-bottom: 8rem;
        }

        /* Sonuç Kartı Tasarımı (Glassmorphism benzeri) */
        .sonuc-karti {
            background-color: #ffffff;
            dark-mode-bg: #1e293b; 
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1.5rem;
        }
        
        /* Dark Mode Uyumu İçin Özel Ayar */
        @media (prefers-color-scheme: dark) {
            .sonuc-karti {
                background-color: #1e1f20;
                border: 1px solid #333;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
            h1, h2, h3, p { color: #e2e8f0; }
        }

        /* Başlıklar */
        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
            text-align: center;
            background: -webkit-linear-gradient(45deg, #e63946, #457b9d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }

        /* Input Alanı (Alt Bar) */
        .stChatInputContainer {
            padding-bottom: 2rem;
        }
        
        /* Kenar Çubuğu (Sidebar) */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.1);
        }
        
        /* Butonlar */
        .stButton button {
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(230, 57, 70, 0.3);
        }
        </style>
    """, unsafe_allow_html=True)

stil_enjekte_et()

# --- 🚪 GİRİŞ MODÜLÜ ---
if not st.session_state.giris_yapildi:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>TürkAI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Kurumsal Araştırma & Analiz Platformu</p>", unsafe_allow_html=True)
        
        kullanici = st.text_input("Kimlik Doğrulama", placeholder="Adınızı giriniz...")
        
        if st.button("Platforma Giriş Yap", use_container_width=True):
            if len(kullanici) >= 2:
                st.session_state.kullanici_adi = kullanici
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.warning("Lütfen geçerli bir kimlik giriniz.")
    st.stop()

# --- 🚀 ANA PLATFORM ---

# Yan Panel (Dashboard)
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.kullanici_adi}")
    st.caption("Pro Lisans: Aktif")
    st.divider()
    
    st.markdown("**📋 Son İşlemler**")
    if st.session_state.gecmis:
        for islem in st.session_state.gecmis[-5:]:
            st.markdown(f"<div style='padding:5px; font-size:0.9rem;'>🔹 {islem}</div>", unsafe_allow_html=True)
    else:
        st.caption("Henüz işlem yapılmadı.")
        
    st.divider()
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

# Ana İçerik
st.title("TürkAI Bilgi Merkezi")

if st.session_state.analiz_sonucu:
    # SONUÇ KARTI
    st.markdown(f"""
    <div class="sonuc-karti">
        <h3 style="color: #e63946; margin-top:0;">📌 Analiz: {st.session_state.su_anki_konu}</h3>
        <p style="line-height: 1.8; font-size: 1.05rem;">
            {st.session_state.analiz_sonucu.replace(chr(10), '<br><br>')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Aksiyon Butonları
    col_pdf, col_bos = st.columns([1, 3])
    with col_pdf:
        pdf_data = rapor_olustur(st.session_state.su_anki_konu, st.session_state.analiz_sonucu, st.session_state.kullanici_adi)
        st.download_button(
            label="📄 Raporu PDF Olarak İndir",
            data=pdf_data,
            file_name=f"Rapor_{st.session_state.su_anki_konu}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

else:
    # Boş Durum Ekranı
    st.markdown("""
    <div style="text-align: center; padding: 3rem; opacity: 0.6;">
        <h3>Hoş Geldiniz</h3>
        <p>Gelişmiş veri madenciliği ve analiz motoru kullanıma hazırdır.<br>
        Aşağıdaki panelden konu başlığı girerek süreci başlatabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)

# --- ALT SORGULAMA BARI ---
sorgu = st.chat_input("Detaylı analiz için konu başlığı giriniz...")

if sorgu:
    if not guvenlik_tarama(sorgu):
        st.error("⛔ Güvenlik Protokolü: Uygunsuz içerik tespit edildi.")
    else:
        with st.spinner("Veri tabanları taranıyor ve analiz ediliyor..."):
            konu_linki = sorgu.strip().capitalize().replace(' ', '_')
            url = f"https://tr.wikipedia.org/wiki/{konu_linki}"
            
            try:
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    paragraflar = [metin_optimizasyonu(p.get_text()) for p in soup.find_all('p') if len(p.get_text()) > 60]
                    
                    if paragraflar:
                        # Geçmişe ekle
                        if sorgu not in st.session_state.gecmis:
                            st.session_state.gecmis.append(sorgu)
                            
                        # Sonucu kaydet (İlk 8 paragraf)
                        st.session_state.analiz_sonucu = "\n".join(paragraflar[:8])
                        st.session_state.su_anki_konu = sorgu
                        st.rerun()
                    else:
                        st.warning("⚠️ Konu ile ilgili yeterli veri seti bulunamadı.")
                else:
                    st.error("❌ Belirtilen başlık veri tabanında mevcut değil.")
            except Exception as e:
                st.error("⚠️ Sunucu bağlantı hatası.")

