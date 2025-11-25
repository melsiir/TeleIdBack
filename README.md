# 📝 Telegram Backup Script
## 🚀 Overview
This Python script lets you backup your Telegram account in style! 🎉
It fetches:
📢 Channels you joined
👥 Groups you are part of
🤖 Bots you interacted with
🧑 Contacts (optional)
No messages or media are downloaded — only links, usernames, descriptions, and bios.
Export your Telegram universe in multiple formats:
🌐 HTML — responsive, Telegram-like UI with embedded profile pictures
📄 JSON — structured for developers or scripts
📊 CSV — perfect for spreadsheets
✨ Features
Fetch all dialogs: channels, groups, bots, and users
Include bio/description, profile photo (embedded in HTML), and Telegram links
Modular: works in terminal or web app integration
Optionally include contacts you messaged
Choose export formats: HTML, JSON, CSV
API credentials stored outside the script in secrets.txt for safety 🔒
🛠 Requirements
- Python 3.10+ 🐍
- Telethon library:

```Bash
pip install telethon

```
# 📝 Setup
1️⃣ Create secrets.txt

```bash

touch secrets.txt


```
Place in the same folder as the script:
API_ID=1234567
API_HASH=0123456789abcdef0123456789abcdef
Get your API_ID and API_HASH from my.telegram.org ✨
Make sure there are no quotes, commas, or extra spaces.
2️⃣ Run the script

```bash
python main.py
```


If it’s your first session, the script asks for your phone number ☎️
Telegram sends a login code to your phone 📩
Enter the code in the terminal 🖊
Optionally, enter 2FA password if prompted 🔑
After login, the script will:
Fetch all your channels, groups, bots, and optionally contacts
Generate backups in selected formats (HTML, JSON, CSV)
3️⃣ Your Backup Files
Generated files appear in the same folder:
backup.html 🌐 — open in browser
backup.json 📄 — structured data
backup.csv 📊 — spreadsheet-ready
The HTML is responsive, looks like Telegram, and works on desktop and mobile! 📱💻
💡 Notes
Profile pictures are embedded in HTML as Base64 — no extra files needed 📸
Large accounts may take a few minutes ⏳
API keys are not stored in the Python script, only in secrets.txt 🔒
To logout/reset session, delete the Telethon session file (e.g., tg_backup.session) 🗑
⚙️ Optional Settings
Include contacts or limit dialogs by editing the script
Choose which export formats to generate: HTML, JSON, CSV
🛠 Troubleshooting
Script stuck on “process…” 😵
Make sure secrets.txt exists with correct keys
Check that API_ID is an integer and API_HASH is valid
Spinner overwriting input 🌀
Spinner is disabled during phone/code input — should not interfere
Connection issues 🌐
Check your internet connection
Verify your API keys are correct

Enjoy backing up your Telegram universe with style! 🚀💖
