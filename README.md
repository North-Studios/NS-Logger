# 🤖 NS Logger Bot v3.1 (nsl-bot)

Telegram bot for viewing and managing logs of other bots. Provides secure access to logs through a role and permission system.

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

## 🗃️ Data Structure

### Configuration Files

```
data/
├── bots_data.json    # Info about bots and their local admins
├── users.json        # User data (ranks, bans, warnings)
└── admins.json       # Lists of operators and global admins
```

### File Formats

**bots\_data.json**:

```json
{
  "bot_name": {
    "ladmins": ["username1", "username2"]
  }
}
```

**users.json**:

```json
{
  "username": {
    "id": 123456789,
    "first_name": "Name",
    "rank": "user",
    "banned": false,
    "warns": 0
  }
}
```

**admins.json**:

```json
{
  "operators": ["operator_username"],
  "global_admins": ["admin1", "admin2"]
}
```

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

Manually add the username to the `operators` section in `admins.json`.

### Add a Global Admin

Manually add the username to the `global_admins` section in `admins.json`.

### Assign a Local Admin

Add the username under the `ladmins` section for the desired bot in `bots_data.json`.

### Register a New User

A user is automatically registered when using the `/start` command for the first time.

---

## 📊 Logging

The bot logs all actions in detail:

* `logs/nsl-bot.log` — logs of the NS Logger bot itself.
* `logs/bot_name.log` — logs of other bots (should be created separately).

---

## 🚀 Highlights

* **Automatic creation** of required files and directories.
* **Error handling** during file read/write.
* **Message overflow protection** (auto-trimming long logs).
* **Permission check** for every action.
* **Support for Russian-language interface.**

---

## 🆘 Support

If issues occur:

1. Check access rights in JSON files.
2. Ensure log files exist and are readable.
3. Check bot logs in `logs/nsl-bot.log`.

---

**Version:** 3.1
