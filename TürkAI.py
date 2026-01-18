import os
import requests
from bs4 import BeautifulSoup
import random
import re

# --- GÜVENLİK PROTOKOLÜ (KARA LİSTE) ---
# Botun asla kabul etmeyeceği ve cevap vermeyeceği kelime kökleri
KARA_LISTE = [
    "amk", "aq", "piç", "oç", "sg", "sik", "yarrak", "göt", "meme", "daşşak",
    "ibne", "kahpe", "yavşak", "gerizekalı", "salak", "aptal", "it", "köpek",
    "şerefsiz", "namussuz", "pezevenk", "fahişe", "mal", "oros", "ananı"
]

def temiz_mi(metin):
    """Metin içinde kara listeden bir kelime olup olmadığını kontrol eder."""
    metin_kucuk = metin.lower()
    for kelime in KARA_LISTE:
        if kelime in metin_kucuk:
            return False
    return True

class TurkAITalimatli:
    def __init__(self):
        self.hafiza = []
        # Hitaplar tamamen saygılı hale getirildi
        self.hitaplar = ["Sayın Kullanıcı", "Değerli Dostum", "Kıymetli Arkadaşım", "Beyefendi / Hanımefendi"]
        self.banner()
        self.isim = "Misafir"

    def banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("="*70)
        print("            🇹🇷  TÜRKAI v45.0 - TAM KORUMALI SİSTEM  🇹🇷")
        print("="*70)
        print("📝 TALİMATLAR:")
        print("1. Konu yazıp ENTER'a basarak araştırmayı başlatabilirsiniz.")
        print("2. Analiz sonuçları gelince soru sormak için sonuna '?' ekleyiniz.")
        print("3. Matematik için: 'hesapla [işlem]' yazınız.")
        print("="*70)

    def arastir(self, konu):
        if not temiz_mi(konu):
            print("\n⚠️ TürkAI: Uygunsuz içerik tespit edildi. Lütfen üslubunuzu bozmadan devam ediniz.")
            return

        hitap = random.choice(self.hitaplar)
        print(f"\n🔎 {hitap}, '{konu}' üzerinde derinlemesine analiz başlatılıyor...")
        
        url = f"https://tr.wikipedia.org/wiki/{konu.replace(' ', '_')}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                self.hafiza = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 60]
                if self.hafiza:
                    print(f"✅ {hitap}, analiz verileri sisteme yüklendi. Sorunuzu sorabilirsiniz.")
                else:
                    print("⚠️ Bu başlık altında yeterli veri bulunamadı.")
            else:
                print("⚠️ Aranan konu bulunamadı veya erişim kısıtlandı.")
        except:
            print("❌ Bağlantı hatası: Sunucuya ulaşılamıyor.")

    def cevapla(self, soru):
        if not temiz_mi(soru):
            return "\n⚠️ TürkAI: Sorunuzda uygunsuz ifadeler bulunmaktadır. Lütfen düzeltiniz."
        
        if not self.hafiza:
            return "❌ Önce araştırılacak bir konu girmelisiniz."
        
        # Soru ile hafızadaki metinleri eşleştirme
        anahtar = soru.replace("?", "").split()[-1].lower()
        bulunanlar = [s for s in self.hafiza if anahtar in s.lower()]
        
        if bulunanlar:
            return f"\n💡 Bulunan Bilgi:\n{bulunanlar[0][:700]}..."
        return "😔 Maalesef kaynaklarda bu sorunun tam cevabını bulamadım."

# --- ANA SİSTEM DÖNGÜSÜ ---
try:
    bot = TurkAITalimatli()
    giriş_ismi = input("🤖 TürkAI: Selamün Aleyküm! Size nasıl hitap etmemi istersiniz?: ")
    
    if temiz_mi(giriş_ismi):
        bot.isim = giriş_ismi
    else:
        print("⚠️ Uygunsuz isim tespit edildi, 'Misafir' olarak devam ediliyor.")
        bot.isim = "Misafir"

    while True:
        try:
            msg = input(f"\n👤 {bot.isim}: ").strip()
            if msg.lower() in ["çıkış", "exit", "kapat"]:
                print(f"🤖 Hoşça kalın {bot.isim}, sistem kapatılıyor.")
                break
            if not msg: continue

            if "hesapla" in msg.lower():
                # Hesaplama mantığı buraya eklenebilir
                print("🔢 Hesaplama modülü aktif.") 
            elif msg.endswith("?"):
                print(bot.cevapla(msg))
            else:
                bot.arastir(msg)
        except Exception as e:
            print(f"🚨 Hata: {e}")
except KeyboardInterrupt:
    print("\n🛑 Sistem durduruldu.")



