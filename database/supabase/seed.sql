-- Geçmiş Yılların Örnek Katsayı Verileri
INSERT INTO public.economic_coefficients (yil, tufe_orani, gh_orani, guncelleme_katsayisi) 
VALUES 
(2021, 0.3608, 0.1100, 1.3938),
(2022, 0.6427, 0.0560, 1.6595),
(2023, 0.6477, 0.0450, 1.6612),
(2024, 0.4481, 0.0320, 1.4577),
(2025, 0.3000, 0.0300, 1.3090)
ON CONFLICT (yil) DO NOTHING;