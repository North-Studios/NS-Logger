import os
import logging
import sqlite3
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
DB_PATH = os.path.join(DATA_DIR, 'ns_system.db')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

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


def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with required tables"""
    conn = get_db_connection()
    try:
        # Check if tables already exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            logger.info("Database already initialized")
            return

        logger.info("Initializing database...")

        # Create tables (same structure as in the documentation)
        conn.executescript('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                rank TEXT NOT NULL DEFAULT 'user',
                banned BOOLEAN NOT NULL DEFAULT FALSE,
                warns INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE bots (
                name TEXT PRIMARY KEY,
                exe_path TEXT NOT NULL,
                username TEXT NOT NULL,
                state BOOLEAN NOT NULL DEFAULT FALSE,
                type TEXT NOT NULL DEFAULT 'Standard',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE bot_ladmins (
                bot_name TEXT NOT NULL,
                username TEXT NOT NULL,
                PRIMARY KEY (bot_name, username),
                FOREIGN KEY (bot_name) REFERENCES bots (name) ON DELETE CASCADE,
                FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
            );

            CREATE TABLE global_admins (
                username TEXT PRIMARY KEY,
                FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
            );

            CREATE TABLE operators (
                username TEXT PRIMARY KEY,
                FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
            );

            CREATE TABLE bans (
                username TEXT PRIMARY KEY,
                banned_by TEXT NOT NULL,
                banned_at INTEGER NOT NULL,
                ban_time INTEGER NOT NULL DEFAULT 0,
                reason TEXT,
                FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
            );

            CREATE TABLE auth_codes (
                code TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                used BOOLEAN NOT NULL DEFAULT FALSE,
                FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
            );
        ''')
        conn.commit()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


def get_user_rank(username: str) -> str:
    """Get user rank from database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if user is operator
        cursor.execute("SELECT 1 FROM operators WHERE username = ?", (username,))
        if cursor.fetchone():
            return 'operator'

        # Check if user is global admin
        cursor.execute("SELECT 1 FROM global_admins WHERE username = ?", (username,))
        if cursor.fetchone():
            return 'gadmin'

        # Get user's rank from users table
        cursor.execute("SELECT rank FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result['rank'] if result else 'none'

    except Exception as e:
        logger.error(f"Error getting user rank for {username}: {e}")
        return 'none'
    finally:
        conn.close()


def get_user_bots(username: str) -> List[str]:
    """Get list of bots that user has access to"""
    user_rank = get_user_rank(username)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Operators and global admins have access to all bots
        if user_rank in ['operator', 'gadmin']:
            cursor.execute("SELECT name FROM bots")
            return [row['name'] for row in cursor.fetchall()]

        # Local admins have access only to specific bots
        cursor.execute('''
            SELECT b.name 
            FROM bots b 
            JOIN bot_ladmins bl ON b.name = bl.bot_name 
            WHERE bl.username = ?
        ''', (username,))

        return [row['name'] for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error getting user bots for {username}: {e}")
        return []
    finally:
        conn.close()


def is_user_allowed(username: str, user_id: int) -> bool:
    """Check if user is allowed to use the bot"""
    # Users without username are not allowed
    if not username:
        logger.warning(f"User without username (ID: {user_id}) tried to access the bot")
        return False

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if user exists and is not banned
        cursor.execute('''
            SELECT banned, rank FROM users WHERE username = ?
        ''', (username,))

        user_data = cursor.fetchone()
        if not user_data:
            logger.warning(f"User @{username} (ID: {user_id}) not found in system")
            return False

        if user_data['banned']:
            logger.warning(f"Banned user @{username} (ID: {user_id}) tried to access the bot")
            return False

        # Regular users are not allowed
        if user_data['rank'] == 'user':
            logger.warning(f"Regular user @{username} (ID: {user_id}) tried to access the bot")
            return False

        return True

    except Exception as e:
        logger.error(f"Error checking user access for {username}: {e}")
        return False
    finally:
        conn.close()


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


def register_user(username: str, user_id: int, first_name: str) -> bool:
    """Register new user in database"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return True

        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, user_id, first_name, rank, banned, warns)
            VALUES (?, ?, ?, 'user', FALSE, 0)
        ''', (username, user_id, first_name))

        conn.commit()
        logger.info(f"Registered new user @{username} (ID: {user_id})")
        return True

    except Exception as e:
        logger.error(f"Error registering user @{username}: {e}")
        return False
    finally:
        conn.close()


@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    """Handle /start command"""
    username = message.from_user.username
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Unknown"

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
    if not register_user(username, user_id, first_name):
        bot.send_message(
            message.chat.id,
            "❌ Ошибка регистрации. Обратитесь к администратору."
        )
        return

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

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Get user data
        cursor.execute('''
            SELECT user_id, first_name, rank, banned, warns 
            FROM users WHERE username = ?
        ''', (username,))

        user_data = cursor.fetchone()
        if not user_data:
            bot.send_message(message.chat.id, "❌ Пользователь не найден.")
            return

        # Prepare rank text
        rank = get_user_rank(username)  # Get actual rank with hierarchy
        rank_text = RANK_TEXT.get(rank, '👤 Пользователь')

        # Prepare banned status
        banned_status = "✅ Нет" if not user_data['banned'] else "❌ Да"
        response = (
            "👤 Информация о пользователе\n\n"
            f"📧 Username: @{username}\n"
            f"👨‍💼 Ранг: {rank_text}\n"
            f"🆔 ID: {user_data['user_id']}\n"
            f"📛 Имя: {user_data['first_name']}"
        )
        # Prepare response based on rank
        if not rank in ['gadmin', 'operator']:
            max_warn = int(os.getenv('MAX_WARN', 3))
            response += (
                f"\n📊 Ограничения: {banned_status}\n"
                f"💢 Предупреждения: {user_data['warns']}/{max_warn}"
            )

        bot.send_message(message.chat.id, response)

    except Exception as e:
        logger.error(f"Error in /me command for @{username}: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка получения информации.")
    finally:
        conn.close()


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

    # Initialize database
    init_database()

    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise