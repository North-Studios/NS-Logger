import logging
import os
from datetime import datetime
from config import Config


class BotLogger:
    def __init__(self):
        os.makedirs(Config.LOGS_DIR, exist_ok=True)

        # Формат логов: [Дата Время] Уровень: Сообщение
        log_format = '[%(asctime)s] %(levelname)s: %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Настройка базового логгера с UTF-8 кодировкой
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                # FileHandler с указанием кодировки UTF-8
                logging.FileHandler(
                    os.path.join(Config.LOGS_DIR, 'ns_logger.log'),
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('NSLogger')

    def log(self, message: str, level: str = 'info'):
        """Логирование сообщения с указанным уровнем"""
        try:
            level = level.lower()
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)
        except Exception as e:
            # Если произошла ошибка логирования, выводим в консоль
            print(f"Ошибка логирования: {str(e)}")
            print(f"Сообщение: {message}")


# Глобальный экземпляр логгера
logger = BotLogger()