import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env dosyasındaki değişkenleri yüklüyoruz
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL veya SUPABASE_KEY .env dosyasından okunamadı!")

# Supabase veritabanı istemcisini başlatıyoruz
supabase: Client = create_client(url, key)