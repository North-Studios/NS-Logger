import json
import os
from config import Config
from logger import logger
from datetime import datetime

class Database:
    def __init__(self):
        self.bots_data = {}
        self.load_data()
    
    def load_data(self):
        """Загрузка данных о ботах из файла"""
        try:
            if os.path.exists(Config.BOTS_DATA_FILE):
                with open(Config.BOTS_DATA_FILE, 'r', encoding='utf-8') as f:
                    self.bots_data = json.load(f)
            logger.log(f"Данные загружены. Всего ботов: {len(self.bots_data)}")
        except Exception as e:
            logger.log(f"Ошибка загрузки данных: {str(e)}", 'error')
            self.bots_data = {}
    
    def save_data(self):
        """Сохранение данных о ботах в файл"""
        try:
            with open(Config.BOTS_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.bots_data, f, ensure_ascii=False, indent=4)
            logger.log("Данные успешно сохранены")
        except Exception as e:
            logger.log(f"Ошибка сохранения данных: {str(e)}", 'error')
    
    def add_bot(self, bot_name: str, log_path: str, added_by: str):
        """Добавление нового бота в систему"""
        if bot_name not in self.bots_data:
            self.bots_data[bot_name] = {
                'log_path': log_path,
                'admins': [added_by],
                'created_at': datetime.now().isoformat()
            }
            self.save_data()
            logger.log(f"Добавлен новый бот: {bot_name} (путь: {log_path})")
            return True
        return False
    
    def remove_bot(self, bot_name: str):
        """Удаление бота из системы"""
        if bot_name in self.bots_data:
            del self.bots_data[bot_name]
            self.save_data()
            logger.log(f"Бот {bot_name} удален")
            return True
        return False
    
    def add_admin(self, bot_name: str, username: str):
        """Добавление администратора для бота"""
        if bot_name in self.bots_data and username not in self.bots_data[bot_name]['admins']:
            self.bots_data[bot_name]['admins'].append(username)
            self.save_data()
            logger.log(f"Добавлен администратор {username} для бота {bot_name}")
            return True
        return False
    
    def remove_admin(self, bot_name: str, username: str):
        """Удаление администратора для бота"""
        if bot_name in self.bots_data and username in self.bots_data[bot_name]['admins']:
            self.bots_data[bot_name]['admins'].remove(username)
            self.save_data()
            logger.log(f"Удален администратор {username} для бота {bot_name}")
            return True
        return False
    
    def get_bot_list(self):
        """Получение списка всех ботов"""
        return list(self.bots_data.keys())
    
    def get_bot_admins(self, bot_name: str):
        """Получение списка администраторов бота"""
        return self.bots_data.get(bot_name, {}).get('admins', [])
    
    def get_bot_log_path(self, bot_name: str):
        """Получение пути к логам бота"""
        return self.bots_data.get(bot_name, {}).get('log_path', '')

    def get_statistics(self):
        """Получение статистики по ботам и админам"""
        return {
            'bot_count': len(self.bots_data),
            'total_admins': sum(len(bot['admins']) for bot in self.bots_data.values())
        }

# Глобальный экземпляр базы данных
db = Database()