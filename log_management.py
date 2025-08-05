import os
from telebot import types
from database import db
from keyboards import Keyboards
from logger import logger

class LogManagement:
    def __init__(self, bot):
        self.bot = bot
        self.realtime_logs = {}  # {chat_id: {'bot_name': name, 'file': file_object, 'position': pos}}
    
    def get_log_lines(self, file_path: str, num_lines: int = 20):
        """Получение последних N строк лога"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-num_lines:]
            return ''.join(lines)
        except Exception as e:
            logger.log(f"Ошибка чтения логов: {str(e)}", 'error')
            return None
    
    def handle_bot_logs(self, message: types.Message, bot_name: str, lines_count: int):
        """Обработка запроса логов бота"""
        chat_id = message.chat.id
        log_path = db.get_bot_log_path(bot_name)
        
        if not log_path:
            self.bot.send_message(
                chat_id,
                f"❌ Не удалось найти путь к логам для бота {bot_name}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        if not os.path.exists(log_path):
            self.bot.send_message(
                chat_id,
                f"❌ Файл логов не найден по пути: {log_path}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        logs = self.get_log_lines(log_path, lines_count)
        if logs:
            self.bot.send_message(
                chat_id,
                f"📋 Последние {lines_count} строк логов бота {bot_name}:\n"
                f"<code>{logs}</code>",
                parse_mode='HTML',
                reply_markup=Keyboards.bot_actions(bot_name)
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Не удалось прочитать логи для бота {bot_name}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
    
    def handle_download_logs(self, message: types.Message, bot_name: str):
        """Обработка запроса на скачивание логов"""
        chat_id = message.chat.id
        log_path = db.get_bot_log_path(bot_name)
        
        if not log_path:
            self.bot.send_message(
                chat_id,
                f"❌ Не удалось найти путь к логам для бота {bot_name}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        if not os.path.exists(log_path):
            self.bot.send_message(
                chat_id,
                f"❌ Файл логов не найден по пути: {log_path}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        try:
            with open(log_path, 'rb') as f:
                self.bot.send_document(
                    chat_id,
                    f,
                    caption=f"📁 Логи бота {bot_name}",
                    reply_markup=Keyboards.bot_actions(bot_name)
                )
            logger.log(f"Логи бота {bot_name} отправлены пользователю {message.from_user.username}")
        except Exception as e:
            self.bot.send_message(
                chat_id,
                f"❌ Ошибка при отправке логов: {str(e)}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            logger.log(f"Ошибка отправки логов: {str(e)}", 'error')
    
    def handle_realtime_logs(self, message: types.Message, bot_name: str):
        """Обработка запроса логов в реальном времени"""
        chat_id = message.chat.id
        log_path = db.get_bot_log_path(bot_name)
        
        if not log_path:
            self.bot.send_message(
                chat_id,
                f"❌ Не удалось найти путь к логам для бота {bot_name}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        if not os.path.exists(log_path):
            self.bot.send_message(
                chat_id,
                f"❌ Файл логов не найден по пути: {log_path}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            return
        
        # Запоминаем текущую позицию в файле
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # Переходим в конец файла
                position = f.tell()
            
            self.realtime_logs[chat_id] = {
                'bot_name': bot_name,
                'file_path': log_path,
                'position': position
            }
            
            self.bot.send_message(
                chat_id,
                f"🔍 Режим реального времени для бота {bot_name} активирован.\n"
                "Новые записи в логах будут приходить автоматически.\n"
                "Для остановки нажмите /stop_realtime",
                reply_markup=Keyboards.back_button()
            )
            
            # Запускаем проверку обновлений
            self.check_log_updates(chat_id)
        except Exception as e:
            self.bot.send_message(
                chat_id,
                f"❌ Ошибка при активации режима реального времени: {str(e)}",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
            logger.log(f"Ошибка активации realtime логов: {str(e)}", 'error')
    
    def check_log_updates(self, chat_id: int):
        """Проверка обновлений логов для realtime режима"""
        if chat_id not in self.realtime_logs:
            return
        
        log_info = self.realtime_logs[chat_id]
        bot_name = log_info['bot_name']
        file_path = log_info['file_path']
        position = log_info['position']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                new_lines = f.read()
                
                if new_lines:
                    self.bot.send_message(
                        chat_id,
                        f"🔄 Новые записи в логах {bot_name}:\n"
                        f"<code>{new_lines}</code>",
                        parse_mode='HTML'
                    )
                
                # Обновляем позицию
                log_info['position'] = f.tell()
                self.realtime_logs[chat_id] = log_info
                
                # Планируем следующую проверку через 5 секунд
                import threading
                timer = threading.Timer(5.0, self.check_log_updates, args=[chat_id])
                timer.start()
        except Exception as e:
            logger.log(f"Ошибка проверки обновлений логов: {str(e)}", 'error')
            self.stop_realtime_logs(chat_id)
            self.bot.send_message(
                chat_id,
                f"❌ Ошибка при чтении логов: {str(e)}\n"
                "Режим реального времени остановлен.",
                reply_markup=Keyboards.bot_actions(bot_name)
            )
    
    def stop_realtime_logs(self, chat_id: int):
        """Остановка realtime режима"""
        if chat_id in self.realtime_logs:
            bot_name = self.realtime_logs[chat_id]['bot_name']
            del self.realtime_logs[chat_id]
            self.bot.send_message(
                chat_id,
                f"⏹ Режим реального времени для бота {bot_name} остановлен.",
                reply_markup=Keyboards.bot_actions(bot_name)
            )