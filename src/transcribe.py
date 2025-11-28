#!/usr/bin/env python3
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
import time
import argparse
import shutil
import re
from pathlib import Path
from client import ASRClient
import config

def normalize_telemost_filename(filename):
    """
    Нормализует имена файлов из Телемоста.
    Пример: "Встреча в Телемосте 01.11.25 11-05-32 — запись Название.mp3" -> "202511011105 Название.mp3"
    """
    # Паттерн для поиска "Встреча в Телемосте DD.MM.YY HH-MM-SS"
    pattern = r'^Встреча в Телемосте (\d{2})\.(\d{2})\.(\d{2}) (\d{2})-(\d{2})-(\d{2})\s*(?:—\s*запись\s*)?(.*)'
    match = re.match(pattern, filename)
    
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
            new_filename = f"{datetime_prefix} {rest}"
        else:
            new_filename = f"{datetime_prefix}{Path(filename).suffix}"
        
        return new_filename
    
    return filename

def main():
    description = """
Универсальный инструмент для транскрибации аудио и последующей саммаризации.
Автоматически обрабатывает файлы, поддерживает переименование записей Телемоста
и организацию результатов в папки.

Пример обработки имени файла:
  "Встреча в Телемосте 01.11.25 11-05-32 — запись Название.mp3"
  -> "202511011105 Название.mp3"
"""
    epilog = """
Установка токена (ASR_TOKEN):
  1. Через команду (рекомендуется):
     transcribe --set-token "ваш_токен"
  2. Переменная окружения:
     PowerShell: $env:ASR_TOKEN="ваш_токен"
     Bash: export ASR_TOKEN="ваш_токен"
"""
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file", nargs="?", help="Путь к аудиофайлу")
    parser.add_argument("--token", help="API Токен (необязательно, если уже сохранен через --set-token)", default=None)
    parser.add_argument("--set-token", help="Сохранить токен в ~/.asr_token для будущего использования и выйти")
    parser.add_argument("--keep-original", action="store_true", 
                        help="Сохранить оригинальный файл на месте (копировать вместо перемещения)")
    parser.add_argument("--output-dir", help="Папка для сохранения результатов (по умолчанию: имя файла)")
    parser.add_argument("--summarize", action="store_true",
                        help="Автоматически создать саммаризацию после транскрибации")
    parser.add_argument("--prompt-id", default="meeting_detailed",
                        help="ID промпта для саммаризации (по умолчанию: meeting_detailed)")
    parser.add_argument("--model", choices=["gpt4", "llama"], default="llama",
                        help="Модель для саммаризации")
    parser.add_argument("--default", action="store_true",
                        help="Использовать параметры по умолчанию для саммаризации без интерактивных вопросов")
    parser.add_argument("--list-prompts", action="store_true",
                        help="Вывести список всех доступных промптов в формате JSON и выйти")
    
    # Если запуск без аргументов, выводим справку
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()

    # Если указан --set-token, сохраняем и выходим
    if args.set_token:
        config.set_token(args.set_token)
        sys.exit(0)

    # Получение токена
    token = config.get_token(args.token)

    # Проверка токена
    if not token:
        print("Ошибка: Не найден токен.")
        print("Используйте --set-token для сохранения токена или установите переменную окружения ASR_TOKEN.")
        sys.exit(1)

    # Если запрошен список промптов
    if args.list_prompts:
        try:
            from summarizer import SummarizerClient
            import json
            sum_client = SummarizerClient(token=token)
            prompts = sum_client.get_prompts()
            if prompts:
                print(json.dumps(prompts, indent=2, ensure_ascii=False))
            else:
                print("Не удалось получить список промптов.")
        except ImportError:
            print("Ошибка: Модуль summarizer.py не найден.")
        except Exception as e:
            print(f"Ошибка: {e}")
        sys.exit(0)

    input_file = args.file
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не найден.")
        sys.exit(1)

    # Получаем абсолютный путь к исходному файлу
    input_path = Path(input_file).resolve()
    original_filename = input_path.name
    parent_dir = input_path.parent

    # Нормализуем имя файла (если это файл из Телемоста)
    normalized_filename = normalize_telemost_filename(original_filename)
    
    # Если имя изменилось, переименовываем файл НА МЕСТЕ
    if normalized_filename != original_filename:
        new_path = parent_dir / normalized_filename
        print(f"Переименование: '{original_filename}' -> '{normalized_filename}'")
        input_path.rename(new_path)
        input_path = new_path
    
    # Очищаем имя файла от пробелов в начале и конце для будущего использования
    base_name = input_path.stem.strip()  # Имя файла без расширения
    file_ext = input_path.suffix  # Расширение файла

    # Файл для транскрибации - это текущий файл (возможно переименованный)
    file_to_transcribe = str(input_path)

    print(f"--- Начало работы ---")
    print(f"Файл: {file_to_transcribe}")
    
    # Инициализация клиента
    client = ASRClient(token=token)

    # 1. Запуск транскрибации
    print("Запуск транскрибации...")
    result = client.start_transcribing(file_to_transcribe)

    if not result:
        print("Ошибка: Не удалось запустить задачу.")
        sys.exit(1)

    # Обработка ответа (ожидаем task_id)
    task_id = result
    if isinstance(result, dict):
        task_id = result.get("task_id") or result.get("id")

    print(f"ID задачи: {task_id}")

    # 2. Ожидание завершения (Polling)
    print("Ожидание завершения обработки...")
    while True:
        status_resp = client.get_status(task_id)
        
        # Статус может быть строкой или словарем
        status = status_resp
        if isinstance(status_resp, dict):
            status = status_resp.get("status", status_resp)
        
        print(f"Текущий статус: {status}")

        # Приводим к нижнему регистру для сравнения
        status_lower = str(status).lower() if status else ""
        
        if status_lower in ["ready", "completed", "done", "finished", "success"]:
            break
        elif status_lower in ["error", "failed", "failure"]:
            print("Ошибка: Задача завершилась с ошибкой.")
            sys.exit(1)
        
        time.sleep(5) # Пауза 5 секунд

    # --- УСПЕХ: Создание папки и перемещение файлов ---
    
    # Определяем папку для результатов
    if args.output_dir:
        output_folder = Path(args.output_dir).resolve()
    else:
        # Используем очищенное имя для папки
        output_folder = parent_dir / base_name

    # Создаем папку для результатов
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"Папка для результатов: {output_folder}")

    # Определяем путь к файлу в новой папке (используем очищенное имя)
    target_audio_path = output_folder / f"{base_name}{file_ext}"
    
    # Перемещаем или копируем файл
    if args.keep_original:
        print(f"Копирование файла в папку результатов...")
        shutil.copy2(input_path, target_audio_path)
    else:
        print(f"Перемещение файла в папку результатов...")
        # Если файл уже там (например, output_dir = parent_dir), move может ругаться, поэтому проверяем
        if input_path != target_audio_path:
            shutil.move(str(input_path), str(target_audio_path))
        else:
            print("Файл уже находится в целевой папке.")

    # Формирование имени выходного файла
    output_file = output_folder / f"{base_name}_text.json"
    print(f"Выходной файл: {output_file}")

    # 3. Скачивание результата
    print("Скачивание результата...")
    if client.get_file(task_id, str(output_file)):
        print(f"\n✓ Транскрибация завершена!")
        print(f"  - Аудио: {target_audio_path.name}")
        print(f"  - Текст: {output_file.name}")
        
        # 4. Саммаризация (если включена)
        if args.summarize:
            print(f"\n--- Саммаризация ---")
            try:
                from summarizer import SummarizerClient
                import json
                
                # Читаем транскрипцию
                with open(output_file, 'r', encoding='utf-8') as f:
                    transcription_data = json.load(f)
                
                # Извлекаем текст из транскрипции
                if isinstance(transcription_data, list):
                    # Если это список сегментов, объединяем текст
                    text = " ".join([segment.get("text", "") for segment in transcription_data if isinstance(segment, dict)])
                elif isinstance(transcription_data, dict):
                    # Если это словарь, ищем поле text
                    text = transcription_data.get("text", str(transcription_data))
                else:
                    text = str(transcription_data)
                
                if not text.strip():
                    print("Предупреждение: Текст для саммаризации пуст, пропускаем.")
                else:
                    # Инициализация клиента саммаризации
                    sum_client = SummarizerClient(token=token)
                    
                    # Определяем prompt_id
                    prompt_id = args.prompt_id
                    
                    # Если prompt_id не был явно указан и не установлен --default, спрашиваем
                    if prompt_id == "meeting_detailed" and "--prompt-id" not in sys.argv and not args.default:
                        print("\nПолучение списка промптов...")
                        prompts = sum_client.get_prompts()
                        
                        if prompts:
                            print("\nДоступные промпты:")
                            prompts_list = []
                            
                            # Нормализация списка промптов (API может вернуть список или словарь)
                            if isinstance(prompts, dict):
                                prompts_list = list(prompts.values())
                            elif isinstance(prompts, list):
                                prompts_list = prompts
                            
                            if prompts_list:
                                for i, prompt in enumerate(prompts_list, 1):
                                    if isinstance(prompt, dict):
                                        # Используем title или name, или id как запасной вариант
                                        name = prompt.get('title') or prompt.get('name') or prompt.get('id', 'N/A')
                                        print(f"{i}. {name}")
                                        
                                        # Вывод деталей промпта
                                        user_part = prompt.get('user_prompt_part')
                                        if user_part:
                                            # \033[3m - курсив, \033[0m - сброс
                                            print(f"   Инструкции: \033[3m{user_part}\033[0m")
                                    else:
                                        print(f"{i}. {prompt}")
                                
                                # Добавляем опцию для произвольного запроса
                                custom_option_index = len(prompts_list) + 1
                                print(f"{custom_option_index}. Произвольный запрос (Custom Prompt)")
                            else:
                                print(json.dumps(prompts, indent=2, ensure_ascii=False))
                            
                            try:
                                choice = input(f"\nВыберите номер (1-{custom_option_index}, Enter для 1): ").strip()
                                
                                if not choice:
                                    if prompts_list:
                                        selected_prompt = prompts_list[0]
                                        prompt_id = selected_prompt.get('id') if isinstance(selected_prompt, dict) else selected_prompt
                                        print(f"Используется промпт по умолчанию: {prompt_id}")
                                    else:
                                        print("Список промптов пуст, используется meeting_detailed")
                                        prompt_id = "meeting_detailed"
                                elif choice.isdigit():
                                    idx = int(choice) - 1
                                    if 0 <= idx < len(prompts_list):
                                        selected_prompt = prompts_list[idx]
                                        prompt_id = selected_prompt.get('id') if isinstance(selected_prompt, dict) else selected_prompt
                                    elif idx == len(prompts_list):
                                        # Выбран произвольный запрос
                                        print("\nВведите ваш промпт (для завершения нажмите Enter дважды):")
                                        lines = []
                                        while True:
                                            try:
                                                line = input()
                                                if not line:
                                                    break
                                                lines.append(line)
                                            except EOFError:
                                                break
                                        user_prompt = "\n".join(lines)
                                        prompt_id = "custom"
                                        print("Принят произвольный запрос.")
                                    else:
                                        print("Неверный номер, используется meeting_detailed")
                                        prompt_id = "meeting_detailed"
                                else:
                                    prompt_id = choice
                            except (KeyboardInterrupt, EOFError):
                                print("\nОтменено пользователем, пропускаем саммаризацию.")
                                prompt_id = None
                    
                    if prompt_id:
                        # Определяем модель
                        model = args.model
                        
                        # Если модель не была явно указана и не установлен --default, спрашиваем
                        if model == "llama" and "--model" not in sys.argv and not args.default:
                            try:
                                model_choice = input("\nВыберите модель (1 - llama [по умолчанию], 2 - gpt4, Enter для llama): ").strip()
                                
                                if not model_choice or model_choice == "1":
                                    model = "llama"
                                elif model_choice == "2":
                                    model = "gpt4"
                                else:
                                    if model_choice.lower() in ["llama", "gpt4"]:
                                        model = model_choice.lower()
                                    else:
                                        print("Неверный выбор, используется llama по умолчанию")
                                        model = "llama"
                            except (KeyboardInterrupt, EOFError):
                                print("\nОтменено пользователем, пропускаем саммаризацию.")
                                model = None
                        
                        if model:
                            print(f"\nПромпт: {prompt_id}")
                            print(f"Модель: {model}")
                            
                            # Создание задачи саммаризации
                            print("Создание задачи саммаризации...")
                            # Передаем user_prompt если он был задан (инициализируем None если нет)
                            if 'user_prompt' not in locals():
                                user_prompt = None
                                
                            sum_task_id = sum_client.create_task(text, prompt_id, model=model, user_prompt=user_prompt)
                            
                            if sum_task_id:
                                # Извлекаем task_id если вернулся словарь
                                if isinstance(sum_task_id, dict):
                                    sum_task_id = sum_task_id.get("task_id") or sum_task_id.get("id") or sum_task_id
                                
                                print(f"ID задачи саммаризации: {sum_task_id}")
                                
                                # Ожидание завершения
                                print("Ожидание завершения саммаризации...")
                                sum_status = sum_client.wait_for_completion(sum_task_id)
                                
                                if sum_status:
                                    # Получение результата
                                    print("Получение результата саммаризации...")
                                    sum_result = sum_client.get_result(sum_task_id)
                                    
                                    if sum_result:
                                        # Извлечение текста саммаризации
                                        if isinstance(sum_result, dict) and "summary" in sum_result:
                                            summary_text = sum_result["summary"]
                                        elif isinstance(sum_result, str):
                                            summary_text = sum_result
                                        else:
                                            summary_text = json.dumps(sum_result, indent=2, ensure_ascii=False)
                                        
                                        # Сохранение саммаризации
                                        summary_file = output_folder / f"{base_name}_sum.md"
                                        with open(summary_file, 'w', encoding='utf-8') as f:
                                            f.write(summary_text)
                                        
                                        print(f"  - Саммаризация: {summary_file.name}")
                                    else:
                                        print("Ошибка: Не удалось получить результат саммаризации.")
                                else:
                                    print("Ошибка: Задача саммаризации не завершена.")
                            else:
                                print("Ошибка: Не удалось создать задачу саммаризации.")
                        
            except ImportError:
                print("Ошибка: Модуль summarizer.py не найден. Пропускаем саммаризацию.")
            except Exception as e:
                print(f"Ошибка при саммаризации: {e}")
        
        print(f"\n✓ Готово! Результаты сохранены в папке: {output_folder}")
    else:
        print("Ошибка при скачивании файла.")
        sys.exit(1)

if __name__ == "__main__":
    main()
