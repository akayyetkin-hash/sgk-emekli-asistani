import pdfplumber
import re
from collections import defaultdict

class SGKPDFParser:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def parse_hizmet_dokumu(self) -> dict:
        summary = {
            "gun_1999_oncesi": 0,
            "kazanc_1999_oncesi": 0.0,
            "gun_1999_2008": 0,
            "kazanc_1999_2008": 0.0,
            "gun_2008_sonrasi": 0,
            "kazanc_2008_sonrasi": 0.0,
            "toplam_gun": 0,
            "toplam_duzeltilmis_kazanc": 0.0,
            "mevzuat_donem_matrisi": {
                "1999_ONCESI": defaultdict(lambda: defaultdict(lambda: {"gun": 0, "kazanc": 0.0})),
                "1999_2008_ARASI": defaultdict(lambda: defaultdict(lambda: {"gun": 0, "kazanc": 0.0})),
                "2008_SONRASI": defaultdict(lambda: defaultdict(lambda: {"gun": 0, "kazanc": 0.0}))
            },
            "statu_listesi": set()
        }

        try:
            full_text = ""
            with pdfplumber.open(self.pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

            # SGK Hizmet Satırı Deseni: YIL/AY ... GÜN ... KAZANÇ
            pattern = re.compile(
                r'(\b19\d{2}|\b20\d{2})\/(\d{1,2})\b'  # Yıl (19xx/20xx) ve Ay (1-12)
                r'.*?'                                  # Aradaki metinler (Belge türü vb.)
                r'\b(30|31|[1-2]?\d)\b'                 # Prim Gün Sayısı (1-31)
                r'\s+([\d\.]+,\d{2})\b'                 # Prime Esas Kazanç (Örn: 1.702.231,50)
            )

            # Statü Tespiti
            summary["statu_listesi"].add("4A")
            if "4/b" in full_text.lower() or "bağ-kur" in full_text.lower():
                summary["statu_listesi"].add("4B")
            if "4/c" in full_text.lower() or "emekli sandığı" in full_text.lower():
                summary["statu_listesi"].add("4C")

            matches = pattern.findall(full_text)

            for match in matches:
                yil = int(match[0])
                ay = int(match[1])
                gun = int(match[2])
                raw_kazanc = match[3].replace('.', '').replace(',', '.')

                if not (1 <= ay <= 12) or gun == 0:
                    continue

                try:
                    kazanc = float(raw_kazanc)
                except ValueError:
                    kazanc = 0.0

                # 2005 öncesi Eski TL -> YTL/TRY Dönüşümü (6 Sıfır Atma)
                if yil < 2005:
                    kazanc = kazanc / 1000000.0

                statu = "4A"

                # Mevzuat Dönem Ayrımı (1999/08 öncesi, 1999/09-2008/09, 2008/10 sonrası)
                if yil < 1999 or (yil == 1999 and ay <= 8):
                    donem_key = "1999_ONCESI"
                    summary["gun_1999_oncesi"] += gun
                    summary["kazanc_1999_oncesi"] += kazanc
                elif 1999 <= yil < 2008 or (yil == 2008 and ay <= 9):
                    donem_key = "1999_2008_ARASI"
                    summary["gun_1999_2008"] += gun
                    summary["kazanc_1999_2008"] += kazanc
                else:
                    donem_key = "2008_SONRASI"
                    summary["gun_2008_sonrasi"] += gun
                    summary["kazanc_2008_sonrasi"] += kazanc

                summary["mevzuat_donem_matrisi"][donem_key][yil][statu]["gun"] += gun
                summary["mevzuat_donem_matrisi"][donem_key][yil][statu]["kazanc"] += kazanc

            # JSON Formatlama
            formatted_mevzuat = {}
            for donem_key, donem_data in summary["mevzuat_donem_matrisi"].items():
                formatted_mevzuat[donem_key] = {}
                sorted_years = sorted(donem_data.keys())
                for y in sorted_years:
                    formatted_mevzuat[donem_key][y] = {}
                    for st in donem_data[y]:
                        formatted_mevzuat[donem_key][y][st] = {
                            "gun": donem_data[y][st]["gun"],
                            "kazanc": round(donem_data[y][st]["kazanc"], 2)
                        }

            summary["mevzuat_donem_matrisi"] = formatted_mevzuat
            summary["statu_listesi"] = sorted(list(summary["statu_listesi"]))
            summary["toplam_gun"] = summary["gun_1999_oncesi"] + summary["gun_1999_2008"] + summary["gun_2008_sonrasi"]
            summary["toplam_duzeltilmis_kazanc"] = round(
                summary["kazanc_1999_oncesi"] + summary["kazanc_1999_2008"] + summary["kazanc_2008_sonrasi"], 2
            )

        except Exception as e:
            print(f"Yerel PDF Parse Hatasi: {str(e)}")

        return summary
