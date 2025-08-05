import os
from telebot import TeleBot
from telebot.types import Message
from config import Config
from database import db
from logger import logger
from keyboards import Keyboards
from bot_management import BotManagement
from log_management import LogManagement

# Инициализация бота
bot = TeleBot(Config.BOT_TOKEN)

# Инициализация модулей
bot_management = BotManagement(bot)
log_management = LogManagement(bot)

@bot.message_handler(commands=['start'])
def start(message: Message):
    """Обработка команды /start"""
    chat_id = message.chat.id
    username = message.from_user.username
    
    if username not in Config.ADMINS:
        bot.send_message(chat_id, "⛔ У вас нет доступа к этому боту.")
        logger.log(f"Попытка доступа от пользователя {username}", 'warning')
        return
    
    bot.send_message(
        chat_id,
        "👋 Добро пожаловать в NS Logger!\n"
        "Этот бот позволяет управлять логами других ваших ботов.\n"
        "Выберите действие:",
        reply_markup=Keyboards.main_menu()
    )
    logger.log(f"Пользователь {username} начал работу с ботом")

@bot.message_handler(func=lambda message: message.text == "📋 Список ботов")
def list_bots(message: Message):
    """Обработка запроса списка ботов"""
    chat_id = message.chat.id
    username = message.from_user.username
    
    if username not in Config.ADMINS:
        bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
        return
    
    bots = db.get_bot_list()
    if not bots:
        bot.send_message(
            chat_id,
            "Нет доступных ботов. Сначала добавьте бота.",
            reply_markup=Keyboards.main_menu()
        )
        return
    
    bot.send_message(
        chat_id,
        "🤖 Список ваших ботов:",
        reply_markup=Keyboards.bot_list(bots)
    )

# Обработчик для выбора бота в обычном режиме
@bot.message_handler(func=lambda message:
    message.text.startswith("🤖 ") and
    not bot_management._get_state(message.chat.id).get('state') == 'admin_management')
def handle_bot_selected(message: Message):
    """Обработка обычного выбора бота"""
    bot_name = message.text[2:]
    bot.send_message(
        message.chat.id,
        f"Выбран бот: {bot_name}",
        reply_markup=Keyboards.bot_actions(bot_name)
    )

# Обработчик для выбора бота в режиме управления админами
@bot.message_handler(func=lambda message:
    message.text.startswith("🤖 ") and
    bot_management._get_state(message.chat.id).get('state') == 'admin_management')
def handle_bot_selected_for_admin(message: Message):
    """Обработка выбора бота для управления админами"""
    bot_management.handle_bot_selection_for_admin(message)

@bot.message_handler(func=lambda message: message.text.startswith("📄 Логи "))
def handle_show_logs(message: Message):
    """Обработка запроса показа логов"""
    chat_id = message.chat.id
    text = message.text
    
    # Извлекаем имя бота и количество строк
    if "(20 строк)" in text:
        bot_name = text.replace("📄 Логи ", "").replace(" (20 строк)", "")
        lines_count = 20
    elif "(50 строк)" in text:
        bot_name = text.replace("📄 Логи ", "").replace(" (50 строк)", "")
        lines_count = 50
    else:
        bot.send_message(chat_id, "❌ Неверный формат команды.")
        return
    
    log_management.handle_bot_logs(message, bot_name, lines_count)

@bot.message_handler(func=lambda message: message.text.startswith("📥 Скачать логи "))
def handle_download_logs(message: Message):
    """Обработка запроса скачивания логов"""
    bot_name = message.text.replace("📥 Скачать логи ", "")
    log_management.handle_download_logs(message, bot_name)

@bot.message_handler(func=lambda message: message.text == "➕ Добавить бота")
def handle_add_bot(message: Message):
    """Обработка запроса добавления бота"""
    bot_management.handle_add_bot(message)

# Остальные обработчики состояний
@bot.message_handler(func=lambda message:
    bot_management._get_state(message.chat.id).get('state') == 'waiting_for_bot_name')
def handle_bot_name_input(message: Message):
    if message.text == "🔙 Назад":
        bot_management.handle_back(message)
    else:
        bot_management.handle_bot_name(message)

@bot.message_handler(func=lambda message:
    bot_management._get_state(message.chat.id).get('state') == 'waiting_for_log_path')
def handle_log_path_input(message: Message):
    if message.text == "🔙 Назад":
        bot_management.handle_back(message)
    else:
        bot_management.handle_log_path(message)

@bot.message_handler(func=lambda message:
    bot_management._get_state(message.chat.id).get('state') == 'waiting_for_new_admin')
def handle_new_admin_input(message: Message):
    if message.text == "🔙 Назад":
        bot_management.handle_back(message)
    else:
        bot_management.handle_new_admin(message)

@bot.message_handler(func=lambda message:
    bot_management._get_state(message.chat.id).get('state') == 'waiting_for_admin_to_remove')
def handle_admin_to_remove_input(message: Message):
    if message.text == "🔙 Назад":
        bot_management.handle_back(message)
    else:
        bot_management.handle_admin_to_remove(message)

@bot.message_handler(func=lambda message: message.text.startswith("❌ Удалить "))
def handle_remove_bot(message: Message):
    """Обработка запроса удаления бота"""
    bot_name = message.text.replace("❌ Удалить ", "")
    bot_management.handle_remove_bot(message, bot_name)

@bot.message_handler(func=lambda message: message.text == "👥 Управление админами")
def handle_admin_management(message: Message):
    """Обработка запроса управления админами"""
    bot_management.handle_admin_management(message)

@bot.message_handler(func=lambda message:
message.text.startswith("👥 Список админов ") or
message.text.startswith("➕ Добавить админа ") or
message.text.startswith("➖ Удалить админа "))
def handle_bot_admin_actions(message: Message):
    """Обработка действий с админами бота"""
    if message.text.startswith("👥 Список админов "):
        bot_name = message.text.replace("👥 Список админов ", "")
        admins = db.get_bot_admins(bot_name)
        if admins:
            bot.reply_to(message,
                         f"Администраторы бота {bot_name}:\n" +
                         "\n".join(f"• @{admin}" for admin in admins),
                         reply_markup=Keyboards.admin_actions(bot_name))
        else:
            bot.reply_to(message,
                         f"У бота {bot_name} нет администраторов",
                         reply_markup=Keyboards.admin_actions(bot_name))

    elif message.text.startswith("➕ Добавить админа "):
        bot_name = message.text.replace("➕ Добавить админа ", "")
        bot_management.handle_add_admin(message, bot_name)

    elif message.text.startswith("➖ Удалить админа "):
        bot_name = message.text.replace("➖ Удалить админа ", "")
        bot_management.handle_remove_admin(message, bot_name)

@bot.message_handler(func=lambda message: message.text.startswith("➕ Добавить админа "))
def handle_add_admin(message: Message):
    """Обработка добавления админа"""
    bot_name = message.text.replace("➕ Добавить админа ", "")
    bot_management.handle_add_admin(message, bot_name)

@bot.message_handler(func=lambda message: message.text.startswith("➖ Удалить админа "))
def handle_remove_admin(message: Message):
    """Обработка удаления админа"""
    bot_name = message.text.replace("➖ Удалить админа ", "")
    bot_management.handle_remove_admin(message, bot_name)

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def handle_back(message: Message):
    """Обработка кнопки 'Назад'"""
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Главное меню:",
        reply_markup=Keyboards.main_menu()
    )

@bot.message_handler(func=lambda message:
    bot_management._get_state(message.chat.id).get('state') == 'admin_management' and
    message.text.startswith("🤖 "))
def handle_bot_selected_for_admin_management(message: Message):
    """Обработка выбора бота для управления админами"""
    bot_name = message.text[2:]
    bot.send_message(
        message.chat.id,
        f"Выбран бот: {bot_name}\nВыберите действие с администраторами:",
        reply_markup=Keyboards.admin_actions(bot_name)
    )
    bot_management._clear_state(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "⚙️ Настройки")
def handle_settings(message: Message):
    """Обработка кнопки настроек"""
    chat_id = message.chat.id
    username = message.from_user.username

    if username not in Config.ADMINS:
        bot.send_message(chat_id, "⛔ У вас нет прав доступа к настройкам")
        return

    bot.send_message(
        chat_id,
        "⚙️ <b>Настройки бота</b>\n\n"
        "Выберите действие:",
        parse_mode='HTML',
        reply_markup=Keyboards.settings_menu()
    )

@bot.message_handler(func=lambda message: message.text in ["🔙 Назад", "Назад в меню"])
def handle_back(message: Message):
    """Обработка кнопки Назад"""
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Главное меню:",
        reply_markup=Keyboards.main_menu()
    )


@bot.message_handler(func=lambda message: message.text == "👥 Управление глобальными админами")
def handle_global_admins(message: Message):
    bot_management.handle_global_admins(message)

@bot.message_handler(func=lambda message:
bot_management._get_state(message.chat.id).get('state') == 'waiting_for_global_admins')
def handle_new_global_admins(message: Message):
    """Обработка ввода новых глобальных админов"""
    if message.text == "🔙 Назад":
        bot_management._clear_state(message.chat.id)
        handle_settings(message)  # Возврат в меню настроек
        return

    # Здесь должна быть логика обновления списка админов
    # Например, сохранение в .env файл
    new_admins = [name.strip() for name in message.text.split(',')]

    # Обновляем конфиг
    Config.ADMINS = new_admins
    bot.send_message(
        message.chat.id,
        "✅ Список глобальных админов обновлен!",
        reply_markup=Keyboards.settings_menu()
    )
    bot_management._clear_state(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def handle_statistics(message: Message):
    """Обработка кнопки статистики"""
    chat_id = message.chat.id
    username = message.from_user.username

    if username not in Config.ADMINS:
        bot.send_message(chat_id, "⛔ У вас нет прав доступа к статистике")
        return

    # Получаем статистику из базы данных
    bot_count = len(db.get_bot_list())
    total_admins = sum(len(db.get_bot_admins(bot)) for bot in db.get_bot_list())

    bot.send_message(
        chat_id,
        f"📊 <b>Статистика бота</b>\n\n"
        f"• Всего ботов в системе: {bot_count}\n"
        f"• Всего администраторов: {total_admins}\n"
        f"• Глобальных админов: {len(Config.ADMINS)}",
        parse_mode='HTML',
        reply_markup=Keyboards.settings_menu()
    )

@bot.message_handler(func=lambda message:
bot_management._get_state(message.chat.id).get('state') == 'waiting_for_global_admins' and
message.text != "📊 Статистика")  # Добавляем исключение
def handle_new_global_admins(message: Message):
    """Обработка ввода новых глобальных админов"""
    if message.text == "🔙 Назад":
        bot_management._clear_state(message.chat.id)
        handle_settings(message)
        return

    new_admins = [name.strip() for name in message.text.split(',') if name.strip()]

    # Обновляем конфиг (здесь должна быть логика сохранения в .env)
    Config.ADMINS = new_admins

    bot.send_message(
        message.chat.id,
        f"✅ Список глобальных админов обновлен:\n{', '.join(f'@{admin}' for admin in new_admins)}",
        reply_markup=Keyboards.settings_menu()
    )
    bot_management._clear_state(message.chat.id)

if __name__ == '__main__':
    # Проверка конфигурации перед запуском
    Config.check_config()
    
    logger.log("NS Logger запущен")
    bot.infinity_polling()