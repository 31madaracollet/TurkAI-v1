import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import hashlib
import urllib.parse
import re
import time
from fpdf import FPDF

# --- CONFIGURATION DU SYSTÈME ---
st.set_page_config(page_title="TürkAI | Analyse Profonde", page_icon="🇹🇷", layout="wide")

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    :root { --primary-red: #cc0000; }
    .stSpinner > div { border-top-color: var(--primary-red) !important; }
    .ai-bubble {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid var(--primary-red);
        margin-bottom: 10px;
        color: #1a1a1a;
    }
    .giris-kutusu {
        padding: 30px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('turkai_v3.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (user TEXT, query TEXT, result TEXT, date TEXT)')
    conn.commit()
    return conn, c

conn, c = init_db()

# --- LOGIQUE DE RECHERCHE ---

def typewriter_effect(text):
    """Affiche le texte de manière progressive (tane tane)."""
    placeholder = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(f"<div class='ai-bubble'>{displayed_text}▌</div>", unsafe_allow_html=True)
        time.sleep(0.01)
    placeholder.markdown(f<div class='ai-bubble'>{displayed_text}</div>", unsafe_allow_html=True)

def is_math(query):
    """Vérifie si la requête est une opération mathématique."""
    return bool(re.match(r'^[0-9+\-*/().\s^]+$', query))

def clean_content(html):
    """Nettoie le contenu pour éviter les publicités."""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'ins', 'iframe']):
        tag.decompose()
    
    # On récupère les paragraphes qui ressemblent à du vrai texte (pas des menus de pub)
    paragraphs = soup.find_all('p')
    valid_text = []
    for p in paragraphs:
        txt = p.get_text().strip()
        if len(txt) > 60 and not any(x in txt.lower() for x in ['reklam', 'tıklayın', 'abone', 'çerez']):
            valid_text.append(txt)
    return "\n\n".join(valid_text[:5])

def deep_search(query):
    """Moteur Derin Düşünen : 25 sites turcs, 10s par site."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    # On force la recherche sur les domaines turcs ou avec le mot clé 'turkce'
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query + ' site:.tr OR site:.com.tr')}"
    
    try:
        r = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "url?q=" in href and not "google.com" in href:
                clean_link = href.split("url?q=")[1].split("&sa=")[0]
                links.append(clean_link)
        
        links = list(dict.fromkeys(links))[:25] # Top 25 sites
        
        for i, link in enumerate(links):
            with st.status(f"Analiz ediliyor ({i+1}/25): {link[:30]}...", expanded=False) as status:
                try:
                    site_res = requests.get(link, headers=headers, timeout=10)
                    content = clean_content(site_res.text)
                    if content:
                        status.update(label="✅ Bilgi bulundu!", state="complete")
                        return content
                except:
                    status.update(label="❌ Zaman aşımı veya erişim reddedildi.", state="error")
                    continue
        return "Üzgünüm, 25 farklı Türkçe kaynağı taradım ancak temiz bir sonuç bulamadım."
    except:
        return "Arama motoru bağlantı hatası."

def fast_search(query):
    """Moteur Hızlı : Wikipedia odaklı."""
    try:
        wiki_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        res = requests.get(wiki_url, timeout=5).json()
        return res.get('extract', "Hızlı motor sonuç bulamadı.")
    except:
        return "Wikipedia bağlantı hatası."

# --- INTERFACE UTILISATEUR ---

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🇹🇷 TürkAI Analiz Platformu")
    col1, col2 = st.columns([2,1])
    
    with col1:
        st.markdown("<div class='giris-kutusu'>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        with tab_log:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("Sisteme Gir", use_container_width=True):
                    h_p = hashlib.sha256(p.encode()).hexdigest()
                    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, h_p))
                    if c.fetchone():
                        st.session_state.user = u
                        st.rerun()
                    else: st.error("Hatalı giriş.")
            with b_col2:
                if st.button("👤 Misafir Girişi", use_container_width=True):
                    st.session_state.user = "Misafir"
                    st.rerun()
        
        with tab_reg:
            nu = st.text_input("Yeni Kullanıcı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (nu, hashlib.sha256(np.encode()).hexdigest()))
                    conn.commit()
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                except: st.error("Bu kullanıcı adı alınmış.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- PANEL ANALİZ ---

with st.sidebar:
    st.write(f"Hoş geldin, **{st.session_state.user}**")
    motor = st.radio("Analiz Motoru Seçin:", ["Hızlı (Wikipedia)", "Derin Düşünen (25 Site)"])
    if st.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()

st.header("🔍 Araştırma Terminali")

query = st.chat_input("Bir konu yazın veya matematiksel işlem yapın...")

if query:
    # On vide l'écran précédent pour simuler la disparition du chat direct
    st.empty()
    
    with st.spinner('TürkAI Düşünüyor...'):
        # 1. Check Matematik
        if is_math(query):
            try:
                # Sécurité basique pour eval
                result = eval(query, {"__builtins__": {}}, {})
                final_text = f"**Matematiksel İşlem Sonucu:** {result}"
            except:
                final_text = "Matematiksel ifade anlaşılamadı."
        
        # 2. Check Motor
        elif motor == "Hızlı (Wikipedia)":
            final_text = fast_search(query)
        else:
            final_text = deep_search(query)
            
    # Affichage progressif
    typewriter_effect(final_text)
    
    # Footer Actions
    f_col1, f_col2 = st.columns([1, 4])
    with f_col1:
        if st.button("👎 Beğenmedim"):
            st.toast("Geri bildiriminiz alındı. Motor geliştirilecek.")
