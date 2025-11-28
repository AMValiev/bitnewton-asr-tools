import requests
import os

class ASRClient:
    def __init__(self, base_url="https://bit-asr-diarize.1bitai.ru", token=None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"token": self.token})

    def health_check(self):
        """Проверка доступности сервиса."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка Health Check: {e}")
            return None

    def start_transcribing(self, file_path, diarize=True, remove_timestamps=True):
        """Запуск транскрибации."""
        if not os.path.exists(file_path):
            print(f"Файл не найден: {file_path}")
            return None

        url = f"{self.base_url}/start_transcribing"
        params = {
            "diarize": str(diarize).lower(),
            "remove_timestamps": str(remove_timestamps).lower()
        }
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(url, params=params, files=files)
            
            if response.status_code != 200:
                print(f"Ошибка при запуске: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            return response.json() 
        except requests.RequestException as e:
            print(f"Исключение при запросе: {e}")
            return None

    def get_status(self, task_id):
        """Получение статуса задачи."""
        url = f"{self.base_url}/get_status"
        params = {"task_id": task_id}
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                print(f"Ошибка статуса: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Исключение при получении статуса: {e}")
            return None

    def get_file(self, task_id, output_path):
        """Скачивание результата."""
        url = f"{self.base_url}/get_file"
        params = {"task_id": task_id}
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                print(f"Ошибка скачивания: {response.status_code} - {response.text}")
                return False
            
            response.raise_for_status()
            
            try:
                content_json = response.json()
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(content_json, f, indent=4, ensure_ascii=False)
            except ValueError:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
            
            print(f"Файл сохранен: {output_path}")
            return True
        except requests.RequestException as e:
            print(f"Исключение при скачивании: {e}")
            return False
