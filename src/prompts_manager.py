import os
import json
from pathlib import Path

class PromptManager:
    def __init__(self, client):
        self.client = client
        # Папка для кастомных промптов находится в корне проекта/prompts
        # Определяем путь относительно этого файла (src/prompts_manager.py -> ../prompts)
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)

    def get_all_prompts(self):
        """
        Получает список промптов из API и локальной папки.
        Возвращает список словарей.
        """
        # 1. Получаем промпты из API
        api_prompts = []
        try:
            raw_prompts = self.client.get_prompts()
            if isinstance(raw_prompts, dict):
                api_prompts = list(raw_prompts.values())
            elif isinstance(raw_prompts, list):
                api_prompts = raw_prompts
        except Exception as e:
            print(f"Ошибка при получении промптов из API: {e}")

        # 2. Получаем локальные кастомные промпты
        local_prompts = []
        if self.prompts_dir.exists():
            for file_path in self.prompts_dir.glob("*.txt"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content:
                        local_prompts.append({
                            "id": "custom_file", # Специальный маркер
                            "name": file_path.stem, # Имя файла без расширения
                            "user_prompt_part": content,
                            "is_local": True
                        })
                except Exception as e:
                    print(f"Ошибка чтения файла промпта {file_path}: {e}")

        # Объединяем: сначала API, потом локальные
        return api_prompts + local_prompts

    def save_custom_prompt(self, name, content):
        """Сохраняет кастомный промпт в файл."""
        try:
            # Очищаем имя файла от недопустимых символов
            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
            if not safe_name:
                safe_name = "custom_prompt"
            
            file_path = self.prompts_dir / f"{safe_name}.txt"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Промпт сохранен: {file_path}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении промпта: {e}")
            return False

    def select_prompt_interactive(self):
        """
        Интерактивный выбор промпта.
        Возвращает tuple (prompt_id, user_prompt_content)
        """
        print("\nПолучение списка промптов...")
        prompts = self.get_all_prompts()
        
        if not prompts:
            print("Список промптов пуст.")
            return None, None

        print("\nДоступные промпты:")
        for i, prompt in enumerate(prompts, 1):
            name = prompt.get('title') or prompt.get('name') or prompt.get('id', 'N/A')
            
            # Маркер для локальных промптов
            local_marker = " [ПОЛЬЗОВАТЕЛЬСКИЙ]" if prompt.get('is_local') else ""
            
            print(f"{i}. {name}{local_marker}")
            
            # Вывод деталей
            user_part = prompt.get('user_prompt_part')
            if user_part:
                # Обрезаем длинные описания для компактности
                preview = user_part.replace('\n', ' ')[:100] + "..." if len(user_part) > 100 else user_part
                print(f"   \033[3m{preview}\033[0m")

        # Опция для нового кастомного промпта
        custom_option_index = len(prompts) + 1
        print(f"{custom_option_index}. Ввести новый произвольный запрос (Custom Prompt)")

        try:
            choice = input(f"\nВыберите номер (1-{custom_option_index}, Enter для 1): ").strip()
            
            if not choice:
                # По умолчанию первый
                selected = prompts[0]
                return (selected.get('id'), selected.get('user_prompt_part')) if selected.get('is_local') else (selected.get('id'), None)

            if not choice.isdigit():
                # Если ввели ID вручную
                return choice, None

            idx = int(choice) - 1
            
            if 0 <= idx < len(prompts):
                selected = prompts[idx]
                if selected.get('is_local'):
                    # Для локальных возвращаем "custom" ID и контент
                    return "custom", selected.get('user_prompt_part')
                else:
                    # Для API промптов возвращаем ID
                    return selected.get('id'), None
            
            elif idx == len(prompts):
                # Новый кастомный промпт
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
                content = "\n".join(lines)
                
                if not content.strip():
                    print("Пустой промпт, отмена.")
                    return None, None

                # Спрашиваем, сохранить ли
                save = input("\nСохранить этот промпт для будущих запусков? (y/N): ").strip().lower()
                if save == 'y':
                    name = input("Введите название для промпта: ").strip()
                    if name:
                        self.save_custom_prompt(name, content)
                
                return "custom", content
            
            else:
                print("Неверный номер.")
                return None, None

        except (KeyboardInterrupt, EOFError):
            print("\nОтменено пользователем.")
            return None, None
