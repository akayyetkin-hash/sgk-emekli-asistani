-- 1. Kullanıcı Hesaplama Geçmişi Tablosu
CREATE TABLE IF NOT EXISTS public.calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tc_no VARCHAR(11),
    ad_soyad VARCHAR(255),
    toplam_gun INT NOT NULL,
    1999_oncesi_gun INT DEFAULT 0,
    1999_2008_gun INT DEFAULT 0,
    2008_sonrasi_gun INT DEFAULT 0,
    tahmini_maas DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Yıllık Güncelleme Katsayıları Tablosu (Milli Gelir + TÜFE)
CREATE TABLE IF NOT EXISTS public.economic_coefficients (
    yil INT PRIMARY KEY,
    tufe_orani DECIMAL(5, 4) NOT NULL, -- Örn: 0.6477 (%64.77)
    gh_orani DECIMAL(5, 4) NOT NULL,   -- Gelişme Hızı (Milli Gelir) Örn: 0.045 (%4.5)
    guncelleme_katsayisi DECIMAL(6, 4) NOT NULL
);