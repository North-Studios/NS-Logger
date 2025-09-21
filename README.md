# 🤖 NS Logger Bot v4.1 (nsl-bot)

Telegram bot for viewing and managing logs of other bots. Provides secure access to logs through a role and permission system with SQLite database backend.

---

## ✨ Features

### 📊 Log Viewing

* **View the last 20/50 lines** of logs from any available bot.
* **Download full logs** as a file.
* **Automatic update** of the list of available bots.

### 👥 Roles and Access System

* **Operator (operator)** — full access to all bots and logs.
* **Global Admin (gadmin)** — access to all bots.
* **Local Admin (ladmin)** — access only to assigned bots.
* **User (user)** — basic access (viewing own info only).

### 🔐 Security

* **Permission checks** before each action.
* **Unauthorized access protection** via username.
* **Ban and warning system.**
* **Action logging** for all events.

### ⌨️ User-Friendly Interface

* **Dynamic keyboard** with available bot buttons.
* **Inline buttons** for quick access to functions.
* **Automatic creation** of required directories and files.

### 🗄️ Database Backend

* **SQLite database** for reliable data storage
* **Structured tables** for users, bots, permissions, and bans
* **Automatic database initialization** on first run

---

## ⚙️ Installation and Run

### Requirements

* Python 3.8+
* Telegram Bot Token

### Installation

1. Clone the project:

```bash
git clone <repo_url>
cd nsl-bot
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and configure parameters:

```env
NSL_TOKEN=your_telegram_bot_token
DATA_DIR=data  # Directory for data (default: data)
LOGS_DIR=logs  # Directory for logs (default: logs)
MAX_WARN=3     # Maximum number of warnings
```

4. Run the bot:

```bash
python nsl-bot.py
```

### Build as Executable (Optional)

To create a standalone version:

```bash
pyinstaller --onefile --add-data ".env;." --additional-hooks-dir=. nsl-bot.py
```

---

## 🗃️ Database Structure

### Database Schema

The bot uses SQLite with the following tables:

* **users** - User accounts with basic information
* **bots** - Registered bot information
* **bot_ladmins** - Local admin assignments
* **global_admins** - Global administrator accounts
* **operators** - System operator accounts
* **bans** - User ban records
* **auth_codes** - Authentication codes (for future use)

### Automatic Initialization

The database is automatically initialized on first run with all required tables.

---

## 🎮 Usage

### Main Commands

* **`/start`** — start working with the bot, get a keyboard with available bots.
* **`/me`** — view your account and access rights info.

### Working with the Interface

1. **Select a bot** — click on a bot button (📊 BotName).
2. **View logs** — use inline buttons to view the last 20 or 50 lines.
3. **Download logs** — press "📥 Download logs" to get the full file.
4. **Update list** — press "🔄 Refresh" to update the list of available bots.

---

## 🔧 Access Management

### Add an Operator

Insert username into the `operators` table:

```sql
INSERT INTO operators (username) VALUES ('operator_username');
```

### Add a Global Admin

Insert username into the `global_admins` table:

```sql
INSERT INTO global_admins (username) VALUES ('admin_username');
```

### Assign a Local Admin

Insert record into the `bot_ladmins` table:

```sql
INSERT INTO bot_ladmins (bot_name, username) VALUES ('bot_name', 'admin_username');
```

### Register a New Bot

Insert record into the `bots` table:

```sql
INSERT INTO bots (name, exe_path, username, state, type) 
VALUES ('bot_name', '/path/to/exe', 'bot_username', FALSE, 'Standard');
```

### Register a New User

A user is automatically registered when using the `/start` command for the first time.

---

## 📊 Logging

The bot logs all actions in detail:

* `logs/nsl-bot.log` — logs of the NS Logger bot itself.
* `logs/bot_name.log` — logs of other bots (should be created separately).

---

## 🚀 Highlights

* **Automatic database initialization** with proper table structure
* **SQLite backend** for reliable data storage
* **Role hierarchy system** with proper permission checking
* **Error handling** during database operations
* **Message overflow protection** (auto-trimming long logs)
* **Permission check** for every action
* **Support for Russian-language interface**

---

## 🆘 Support

If issues occur:

1. Check database file permissions in the data directory
2. Ensure log files exist and are readable
3. Check bot logs in `logs/nsl-bot.log`
4. Verify database structure using SQLite browser if needed

---

**Version:** 4.1