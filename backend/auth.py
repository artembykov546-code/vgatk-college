import hashlib
import secrets
import string

def hash_password(password: str) -> str:
    """
    Хешурует пароль с помощью SHA-256.
    Возвращает строку в hex-формате, которую можно сразу сохранять в Supabase.
    """
    if not password:
        return ""
    # Кодируем строку в байты, хешируем, переводим обратно в строку
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли введённый пароль сохранённому хешу.
    Возвращает True, если пароли совпадают, иначе False.
    """
    if not plain_password or not hashed_password:
        return False
    return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password

def generate_temp_password(length: int = 8) -> str:
    """
    Генерирует случайный временный пароль из букв, цифр и спецсимволов.
    Используется администраторами для сброса пароля пользователю.
    """
    # Набор символов: заглавные, строчные, цифры, безопасные спецсимволы
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # secrets.choice криптографически безопаснее random.choice
    return ''.join(secrets.choice(alphabet) for _ in range(length))