from telebot import types

class Keyboards:
    @staticmethod
    def main_menu():
        """Главное меню"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📋 Список ботов"),
            types.KeyboardButton("➕ Добавить бота"),
            types.KeyboardButton("👥 Управление админами"),
            types.KeyboardButton("⚙️ Настройки")
        )
        return markup
    
    @staticmethod
    def back_button():
        """Кнопка 'Назад'"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад"))
        return markup
    
    @staticmethod
    def bot_actions(bot_name: str):
        """Действия с конкретным ботом"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton(f"📄 Логи {bot_name} (20 строк)"),
            types.KeyboardButton(f"📄 Логи {bot_name} (50 строк)"),
            types.KeyboardButton(f"📥 Скачать логи {bot_name}"),
            types.KeyboardButton(f"❌ Удалить {bot_name}"),
            types.KeyboardButton("🔙 Назад")
        )
        return markup

    @staticmethod
    def admin_actions(bot_name: str):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton(f"👥 Список админов {bot_name}"),
            types.KeyboardButton(f"➕ Добавить админа {bot_name}"),
            types.KeyboardButton(f"➖ Удалить админа {bot_name}"),
            types.KeyboardButton("🔙 Назад")
        )
        return markup
    
    @staticmethod
    def confirm_action():
        """Подтверждение действия"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("✅ Подтвердить"),
            types.KeyboardButton("❌ Отменить")
        )
        return markup
    
    @staticmethod
    def bot_list(bots: list):
        """Список ботов с кнопками"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for bot in bots:
            markup.add(types.KeyboardButton(f"🤖 {bot}"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        return markup

    @staticmethod
    def settings_menu():
        """Клавиатура меню настроек"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("👥 Управление глобальными админами"),
            types.KeyboardButton("📊 Статистика"),
            types.KeyboardButton("🔙 Назад")
        )
        return markup