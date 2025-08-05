import os
import json
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    # Токен бота из .env
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Список админов (по username) в формате JSON массива
    ADMINS = json.loads(os.getenv('ADMINS'))
    
    # Директория для логов самого бота
    LOGS_DIR = os.getenv('LOGS_DIR')
    
    # Файл для хранения данных о ботах
    BOTS_DATA_FILE = os.getenv('BOTS_DATA_FILE')
    
    @classmethod
    def check_config(cls):
        """Проверка корректности конфигурации"""
        required_vars = ['BOT_TOKEN', 'ADMINS', 'LOGS_DIR', 'BOTS_DATA_FILE']
        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f'Необходимо установить переменную {var} в .env файле')