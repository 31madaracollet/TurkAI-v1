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
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# --- ⚙️ SİSTEM VE TEMA AYARLARI ---
st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")

# --- 🔗 GITHUB DIREKT INDIRME LINKI ---
APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"

# --- 🎨 DİNAMİK TEMA VE KURUMSAL TASARIM ---
st.markdown("""
    <style>
    :root { 
        --primary-red: #cc0000;
        --futuristic-blue: #00b4d8;
        --neon-green: #39ff14;
        --cyber-purple: #bc00dd;
    }
    
    h1, h2, h3 { 
        color: var(--primary-red) !important; 
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(204, 0, 0, 0.3);
    }

    .giris-kapsayici {
        border: 2px solid rgba(204, 0, 0, 0.3);
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        background: linear-gradient(135deg, rgba(204,0,0,0.05) 0%, rgba(0,0,0,0.1) 100%);
        backdrop-filter: blur(10px);
    }

    .apk-buton-link {
        display: block;
        width: 100%;
        background: linear-gradient(45deg, var(--primary-red), #ff3333);
        color: white !important;
        text-align: center;
        padding: 16px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 600;
        margin-bottom: 20px;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(204, 0, 0, 0.3);
        border: none;
    }

    .apk-buton-link:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(204, 0, 0, 0.4);
    }

    .sidebar-indir-link {
        display: block;
        background: transparent;
        color: var(--futuristic-blue) !important;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        text-decoration: none;
        border: 1px solid var(--futuristic-blue);
        font-size: 14px;
        margin-top: 10px;
        transition: 0.3s;
    }

    .sidebar-indir-link:hover {
        background: rgba(0, 180, 216, 0.1);
    }

    .not-alani {
        background: linear-gradient(135deg, rgba(204, 0, 0, 0.1), rgba(0, 180, 216, 0.1));
        color: var(--primary-red);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid var(--primary-red);
        margin-bottom: 20px;
        font-size: 0.9rem;
        text-align: center;
        backdrop-filter: blur(5px);
    }

    .tuyo-metni {
        font-size: 0.95rem;
        opacity: 0.9;
        margin-bottom: 20px;
        padding: 12px;
        border-left: 4px solid var(--futuristic-blue);
        background: rgba(0, 180, 216, 0.05);
        border-radius: 0 8px 8px 0;
    }

    .ai-rapor-alani {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.03), rgba(204, 0, 0, 0.05));
        padding: 25px;
        border-radius: 12px;
        border: 1px solid rgba(204, 0, 0, 0.2);
        margin: 20px 0;
        line-height: 1.8;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }

    .spinner-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px;
        margin: 20px 0;
    }

    .spinner {
        width: 50px;
        height: 50px;
        border: 5px solid rgba(204, 0, 0, 0.1);
        border-top: 5px solid var(--primary-red);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .futuristic-card {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.05), rgba(188, 0, 221, 0.05));
        border: 1px solid rgba(188, 0, 221, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }

    .futuristic-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(188, 0, 221, 0.15);
    }

    .site-result {
        background: rgba(57, 255, 20, 0.05);
        border-left: 4px solid var(--neon-green);
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }

    .guest-badge {
        background: linear-gradient(45deg, var(--cyber-purple), var(--futuristic-blue));
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 10px;
    }
    
    .motor-badge {
        background: linear-gradient(45deg, #ff6b00, #ffa500);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0 5px;
    }
    
    .calculator-panel {
        background: linear-gradient(135deg, rgba(0, 180, 216, 0.1), rgba(57, 255, 20, 0.1));
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--futuristic-blue);
        margin: 20px 0;
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
if "user" not in st.session_state: 
    st.session_state.user = None
    st.session_state.is_guest = False

if "bilgi" not in st.session_state: st.session_state.bilgi = None
if "konu" not in st.session_state: st.session_state.konu = ""
if "son_sorgu" not in st.session_state: st.session_state.son_sorgu = None
if "searching" not in st.session_state: st.session_state.searching = False
if "site_results" not in st.session_state: st.session_state.site_results = []

# --- 🔧 YARDIMCI FONKSİYONLAR ---
def temizle_metin(metin):
    """Reklam ve gereksiz içeriği temizle"""
    if not metin:
        return ""
    
    # Reklam anahtar kelimeleri
    reklam_kelimeler = [
        'reklam', 'sponsor', 'kupon', 'indirim', 'fırsat', 'satın al',
        'kampanya', 'bülten', 'abone ol', 'kaydol', 'üye ol', 'sepete ekle',
        'alışveriş', 'fiyat', 'TL', '$', '€', 'kampanyası', 'ürün'
    ]
    
    # Gereksiz ifadeler
    gereksiz_ifadeler = [
        'bu sayfayı paylaş', 'bizi takip edin', 'sosyal medya', 
        'yorum yap', 'yorumlar', 'tavsiye', 'öneri', 'ilginizi çekebilir'
    ]
    
    temiz_metin = metin
    for kelime in reklam_kelimeler + gereksiz_ifadeler:
        temiz_metin = re.sub(f'\\b{kelime}\\b', '', temiz_metin, flags=re.IGNORECASE)
    
    # HTML etiketlerini temizle
    temiz_metin = re.sub(r'<[^>]+>', ' ', temiz_metin)
    # Fazla boşlukları temizle
    temiz_metin = re.sub(r'\s+', ' ', temiz_metin).strip()
    
    return temiz_metin

def site_tara(url, sorgu, site_adi, timeout=15):
    """Belirli bir siteyi tarar ve içerik çıkarır"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sayfa metnini al
        metin = soup.get_text()
        
        # Reklamları temizle
        temiz_metin = temizle_metin(metin)
        
        # İlk 500 karakter al (gereksiz kısımları at)
        if len(temiz_metin) > 500:
            # Sorgu kelimelerine yakın kısımları bul
            kelimeler = sorgu.split()
            for kelime in kelimeler:
                if len(kelime) > 3:  # Kısa kelimeleri atla
                    idx = temiz_metin.lower().find(kelime.lower())
                    if idx != -1:
                        start = max(0, idx - 200)
                        end = min(len(temiz_metin), idx + 300)
                        temiz_metin = temiz_metin[start:end]
                        break
        
        return {
            'site': site_adi,
            'url': url,
            'icerik': temiz_metin[:500] + '...' if len(temiz_metin) > 500 else temiz_metin,
            'durum': 'başarılı'
        }
        
    except Exception as e:
        return {
            'site': site_adi,
            'url': url,
            'icerik': f"Site taranamadı: {str(e)}",
            'durum': 'hata'
        }

def hizli_arama(sorgu):
    """10 farklı siteyi paralel olarak tarar"""
    site_listesi = [
        {
            'url': f'https://tr.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': 'Wikipedia (Türkçe)'
        },
        {
            'url': f'https://en.wikipedia.org/wiki/{urllib.parse.quote(sorgu)}',
            'adi': 'Wikipedia (İngilizce)'
        },
        {
            'url': f'https://www.britannica.com/search?query={urllib.parse.quote(sorgu)}',
            'adi': 'Britannica'
        },
        {
            'url': f'https://www.etimolojiturkce.com/ara?q={urllib.parse.quote(sorgu)}',
            'adi': 'Etimoloji Türkçe'
        },
        {
            'url': f'https://www.tdk.gov.tr/ara?k={urllib.parse.quote(sorgu)}',
            'adi': 'TDK Sözlük'
        },
        {
            'url': f'https://www.biyografi.info/kisi/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': 'Biyografi.info'
        },
        {
            'url': f'https://www.techopedia.com/definition/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': 'Techopedia'
        },
        {
            'url': f'https://www.history.com/topics/{urllib.parse.quote(sorgu.lower().replace(" ", "-"))}',
            'adi': 'History.com'
        },
        {
            'url': f'https://www.nasa.gov/search/?q={urllib.parse.quote(sorgu)}',
            'adi': 'NASA'
        },
        {
            'url': f'https://www.ncbi.nlm.nih.gov/search/?term={urllib.parse.quote(sorgu)}',
            'adi': 'NCBI'
        }
    ]
    
    sonuclar = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_site = {
            executor.submit(site_tara, site['url'], sorgu, site['adi'], 15): site 
            for site in site_listesi
        }
        
        for future in as_completed(future_to_site):
            site = future_to_site[future]
            try:
                sonuc = future.result()
                sonuclar.append(sonuc)
            except Exception as e:
                sonuclar.append({
                    'site': site['adi'],
                    'url': site['url'],
                    'icerik': f"Hata: {str(e)}",
                    'durum': 'hata'
                })
    
    return sonuclar

def hesap_makinesi(ifade):
    """Güvenli hesap makinesi"""
    try:
        # Güvenlik için sadece matematiksel karakterlere izin ver
        guvenli_ifade = re.sub(r'[^0-9+\-*/(). ]', '', ifade)
        result = eval(guvenli_ifade, {"__builtins__": {}}, {})
        return f"📟 **Hesap Makinesi Sonucu:** {ifade} = **{result}**"
    except Exception as e:
        return f"⚠️ **Hesaplama Hatası:** {str(e)}"

# --- 🔐 KİMLİK DOĞRULAMA EKRANI ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='giris-kapsayici'><h1>TürkAI Analiz Merkezi</h1></div>", unsafe_allow_html=True)
        
        # Misafir Girişi Seçeneği
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Misafir Girişi", use_container_width=True):
                st.session_state.user = "Misafir"
                st.session_state.is_guest = True
                st.rerun()
        
        with col2:
            if st.button("📱 APK İndir", use_container_width=True):
                st.markdown(f'<a href="{APK_URL}" class="apk-buton-link" target="_blank">TürkAI Mobil Uygulamasını Yükle</a>', unsafe_allow_html=True)
        
        # Giriş Notu
        st.markdown("""
        <div class='not-alani'>
        <b>🤖 TürkAI Beta Sürümü</b><br>
        <small>• Hızlı mod ile 10 farklı siteyi paralel tarar</small><br>
        <small>• Her motorda hesap makinesi mevcut</small><br>
        <small>• Misafir olarak hızlı erişim imkanı</small>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Sistem Girişi", "📝 Yeni Kayıt"])
        
        with tab_login:
            u_in = st.text_input("Kullanıcı Kimliği")
            p_in = st.text_input("Erişim Şifresi", type="password")
            if st.button("Sisteme Eriş", use_container_width=True):
                h_p = hashlib.sha256(p_in.encode()).hexdigest()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, h_p))
                if c.fetchone():
                    st.session_state.user = u_in
                    st.session_state.is_guest = False
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
    # Kullanıcı Bilgisi
    user_display = st.session_state.user
    if st.session_state.is_guest:
        user_display += " <span class='guest-badge'>Misafir</span>"
    
    st.markdown(f"### 🛡️ Yetkili: {user_display}", unsafe_allow_html=True)
    
    if st.button("Oturumu Sonlandır", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Motor Seçimi
    m_secim = st.radio("Analiz Metodolojisi:", 
                      ["V1 (Ansiklopedik)", "V2 (Global Kaynaklar)", 
                       "V3 (Matematik Birimi)", "⚡ Hızlı (Çoklu Kaynak)"])
    
    # Hızlı Mod Açıklaması
    if m_secim == "⚡ Hızlı (Çoklu Kaynak)":
        st.info("""
        **Hızlı Mod Özellikleri:**
        • 10 farklı siteyi paralel tarar
        • Her site için 15 saniye zaman aşımı
        • Reklamlar otomatik temizlenir
        • Ansiklopedik format
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
    c.execute("SELECT konu, icerik FROM aramalar WHERE kullanici=? ORDER BY tarih DESC LIMIT 8", 
              (st.session_state.user,))
    for k, i in c.fetchall():
        if st.button(f"📄 {k[:22]}", key=f"h_{k}_{datetime.datetime.now().microsecond}", 
                    use_container_width=True):
            st.session_state.bilgi, st.session_state.konu, st.session_state.son_sorgu = i, k, k
            st.rerun()
    
    # Sidebar İndirme Butonu
    st.divider()
    st.markdown(f'<a href="{APK_URL}" class="sidebar-indir-link" target="_blank">📥 Uygulamayı İndir</a>', 
                unsafe_allow_html=True)

# --- 💻 ARAŞTIRMA ALANI ---
st.title("🔍 Araştırma Terminali")
st.markdown("""
<div class='tuyo-metni'>
💡 <b>Kullanım Yönergesi:</b> Araştırmak istediğiniz şeyin anahtar kelimesini yazınız 
(Örn: Türk kimdir? ❌ <b>Türk</b> ✅)<br>
<span class='motor-badge'>V1</span> + <span class='motor-badge'>V2</span> = <span class='motor-badge' style='background:linear-gradient(45deg, #cc0000, #ffa500);'>⚡ Hızlı</span>
</div>
""", unsafe_allow_html=True)

sorgu = st.chat_input("Veri girişi yapınız...")

if sorgu:
    st.session_state.son_sorgu = sorgu
    st.session_state.searching = True
    st.session_state.site_results = []
    
    # Düşünme animasyonunu göster
    with st.spinner(""):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class='spinner-container'>
            <div class='spinner'></div>
            <h3 style='color: #cc0000;'>TürkAI düşünüyor...</h3>
            <p>10 farklı kaynak taranıyor, reklamlar temizleniyor...</p>
        </div>
        """, unsafe_allow_html=True)
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        if m_secim == "V1 (Ansiklopedik)":
            try:
                r = requests.get(f"https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch={sorgu}&format=json", headers=headers).json()
                title = r['query']['search'][0]['title']
                page = requests.get(f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}", headers=headers).text
                soup = BeautifulSoup(page, 'html.parser')
                info = "\n\n".join([p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60][:5])
                st.session_state.bilgi, st.session_state.konu = info, title
            except Exception as e:
                st.session_state.bilgi = f"Sorgu sonucu bulunamadı: {str(e)}"
                st.session_state.konu = sorgu
        
        elif m_secim == "V2 (Global Kaynaklar)":
            try:
                wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                res = requests.get(wiki_api, headers=headers).json()
                st.session_state.bilgi, st.session_state.konu = res.get('extract', "Veri çekilemedi."), sorgu.upper()
            except Exception as e:
                st.session_state.bilgi = f"Sunucu bağlantı hatası: {str(e)}"
                st.session_state.konu = sorgu
        
        elif m_secim == "V3 (Matematik Birimi)":
            try:
                result = eval("".join(c for c in sorgu if c in "0123456789+-*/(). "), {"__builtins__": {}}, {})
                st.session_state.bilgi, st.session_state.konu = f"İşlem Sonucu: {result}", "MATEMATİKSEL ANALİZ"
            except Exception as e:
                st.session_state.bilgi = f"Hatalı matematiksel ifade: {str(e)}"
                st.session_state.konu = "HESAPLAMA HATASI"
        
        elif m_secim == "⚡ Hızlı (Çoklu Kaynak)":
            try:
                # Wikipedia'dan temel bilgi
                try:
                    wiki_api = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sorgu)}"
                    wiki_res = requests.get(wiki_api, headers=headers, timeout=10).json()
                    temel_bilgi = wiki_res.get('extract', '')
                except:
                    temel_bilgi = ''
                
                # 10 farklı siteyi tara
                site_sonuclari = hizli_arama(sorgu)
                st.session_state.site_results = site_sonuclari
                
                # Tüm sonuçları birleştir
                birlesik_icerik = f"# ⚡ HIZLI MOD SONUÇLARI: {sorgu.upper()}\n\n"
                
                if temel_bilgi:
                    birlesik_icerik += f"## 📚 Temel Bilgi (Wikipedia)\n{temel_bilgi}\n\n"
                
                birlesik_icerik += "## 🌐 Çoklu Kaynak Taraması\n"
                
                basarili_sayisi = sum(1 for s in site_sonuclari if s['durum'] == 'başarılı')
                birlesik_icerik += f"**{basarili_sayisi} site başarıyla tarandı:**\n\n"
                
                for sonuc in site_sonuclari:
                    if sonuc['durum'] == 'başarılı' and len(sonuc['icerik']) > 50:
                        birlesik_icerik += f"### 🔍 {sonuc['site']}\n"
                        birlesik_icerik += f"{sonuc['icerik']}\n\n"
                
                st.session_state.bilgi = birlesik_icerik
                st.session_state.konu = f"HIZLI: {sorgu.upper()}"
                
            except Exception as e:
                st.session_state.bilgi = f"Hızlı arama sırasında hata: {str(e)}"
                st.session_state.konu = sorgu
        
        # Düşünme animasyonunu kaldır
        thinking_placeholder.empty()
        st.session_state.searching = False
        
        # Veritabanına kaydet
        if st.session_state.bilgi and not st.session_state.is_guest:
            c.execute("INSERT INTO aramalar VALUES (?,?,?,?,?)", 
                     (st.session_state.user, st.session_state.konu, 
                      st.session_state.bilgi, str(datetime.datetime.now()), m_secim))
            conn.commit()
        
        st.rerun()

# --- 📊 RAPORLAMA ---
if st.session_state.son_sorgu:
    st.info(f"**Aktif Sorgu:** {st.session_state.son_sorgu}")
    
    # Hesap makinesi kontrolü (tüm sorgular için)
    if any(op in st.session_state.son_sorgu for op in ['+', '-', '*', '/', '(', ')']):
        try:
            hesap_sonucu = hesap_makinesi(st.session_state.son_sorgu)
            st.success(hesap_sonucu)
        except:
            pass

if st.session_state.bilgi:
    st.subheader(f"📊 Analiz Raporu: {st.session_state.konu}")
    
    # Site sonuçlarını göster (Hızlı mod için)
    if m_secim == "⚡ Hızlı (Çoklu Kaynak)" and st.session_state.site_results:
        with st.expander(f"🌐 Site Tarama Sonuçları ({len(st.session_state.site_results)} site)", expanded=True):
            basarili_sayisi = sum(1 for s in st.session_state.site_results if s['durum'] == 'başarılı')
            st.metric("Başarılı Tarama", f"{basarili_sayisi}/10 site")
            
            for sonuc in st.session_state.site_results:
                with st.container():
                    durum_emoji = "✅" if sonuc['durum'] == 'başarılı' else "❌"
                    st.markdown(f"**{durum_emoji} {sonuc['site']}**")
                    if sonuc['durum'] == 'başarılı':
                        st.markdown(f"<div class='site-result'>{sonuc['icerik']}</div>", unsafe_allow_html=True)
                    else:
                        st.warning(sonuc['icerik'])
                    st.divider()
    
    # Ana raporu göster
    st.markdown(f"<div class='ai-rapor-alani'>{st.session_state.bilgi}</div>", unsafe_allow_html=True)
    
    # PDF Rapor Oluşturma
    def rapor_pdf_olustur():
        try:
            pdf = FPDF()
            pdf.add_page()
            
            def tr_fix(t):
                d = {'İ':'I','ı':'i','Ş':'S','ş':'s','Ğ':'G','ğ':'g','Ü':'U','ü':'u','Ö':'O','ö':'o','Ç':'C','ç':'c'}
                for k,v in d.items(): 
                    t = t.replace(k,v)
                return re.sub(r'[^\x00-\x7F]+', ' ', t)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, txt="TURKAI HIZLI ANALIZ RAPORU", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            
            content = f"\nKonu: {tr_fix(st.session_state.konu)}\n\n"
            content += f"Kullanılan Motor: {m_secim}\n\n"
            content += f"Analiz Sonucu:\n{tr_fix(st.session_state.bilgi[:2000])}\n\n"
            
            if m_secim == "⚡ Hızlı (Çoklu Kaynak)" and st.session_state.site_results:
                content += "\nSite Tarama Özeti:\n"
                for sonuc in st.session_state.site_results:
                    content += f"- {sonuc['site']}: {sonuc['durum']}\n"
            
            content += f"\n\nYetkili: {tr_fix(st.session_state.user)}"
            if st.session_state.is_guest:
                content += " (Misafir)"
            content += f"\nTarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            pdf.multi_cell(0, 10, txt=content)
            return pdf.output(dest='S').encode('latin-1', 'replace')
        except Exception as e:
            return None

    pdf_v = rapor_pdf_olustur()
    if pdf_v:
        st.download_button(
            label="📊 Raporu Arşivle (PDF)", 
            data=pdf_v, 
            file_name=f"TurkAI_Rapor_{st.session_state.konu.replace(' ', '_')}.pdf", 
            mime="application/pdf",
            use_container_width=True
        )
    
    # Futuristik Özellikler
    st.markdown("---")
    st.markdown("### 🚀 Futuristik Özellikler")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 AI Özet Oluştur", use_container_width=True):
            st.info("Özellik geliştirme aşamasında...")
    
    with col2:
        if st.button("📈 Görselleştir", use_container_width=True):
            st.info("Veri görselleştirme aktif edilecek...")
    
    with col3:
        if st.button("🔗 İlgili Konular", use_container_width=True):
            st.info("İlgili konular analiz ediliyor...")
