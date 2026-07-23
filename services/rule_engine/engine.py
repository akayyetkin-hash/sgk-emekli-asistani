import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_economic_coefficients() -> dict:
    """Supabase'den tüm ekonomik katsayıları çeker."""
    try:
        response = supabase.table("economic_coefficients").select("*").execute()
        coefficients = {}
        for row in response.data:
            coefficients[row["yil"]] = {
                "tufe": float(row["tufe_orani"]),
                "gh": float(row["gh_orani"]),
                "guncelleme_katsayisi": float(row["guncelleme_katsayisi"])
            }
        return coefficients
    except Exception as e:
        print(f"Katsayı çekme hatası: {e}")
        return {}


def calculate_pension(parsed_data: Dict[str, Any], extra_questions_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    PDF Parser verileri, Supabase katsayıları ve Kullanıcı Özel Durum Yanıtları (Askerlik, Bağ-Kur vb.)
    ile nihai emekli maaşı ve SGK analizini gerçekleştirir.
    """
    coefficients = fetch_economic_coefficients()
    if not extra_questions_data:
        extra_questions_data = {}

    donem_1999_oncesi = parsed_data.get("donem_1999_oncesi", {"gun": 0, "kazanc": 0.0})
    donem_1999_2008 = parsed_data.get("donem_1999_2008", {"gun": 0, "kazanc": 0.0})
    donem_2008_sonrasi = parsed_data.get("donem_2008_sonrasi", {"gun": 0, "kazanc": 0.0})

    # 1. Ek Durumlar İşleniyor (Askerlik / Doğum Borçlanması & 4B Aktarımı)
    ek_gun_1999_oncesi = 0
    ek_kazanc_1999_oncesi = 0.0
    uyarilar_ve_notlar = []

    # Askerlik Borçlanması Kontrolü
    askerlik = extra_questions_data.get("askerlik_borclanmasi", {})
    if askerlik.get("yapildi_mi") and askerlik.get("odendi_mi"):
        borclanan_gun = askerlik.get("gun_sayisi", 0)
        # Askerlik sigorta başlangıcından önce yapıldıysa sigorta başlangıcını geriye çeker
        if askerlik.get("sigortadan_once_mi", False):
            ek_gun_1999_oncesi += borclanan_gun
            uyarilar_ve_notlar.append(f"Askerlik borçlanması ({borclanan_gun} gün) sigorta başlangıcınızı geriye çekti ve 1999 öncesi prime eklendi.")
        else:
            # Sigortadan sonra yapıldıysa sadece prim gününe eklenir
            donem_1999_2008["gun"] += borclanan_gun
            uyarilar_ve_notlar.append(f"Askerlik borçlanması ({borclanan_gun} gün) prim gün sayınıza eklendi.")

    # 4B (Bağ-Kur) Borç Ödeme ve 4A'ya Aktarım Kontrolü
    bagkur = extra_questions_data.get("bagkur_durumu", {})
    if bagkur.get("var_mi"):
        if bagkur.get("borc_odendi_mi") and bagkur.get("aktarim_yapildi_mi"):
            bagkur_gun = bagkur.get("aktarilan_gun_sayisi", 0)
            donem_1999_2008["gun"] += bagkur_gun
            uyarilar_ve_notlar.append(f"Ödenen ve 4A'ya aktarılan {bagkur_gun} günlük 4B (Bağ-Kur) hizmeti birleştirildi.")
        elif not bagkur.get("borc_odendi_mi"):
            uyarilar_ve_notlar.append("Uyarı: Ödenmemiş 4B (Bağ-Kur) prim borcunuz bulunmaktadır. Borç ihya edilip ödenmeden emeklilik aylığı bağlanamaz.")

    # Toplam Gün Hesaplama
    toplam_gun = (donem_1999_oncesi["gun"] + ek_gun_1999_oncesi +
                  donem_1999_2008["gun"] +
                  donem_2008_sonrasi["gun"])

    if toplam_gun == 0:
        return {
            "status": "error",
            "message": "Hesaplama yapmak için yeterli prim günü bulunamadı."
        }

    # 2. Katsayılı Güncelleme Hesaplama Mantığı
    guncel_kazanc_toplami = 0.0
    for yil, katsayi_bilgisi in coefficients.items():
        gk = katsayi_bilgisi["guncelleme_katsayisi"]
        guncel_kazanc_toplami += (donem_2008_sonrasi["kazanc"] / max(1, donem_2008_sonrasi["gun"])) * gk

    # Aylık Bağlama Oranı (ABO)
    abo = min(0.70, 0.35 + (toplam_gun / 360) * 0.02)
    tahmini_maas = round((guncel_kazanc_toplami / 30) * abo, 2)

    return {
        "status": "success",
        "toplam_gun": toplam_gun,
        "gun_breakdown": {
            "1999_oncesi": donem_1999_oncesi["gun"] + ek_gun_1999_oncesi,
            "1999_2008": donem_1999_2008["gun"],
            "2008_sonrasi": donem_2008_sonrasi["gun"]
        },
        "tahmini_maas": tahmini_maas,
        "uyarilar_ve_notlar": uyarilar_ve_notlar
    }