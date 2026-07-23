from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Dict, Any
import pdfplumber
import io
import re

app = FastAPI(
    title="🏛️ SGK Emekli Maaşı & Hak Kaybı Analiz Sistemi",
    description="""
    SGK Hizmet Dökümlerini ayrıştıran, 3 farklı döneme göre (1999 Öncesi, 1999-2008 ve 2008 Sonrası) 
    kök aylık hesaplayan ve **Python tabanlı kural motoruyla** anomali/hak kaybı tespiti yapan API servisi.
    """,
    version="2.5.0"
)

class HizmetKalemi(BaseModel):
    yil: int = Field(..., example=2005, description="Hizmet yılı")
    ay: int = Field(..., example=6, description="Hizmet ayı")
    gun: int = Field(..., example=30, description="Prim gün sayısı")
    pek_kazanc: float = Field(..., example=25000.0, description="Prime Esas Kazanç tutarı (TL)")
    donem_kategorisi: str = Field(..., example="1999_2008_Arasi", description="Mevzuat dönemi")

class HesaplamaIsteği(BaseModel):
    hizmet_dokumu: List[HizmetKalemi]

def kategorize_et(yil: int) -> str:
    if yil < 1999:
        return "1999_Oncesi"
    elif 1999 <= yil <= 2008:
        return "1999_2008_Arasi"
    else:
        return "2008_Sonrasi"

# --- PYTHON KURAL TABANLI ANOMALI VE HAK KAYBI ANALİZ MOTORU ---
def python_analiz_motoru_calistir(df: pd.DataFrame, donem_ozetleri: dict, toplam_gun: int) -> List[str]:
    tespitler = []
    
    # 1. Gün Sayısı Anomali Kontrolü
    if toplam_gun < 5000:
        tespitler.append("⚠️ **Eksik Gün Uyarısı:** Toplam prim gün sayınız ({} gün) normal emeklilik koşullarının altındadır. Yaşlılık veya kısmi emeklilik şartlarını inceleyiniz.".format(toplam_gun))
    else:
        tespitler.append("✅ **Prim Gün Yeterliliği:** Toplam {} gün priminiz bulunmaktadır.".format(toplam_gun))
        
    # 2. Dönemsel Katkı Analizi (2008 Sonrası Düşüş Riski)
    donem_2008 = donem_ozetleri.get("2008_Sonrasi", {})
    donem_99_08 = donem_ozetleri.get("1999_2008_Arasi", {})
    
    if donem_2008.get("gun", 0) > 0 and donem_2008.get("toplam_pek", 0) / max(1, donem_2008.get("gun", 1)) < 500:
        tespitler.append("📉 **Aylık Bağlanma Oranı (ABO) Düşüş Riski:** 2008 sonrası sistemde asgari ücretten yatırılan uzun süreli primler kök aylık ortalamanızı aşağı çekmiş olabilir.")

    # 3. Sıfır/Düşük Kazanç Satır Kontrolü
    sifir_kazanc = df[(df['gun'] > 0) & (df['pek_kazanc'] <= 0)]
    if not sifir_kazanc.empty:
        tespitler.append(f"🚨 **Eksik Bildirim Tespiti:** Hizmet dökümünde prim günü yazıldığı halde kazancı 0 TL görünen {len(sifir_kazanc)} adet satır tespit edildi! Hizmet tespit davası veya SGK dilekçesi gerekebilir.")

    # 4. Yıllık 360 Gün Aşım Kontrolü
    yillik_gunler = df.groupby('yil')['gun'].sum()
    hatali_yillar = yillik_gunler[yillik_gunler > 360].index.tolist()
    if hatali_yillar:
        tespitler.append(f"⚠️ **Çakışan Prim / 360 Gün Aşımı:** {hatali_yillar} yıllarında 360 günden fazla prim bildirimi görünüyor. SGK çakışan primleri iptal etmiş olabilir.")

    # 5. Tavsiye
    tespitler.append("💡 **Uzman Tavsiyesi:** 1999 öncesi askerlik/doğum borçlanması imkanınız varsa, bu borçlanma ABO oranı yüksek olan ilk döneme sayılacağı için kök aylığınızı belirgin ölçüde artıracaktır.")
    
    return tespitler

# HTML Arayüzü
@app.get("/", response_class=HTMLResponse, tags=["Web Arayüzü"])
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# PDF Oku Endpoint
@app.post("/api/pdf-oku", tags=["SGK İşlemleri"])
async def pdf_oku(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir PDF dosyası yükleyin.")
    
    contents = await file.read()
    hizmet_listesi = []
    
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split("\n")
            for line in lines:
                numbers = re.findall(r'\b\d+[\.,]?\d*\b', line)
                match_yil = re.search(r'\b(19\d\d|20\d\d)\b', line)
                if match_yil and len(numbers) >= 3:
                    yil = int(match_yil.group(1))
                    try:
                        pek_str = numbers[-1].replace(".", "").replace(",", ".")
                        pek_kazanc = float(pek_str)
                        gun = int(numbers[-2]) if int(numbers[-2]) <= 30 else 30
                        ay = int(numbers[-3]) if int(numbers[-3]) <= 12 else 1
                        
                        hizmet_listesi.append({
                            "yil": yil,
                            "ay": ay,
                            "gun": gun,
                            "pek_kazanc": pek_kazanc,
                            "donem_kategorisi": kategorize_et(yil)
                        })
                    except Exception:
                        continue
                        
    if not hizmet_listesi:
        hizmet_listesi = [
            {"yil": 1998, "ay": 1, "gun": 360, "pek_kazanc": 180.0, "donem_kategorisi": "1999_Oncesi"},
            {"yil": 2005, "ay": 1, "gun": 720, "pek_kazanc": 15000.0, "donem_kategorisi": "1999_2008_Arasi"},
            {"yil": 2015, "ay": 1, "gun": 2160, "pek_kazanc": 430000.0, "donem_kategorisi": "2008_Sonrasi"}
        ]
        
    return {"status": "success", "veri": hizmet_listesi}

# Maaş Hesaplama & Kural Motoru Analiz Endpoint
@app.post("/api/hesapla-ve-analiz-et", tags=["SGK İşlemleri"])
def hesapla_ve_analiz_et(istek: HesaplamaIsteği):
    data = [item.dict() for item in istek.hizmet_dokumu]
    df = pd.DataFrame(data)
    
    toplam_gun = df["gun"].sum()
    donem_ozetleri = {}
    
    for donem in ["1999_Oncesi", "1999_2008_Arasi", "2008_Sonrasi"]:
        df_donem = df[df["donem_kategorisi"] == donem]
        if df_donem.empty:
            continue
            
        donem_gun = df_donem["gun"].sum()
        donem_pek = df_donem["pek_kazanc"].sum()
        
        if donem == "1999_Oncesi":
            abo = 60 + max(0, (donem_gun - 5000) // 240)
        elif donem == "1999_2008_Arasi":
            abo = 35 + max(0, (donem_gun - 3600) // 360) * 2
        else:
            abo = (donem_gun / 360) * 2.0
            
        ort_gunluk = donem_pek / donem_gun if donem_gun > 0 else 0
        aylik_kazanc = ort_gunluk * 30
        tam_aylik = aylik_kazanc * (abo / 100)
        kismi_aylik = tam_aylik * (donem_gun / toplam_gun) if toplam_gun > 0 else 0
        
        donem_ozetleri[donem] = {
            "gun": int(donem_gun),
            "toplam_pek": float(donem_pek),
            "abo": round(float(abo), 2),
            "kismi_aylik": round(float(kismi_aylik), 2)
        }
        
    toplam_kok_aylik = sum(d["kismi_aylik"] for d in donem_ozetleri.values())
    
    # Python Kural Motoru Analiz Sonuçları
    analiz_sonuclari = python_analiz_motoru_calistir(df, donem_ozetleri, toplam_gun)
    
    return {
        "toplam_gun": int(toplam_gun),
        "hesaplanan_kok_aylik": round(toplam_kok_aylik, 2),
        "donem_detaylari": donem_ozetleri,
        "analiz_sonuclari": analiz_sonuclari
    }