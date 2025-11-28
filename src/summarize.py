#!/usr/bin/env python3
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
import argparse
import json
from pathlib import Path
from summarizer import SummarizerClient
import config

def main():
    description = """
Инструмент для автоматической саммаризации текста с использованием LLM (GPT-4, Llama).
Позволяет выбрать готовый промпт или ввести свой собственный.
"""
    epilog = """
Установка токена (ASR_TOKEN):
  1. Через команду (рекомендуется):
     summarize --set-token "ваш_токен"
  2. Переменная окружения:
     PowerShell: $env:ASR_TOKEN="ваш_токен"
     Bash: export ASR_TOKEN="ваш_токен"
"""
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file", nargs="?", help="Путь к текстовому файлу")
    parser.add_argument("--token", help="API Токен (необязательно, если уже сохранен через --set-token)", default=None)
    parser.add_argument("--set-token", help="Сохранить токен в ~/.asr_token для будущего использования и выйти")
    parser.add_argument("--prompt-id", help="ID промпта (если не указан, будет интерактивный выбор)")
    parser.add_argument("--model", choices=["gpt4", "llama"], default="llama", help="Модель для саммаризации")
    parser.add_argument("--user-prompt", help="Кастомный промпт пользователя")
    parser.add_argument("--default", action="store_true",
                        help="Использовать параметры по умолчанию без интерактивных вопросов")
    parser.add_argument("--list-prompts", action="store_true",
                        help="Показать список промптов (включая из папки 'prompts' в корне программы) и завершить работу")
    
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
    
    # Инициализация клиента
    client = SummarizerClient(token=token)

    # Если запрошен список промптов
    if args.list_prompts:
        from prompts_manager import PromptManager
        prompts = pm.get_all_prompts()
        if prompts:
            print(json.dumps(prompts, indent=2, ensure_ascii=False))
        else:
            print("Не удалось получить список промптов.")
        print(f"\nПапка с кастомными промптами: {pm.prompts_dir.resolve()}")
        sys.exit(0)

    input_file = args.file
    if not input_file:
        print("Ошибка: Не указан входной файл.")
        sys.exit(1)
        
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не найден.")
        sys.exit(1)

    # Читаем текст из файла
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Формируем имя выходного файла
    input_path = Path(input_file)
    output_file = input_path.parent / f"{input_path.stem}_sum.md"

    print(f"--- Саммаризация ---")
    print(f"Входной файл: {input_file}")
    print(f"Выходной файл: {output_file}")

    # Получение промптов, если не указан prompt_id и не установлен --default
    prompt_id = args.prompt_id
    if not prompt_id and not args.default:
        from prompts_manager import PromptManager
        pm = PromptManager(client)
        
        selected_id, selected_content = pm.select_prompt_interactive()
        
        if selected_id:
            prompt_id = selected_id
            if selected_content:
                args.user_prompt = selected_content
        else:
            print("Используется промпт по умолчанию: meeting_detailed")
            prompt_id = "meeting_detailed"
    elif not prompt_id:
        # Если --default и prompt_id не указан, используем meeting_detailed
        prompt_id = "meeting_detailed"

    print(f"\nИспользуется промпт: {prompt_id}")
    
    # Выбор модели (если не указана через аргумент и не установлен --default)
    if not args.default and (not args.model or args.model == "llama"):
        try:
            model_choice = input("\nВыберите модель (1 - llama [по умолчанию], 2 - gpt4, Enter для llama): ").strip()
            
            if not model_choice or model_choice == "1":
                model = "llama"
            elif model_choice == "2":
                model = "gpt4"
            else:
                # Если введено название модели напрямую
                if model_choice.lower() in ["llama", "gpt4"]:
                    model = model_choice.lower()
                else:
                    print("Неверный выбор, используется llama по умолчанию")
                    model = "llama"
        except (KeyboardInterrupt, EOFError):
            print("\nОтменено пользователем")
            sys.exit(1)
    else:
        model = args.model
    
    print(f"Модель: {model}")

    # Создание задачи
    print("Создание задачи саммаризации...")
    task_id = client.create_task(text, prompt_id, model=model, user_prompt=args.user_prompt)
    
    if not task_id:
        print("Ошибка: Не удалось создать задачу.")
        sys.exit(1)

    # Если вернулся словарь, извлекаем task_id
    if isinstance(task_id, dict):
        task_id = task_id.get("task_id") or task_id.get("id") or task_id

    print(f"ID задачи: {task_id}")

    # Ожидание завершения
    print("Ожидание завершения...")
    status = client.wait_for_completion(task_id)
    
    if not status:
        print("Ошибка: Задача не завершена.")
        sys.exit(1)

    # Получение результата
    print("Получение результата...")
    result = client.get_result(task_id)
    
    if not result:
        print("Ошибка: Не удалось получить результат.")
        sys.exit(1)

    # Извлечение текста саммаризации
    if isinstance(result, dict) and "summary" in result:
        # Если результат - JSON с ключом summary, извлекаем его
        result_text = result["summary"]
    elif isinstance(result, str):
        # Если результат - строка, используем как есть
        result_text = result
    else:
        # Иначе сохраняем как JSON
        result_text = json.dumps(result, indent=2, ensure_ascii=False)
    
    # Сохранение результата как Markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result_text)
    
    print(f"\n✓ Готово! Результат сохранен в: {output_file}")

if __name__ == "__main__":
    main()
