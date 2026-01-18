import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from fpdf import FPDF
import datetime
import sqlite3
import hashlib

# --- ⚙️ KARAKTER TEMİZLEME MOTORU (YENİ) ---
def metni_pırıl_pırıl_yap(metin):
    """Okunmayan garip karakterleri, Unicode hatalarını ve gereksiz sembolleri temizler."""
    if not metin: return ""
    
    # 1. Unicode bozukluklarını ve gizli karakterleri temizle (\xa0, \u200b vb.)
    metin = metin.replace('\xa0', ' ').replace('\u200b', '').replace('\u200e', '').replace('\u200f', '')
    
    # 2. Okunmayan '' sembollerini ve garip ASCII karakterlerini kaldır
    metin = metin.replace('', '')
    
    # 3. Wikipedia'dan gelen [1], [2] gibi kaynak numaralarını temizle
    metin = re.sub(r'\[\d+\]', '', metin)
    
    # 4. Sadece harfler, rakamlar ve temel noktalama işaretleri kalsın (Gereksiz abuk subuk simgeleri siler)
    # Bu kısım metni "insan okuyabilir" hale getirir
    metin = re.sub(r'[^\w\s\.\,\!\?\-\:\(\)\"\']+', ' ', metin)
    
    # 5. Çift boşlukları tek boşluğa indir
    metin = re.sub(r'\s+', ' ', metin).strip()
    
    return metin

def kalkan(metin):
    """Gelişmiş Küfür ve Filtreleme Kalkanı"""
    t = metin.lower()
    # Türkçe harfleri İngilizceye çevirerek kontrol et (Hileleri yakalamak için)
    tr_map = str.maketrans("şçğüöıİ", "scguoiI")
    t = t.translate(tr_map)
    # Sayıları harfe çevir (s1k -> sik gibi)
    t = t.translate(str.maketrans("01347", "oiEat"))
    # Sadece harfler kalsın (araya nokta koyanları yakalar: s.i.k -> sik)
    t = re.sub(r'[^a-z]', '', t)
    
    kara_liste = ["amk", "aq", "pic", "sik", "yarrak", "got", "meme", "dassak", "ibne", "kahpe", "oros"]
    return not any(kelime in t for kelime in kara_liste)

# --- 📄 PDF VE DİĞER FONKSİYONLARDA KULLANIMI ---
def pdf_yap(konu, icerik):
    pdf = FPDF()
    pdf.add_page()
    def tr(m):
        # PDF Latin-1 desteklediği için karakterleri güvenli hale getir
        m = metni_pırıl_pırıl_yap(m)
        map = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ü":"U","ü":"u","Ö":"O","ö":"o","Ç":"C","ç":"c"}
        for k, v in map.items(): m = m.replace(k, v)
        return m.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, tr(konu), ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, tr(icerik))
    return pdf.output(dest='S').encode('latin-1')

# --- 📥 SORGULAMA BÖLÜMÜNDEKİ DEĞİŞİKLİK ---
# Wikipedia'dan veri geldiğinde 'metni_pırıl_pırıl_yap' fonksiyonunu çağırıyoruz:
# bilgi = metni_pırıl_pırıl_yap("\n\n".join(paragraf[:6]))
