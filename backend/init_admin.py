import hashlib
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def hash_password(password):
    """Хеширование пароля через SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    phone = os.getenv("ADMIN_PHONE")
    password = os.getenv("ADMIN_PASSWORD")
    
    if not phone or not password:
        print("❌ Ошибка: ADMIN_PHONE или ADMIN_PASSWORD не указаны в .env")
        return
    
    hashed = hash_password(password)
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Проверяем, существует ли уже пользователь
    check_url = f"{SUPABASE_URL}/rest/v1/users?phone=eq.{phone}&select=id"
    
    try:
        response = requests.get(check_url, headers=headers)
        
        if response.status_code == 200 and response.json():
            print(f"⚠️ Пользователь с телефоном {phone} уже существует")
            return
        
        # Создаём пользователя
        insert_url = f"{SUPABASE_URL}/rest/v1/users"
        data = {
            "phone": phone,
            "password_hash": hashed,
            "role": "главный_админ",
            "first_login": False,
            "position": "Главный администратор системы"
        }
        
        insert_response = requests.post(insert_url, headers=headers, json=data)
        
        if insert_response.status_code == 201:
            print(f"✅ Главный администратор {phone} успешно создан")
            print(f"📝 Пароль для входа: {password}")
        else:
            print(f"❌ Ошибка: {insert_response.status_code}")
            print(f"Текст ошибки: {insert_response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    print("🔄 Создание главного администратора...")
    create_admin()