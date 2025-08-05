import os
import json
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')

    try:
        ADMINS = json.loads(os.getenv('ADMINS', '[]'))
    except json.JSONDecodeError:
        ADMINS = []

    LOGS_DIR = os.getenv('LOGS_DIR', './logs')
    BOTS_DATA_FILE = os.getenv('BOTS_DATA_FILE', './bots_data.json')

    @classmethod
    def check_config(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("Токен бота не указан в .env файле")
        """Проверка корректности конфигурации"""
        required_vars = ['BOT_TOKEN', 'ADMINS', 'LOGS_DIR', 'BOTS_DATA_FILE']
        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f'Необходимо установить переменную {var} в .env файле')