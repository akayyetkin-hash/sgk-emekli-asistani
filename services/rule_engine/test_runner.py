import sys
import os
import json
import pandas as pd

# 1. Katsayılar ve Mevzuat Verilerinin Yüklenmesi
def load_katsayilar():
    # katsayilar.json dosyasının yolunu bul
    json_path = os.path.join(os.path.dirname(__file__), 'katsayilar.json')
    
    # Varsayılan test mevzuat verisi (JSON yoksa fallback olarak kullanılır)
    default_data = {
        "1999_ONCESI": {"base_abo": 60, "memur_katsayisi": 0.04183},
        "1999_2008": {"base_abo": 35, "tufe_yansima": 1.0, "gh_yansima": 1.0},
        "2008_SONRASI": {"base_abo": 0, "tufe_yansima": 1.0, "gh_yansima": 0.30},
        "yıllık_katsayılar": {
            "2022": {"tufe": 0.6427, "gh": 0.056},
            "2023": {"tufe": 0.6477, "gh": 0.045}
        }
    }
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_data

# 2. Canlı Hesaplama Test Motoru
def run_live_test(hizmet_dokumu_df):
    print("=" * 60)
    print("🧪 SGK EMEKLİ AYLIĞI HESAPLAMA MOTORU CANLI TESTİ")
    print("=" * 60)
    
    katsayilar = load_katsayilar()
    toplam_gun = hizmet_dokumu_df["gun"].sum()
    
    print(f"📌 Toplam Hizmet Gün Sayısı: {toplam_gun} Gün")
    print("-" * 60)
    
    donem_ozetleri = {}
    
    # 3 Dönemlik Hesaplama Döngüsü
    for donem in ["1999_Oncesi", "1999_2008_Arasi", "2008_Sonrasi"]:
        df_donem = hizmet_dokumu_df[hizmet_dokumu_df["donem_kategorisi"] == donem]
        
        if df_donem.empty:
            continue
            
        donem_gun = df_donem["gun"].sum()
        donem_pek = df_donem["pek_kazanc"].sum()
        
        # Dönemsel ABO Hesaplama
        if donem == "1999_Oncesi":
            abo = 60 + max(0, (donem_gun - 5000) // 240)
        elif donem == "1999_2008_Arasi":
            abo = 35 + max(0, (donem_gun - 3600) // 360) * 2
        else: # 2008_Sonrasi
            abo = (donem_gun / 360) * 2.0
            
        # Güncellenmiş Ortalama Kazanç (Örnekleştirilmiş Simülasyon)
        ort_gunluk = donem_pek / donem_gun if donem_gun > 0 else 0
        aylik_kazanc = ort_gunluk * 30
        
        # Dönem Kısmi Aylık Hesabı: (Göz önüne alınan Aylık * ABO) * (Dönem Gün / Toplam Gün)
        tam_aylik = aylik_kazanc * (abo / 100)
        kismi_aylik = tam_aylik * (donem_gun / toplam_gun)
        
        donem_ozetleri[donem] = {
            "gun": donem_gun,
            "toplam_pek": donem_pek,
            "abo": round(abo, 2),
            "kismi_aylik": round(kismi_aylik, 2)
        }
        
        print(f"🔹 Dönem: {donem}")
        print(f"   • Prim Gün Sayısı : {donem_gun} gün")
        print(f"   • Dönem PEK Tutarı: {donem_pek:,.2f} TL")
        print(f"   • Uygulanan ABO   : %{abo:.2f}")
        print(f"   • Hesaplanan Kısmi Aylık: {kismi_aylik:,.2f} TL\n")

    toplam_tahmini_aylik = sum(d["kismi_aylik"] for d in donem_ozetleri.values())
    
    print("=" * 60)
    print(f"🏆 HESAPLANAN TAHMİNİ KÖK AYLIĞI: {toplam_tahmini_aylik:,.2f} TL")
    print("=" * 60)
    
    return donem_ozetleri

# 3. Örnek PDF Verisi Simülasyonu
if __name__ == "__main__":
    # Test Veri Seti (Örnek e-Devlet Dökümü Verisi)
    test_data = pd.DataFrame([
        {"yil": 1998, "ay": 5, "gun": 360, "pek_kazanc": 180.0, "donem_kategorisi": "1999_Oncesi"},
        {"yil": 2005, "ay": 10, "gun": 720, "pek_kazanc": 15000.0, "donem_kategorisi": "1999_2008_Arasi"},
        {"yil": 2021, "ay": 1, "gun": 1440, "pek_kazanc": 180000.0, "donem_kategorisi": "2008_Sonrasi"},
        {"yil": 2023, "ay": 6, "gun": 720, "pek_kazanc": 250000.0, "donem_kategorisi": "2008_Sonrasi"}
    ])
    
    run_live_test(test_data)