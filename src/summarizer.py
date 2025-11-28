import requests
import time

class SummarizerClient:
    def __init__(self, base_url="https://bit-summarize.1bitai.ru", token=None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"authorization": f"Bearer {self.token}"})

    def get_prompts(self):
        """Получить список доступных промптов."""
        url = f"{self.base_url}/api/v1/prompts"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения промптов: {e}")
            return None

    def create_task(self, text, prompt_id, model="llama", user_prompt=None):
        """Создать задачу саммаризации."""
        url = f"{self.base_url}/api/v1/tasks"
        data = {
            "text": text,
            "prompt_id": prompt_id,
            "model": model
        }
        if user_prompt:
            data["user_prompt"] = user_prompt
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка создания задачи: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            return None

    def get_status(self, task_id):
        """Получить статус задачи."""
        url = f"{self.base_url}/api/v1/tasks/{task_id}/status"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения статуса: {e}")
            return None

    def get_result(self, task_id):
        """Получить результат саммаризации."""
        url = f"{self.base_url}/api/v1/tasks/{task_id}/result"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения результата: {e}")
            return None

    def wait_for_completion(self, task_id, poll_interval=5, timeout=300):
        """Ожидание завершения задачи с polling."""
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                print("Превышено время ожидания")
                return None
            
            status = self.get_status(task_id)
            if not status:
                return None
            
            # Статус может быть строкой или словарем
            status_str = status if isinstance(status, str) else status.get("status", status)
            print(f"Статус: {status_str}")
            
            status_lower = str(status_str).lower() if status_str else ""
            
            if status_lower in ["ready", "completed", "done", "finished", "success"]:
                return status
            elif status_lower in ["error", "failed", "failure"]:
                print("Задача завершилась с ошибкой")
                return None
            
            time.sleep(poll_interval)
