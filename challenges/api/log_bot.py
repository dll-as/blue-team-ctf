import requests
import time
import threading

BOT_TOKEN:str = ""

class TelegramLogMonitor:
    def __init__(self, chat_id, log_file_path):
        self.chat_id = chat_id
        self.log_file_path = log_file_path
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.running = False

    def send_message(self, text):
        response = requests.post(
            url= f"{self.base_url}/sendMessage",
            params= {
                "chat_id": self.chat_id,
                "text": text
            }
        )
        return response.json()

    def send_document(self, file_path):
        with open(file_path, 'rb') as file:
            files = {"document": file}

        response = requests.post(
            url= f"{self.base_url}/sendDocument",
            files= files, params= {'chat_id': self.chat_id}
        )
        return response.json()

    def monitor_logs(self):
        self.running = True
        while self.running:
            try:
                with open(self.log_file_path, 'r') as file:
                    file.seek(self.last_position)
                    new_content = file.read()
                    self.last_position = file.tell()

                    if new_content:
                        self.send_message(f"New log entries:\n{new_content}")
                        self.send_document(self.log_file_path)

            except Exception as e:
                print(f"Error monitoring logs: {e}")

            time.sleep(60)

    def start(self):
        thread = threading.Thread(target=self.monitor_logs)
        thread.daemon = True
        thread.start()
        print("Log monitoring started. Press Ctrl+C to stop.")

    def stop(self):
        self.running = False

CHAT_ID:str = ""
LOG_FILE:str = "./api_requests.log"

monitor = TelegramLogMonitor(CHAT_ID, LOG_FILE)
monitor.start()


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    monitor.stop()
    print("Monitoring stopped.")