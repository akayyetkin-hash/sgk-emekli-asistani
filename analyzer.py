import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

SYSTEM_PROMPT = """
Sen 30 yıllık tecrübeye sahip kıdemli bir SGK Başmüfettişi ve Emeklilik Mevzuatı Uzmanısın.
Sana bir vatandaşın e-Devlet SGK Hizmet Dökümü PDF'inden çıkarılan TÜM HAM METİN VE TABLOLAR sunulmaktadır.

Görevin bu hizmet dökümünü Türk SGK Emeklilik Mevzuatına (506, 1479, 5434 ve 5510 sayılı Kanunlar) göre eksiksiz ve detaylıca incelemektir.

Aşağıdaki başlıklar altında KISA, NET, ANLAŞILIR ve Doğrudan Aksiyon Alınabilir bir SGK Denetim ve Kök Maaş Analiz Raporu oluştur:

### 1. 📊 Genel Hizmet Özeti ve Statü Analizi
- Toplam prim gün sayısı, ilk sigorta başlangıç tarihi ve 4A/4B/4C hizmet dağılımı.
- Son 2520 gün (son 7 yıl) kuralına göre emekli olunması gereken / olunan asıl statü teyidi.

### 2. ⚠️ Kök Maaş ve Bağlanma Aylığını Düşüren / Etkileyen Kritik Noktalar
- 1999 Öncesi, 1999-2008 ve 2008 Sonrası SPEK (Sigorta Primine Esas Kazanç) matrahlarının genel seyri.
- Özellikle 2008 sonrası prim gün sayısı artarken bildirilen kazançlarda kök maaşı olumsuz etkileyen düşüşler veya tavan/taban sapmaları.

### 3. 🔍 Mevzuat İhlalleri, Çakışan Süreler ve Şüpheli Kodlar
- Aynı dönemde hem 4A hem 4B/4C çakışması var mı? Hangi statü geçerli sayılmalı?
- İşyeri sicil numaralarında veya hizmet dökümünde yer alan K (Kontrollü), Ş (Şüpheli), İ (İptal) kodlu işyerleri ve silinme riski taşıyan günler.
- Eksik gün kodları ve varsa çakışan prim aktarım hataları.

### 4. 💡 SGK İtiraz ve Kök Maaş Düzeltme Önerileri
- Emekli maaşının veya kök aylığın eksik/hatalı hesaplanma riski olan noktaları.
- Vatandaşın SGK'ya dilekçe vererek düzelttirmesi gereken somut dönemler ve konular.

Yanıtını Markdown formatında başlıklar (###), kalın yazılar (**bold**) ve maddeler kullanarak ver.
"""

def analyze_sgk_pdf_content(pdf_raw_text: str) -> str:
    """
    PDF'ten çıkarılan BÜTÜN ham metni (hiçbir veri kesintisi olmadan) Google Gemini API'ye gönderir.
    Gelişmiş hata yönetimi ve Türkçe bilgilendirme içerir.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "⚠️ **SİSTEM HATASI:** `GEMINI_API_KEY` yapılandırması bulunamadı. Lütfen `.env` dosyanızı kontrol edin."

    try:
        client = genai.Client(api_key=api_key)
        
        # Veri bütünlüğü için metin aynen korunur
        prompt = f"{SYSTEM_PROMPT}\n\n--- SGK HİZMET DÖKÜMÜ TÜM HAM METNİ ---\n{pdf_raw_text}"
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text

    except APIError as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return (
                "⌛ **ÜCRETSİZ KOTA SINIRI / YOĞUNLUK UYARISI**\n\n"
                "Sistem şu anda ücretsiz test kotası sınırına ulaştı. "
                "**Lütfen 15-20 saniye bekleyip 'Yeni Analiz' butonuna tekrar basınız.**\n\n"
                f"---\n**Sistem Açıklaması:**\n`{error_msg}`"
            )
        return (
            "⚠️ **YAPAY ZEKA SERVİS HATASI**\n\n"
            "Analiz sırasında bir API hatası oluştu. Lütfen tekrar deneyiniz.\n\n"
            f"---\n**Hata Detayı:**\n`{error_msg}`"
        )
    except Exception as e:
        return f"⚠️ **BEKLENMEYEN HATA:** {str(e)}"