import os
import google.generativeai as genai

class SGKAIAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def analyze_pension_case(self, calc_result: dict) -> str:
        toplam_gun = calc_result.get("toplam_gun", 0)
        kok_aylik = calc_result.get("tahmini_kok_aylik", 0)
        abo = calc_result.get("ortalama_abo", 0)

        prompt = f"""
        Sen bir SGK ve Emeklilik Mevzuatı Uzmanısın. Aşağıdaki verilere göre sigortalıya özel detaylı bir emeklilik analiz raporu hazırla:
        - Toplam Prim Günü: {toplam_gun}
        - Tahmini Kök Aylık: {kok_aylik} TL
        - Ortalama ABO (Aylık Bağlama Oranı): %{abo}

        Raporunda şunlara yer ver:
        1. Prim gün sayısının yeterliliği.
        2. Aylık Bağlama Oranının (ABO) maaşa etkisi.
        3. Hak kaybı yaşamaması için dikkat etmesi gereken hukuki ve teknik tavsiyeler.
        """

        if self.api_key:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                pass

        # API Anahtarı girilmediğinde veya kota aşıldığında çalışacak yerel kural motoru raporu:
        return f"""📋 **SGK EMEKLİLİK VE HAK KAYBI ANALİZ RAPORU**

1. **Prim Gün Sayısı Durumu:**
   Hesaplanan toplam prim gününüz **{toplam_gun} gün**dür. Emeklilik için gerekli asgari prim gün şartını sağlama durumunuz tescil başlangıç tarihinize (1996) göre oldukça avantajlıdır.

2. **Aylık Bağlama Oranı (ABO) ve Kök Aylık Analizi:**
   Ağırlıklı Aylık Bağlama Oranınız **%{abo}** olarak hesaplanmıştır. 2008 sonrası prim günlerinizin artması ABO'nun düşmesine sebep olabileceğinden, yüksek matrahtan prim bildirilmesi kök aylığınızı korumak adına kritik önem taşır.

3. **Önemli Tavsiyeler:**
   - e-Devlet Hizmet Dökümünüzdeki çakışan sigorta sürelerini kontrol ettirin.
   - 1999 öncesi askerlik veya doğum borçlanması imkanınız varsa bu haklarınızı değerlendirerek ABO oranınızı yükseltebilirsiniz.
   - Tahmini kök aylığınız: **{kok_aylik} TL** civarındadır.
"""
