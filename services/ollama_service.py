import ollama

SYSTEM_PROMPT = """
Sen SGK (Sosyal Güvenlik Kurumu) ve emeklilik mevzuatı konusunda uzmanlaşmış yapay zeka asistanısın.
Görevin:
1. Kullanıcıdan gelen emeklilik, prim günü, sigortalılık süresi ve yaş hesaplaması verilerini analiz etmek.
2. SGK mevzuatına uygun, net, resmi ve anlaşılır teknik analizler sunmak.
3. Yanıtları maddeler halinde ve okuması kolay bir formatta vermek.
"""


def sgk_analiz_yap(user_prompt: str) -> str:
    """Ollama qwen2.5:3b modelini kullanarak SGK analizi üretir."""
    try:
        response = ollama.chat(
            model='qwen2.5:3b',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        return response['message']['content']
    except Exception as e:
        return f'SGK Analiz Servisi Hatası: {str(e)}'