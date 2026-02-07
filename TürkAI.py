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

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 DİNAMİK TEMA VE KURUMSAL TASARIM ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    
    h1, h2, h3 { 
        color: var(--primary-red) !important; 
        font-weight: 700 !important;
    }

    .giris-kapsayici {
        border: 1px solid rgba(204, 0, 0, 0.3);
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        background-color: transparent;
    }

    .apk-buton-link {
        display: block;
        width: 100%;
        background-color: var(--primary-red);
        color: white !important;
        text-align: center;
        padding: 14px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 20px;
        transition: 0.3s;
    }

    .sidebar-indir-link {
        display: block;
        background-color: transparent;
        color: inherit !important;
        text-align: center;
        padding: 8px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid var(--primary-red);
        font-size: 13px;
        margin-top: 10px;
    }

    .not-alani {
        background-color: rgba(204, 0, 0, 0.05);
        color: var(--primary-red);
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed var(--primary-red);
        margin-bottom: 20px;
        font-size: 0.85rem;
        text-align: center;
    }

    .tuyo-metni {
        font-size: 0.9rem;
        opacity: 0.8;
        margin-bottom: 20px;
        padding: 10px;
        border-left: 3px solid var(--primary-red);
    }
    
    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        margin: 20px 0;
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(204, 0, 0, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .motor-badge {
        background-color: var(--primary-red);
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0 5px;
    }
    
    .site-bilgi {
        background-color: rgba(0, 100, 0, 0.05);
        border-left: 4px solid #006400;
        padding: 12px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 💾 VERİTABANI YÖNETİMİ ---
def db_baslat():
    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')
    conn.commit()
    return conn, c

conn, c = db_baslat()

# --- 🔑 OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "arama_devam" not in st.session_state: st.session_state.arama_devam = False

# --- 🔧 YARDIMCI FONKSİYONLAR ---
def bilgiyi_sirala(bilgiler):
    """Bilgileri en bilgiliden en az bilgiliye sırala"""
    sirali = []
    for site, icerik in bilgiler:
        if not icerik or len(icerik.strip()) < 50:
            continue
        
        # Bilgi kalitesini puanla
        puan = 0
        
        # Uzunluk puanı (optimal 300-1000 karakter)
        if 300 <= len(icerik) <= 1000:
            puan += 3
        elif len(icerik) > 1000:
            puan += 2
        elif len(icerik) > 100:
            puan += 1
            
        # Noktalama ve yapı puanı
        nokta_sayisi = icerik.count('.') + icerik.count(',') + icerik.count(';')
        if nokta_sayisi > 5:
            puan += 2
            
        # Anahtar kelime yoğunluğu (spam kontrolü)
        kelimeler = icerik.lower().split()
        if len(kelimeler) > 0:
            benzersiz_kelimeler = len(set(kelimeler))
            if benzersiz_kelimeler / len(kelimeler) > 0.5:  # %50'den fazla benzersiz
                puan += 1
                
        sirali.append((site, icerik, puan))
    
    # Puanı yüksekten düşüğe sırala
    sirali.sort(key=lambda x: x[2], reverse=True)
    return [(site, icerik) for site, icerik, _ in sirali]

def site_tara(url, sorgu, site_adi, timeout=10):
    """Tek bir siteyi tarar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ana içerik alanlarını bul
        icerik = ""
        
        # Önce paragraf etiketlerini kontrol et
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 80 and sorgu.lower() in text.lower():
                icerik += text + "\n\n"
        
        # Eğer yeterli paragraf yoksa, tüm metni al
        if len(icerik) < 100:
            all_text = soup.get_text()
            lines = all_text.split('\n')
            for line in lines:
                clean_line = line.strip()
                if len(clean_line) > 60 and sorgu.lower() in clean_line.lower():
                    icerik += clean_line + "\n\n"
        
        # Fazla boşlukları temizle
        icerik = re.sub(r'\s+', ' ', icerik).strip()
        
        if len(icerik) > 50:
            return (site_adi, icerik[:1500])
        else:
            return (site_adi, None)
            
    except Exception as e:
        return (site_adi, None)

def derin_arama_yap(sorgu):
    """Derin düşünerek arama yapar - ilk bulduğu siteden başlar"""
    
    # Site listesini en güvenilirden en az güvenilire
    site_listesi = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': 'Wikipedia (Türkçe)',
            'oncelik': 10
        },
        {
            'url': f'https://en.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': 'Wikipedia (İngilizce)',
            'oncelik': 9
        },
        {
            'url': f'https://www.britannica.com/search?query={urllib.parse.quote(sorgu)}',
            'adi': 'Britannica',
            'oncelik': 8
        },
        {
            'url': f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}',
            'adi': 'TDK Sözlük',
            'oncelik': 7
        },
        {
            'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}',
            'adi': 'Etimoloji Türkçe',
            'oncelik': 6
        },
        {
            'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': 'Biyografi.info',
            'oncelik': 5
        },
        {
            'url': f'https://www.google.com/search?q={urllib.parse.quote(sorgu)}+ansiklopedi',
            'adi': 'Google Ansiklopedik',
            'oncelik': 4
        },
        {
            'url': f'https://www.wiktionary.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': 'Wiktionary',
            'oncelik': 3
        }
    ]
    
    tum_bilgiler = []
    basarili_siteler = []
    
    # Öncelik sırasına göre site listesini sırala
    site_listesi.sort(key=lambda x: x['oncelik'], reverse=True)
    
    # Düşünme animasyonu için
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, site in enumerate(site_listesi):
        status_text.text(f"🔍 {site['adi']} taranıyor...")
        progress_bar.progress((i + 1) / len(site_listesi))
        
        site_adi, icerik = site_tara(site['url'], sorgu, site['adi'])
        
        if icerik:
            basarili_siteler.append(site['adi'])
            tum_bilgiler.append((site['adi'], icerik))
            
            # Yeterli bilgi bulduysa daha fazla site taramaya gerek yok
            if len(icerik) > 300:
                status_text.text(f"✅ Yeterli bilgi bulundu ({site['adi']})")
                time.sleep(0.5)
                break
        else:
            status_text.text(f"⚠️ {site['adi']}'de yeterli bilgi bulunamadı")
            time.sleep(0.3)
    
    progress_bar.empty()
    status_text.empty()
    
    return tum_bilgiler, basarili_siteler

def hesap_makinesi(ifade):
    """Güvenli hesap makinesi"""
    try:
        # Matematiksel karakterler dışındakileri temizle
        guvenli_ifade = re.sub(r'[^0-9+\-*/(). ]', '', ifade)
        result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        return f"**Sonuç:** {ifade} = **{result}**"
    except:
        return "Hesaplama hatası. Lütfen geçerli bir matematiksel ifade girin."

# --- 🔐 KİMLİK DOĞRULAMA EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        
        # Giriş Notu
        st.markdown("<div class='not-alani'>Derin Düşünen motoru ile hızlı ve kaliteli arama</div>", unsafe_allow_html=True)
        
        # Giriş APK Butonu
        st.markdown(f'<a href="{APK_URL}" class="apk-buton-link">TürkAI Mobil Uygulamasını Yükle</a>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Sistem Girişi", "📝 Yeni Kayıt"])
        
        with tab_login:
            u_in = st.text_input("Kullanıcı Kimliği")
            p_in = st.text_input("Erişim Şifresi", type="password")
            if st.button("Sisteme Eriş", use_container_width=True):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in
                    st.rerun()
                else:
                    st.error("Giriş bilgileri hatalı.")
        
        with tab_register:
            nu = st.text_input("Yeni Kullanıcı Adı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kaydı Tamamla", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kayıt başarılı. Giriş yapabilirsiniz.")
                except:
                    st.error("Bu isim sistemde mevcut.")
    st.stop()

# --- 🚀 OPERASYONEL PANEL ---
with st.sidebar:
    st.markdown(f"### 🛡️ Yetkili: {st.session_state.user}")
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    
    m_secim = st.radio("Analiz Metodolojisi:", 
                      ["V1 (Ansiklopedik)", 
                       "V2 (Global Kaynaklar)", 
                       "V3 (Matematik Birimi)",
                       "🤔 Derin Düşünen"])
    
    # Derin Düşünen Mod Açıklaması
    if m_secim == "🤔 Derin Düşünen":
        st.info("""
        **Derin Düşünen Modu:**
        • İlk bulduğu siteden başlar
        • En bilgiliden en aza sıralar
        • Ciddi ve öz bilgiler verir
        • Gereksiz siteleri atlar
        """)
    
    # Matematik Modu Notu
    if m_secim == "V3 (Matematik Birimi)":
        st.info("⚠️ Not: Çarpı (x) yerine yıldız (*) kullanınız.")
        
    st.divider()
    
    # Hesap Makinesi (Tüm Modlar için)
    st.markdown("##### 🧮 Hızlı Hesap Makinesi")
    hesap_ifade = st.text_input("Matematiksel ifade:", key="hesap_makinesi", 
                                placeholder="Örnek: 45*2+18/3")
    if hesap_ifade:
        sonuc = hesap_makinesi(hesap_ifade)
        st.success(sonuc)
    
    st.divider()
    st.markdown("##### 📜 Geçmiş Kayıtlar")
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📄 {k[:22]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()
    
    # Sidebar İndirme Butonu
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link">📥 Uygulamayı İndir</a>', unsafe_allow_html=True)

# --- 💻 ARAŞTIRMA ALANI ---
st.title("Araştırma Terminali")
st.markdown("""
<div class='tuyo-metni'>
💡 <b>Kullanım Yönergesi:</b> Araştırmak istediğiniz şeyin anahtar kelimesini yazınız 
(Örn: Türk kimdir? ❌ <b>Türk</b> ✅)<br>
<span class='motor-badge'>V1</span> + <span class='motor-badge'>V2</span> = <span class='motor-badge'>🤔 Derin Düşünen</span>
</div>
""", unsafe_allow_html=True)

sorgu = st.chat_input("Veri girişi yapınız...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.arama_devam = True
    
    # Düşünme animasyonunu göster
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class='spinner-container'>
            <div class='spinner'></div>
            <h3 style='color: #cc0000;'>TürkAI Derin Düşünüyor...</h3>
            <p>En iyi kaynak aranıyor, gereksiz bilgiler ayıklanıyor...</p>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(1)  # Düşünme efekti için
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        if m_secim == "V1 (Ansiklopedik)":
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
                title = r['query']['search'][0]['title']
                page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}", headers=headers).text
                soup = BeautifulSoup(page, 'html.parser')
                paragraphs = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                info = "\n\n".join(paragraphs[:4])  # Sadece 4 paragraf
                st.session_state.bilgi, st.session_state.konu = info, title
            except:
                st.session_state.bilgi = "Sorgu sonucu bulunamadı."
                st.session_state.konu = sorgu
        
        elif m_secim == "V2 (Global Kaynaklar)":
            try:
                wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                res = requests.get(wiki_api, headers=headers).json()
                st.session_state.bilgi, st.session_state.konu = res.get('extract', "Veri çekilemedi."), sorgu.upper()
            except:
                st.session_state.bilgi = "Sunucu bağlantı hatası."
                st.session_state.konu = sorgu
        
        elif m_secim == "V3 (Matematik Birimi)":
            try:
                result = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
                st.session_state.bilgi, st.session_state.konu = f"**İşlem Sonucu:** {sorgu} = {result}", "MATEMATİKSEL ANALİZ"
            except:
                st.session_state.bilgi = "Hatalı matematiksel ifade."
                st.session_state.konu = "HESAPLAMA HATASI"
        
        elif m_secim == "🤔 Derin Düşünen":
            # Düşünme animasyonunu kaldır
            thinking_placeholder.empty()
            
            # Derin arama yap
            tum_bilgiler, basarili_siteler = derin_arama_yap(sorgu)
            
            if tum_bilgiler:
                # Bilgileri sırala
                sirali_bilgiler = bilgiyi_sirala(tum_bilgiler)
                
                # Sonuçları birleştir
                birlesik_icerik = f"# 🤔 DERİN ANALİZ: {sorgu.upper()}\n\n"
                birlesik_icerik += f"**Taranan siteler:** {len(basarili_siteler)} farklı kaynak\n\n"
                
                # En iyi bilgileri göster
                for i, (site, icerik) in enumerate(sirali_bilgiler[:3]):  # Sadece en iyi 3
                    birlesik_icerik += f"### 📚 {site}\n"
                    birlesik_icerik += f"{icerik[:800]}"
                    if len(icerik) > 800:
                        birlesik_icerik += "...\n\n"
                    else:
                        birlesik_icerik += "\n\n"
                
                if len(sirali_bilgiler) > 3:
                    birlesik_icerik += f"*Ve {len(sirali_bilgiler) - 3} ek kaynak daha incelendi...*\n"
                
                st.session_state.bilgi = birlesik_icerik
                st.session_state.konu = f"DERİN: {sorgu.upper()}"
                
                # Site bilgilerini session'a kaydet
                st.session_state.basarili_siteler = basarili_siteler
                st.session_state.tum_bilgiler = sirali_bilgiler
                
            else:
                st.session_state.bilgi = "Hiçbir kaynakta yeterli bilgi bulunamadı."
                st.session_state.konu = sorgu
        
        st.session_state.arama_devam = False
        
        # Veritabanına kaydet
        if st.session_state.bilgi and st.session_state.user:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        
        st.rerun()

# --- 📊 RAPORLAMA ---
if st.session_state.son_sorgu:
    st.info(f"**Aktif Sorgu:** {st.session_state.son_sorgu}")
    
    # Hesap makinesi kontrolü
    if any(op in st.session_state.son_sorgu for op in ['+', '-', '*', '/', '(', ')']):
        try:
            hesap_sonucu = hesap_makinesi(st.session_state.son_sorgu)
            st.success(hesap_sonucu)
        except:
            pass

if st.session_state.bilgi and not st.session_state.arama_devam:
    st.subheader(f"📊 Analiz Raporu: {st.session_state.konu}")
    
    # Derin Düşünen modunda site bilgilerini göster
    if m_secim == "🤔 Derin Düşünen" and hasattr(st.session_state, 'basarili_siteler'):
        st.markdown(f"<div class='site-bilgi'>✅ **{len(st.session_state.basarili_siteler)}** kaynak başarıyla tarandı</div>", 
                   unsafe_allow_html=True)
    
    st.markdown(st.session_state.bilgi)
    
    # PDF Rapor Oluşturma (ORİJİNAL FPDF İLE)
    def rapor_pdf_olustur():
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Türkçe karakterler için düzenleme
            def tr_fix(t):
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): 
                    t = t.replace(k,v)
                return re.sub(r'[^\x00-\x7F]+', ' ', t)
            
            # Başlık
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="TURKAI ANALIZ RAPORU", ln=True, align='C')
            
            # Alt başlık
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(190, 10, txt=f"Konu: {tr_fix(st.session_state.konu)}", ln=True)
            
            # İçerik
            pdf.set_font("Arial", size=11)
            
            # Bilgiyi PDF'ye ekle
            icerik = st.session_state.bilgi
            
            # Markdown formatını düz metne çevir
            icerik = re.sub(r'#+\s*', '', icerik)  # Başlıkları kaldır
            icerik = re.sub(r'\*\*(.*?)\*\*', r'\1', icerik)  # Kalın yazıları kaldır
            icerik = re.sub(r'\*', '', icerik)  # Yıldızları kaldır
            
            # Satırları böl
            lines = icerik.split('\n')
            for line in lines:
                if len(line.strip()) > 0:
                    # Uzun satırları böl
                    if len(line) > 80:
                        words = line.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 < 80:
                                current_line += word + " "
                            else:
                                pdf.multi_cell(0, 5, txt=tr_fix(current_line))
                                current_line = word + " "
                        if current_line:
                            pdf.multi_cell(0, 5, txt=tr_fix(current_line))
                    else:
                        pdf.multi_cell(0, 5, txt=tr_fix(line))
                pdf.ln(2)
            
            # Alt bilgi
            pdf.ln(10)
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(190, 5, txt=f"Kullanıcı: {tr_fix(st.session_state.user)}", ln=True)
            pdf.cell(190, 5, txt=f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
            pdf.cell(190, 5, txt=f"Motor: {m_secim}", ln=True)
            
            return pdf.output(dest='S').encode('latin-1')
        except Exception as e:
            return None

    pdf_v = rapor_pdf_olustur()
    if pdf_v:
        st.download_button(
            label="📊 Raporu PDF Olarak İndir", 
            data=pdf_v, 
            file_name=f"TurkAI_Rapor_{st.session_state.konu[:30]}.pdf", 
            mime="application/pdf"
        )
    
    # Matematik modunda ekstra bilgi
    if m_secim == "V3 (Matematik Birimi)":
        st.divider()
        st.markdown("##### 🧮 Ek Matematik İşlemleri")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Kare Hesapla", use_container_width=True):
                try:
                    num = float(re.findall(r'\d+', sorgu)[0])
                    st.success(f"{num}² = {num**2}")
                except:
                    st.error("Sayı bulunamadı")
        
        with col2:
            if st.button("Karekök Hesapla", use_container_width=True):
                try:
                    num = float(re.findall(r'\d+', sorgu)[0])
                    st.success(f"√{num} = {num**0.5:.2f}")
                except:
                    st.error("Sayı bulunamadı")
        
        with col3:
            if st.button("Yüzde Hesapla", use_container_width=True):
                try:
                    nums = re.findall(r'\d+', sorgu)
                    if len(nums) >= 2:
                        num1, num2 = float(nums[0]), float(nums[1])
                        st.success(f"{num1}%{num2} = {num1*num2/100}")
                except:
                    st.error("Hesaplanamadı")
