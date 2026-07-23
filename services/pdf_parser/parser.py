import pdfplumber
import re
from typing import Dict, Any, List
from datetime import datetime

def parse_sgk_pdf(file_bytes: bytes) -> Dict[str, Any]:
    """
    SGK Tescil ve Hizmet Dökümü PDF dosyasından 
    tarih aralıklarına göre prim günlerini ve kazançları ayrıştırır.
    """
    donem_1999_oncesi = {"gun": 0, "kazanc": 0.0}
    donem_1999_2008 = {"gun": 0, "kazanc": 0.0}
    donem_2008_sonrasi = {"gun": 0, "kazanc": 0.0}
    
    sigorta_baslangic = None
    tc_no = None
    ad_soyad = None

    import io
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # 1. Temel Bilgi Ayıklama (TC, Ad Soyad, İlk İşe Giriş Tarihi)
    tc_match = re.search(r"T\.C\.\s*Kimlik\s*No\s*:\s*(\d{11})", full_text, re.IGNORECASE)
    if tc_match:
        tc_no = tc_match.group(1)

    baslangic_match = re.search(r"İlk\s*İşe\s*Giriş\s*Tarihi\s*:\s*(\d{2}\.\d{2}\.\d{4})", full_text, re.IGNORECASE)
    if baslangic_match:
        sigorta_baslangic = baslangic_match.group(1)

    # 2. Satır Satır Hizmet Dökümü Ayrıştırma
    # Örnek SGK Satır Formatı: Yıl/Ay (Örn: 2015/05 veya 2002/12) - Gün - Kazanç
    lines = full_text.split("\n")
    
    # Regex pattern: Yıl/Ay, Gün ve Kazanç değerlerini bulur
    # Örn: "2018/03 4A ... 30 4.500,00"
    pattern = re.compile(r"(\d{4})/(\d{2})\s+.*?\s+(\d{1,2})\s+([\d\.]+,\d{2})")

    for line in lines:
        match = pattern.search(line)
        if match:
            yil = int(match.group(1))
            ay = int(match.group(2))
            gun = int(match.group(3))
            kazanc_str = match.group(4).replace(".", "").replace(",", ".")
            kazanc = float(kazanc_str)

            # Dönemsel Ayırma Mantığı
            if yil < 1999 or (yil == 1999 and ay < 9):
                donem_1999_oncesi["gun"] += gun
                donem_1999_oncesi["kazanc"] += kazanc
            elif yil < 2008 or (yil == 2008 and ay < 10):
                donem_1999_2008["gun"] += gun
                donem_1999_2008["kazanc"] += kazanc
            else:
                donem_2008_sonrasi["gun"] += gun
                donem_2008_sonrasi["kazanc"] += kazanc

    # Eğer regex ile bulunamadıysa varsayılan/fallback kontroller
    if not sigorta_baslangic:
        sigorta_baslangic = "2000-01-01"  # Varsayılan değer
    else:
        # DD.MM.YYYY -> YYYY-MM-DD çevrimi
        try:
            dt = datetime.strptime(sigorta_baslangic, "%d.%m.%Y")
            sigorta_baslangic = dt.strftime("%Y-%m-%d")
        except:
            sigorta_baslangic = "2000-01-01"

    return {
        "tc_no": tc_no,
        "ad_soyad": ad_soyad,
        "sigorta_baslangic_tarihi": sigorta_baslangic,
        "donem_1999_oncesi": donem_1999_oncesi,
        "donem_1999_2008": donem_1999_2008,
        "donem_2008_sonrasi": donem_2008_sonrasi
    }