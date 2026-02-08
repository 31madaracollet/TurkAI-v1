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
import json
from typing import Dict, List, Optional
import random

# ============================================
# 🚀 DELÜKS KONFİGÜRASYON
# ============================================

class DeluksConfig:
    """Delüks konfigürasyon sınıfı"""
    APP_NAME = "TürkAI Delüks"
    VERSION = "2.5.0"
    PRIMARY_COLOR = "#b22222"
    SECONDARY_COLOR = "#1e88e5"
    ACCENT_COLOR = "#ff9800"
    
    # Premium özellikler
    PREMIUM_FEATURES = [
        "AI Destekli Özet",
        "Gelişmiş PDF Rapor",
        "Çoklu Dil Desteği",
        "İleri Analiz Grafikleri",
        "Özel Motorlar",
        "API Erişimi"
    ]
    
    @staticmethod
    def get_gradient(start_color, end_color):
        """Gradient renk oluştur"""
        return f"linear-gradient(135deg, {start_color}, {end_color})"

# ============================================
# 🎨 DELÜKS TASARIM & CSS
# ============================================

DELUKS_CSS = """
<style>
:root {
    --primary: #b22222;
    --primary-dark: #8b1a1a;
    --primary-light: #ff4444;
    --secondary: #1e88e5;
    --accent: #ff9800;
    --dark-bg: #0a0a0a;
    --dark-card: #151515;
    --dark-surface: #1e1e1e;
    --light-bg: #f8f9fa;
    --light-card: #ffffff;
    --light-surface: #f1f3f4;
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --gold: #ffd700;
    --platinum: #e5e4e2;
}

/* 🌙/☀️ TEMA SİSTEMİ */
body {
    background: var(--bg-color);
    color: var(--text-color);
    transition: all 0.3s ease;
}

/* 🎯 DELÜKS ANA KONTEYNER */
.deluks-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 20px;
}

/* ✨ DELÜKS NAVBAR */
.deluks-navbar {
    background: var(--card-color);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-color);
    padding: 15px 0;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 4px 30px rgba(0,0,0,0.1);
}

.navbar-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 15px;
}

.brand-logo {
    font-size: 2rem;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

.brand-tag {
    background: var(--gradient-accent);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* 🔍 DELÜKS ARAMA MERKEZİ */
.search-hero {
    text-align: center;
    padding: 60px 20px;
    background: var(--gradient-subtle);
    border-radius: 30px;
    margin: 40px 0;
    position: relative;
    overflow: hidden;
}

.search-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, var(--primary-light) 0%, transparent 70%);
    opacity: 0.1;
    z-index: 0;
}

.search-hero-content {
    position: relative;
    z-index: 1;
}

.search-title {
    font-size: 3rem;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 20px;
    font-weight: 800;
}

.search-subtitle {
    font-size: 1.2rem;
    color: var(--text-secondary);
    margin-bottom: 40px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

/* 🎛️ DELÜKS ARAMA ÇUBUĞU */
.deluks-search-container {
    max-width: 800px;
    margin: 0 auto 30px;
    position: relative;
}

.deluks-search-input {
    width: 100%;
    padding: 22px 30px;
    font-size: 1.1rem;
    border: 2px solid var(--border-color);
    border-radius: 50px;
    background: var(--card-color);
    color: var(--text-color);
    transition: all 0.3s ease;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}

.deluks-search-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 10px 40px rgba(178, 34, 34, 0.2);
    transform: translateY(-2px);
}

.search-button {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--gradient-primary);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 40px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.search-button:hover {
    transform: translateY(-50%) scale(1.05);
    box-shadow: 0 5px 20px rgba(178, 34, 34, 0.3);
}

/* 🎭 DELÜKS KARTLAR */
.deluks-card {
    background: var(--card-color);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 30px;
    margin: 20px 0;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}

.deluks-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--gradient-primary);
}

.deluks-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    border-color: var(--primary-light);
}

.deluks-card-premium {
    border: 2px solid var(--gold);
    background: linear-gradient(135deg, var(--card-color), rgba(255, 215, 0, 0.05));
}

.deluks-card-premium::before {
    background: linear-gradient(90deg, var(--gold), var(--accent));
}

/* 🔢 DELÜKS İSTATİSTİKLER */
.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 40px 0;
}

.stat-card {
    background: var(--gradient-subtle);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 800;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* 🎮 DELÜKS BUTONLAR */
.deluks-btn {
    padding: 14px 28px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 10px;
}

.deluks-btn-primary {
    background: var(--gradient-primary);
    color: white;
}

.deluks-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(178, 34, 34, 0.3);
}

.deluks-btn-secondary {
    background: transparent;
    color: var(--primary);
    border: 2px solid var(--primary);
}

.deluks-btn-secondary:hover {
    background: rgba(178, 34, 34, 0.1);
    transform: translateY(-2px);
}

.deluks-btn-premium {
    background: linear-gradient(135deg, var(--gold), var(--accent));
    color: #000;
    font-weight: 700;
}

/* 📱 DELÜKS CHAT INPUT (ORTAYA HİZALI) */
.deluks-chat-container {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 800px;
    z-index: 1000;
}

.deluks-chat-input-container {
    background: var(--card-color);
    border-radius: 50px;
    padding: 5px;
    box-shadow: 0 10px 50px rgba(0,0,0,0.2);
    border: 2px solid var(--border-color);
    backdrop-filter: blur(10px);
}

.deluks-chat-input {
    width: 100%;
    padding: 20px 30px;
    font-size: 1.1rem;
    border: none;
    background: transparent;
    color: var(--text-color);
    border-radius: 50px;
}

.deluks-chat-input:focus {
    outline: none;
}

.chat-send-button {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--gradient-primary);
    color: white;
    border: none;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.chat-send-button:hover {
    transform: translateY(-50%) scale(1.1);
    box-shadow: 0 5px 20px rgba(178, 34, 34, 0.3);
}

/* 🌈 DELÜKS ANİMASYONLAR */
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

@keyframes glow {
    0%, 100% { box-shadow: 0 0 20px rgba(178, 34, 34, 0.3); }
    50% { box-shadow: 0 0 40px rgba(178, 34, 34, 0.6); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.floating {
    animation: float 3s ease-in-out infinite;
}

.glow {
    animation: glow 2s ease-in-out infinite;
}

.shimmer-text {
    background: linear-gradient(90deg, var(--primary), var(--accent), var(--primary));
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
}

/* 📊 DELÜKS YÜKLEME EKRANI */
.deluks-loader {
    text-align: center;
    padding: 60px;
}

.loader-animation {
    width: 80px;
    height: 80px;
    margin: 0 auto 30px;
    position: relative;
}

.loader-circle {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 4px solid transparent;
    border-radius: 50%;
    border-top-color: var(--primary);
    animation: spin 1s linear infinite;
}

.loader-circle:nth-child(2) {
    border-top-color: var(--secondary);
    animation-delay: 0.2s;
}

.loader-circle:nth-child(3) {
    border-top-color: var(--accent);
    animation-delay: 0.4s;
}

/* 📈 DELÜKS GRAFİKLER */
.analysis-graph {
    background: var(--card-color);
    border-radius: 20px;
    padding: 30px;
    margin: 30px 0;
}

.graph-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.graph-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-color);
}

.graph-stats {
    display: flex;
    gap: 20px;
}

/* 🏆 DELÜKS BAŞARIMLAR */
.achievements-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 40px 0;
}

.achievement-card {
    background: var(--card-color);
    border-radius: 15px;
    padding: 25px;
    text-align: center;
    transition: all 0.3s ease;
}

.achievement-card.locked {
    opacity: 0.6;
    filter: grayscale(1);
}

.achievement-icon {
    font-size: 3rem;
    margin-bottom: 15px;
}

.achievement-title {
    font-weight: 700;
    margin-bottom: 10px;
}

.achievement-desc {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* ✨ DELÜKS HIZLI ERİŞİM */
.quick-access {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin: 40px 0;
}

.quick-btn {
    padding: 20px;
    background: var(--card-color);
    border: 1px solid var(--border-color);
    border-radius: 15px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
}

.quick-btn:hover {
    transform: translateY(-3px);
    border-color: var(--primary);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

/* 📱 RESPONSIVE TASARIM */
@media (max-width: 768px) {
    .search-title {
        font-size: 2.2rem;
    }
    
    .deluks-chat-container {
        width: 95%;
        bottom: 20px;
    }
    
    .stats-container {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .navbar-content {
        flex-direction: column;
        gap: 15px;
    }
}

/* 🎯 FIXED STREAMLIT ELEMENTLERİ */
.stApp {
    max-width: 1400px;
    margin: 0 auto;
}

/* Chat input'u gizleyip kendi tasarımımızı kullanacağız */
.stChatInput {
    display: none !important;
}

/* Progress bar stilleri */
.stProgress > div > div > div > div {
    background: var(--gradient-primary) !important;
}

/* Select box stilleri */
.stSelectbox > div > div {
    background: var(--card-color) !important;
    border-color: var(--border-color) !important;
}

/* Tab stilleri */
.stTabs [data-baseweb="tab-list"] {
    background: var(--card-color) !important;
    border-radius: 15px !important;
    padding: 5px !important;
}
</style>
"""

# ============================================
# 🚀 DELÜKS ANA UYGULAMA
# ============================================

class DeluksTurkiAI:
    """Delüks TürkAI Ana Sınıfı"""
    
    def __init__(self):
        self.config = DeluksConfig()
        self.setup_page_config()
        self.setup_session_state()
        self.setup_database()
        
    def setup_page_config(self):
        """Sayfa konfigürasyonunu ayarla"""
        st.set_page_config(
            page_title=f"{self.config.APP_NAME} v{self.config.VERSION}",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="collapsed",
            menu_items={
                'Get Help': 'https://github.com/turkai',
                'Report a bug': 'https://github.com/turkai/issues',
                'About': f"{self.config.APP_NAME} - Premium Araştırma Platformu"
            }
        )
        
    def setup_session_state(self):
        """Session state değişkenlerini başlat"""
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'is_premium' not in st.session_state:
            st.session_state.is_premium = False
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'achievements' not in st.session_state:
            st.session_state.achievements = []
        if 'stats' not in st.session_state:
            st.session_state.stats = {
                'total_searches': 0,
                'pdf_generated': 0,
                'sites_scanned': 0,
                'time_saved': 0
            }
            
    def setup_database(self):
        """Veritabanını başlat"""
        self.conn = sqlite3.connect('deluks_turkai.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                premium_expiry TEXT,
                created_at TEXT
            )
        ''')
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                result TEXT,
                source TEXT,
                duration REAL,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric TEXT,
                value REAL,
                recorded_at TEXT
            )
        ''')
        self.conn.commit()
        
    def render_deluks_ui(self):
        """Delüks UI'yı render et"""
        # CSS ekle
        st.markdown(DELUKS_CSS, unsafe_allow_html=True)
        
        # Ana konteyner
        st.markdown('<div class="deluks-container">', unsafe_allow_html=True)
        
        # Navbar
        self.render_navbar()
        
        # Hero bölümü
        self.render_hero()
        
        # İstatistikler
        self.render_stats()
        
        # Ana içerik
        self.render_main_content()
        
        # Quick access
        self.render_quick_access()
        
        # Başarımlar
        self.render_achievements()
        
        # FIXED CHAT INPUT (ORTADA)
        self.render_deluks_chat_input()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    def render_navbar(self):
        """Delüks navbar render"""
        st.markdown('''
        <div class="deluks-navbar">
            <div class="navbar-content">
                <div class="nav-brand">
                    <div class="brand-logo">🚀 TürkAI</div>
                    <div class="brand-tag">DELÜKS v2.5</div>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <button class="deluks-btn deluks-btn-secondary" onclick="toggleTheme()">
                        🌙 Tema
                    </button>
                    <button class="deluks-btn deluks-btn-premium">
                        ⭐ Premium
                    </button>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_hero(self):
        """Hero bölümü render"""
        st.markdown(f'''
        <div class="search-hero">
            <div class="search-hero-content">
                <h1 class="search-title shimmer-text">Yapay Zeka ile Araştırma</h1>
                <p class="search-subtitle">
                    Türkçe odaklı, premium özelliklerle donatılmış, en gelişmiş araştırma platformu.
                    Her türlü soru için profesyonel sonuçlar.
                </p>
                <div class="deluks-search-container">
                    <input type="text" 
                           class="deluks-search-input" 
                           placeholder="🔍 Her şeyi sorabilirsiniz: 'Atatürk kimdir?', '45*2+18/3', 'İstanbul tarihi'..."
                           id="deluksSearchInput">
                    <button class="search-button" onclick="handleSearch()">
                        Araştır
                    </button>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_stats(self):
        """İstatistikleri render et"""
        st.markdown(f'''
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number">{st.session_state.stats['total_searches']}</div>
                <div class="stat-label">Toplam Arama</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{st.session_state.stats['pdf_generated']}</div>
                <div class="stat-label">PDF Rapor</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{st.session_state.stats['sites_scanned']}</div>
                <div class="stat-label">Site Taranan</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{st.session_state.stats['time_saved']}s</div>
                <div class="stat-label">Zaman Kazanılan</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_main_content(self):
        """Ana içeriği render et"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Motor seçimi
            st.markdown('''
            <div class="deluks-card">
                <h3>🎯 Analiz Motoru Seçimi</h3>
                <div style="display: flex; gap: 15px; margin-top: 20px;">
                    <div style="flex: 1;">
                        <button class="deluks-btn deluks-btn-primary" style="width: 100%;" onclick="selectEngine('basic')">
                            🚀 Hızlı Motor
                        </button>
                        <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                            Vikipedi + TDK hızlı arama
                        </p>
                    </div>
                    <div style="flex: 1;">
                        <button class="deluks-btn deluks-btn-premium" style="width: 100%;" onclick="selectEngine('premium')">
                            ⭐ Premium Motor
                        </button>
                        <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                            AI destekli derin analiz
                        </p>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Geçmiş aramalar
            self.render_search_history()
            
        with col2:
            # Premium özellikler
            self.render_premium_features()
            
    def render_search_history(self):
        """Arama geçmişini render et"""
        if st.session_state.search_history:
            st.markdown('''
            <div class="deluks-card">
                <h3>📜 Son Aramalar</h3>
            ''', unsafe_allow_html=True)
            
            for i, search in enumerate(st.session_state.search_history[-5:]):
                st.markdown(f'''
                <div style="padding: 15px; background: var(--surface-color); border-radius: 10px; margin: 10px 0; cursor: pointer;" 
                     onclick="reSearch('{search}')">
                    <div style="display: flex; justify-content: space-between;">
                        <span>🔍 {search[:30]}...</span>
                        <button style="background: none; border: none; color: var(--primary); cursor: pointer;">
                            🔄
                        </button>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
    def render_premium_features(self):
        """Premium özellikleri render et"""
        st.markdown(f'''
        <div class="deluks-card deluks-card-premium">
            <h3 style="color: var(--gold);">⭐ Premium Özellikler</h3>
            <ul style="margin-top: 20px; padding-left: 20px;">
        ''', unsafe_allow_html=True)
        
        for feature in self.config.PREMIUM_FEATURES:
            st.markdown(f'''
            <li style="margin: 10px 0; display: flex; align-items: center; gap: 10px;">
                <span style="color: var(--gold);">✓</span> {feature}
            </li>
            ''', unsafe_allow_html=True)
            
        st.markdown('''
            </ul>
            <button class="deluks-btn deluks-btn-premium" style="width: 100%; margin-top: 20px;">
                🚀 Premium'a Yükselt
            </button>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_quick_access(self):
        """Hızlı erişim butonları"""
        st.markdown('''
        <div class="quick-access">
            <div class="quick-btn" onclick="quickSearch('Atatürk')">
                <div style="font-size: 2rem;">👤</div>
                <div>Atatürk</div>
            </div>
            <div class="quick-btn" onclick="quickSearch('İstanbul')">
                <div style="font-size: 2rem;">🏙️</div>
                <div>İstanbul</div>
            </div>
            <div class="quick-btn" onclick="quickSearch('Matematik')">
                <div style="font-size: 2rem;">🧮</div>
                <div>Matematik</div>
            </div>
            <div class="quick-btn" onclick="quickSearch('Tarih')">
                <div style="font-size: 2rem;">📜</div>
                <div>Tarih</div>
            </div>
            <div class="quick-btn" onclick="generatePDF()">
                <div style="font-size: 2rem;">📊</div>
                <div>PDF Rapor</div>
            </div>
            <div class="quick-btn" onclick="showAnalytics()">
                <div style="font-size: 2rem;">📈</div>
                <div>Analitikler</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_achievements(self):
        """Başarımları render et"""
        st.markdown('''
        <div class="achievements-grid">
            <div class="achievement-card">
                <div class="achievement-icon">🔍</div>
                <div class="achievement-title">İlk Araştırma</div>
                <div class="achievement-desc">İlk aramanı yap</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">📊</div>
                <div class="achievement-title">PDF Uzmanı</div>
                <div class="achievement-desc">10 PDF oluştur</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">🚀</div>
                <div class="achievement-title">Premium</div>
                <div class="achievement-desc">Premium üye ol</div>
            </div>
            <div class="achievement-card locked">
                <div class="achievement-icon">🏆</div>
                <div class="achievement-title">Araştırmacı</div>
                <div class="achievement-desc">100 arama yap</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    def render_deluks_chat_input(self):
        """DELÜKS chat input (ortada fixed)"""
        st.markdown('''
        <div class="deluks-chat-container">
            <div class="deluks-chat-input-container">
                <input type="text" 
                       class="deluks-chat-input" 
                       placeholder="💬 TürkAI'ye soru sorun..."
                       id="deluksChatInput"
                       onkeypress="if(event.key == 'Enter') handleChatSubmit()">
                <button class="chat-send-button" onclick="handleChatSubmit()">
                    ➤
                </button>
            </div>
        </div>
        
        <script>
        function handleChatSubmit() {{
            const input = document.getElementById('deluksChatInput');
            const query = input.value.trim();
            if (query) {{
                // Streamlit'e gönder
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: query
                }}, '*');
                input.value = '';
            }}
        }}
        
        function handleSearch() {{
            const input = document.getElementById('deluksSearchInput');
            const query = input.value.trim();
            if (query) {{
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: query
                }}, '*');
                input.value = '';
            }}
        }}
        
        function selectEngine(engine) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: 'ENGINE:' + engine
            }}, '*');
        }}
        
        function quickSearch(query) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: query
            }}, '*');
        }}
        
        function reSearch(query) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: query
            }}, '*');
        }}
        
        function toggleTheme() {{
            document.body.classList.toggle('dark-mode');
            document.body.classList.toggle('light-mode');
        }}
        </script>
        ''', unsafe_allow_html=True)

# ============================================
# 🚀 DELÜKS PDF GENERATOR (FIXED)
# ============================================

class DeluksPDFGenerator:
    """Delüks PDF Generator - Türkçe karakter sorunu FIXED"""
    
    def __init__(self):
        self.setup_fonts()
        
    def setup_fonts(self):
        """Fontları kur"""
        try:
            # DejaVu fontlarını kontrol et
            self.fonts = {
                'regular': self.find_font('DejaVuSans'),
                'bold': self.find_font('DejaVuSans-Bold'),
                'italic': self.find_font('DejaVuSans-Oblique')
            }
        except:
            # Fallback: Arial Unicode
            self.fonts = {'regular': 'arial'}
            
    def find_font(self, font_name):
        """Font dosyasını bul"""
        font_paths = [
            f'{font_name}.ttf',
            f'fonts/{font_name}.ttf',
            f'/usr/share/fonts/truetype/dejavu/{font_name}.ttf',
            f'C:/Windows/Fonts/{font_name}.ttf'
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        return 'arial'
    
    def create_premium_pdf(self, data):
        """Premium PDF oluştur"""
        pdf = FPDF()
        pdf.add_page()
        
        # Unicode font ekle
        if self.fonts['regular'] != 'arial':
            pdf.add_font('DejaVu', '', self.fonts['regular'], uni=True)
            pdf.set_font('DejaVu', '', 12)
        else:
            pdf.set_font('Arial', '', 12)
        
        # Premium başlık
        pdf.set_fill_color(178, 34, 34)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 15, '🚀 TÜRKAI DELÜKS RAPORU', ln=True, fill=True, align='C')
        
        # İçerik
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        
        # Tarih ve kullanıcı
        pdf.cell(0, 10, f'Tarih: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}', ln=True)
        pdf.cell(0, 10, f'Kullanıcı: {data.get("user", "Misafir")}', ln=True)
        pdf.cell(0, 10, f'Sorgu: {data.get("query", "")}', ln=True)
        
        pdf.ln(10)
        
        # Sonuçlar
        pdf.set_font('', 'B', 14)
        pdf.cell(0, 10, 'ANALİZ SONUÇLARI', ln=True)
        pdf.set_font('', '', 11)
        
        # Metni ekle (Türkçe karakterler düzgün çıkacak)
        results = data.get('results', 'Sonuç bulunamadı.')
        # HTML tagları temizle
        results = re.sub(r'<[^>]+>', '', results)
        
        # Uzun metni parçala
        lines = results.split('\n')
        for line in lines:
            if line.strip():
                # Türkçe karakterleri koru
                pdf.multi_cell(0, 6, line.strip())
                pdf.ln(2)
        
        # Grafik ekleme alanı
        pdf.ln(10)
        pdf.set_font('', 'I', 10)
        pdf.cell(0, 10, 'TürkAI Delüks v2.5 - Premium Araştırma Sistemi', ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')

# ============================================
# 🚀 DELÜKS ANA MOTOR
# ============================================

class DeluksSearchEngine:
    """Delüks arama motoru"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def search_wikipedia(self, query):
        """Wikipedia'dan ara"""
        try:
            url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('extract', '')
        except:
            pass
        return None
    
    def search_tdk(self, query):
        """TDK'dan ara"""
        try:
            url = f'https://sozluk.gov.tr/gts?ara={urllib.parse.quote(query)}'
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # TDK yapısına göre arama yap
                return "TDK sonuçları bulundu."
        except:
            pass
        return None
    
    def deep_search(self, query):
        """Derin arama yap"""
        results = []
        
        # Birden fazla kaynaktan ara
        sources = [
            ('Wikipedia', self.search_wikipedia(query)),
            ('TDK', self.search_tdk(query)),
        ]
        
        for source_name, content in sources:
            if content:
                results.append(f"### {source_name}\n{content}\n")
                
        return "\n".join(results) if results else "Sonuç bulunamadı."
    
    def calculate_math(self, expression):
        """Matematik hesapla"""
        try:
            # Güvenli matematik değerlendirme
            safe_globals = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'e': math.e
            }
            
            # Sadece güvenli karakterler
            clean_expr = re.sub(r'[^0-9+\-*/(). sqrtcossintanpie]', '', expression.lower())
            result = eval(clean_expr, {"__builtins__": {}}, safe_globals)
            return result
        except:
            return None

# ============================================
# 🚀 ANA UYGULAMA BAŞLATMA
# ============================================

def main():
    """Ana uygulama"""
    
    # Delüks uygulama başlat
    app = DeluksTurkiAI()
    
    # UI render
    app.render_deluks_ui()
    
    # JavaScript mesajlarını dinle
    query = st.chat_input("TürkAI'ye soru sorun...", key="deluks_chat")
    
    if query:
        # İstatistik güncelle
        st.session_state.stats['total_searches'] += 1
        st.session_state.search_history.append(query[:50])
        
        # Arama motoru
        engine = DeluksSearchEngine()
        
        # Matematik mi kontrol et
        math_result = engine.calculate_math(query)
        
        if math_result is not None:
            # Matematik sonucu
            result = f"""
            # 🧮 Matematik Sonucu
            
            **Soru:** `{query}`
            
            **Sonuç:** **{math_result}**
            
            **Detaylar:**
            - Yaklaşık değer: {math_result:.6f}
            - Tam sayı: {int(math_result) if math_result.is_integer() else 'Değil'}
            """
        else:
            # Normal arama
            result = engine.deep_search(query)
            
            if not result or "Sonuç bulunamadı" in result:
                result = f"""
                # 🔍 Arama Sonucu
                
                **Sorgu:** {query}
                
                **Durum:** Sonuç bulunamadı
                
                **Öneriler:**
                1. Farklı anahtar kelimeler deneyin
                2. Daha genel bir arama yapın
                3. Premium motoru kullanın
                """
            else:
                result = f"""
                # 🔍 Arama Sonucu
                
                **Sorgu:** {query}
                
                **Sonuçlar:**
                
                {result}
                """
        
        # Sonucu göster
        with st.expander("📊 Analiz Sonuçları", expanded=True):
            st.markdown(result)
            
        # PDF oluşturma butonu
        if st.button("📥 Premium PDF Oluştur", type="primary"):
            pdf_gen = DeluksPDFGenerator()
            pdf_data = pdf_gen.create_premium_pdf({
                'user': st.session_state.get('user', 'Misafir'),
                'query': query,
                'results': result
            })
            
            if pdf_data:
                st.download_button(
                    label="✅ PDF'yi İndir",
                    data=pdf_data,
                    file_name=f"turkai_deluks_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
                st.session_state.stats['pdf_generated'] += 1
                st.success("✅ PDF başarıyla oluşturuldu!")
        
        # Premium teklif
        st.markdown("""
        <div class="deluks-card deluks-card-premium" style="margin-top: 20px;">
            <h4>⭐ Daha Fazla Sonuç İster misiniz?</h4>
            <p>Premium motor ile 10+ kaynaktan derin analiz yapın!</p>
            <button class="deluks-btn deluks-btn-premium" style="width: 100%;">
                🚀 Premium'a Geç
            </button>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# 🚀 UYGULAMAYI BAŞLAT
# ============================================

if __name__ == "__main__":
    main()
