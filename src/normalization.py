import re
import json
from pathlib import Path

def load_filename_patterns():
    """
    Загружает шаблоны имен файлов из конфигурационного файла.
    Возвращает список шаблонов или None при ошибке.
    """
    try:
        # Ищем файл конфига на уровень выше от папки src
        config_path = Path(__file__).parent.parent / "filename_patterns.json"
        
        if not config_path.exists():
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("patterns", [])
    except Exception as e:
        print(f"Предупреждение: Не удалось загрузить конфиг шаблонов: {e}")
        return None

def normalize_telemost_filename(filename):
    """
    Нормализует имена файлов из Телемоста.
    Пример: "Встреча в Телемосте 01.11.25 11-05-32 — запись Название.mp3" -> "202511011105 Название.mp3"
    """
    # 1. Сначала пробуем загрузить пользовательские шаблоны
    patterns = load_filename_patterns()
    
    if patterns:
        for pattern_config in patterns:
            # Пока поддерживаем только простую логику regex, если она там есть
            # В будущем сюда можно вернуть сложную логику, если понадобится
            pass

    # 2. Если шаблоны не помогли или их нет, используем хардкод для Телемоста
    
    # Работаем с именем без расширения, чтобы не путаться
    file_path = Path(filename)
    suffix = file_path.suffix
    stem = file_path.stem # Имя без расширения
    
    # Паттерн для поиска "Встреча в Телемосте DD.MM.YY HH-MM-SS"
    # Убрали расширение, поэтому ищем только в stem
    pattern = r'^Встреча в Телемосте (\d{2})\.(\d{2})\.(\d{2}) (\d{2})-(\d{2})-(\d{2})\s*(?:—\s*запись\s*)?(.*)'
    match = re.match(pattern, stem)
    
    if match:
        day, month, year, hour, minute, second, rest = match.groups()
        # Преобразуем год из YY в YYYY (предполагаем 20YY)
        full_year = f"20{year}"
        # Формируем дату+время
        datetime_prefix = f"{full_year}{month}{day}{hour}{minute}"
        
        # Очищаем остаток имени от лишних пробелов
        rest = rest.strip()
        
        # Формируем новое имя
        if rest:
            new_filename = f"{datetime_prefix} {rest}{suffix}"
        else:
            new_filename = f"{datetime_prefix}{suffix}"
        
        return new_filename
    
    return filename
