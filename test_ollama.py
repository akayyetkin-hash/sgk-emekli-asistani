import ollama

print("Ollama ile baglanti kuruluyor...")

try:
    response = ollama.chat(
        model='qwen2.5:3b',
        messages=[
            {
                'role': 'user',
                'content': 'Merhaba! SGK ve emeklilik analizleri icin hazir misin?',
            },
        ],
    )
    print("\n--- Yanit ---")
    print(response['message']['content'])
except Exception as e:
    print("\nHata olustu:", e)