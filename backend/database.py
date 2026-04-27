import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def supabase_request(endpoint, method="GET", data=None):
    """Универсальная функция для запросов к Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Метод {method} не поддерживается")
    
    return response

def test_connection():
    try:
        # Пробуем прочитать таблицу users
        response = supabase_request("users?limit=1")
        if response.status_code == 200:
            print("✅ Подключение к Supabase успешно!")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def get_supabase_client():
    """Возвращает клиент Supabase (для совместимости)"""
    return None  # Пока не используется

if __name__ == "__main__":
    test_connection()