from telebot import types

from config import Config
from database import db
from keyboards import Keyboards
from logger import logger


class BotManagement:
    def __init__(self, bot):
        self.waiting_for_new_admin = None
        self.waiting_for_admin_to_remove = None
        self.bot = bot
        # Используем словарь для хранения состояний
        self.user_states = {}  # {chat_id: {'state': 'waiting_for_X', 'data': {...}}}

    def _set_state(self, chat_id, state, data=None):
        """Установка состояния пользователя"""
        self.user_states[chat_id] = {
            'state': state,
            'data': data or {}
        }

    def _get_state(self, chat_id):
        """Получение состояния пользователя"""
        return self.user_states.get(chat_id, {})

    def _clear_state(self, chat_id):
        """Очистка состояния пользователя"""
        if chat_id in self.user_states:
            del self.user_states[chat_id]

    def handle_add_bot(self, message: types.Message):
        """Обработка команды добавления бота"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        self._set_state(chat_id, 'waiting_for_bot_name')
        self.bot.send_message(
            chat_id,
            "Введите имя нового бота:",
            reply_markup=Keyboards.back_button()
        )

    def handle_bot_name(self, message: types.Message):
        """Обработка ввода имени бота"""
        chat_id = message.chat.id
        bot_name = message.text

        if bot_name == "🔙 Назад":
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Добавление бота отменено.",
                reply_markup=Keyboards.main_menu()
            )
            return

        self._set_state(chat_id, 'waiting_for_log_path', {'bot_name': bot_name})
        self.bot.send_message(
            chat_id,
            f"Введите путь к логам для бота {bot_name}:",
            reply_markup=Keyboards.back_button()
        )

    def handle_log_path(self, message: types.Message):
        """Обработка ввода пути к логам"""
        chat_id = message.chat.id
        log_path = message.text

        if log_path == "🔙 Назад":
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Добавление бота отменено.",
                reply_markup=Keyboards.main_menu()
            )
            return

        state = self._get_state(chat_id)
        bot_name = state.get('data', {}).get('bot_name')

        if not bot_name:
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Ошибка: не найдено имя бота. Начните заново.",
                reply_markup=Keyboards.main_menu()
            )
            return

        if db.add_bot(bot_name, log_path, message.from_user.username):
            self.bot.send_message(
                chat_id,
                f"✅ Бот {bot_name} успешно добавлен!\nПуть к логам: {log_path}",
                reply_markup=Keyboards.main_menu()
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Бот с именем {bot_name} уже существует!",
                reply_markup=Keyboards.main_menu()
            )

        self._clear_state(chat_id)

    def handle_add_admin(self, message: types.Message, bot_name: str):
        """Обработка добавления админа"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        self._set_state(chat_id, 'waiting_for_new_admin', {'bot_name': bot_name})
        self.bot.send_message(
            chat_id,
            f"Введите username нового администратора для бота {bot_name} (без @):",
            reply_markup=Keyboards.back_button()
        )

    def handle_new_admin(self, message: types.Message):
        """Обработка ввода username нового админа"""
        chat_id = message.chat.id
        new_admin = message.text

        if new_admin == "🔙 Назад":
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Добавление администратора отменено.",
                reply_markup=Keyboards.main_menu()
            )
            return

        state = self._get_state(chat_id)
        bot_name = state.get('data', {}).get('bot_name')

        if not bot_name:
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Ошибка: не найдено имя бота.",
                reply_markup=Keyboards.main_menu()
            )
            return

        if db.add_admin(bot_name, new_admin):
            self.bot.send_message(
                chat_id,
                f"✅ Пользователь @{new_admin} добавлен как администратор для бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Пользователь @{new_admin} уже является администратором для бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )

        self._clear_state(chat_id)

    def handle_remove_admin(self, message: types.Message, bot_name: str):
        """Обработка удаления админа"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        admins = db.get_bot_admins(bot_name)
        if not admins:
            self.bot.send_message(
                chat_id,
                f"У бота {bot_name} нет администраторов.",
                reply_markup=Keyboards.main_menu()
            )
            return

        self.bot.send_message(
            chat_id,
            f"Введите username администратора для удаления из бота {bot_name}:",
            reply_markup=Keyboards.back_button()
        )
        self.waiting_for_admin_to_remove[chat_id] = bot_name

    def handle_admin_to_remove(self, message: types.Message):
        """Обработка ввода username админа для удаления"""
        chat_id = message.chat.id
        admin_to_remove = message.text

        if admin_to_remove == "🔙 Назад":
            del self.waiting_for_admin_to_remove[chat_id]
            self.bot.send_message(
                chat_id,
                "Удаление администратора отменено.",
                reply_markup=Keyboards.main_menu()
            )
            return

        bot_name = self.waiting_for_admin_to_remove.get(chat_id)
        if not bot_name:
            self.bot.send_message(
                chat_id,
                "Ошибка: не найдено имя бота.",
                reply_markup=Keyboards.main_menu()
            )
            return

        if db.remove_admin(bot_name, admin_to_remove):
            self.bot.send_message(
                chat_id,
                f"✅ Пользователь @{admin_to_remove} удален из администраторов бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Пользователь @{admin_to_remove} не является администратором бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )

        del self.waiting_for_admin_to_remove[chat_id]

    def handle_back(self, message: types.Message):
        """Обработка кнопки 'Назад'"""
        chat_id = message.chat.id
        self._clear_state(chat_id)
        self.bot.send_message(
            chat_id,
            "Главное меню:",
            reply_markup=Keyboards.main_menu()
        )

    def handle_remove_admin(self, message: types.Message, bot_name: str):
        """Обработка удаления админа"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        admins = db.get_bot_admins(bot_name)
        if not admins:
            self.bot.send_message(
                chat_id,
                f"У бота {bot_name} нет администраторов.",
                reply_markup=Keyboards.main_menu()
            )
            return

        self._set_state(chat_id, 'waiting_for_admin_to_remove', {'bot_name': bot_name})
        self.bot.send_message(
            chat_id,
            f"Введите username администратора для удаления из бота {bot_name}:",
            reply_markup=Keyboards.back_button()
        )

    def handle_admin_to_remove(self, message: types.Message):
        """Обработка ввода админа для удаления"""
        chat_id = message.chat.id
        admin_to_remove = message.text

        if admin_to_remove == "🔙 Назад":
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Удаление администратора отменено.",
                reply_markup=Keyboards.main_menu()
            )
            return

        state = self._get_state(chat_id)
        bot_name = state.get('data', {}).get('bot_name')

        if not bot_name:
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Ошибка: не найдено имя бота.",
                reply_markup=Keyboards.main_menu()
            )
            return

        if db.remove_admin(bot_name, admin_to_remove):
            self.bot.send_message(
                chat_id,
                f"✅ Пользователь @{admin_to_remove} удален из администраторов бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Пользователь @{admin_to_remove} не является администратором бота {bot_name}!",
                reply_markup=Keyboards.main_menu()
            )

        self._clear_state(chat_id)

    def handle_admin_management(self, message: types.Message):
        """Обработка входа в меню управления админами"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        bots = db.get_bot_list()
        if not bots:
            self.bot.send_message(
                chat_id,
                "Нет доступных ботов. Сначала добавьте бота.",
                reply_markup=Keyboards.main_menu()
            )
            return

        self._set_state(chat_id, 'admin_management')
        self.bot.send_message(
            chat_id,
            "Выберите бота для управления админами:",
            reply_markup=Keyboards.bot_list(bots)
        )

    def handle_bot_selection_for_admin(self, message: types.Message):
        """Обработка выбора бота в контексте управления админами"""
        chat_id = message.chat.id
        bot_name = message.text[2:]  # Убираем "🤖 " в начале

        self.bot.send_message(
            chat_id,
            f"Управление администраторами бота {bot_name}:",
            reply_markup=Keyboards.admin_actions(bot_name)
        )
        self._clear_state(chat_id)

    def handle_global_admins(self, message: types.Message):
        """Обработка управления глобальными админами"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для этой команды")
            return

        current_admins = ", ".join(f"@{admin}" for admin in Config.ADMINS)
        self.bot.send_message(
            chat_id,
            f"Текущие глобальные админы:\n{current_admins}\n\n"
            "Отправьте список новых админов через запятую (только username, без @):",
            reply_markup=Keyboards.back_button()
        )
        self._set_state(chat_id, 'waiting_for_global_admins')

    def handle_remove_bot(self, message: types.Message, bot_name: str):
        """Обработка удаления бота"""
        chat_id = message.chat.id
        username = message.from_user.username

        if username not in Config.ADMINS:
            self.bot.send_message(chat_id, "⛔ У вас нет прав для выполнения этой команды.")
            return

        # Создаем клавиатуру подтверждения
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton(f"✅ Да, удалить {bot_name}"),
            types.KeyboardButton("❌ Отмена")
        )

        self.bot.send_message(
            chat_id,
            f"Вы уверены, что хотите удалить бота {bot_name}?",
            reply_markup=markup
        )
        self._set_state(chat_id, 'confirm_bot_removal', {'bot_name': bot_name})

    def handle_confirm_removal(self, message: types.Message):
        """Обработка подтверждения удаления бота"""
        chat_id = message.chat.id
        state = self._get_state(chat_id)
        bot_name = state.get('data', {}).get('bot_name')

        if not bot_name:
            self._clear_state(chat_id)
            self.bot.send_message(
                chat_id,
                "Ошибка: не найдено имя бота.",
                reply_markup=Keyboards.main_menu()
            )
            return

        if message.text == f"✅ Да, удалить {bot_name}":
            if db.remove_bot(bot_name):
                self.bot.send_message(
                    chat_id,
                    f"✅ Бот {bot_name} успешно удален!",
                    reply_markup=Keyboards.main_menu()
                )
            else:
                self.bot.send_message(
                    chat_id,
                    f"❌ Не удалось удалить бота {bot_name}!",
                    reply_markup=Keyboards.main_menu()
                )
        else:
            self.bot.send_message(
                chat_id,
                "Удаление отменено.",
                reply_markup=Keyboards.main_menu()
            )

        self._clear_state(chat_id)
