class SGKPensionCalculator:
    def __init__(self):
        pass

    def calculate_summary(self, data: dict) -> dict:
        """
        Gelen dönem bazlı prim günleri ve kazanç verilerine göre 
        tahmini kök aylık ve ABO hesaplar.
        """
        gun_1999 = data.get("gun_1999_oncesi", 0)
        gun_2008 = data.get("gun_1999_2008", 0)
        gun_sonra = data.get("gun_2008_sonrasi", 0)
        
        toplam_gun = gun_1999 + gun_2008 + gun_sonra

        kazanc_1999 = data.get("kazanc_1999_oncesi", 0.0)
        kazanc_2008 = data.get("kazanc_1999_2008", 0.0)
        kazanc_sonra = data.get("kazanc_2008_sonrasi", 0.0)
        toplam_kazanc = kazanc_1999 + kazanc_2008 + kazanc_sonra

        # Temel ABO (Aylık Bağlama Oranı) Yaklaşık Hesabı
        abo_1999 = 60.0 if gun_1999 > 0 else 0.0
        abo_2008 = 50.0 if gun_2008 > 0 else 0.0
        abo_sonra = 40.0 if gun_sonra > 0 else 0.0

        if toplam_gun > 0:
            ortalama_abo = round((abo_1999 * gun_1999 + abo_2008 * gun_2008 + abo_sonra * gun_sonra) / toplam_gun, 2)
        else:
            ortalama_abo = 50.0

        # Tahmini Kök Aylık Hesabı (Örnek Basit Formül)
        if toplam_gun > 0:
            gunluk_ort_kazanc = toplam_kazanc / toplam_gun
            tahmini_kok_aylik = round((gunluk_ort_kazanc * 30) * (ortalama_abo / 100), 2)
        else:
            tahmini_kok_aylik = 0.0

        return {
            "toplam_gun": toplam_gun,
            "toplam_kazanc": round(toplam_kazanc, 2),
            "ortalama_abo": ortalama_abo,
            "tahmini_kok_aylik": tahmini_kok_aylik,
            "donem_detaylari": {
                "1999_oncesi": {"gun": gun_1999, "kazanc": kazanc_1999},
                "1999_2008": {"gun": gun_2008, "kazanc": kazanc_2008},
                "2008_sonrasi": {"gun": gun_sonra, "kazanc": kazanc_sonra}
            }
        }
