import os
import json
import logging
from typing import Dict, List, Optional, Tuple
import telebot
from dotenv import load_dotenv
from telebot.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
import time

load_dotenv()

# Configuration
TOKEN = os.getenv('NSL_TOKEN')  # Token from environment variable
DATA_DIR = os.getenv('DATA_DIR', 'data')
LOGS_DIR = os.getenv('LOGS_DIR', 'logs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

BOTS_DATA_PATH = os.path.join(DATA_DIR, 'bots_data.json')
USERS_DATA_PATH = os.path.join(DATA_DIR, 'users.json')
ADMINS_DATA_PATH = os.path.join(DATA_DIR, 'admins.json')

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'nsl-bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nsl-bot')

# Rank translations
RANK_TEXT = {
    'operator': '⚡ Оператор',
    'gadmin': '🔧 Глобальный администратор',
    'ladmin': '🪛 Локальный администратор',
    'user': '👤 Пользователь'
}


def load_json(file_path: str) -> Dict:
    """Load JSON data from file"""
    try:
        if not os.path.exists(file_path):
            # Create empty file if it doesn't exist
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading JSON from {file_path}: {e}. Creating new file.")
        # Create empty file if there's an error
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}


def save_json(file_path: str, data: Dict) -> bool:
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False


def get_user_rank(username: str) -> str:
    """Get user rank from all data sources"""
    users_data = load_json(USERS_DATA_PATH)
    admins_data = load_json(ADMINS_DATA_PATH)

    # Check if user exists
    if username not in users_data:
        return "none"

    # Check operators
    if admins_data.get('operators') and username in admins_data['operators']:
        return 'operator'

    # Check global admins
    if admins_data.get('global_admins') and username in admins_data['global_admins']:
        return 'gadmin'

    # Return user's rank from users.json
    return users_data[username].get('rank', 'user')


def get_user_bots(username: str) -> List[str]:
    """Get list of bots that user has access to"""
    user_rank = get_user_rank(username)
    bots_data = load_json(BOTS_DATA_PATH)

    # Operators and global admins have access to all bots
    if user_rank in ['operator', 'gadmin']:
        return list(bots_data.keys())

    # Local admins have access only to specific bots
    user_bots = []
    for bot_name, bot_info in bots_data.items():
        if username in bot_info.get('ladmins', []):
            user_bots.append(bot_name)

    return user_bots


def is_user_allowed(username: str, user_id: int) -> bool:
    """Check if user is allowed to use the bot"""
    # Users without username are not allowed
    if not username:
        logger.warning(f"User without username (ID: {user_id}) tried to access the bot")
        return False

    users_data = load_json(USERS_DATA_PATH)

    # Users not in the system are not allowed
    if username not in users_data:
        logger.warning(f"User @{username} (ID: {user_id}) not found in system")
        return False

    user_data = users_data[username]

    # Banned users are not allowed
    if user_data.get('banned', False):
        logger.warning(f"Banned user @{username} (ID: {user_id}) tried to access the bot")
        return False

    # Regular users are not allowed
    if user_data.get('rank', 'user') == 'user':
        logger.warning(f"Regular user @{username} (ID: {user_id}) tried to access the bot")
        return False

    return True


def get_log_lines(bot_name: str, num_lines: int) -> Optional[str]:
    """Get last N lines from bot's log file"""
    log_file = os.path.join(LOGS_DIR, f"{bot_name}.log")

    try:
        if not os.path.exists(log_file):
            logger.warning(f"Log file for bot {bot_name} not found at {log_file}")
            return None

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-num_lines:] if len(lines) > num_lines else lines
            return ''.join(last_lines)
    except Exception as e:
        logger.error(f"Error reading log file for bot {bot_name}: {e}")
        return None


def create_main_keyboard(username: str) -> ReplyKeyboardMarkup:
    """Create main keyboard based on user's access level"""
    user_bots = get_user_bots(username)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if not user_bots:
        keyboard.add(KeyboardButton("🔄 Обновить"))
        return keyboard

    # Add buttons for each bot the user has access to
    row = []
    for i, bot_name in enumerate(user_bots):
        row.append(KeyboardButton(f"📊 {bot_name}"))
        if (i + 1) % 2 == 0 or i == len(user_bots) - 1:
            keyboard.add(*row)
            row = []

    # Add utility buttons
    keyboard.add(KeyboardButton("🔄 Обновить"))

    return keyboard


def create_bot_keyboard(bot_name: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for a specific bot"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📃 20 строк", callback_data=f"log_{bot_name}_20"),
        InlineKeyboardButton("📋 50 строк", callback_data=f"log_{bot_name}_50"),
        InlineKeyboardButton("📥 Скачать логи", callback_data=f"download_{bot_name}")
    )

    return keyboard


@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    """Handle /start command"""
    username = message.from_user.username
    user_id = message.from_user.id

    logger.info(f"Received /start from @{username} (ID: {user_id})")

    # Check if user is allowed
    if not is_user_allowed(username, user_id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к этому боту.\n\n"
            "Этот бот предназначен только для администраторов системы.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Register new user if needed
    users_data = load_json(USERS_DATA_PATH)
    if username not in users_data:
        users_data[username] = {
            "id": user_id,
            "first_name": message.from_user.first_name,
            "rank": "user",
            "banned": False,
            "warns": 0
        }
        save_json(USERS_DATA_PATH, users_data)
        logger.info(f"Registered new user @{username} (ID: {user_id})")

    # Send welcome message with keyboard
    user_bots = get_user_bots(username)
    if not user_bots:
        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в NS Logger!\n\n"
            "❌ У вас нет доступа ни к одному боту.\n"
            "Обратитесь к оператору системы для получения прав доступа.",
            reply_markup=create_main_keyboard(username)
        )
    else:
        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в NS Logger!\n\n"
            "Выберите бот для просмотра логов:",
            reply_markup=create_main_keyboard(username)
        )


@bot.message_handler(commands=['me'])
def handle_me(message: Message):
    """Handle /me command"""
    username = message.from_user.username
    user_id = message.from_user.id

    logger.info(f"Received /me from @{username} (ID: {user_id})")

    # Check if user is allowed
    if not is_user_allowed(username, user_id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к этому боту.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Get user data
    users_data = load_json(USERS_DATA_PATH)
    user_data = users_data.get(username, {})

    # Prepare rank text
    rank = user_data.get('rank', 'user')
    rank_text = RANK_TEXT.get(rank, '👤 Пользователь')

    # Prepare banned status
    banned = user_data.get('banned', False)
    banned_status = "✅ Нет" if not banned else "❌ Да"

    # Prepare response based on rank
    if rank in ['gadmin', 'operator']:
        response = (
            "👤 Информация о пользователе\n\n"
            f"📧 Username: @{username}\n"
            f"👨‍💼 Ранг: {rank_text}\n"
            f"🆔 ID: {user_data.get('id', 'N/A')}\n"
            f"📛 Имя: {user_data.get('first_name', 'N/A')}"
        )
    else:
        max_warn = os.getenv('MAX_WARN', 3)
        response = (
            "👤 Информация о пользователе\n\n"
            f"📧 Username: @{username}\n"
            f"👨‍💼 Ранг: {rank_text}\n"
            f"🆔 ID: {user_data.get('id', 'N/A')}\n"
            f"📛 Имя: {user_data.get('first_name', 'N/A')}\n"
            f"📊 Ограничения: {banned_status}\n"
            f"💢 Предупреждения: {user_data.get('warns', 0)}/{max_warn}"
        )

    bot.send_message(message.chat.id, response)



@bot.message_handler(func=lambda message: message.text == "🔄 Обновить")
def handle_refresh(message: Message):
    """Handle refresh button"""
    username = message.from_user.username
    user_id = message.from_user.id

    logger.info(f"Received refresh from @{username} (ID: {user_id})")

    # Check if user is allowed
    if not is_user_allowed(username, user_id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к этому боту.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    user_bots = get_user_bots(username)
    if not user_bots:
        bot.send_message(
            message.chat.id,
            "🔄 Список обновлен!\n\n"
            "❌ У вас по-прежнему нет доступа ни к одному боту.\n"
            "Обратитесь к оператору системы для получения прав доступа.",
            reply_markup=create_main_keyboard(username)
        )
    else:
        bot.send_message(
            message.chat.id,
            "🔄 Список ботов обновлен!",
            reply_markup=create_main_keyboard(username)
        )


@bot.message_handler(func=lambda message: message.text.startswith("📊 "))
def handle_bot_selection(message: Message):
    """Handle bot selection from keyboard"""
    username = message.from_user.username
    user_id = message.from_user.id

    # Extract bot name from button text
    bot_name = message.text[2:]  # Remove "📊 " prefix

    logger.info(f"User @{username} selected bot {bot_name}")

    # Check if user has access to this bot
    user_bots = get_user_bots(username)
    if bot_name not in user_bots:
        logger.warning(f"User @{username} tried to access unauthorized bot {bot_name}")
        bot.send_message(
            message.chat.id,
            f"❌ У вас нет доступа к логам бота {bot_name}."
        )
        return

    # Send bot options
    bot.send_message(
        message.chat.id,
        f"🤖 Выбран бот: {bot_name}\n\n"
        "Выберите действие:",
        reply_markup=create_bot_keyboard(bot_name)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('log_'))
def handle_log_callback(call):
    """Handle log view callback"""
    username = call.from_user.username
    user_id = call.from_user.id

    # Parse callback data
    _, bot_name, num_lines_str = call.data.split('_')
    num_lines = int(num_lines_str)

    logger.info(f"User @{username} requested {num_lines} lines from {bot_name}")

    # Check if user has access to this bot
    user_bots = get_user_bots(username)
    if bot_name not in user_bots:
        logger.warning(f"User @{username} tried to access unauthorized bot {bot_name}")
        bot.answer_callback_query(call.id, "❌ У вас нет доступа к этому боту.")
        return

    # Get log lines
    log_content = get_log_lines(bot_name, num_lines)

    if not log_content:
        bot.answer_callback_query(
            call.id,
            f"❌ Не удалось получить логи бота {bot_name}. Файл не найден или пуст."
        )
        return

    # Send log content as a quote
    try:
        # Truncate if too long for Telegram (4096 characters limit)
        if len(log_content) > 4000:
            log_content = log_content[-4000:]
            logger.warning(f"Truncated log content for {bot_name}")

        bot.send_message(
            call.message.chat.id,
            f"📄 Логи бота {bot_name} (последние {num_lines} строк):\n\n"
            f"<code>{log_content}</code>",
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id, "✅ Логи получены")
    except Exception as e:
        logger.error(f"Error sending log message: {e}")
        bot.answer_callback_query(
            call.id,
            "❌ Ошибка при отправке логов. Возможно, логи слишком длинные."
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('download_'))
def handle_download_callback(call):
    """Handle log download callback"""
    username = call.from_user.username
    user_id = call.from_user.id

    # Parse callback data
    bot_name = call.data.split('_')[1]

    logger.info(f"User @{username} requested download logs from {bot_name}")

    # Check if user has access to this bot
    user_bots = get_user_bots(username)
    if bot_name not in user_bots:
        logger.warning(f"User @{username} tried to download logs from unauthorized bot {bot_name}")
        bot.answer_callback_query(call.id, "❌ У вас нет доступа к этому боту.")
        return

    # Send log file
    log_file = os.path.join(LOGS_DIR, f"{bot_name}.log")

    if os.path.exists(log_file):
        try:
            with open(log_file, 'rb') as f:
                bot.send_document(
                    call.message.chat.id,
                    f,
                    caption=f"📁 Логи бота {bot_name}"
                )
            bot.answer_callback_query(call.id, "✅ Файл логов отправлен")
        except Exception as e:
            logger.error(f"Error sending log file: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при отправке файла")
    else:
        bot.answer_callback_query(call.id, "❌ Файл логов не найден")


@bot.message_handler(func=lambda message: True)
def handle_unknown(message: Message):
    """Handle unknown messages"""
    username = message.from_user.username
    user_id = message.from_user.id

    logger.warning(f"Received unknown message from @{username} (ID: {user_id}): {message.text}")

    bot.send_message(
        message.chat.id,
        "❌ Неизвестная команда.\n\n"
        "Используйте кнопки на клавиатуре для взаимодействия с ботом."
    )


if __name__ == "__main__":
    logger.info("Starting NS Logger bot...")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Logs directory: {LOGS_DIR}")

    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise