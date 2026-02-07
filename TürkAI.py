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



# --- ⚙️ SİSTEM AYARLARI ---

st.set_page_config(page_title="TürkAI | Kurumsal Analiz Platformu", page_icon="🇹🇷", layout="wide")



# --- 🔗 GITHUB APK LINKI ---

APK_URL = "https://github.com/31madaracollet/TurkAI-v1/raw/refs/heads/main/4e47617eff77a24ebec8.apk"



# --- 🎨 TASARIM ---

st.markdown("""

    <style>

    :root { --primary-red: #cc0000; }

    h1, h2, h3 { color: var(--primary-red) !important; font-weight: 700 !important; }

    .giris-kapsayici { border: 1px solid rgba(204, 0, 0, 0.3); border-radius: 12px; padding: 40px; text-align: center; }

    .apk-buton-link { display: block; width: 100%; background-color: var(--primary-red); color: white !important; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-bottom: 20px; transition: 0.3s; }

    .sidebar-indir-link { display: block; background-color: transparent; color: inherit !important; text-align: center; padding: 8px; border-radius: 6px; text-decoration: none; border: 1px solid var(--primary-red); font-size: 13px; margin-top: 10px; }

    .not-alani { background-color: rgba(204, 0, 0, 0.05); color: var(--primary-red); padding: 10px; border-radius: 8px; border: 1px dashed var(--primary-red); margin-bottom: 20px; font-size: 0.85rem; text-align: center; }

    .ai-rapor-alani { border-left: 4px solid var(--primary-red); padding: 20px; background-color: rgba(128,128,128,0.05); border-radius: 4px; line-height: 1.6; }

    .stSpinner > div { border-top-color: #cc0000 !important; }

    </style>

""", unsafe_allow_html=True)



# --- 💾 VERİTABANI ---

def db_baslat():

    conn = sqlite3.connect('turkai_v220.db', check_same_thread=False)

    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')

    c.execute('CREATE TABLE IF NOT EXISTS aramalar (kullanici TEXT, konu TEXT, icerik TEXT, tarih TEXT, motor TEXT)')

    conn.commit()

    return conn, c

conn, c = db_baslat()



# --- 🔄 FONKSİYONLAR ---



def yazi_efekti(text):

    placeholder = st.empty()

    full_text = ""

    for word in text.split():

        full_text += word + " "

        placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}▌</div>", unsafe_allow_html=True)

        time.sleep(0.02)

    placeholder.markdown(f"<div class='ai-rapor-alani'>{full_text}</div>", unsafe_allow_html=True)



def derin_dusunen_motor(sorgu):

    """Kütüphanesiz, garantili derin arama motoru"""

    durum = st.empty()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

    

    try:

        # DuckDuckGo HTML sürümünü kullanarak bot engelini aşıyoruz

        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(sorgu + ' sitesi:.tr')}"

        res = requests.get(search_url, headers=headers, timeout=10)

        soup = BeautifulSoup(res.text, 'html.parser')

        

        # Linkleri bul

        links = [a['href'] for a in soup.find_all('a', class_='result__url', href=True)][:10]

        

        if not links:

            return wiki_arama(sorgu)



        derin_bilgi = ""

        sayac = 0

        

        for link in links:

            sayac += 1

            durum.caption("🧠 TürkAI Derin Analiz Yapıyor")
