import os
from pathlib import Path

# Файл для хранения токена в домашней директории пользователя
TOKEN_FILE = Path.home() / ".asr_token"

def get_token(arg_token=None):
    """
    Получает токен из разных источников в порядке приоритета:
    1. Аргумент командной строки
    2. Переменная окружения ASR_TOKEN
    3. Файл конфигурации ~/.asr_token
    """
    # 1. Аргумент
    if arg_token:
        return arg_token
    
    # 2. Переменная окружения
    env_token = os.environ.get("ASR_TOKEN")
    if env_token:
        return env_token.strip().strip('"').strip("'")
        
    # 3. Файл конфигурации
    if TOKEN_FILE.exists():
        try:
            token = TOKEN_FILE.read_text(encoding='utf-8').strip()
            if token:
                return token
        except Exception:
            pass
            
    return None

def set_token(token):
    """
    Сохраняет токен в файл конфигурации.
    """
    try:
        # Очистка токена
        clean_token = token.strip().strip('"').strip("'")
        
        TOKEN_FILE.write_text(clean_token, encoding='utf-8')
        print(f"✓ Токен успешно сохранен в: {TOKEN_FILE}")
        print("Теперь вы можете запускать команды без указания флага --token.")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении токена: {e}")
        return False
