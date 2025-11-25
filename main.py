import os
import asyncio
import tempfile
import base64
import json
import csv
import sys
import threading
import time

from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from html import escape

SESSION_NAME = "tg_backup"
OUTPUT_HTML = "telegram_entities_backup.html"
OUTPUT_JSON = "telegram_entities_backup.json"
OUTPUT_CSV = "telegram_entities_backup.csv"


def load_secrets(file_path="secrets.txt"):
    api_id = None
    api_hash = None

    if not os.path.exists(file_path):
        print(f"[ERROR] secrets.txt not found. Please create it.")
        exit(1)

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("API_ID="):
                api_id = line.split("=", 1)[1].strip()
            elif line.startswith("API_HASH="):
                api_hash = line.split("=", 1)[1].strip()

    if not api_id or not api_hash:
        print("[ERROR] secrets.txt is missing API_ID or API_HASH")
        exit(1)

    try:
        api_id = int(api_id)
    except:
        print("[ERROR] API_ID must be an integer")
        exit(1)

    return api_id, api_hash



API_ID, API_HASH = load_secrets()

print(API_ID, API_HASH)

# --------------------- SPINNER ---------------------
spinner_running = False
def spinner(msg="Working"):
    spinner_icons = ["|", "/", "-", "\\"]
    i = 0
    while spinner_running:
        sys.stdout.write(f"\r{msg}... {spinner_icons[i % 4]}")
        sys.stdout.flush()
        i += 1
        time.sleep(0.12)
    sys.stdout.write("\r" + " " * 40 + "\r")


# --------------------- HELPERS ---------------------
def bytes_to_data_uri(data: bytes, mime="image/jpeg"):
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def html_header():
    return """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Telegram Backup</title>
<style>
/* ---- BODY & CONTAINER ---- */
body {
    font-family: 'Segoe UI', Roboto, sans-serif;
    background: #e6ecf0;
    margin:0;
    padding:0;
}
.container {
    max-width: 800px;
    width: 100%;
    margin: auto;
    padding: 10px;
}

/* ---- TELEGRAM-STYLE ITEM ---- */
.item {
    background: #ffffff;
    padding: 12px 14px;
    border-radius: 12px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: background 0.2s;
}
.item:hover {
    background: #f0f7ff;
}

/* ---- AVATAR ---- */
.item img {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    margin-right: 14px;
    object-fit: cover;
    flex-shrink: 0;
}

/* ---- INFO SECTION ---- */
.item .info {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-width: 150px;
    overflow-wrap: anywhere;
}
.title {
    font-size: 16px;
    font-weight: 600;
    color: #111;
}
.subtitle {
    font-size: 13px;
    color: #8899a6;
    margin-top: 2px;
}
.bio {
    font-size: 13px;
    color: #444;
    margin-top: 4px;
    line-height: 1.4;
}

/* ---- FALLBACK CIRCLE (for no avatar) ---- */
.avatar-fallback {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: #dfe8ee;
    margin-right: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #555;
    flex-shrink: 0;
}

/* ---- MOBILE RESPONSIVE ---- */
@media screen and (max-width: 480px) {
    .item {
        flex-direction: row; /* keeps row, avatars small */
        padding: 10px;
    }
    .item img, .avatar-fallback {
        width: 48px;
        height: 48px;
        margin-right: 10px;
    }
    .title { font-size: 16px; }
    .subtitle, .bio { font-size: 13px; }
}

/* ---- HEADER ---- */
h2 {
    text-align: center;
    margin: 20px 0;
    font-weight: 600;
    color: #111;
}
</style>
</head>
<body>
<div class="container">
<h2>Telegram Backup</h2>
"""

def html_footer():
    return "</div></body></html>"


def safe_bio_text(b):
    if not b:
        return ""
    return escape(b.strip().replace("\n", "<br>"))


# --------------------- MAIN SCRIPT ---------------------
async def main():
    # ---- Ask user what exports to create ----
    include_contacts = input("Backup contacts you have chatted with? (y/n): ").strip().lower() == "y"
    export_json = input("Export also as JSON? (y/n): ").strip().lower() == "y"
    export_csv = input("Export also as CSV? (y/n): ").strip().lower() == "y"

    # ---- LOGIN PHASE: NO SPINNER (prevents input being erased) ----
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Please enter your phone number (international format, e.g. +123456789):")
        phone = input("> ").strip()
        try:
            await client.send_code_request(phone)
        except Exception as e:
            print("Failed to send code request:", e)
            return

        print("Enter the login code Telegram sent you:")
        code = input("> ").strip()
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            # If 2FA password is enabled, Telethon raises SessionPasswordNeededError
            from telethon.errors import SessionPasswordNeededError
            if isinstance(e, SessionPasswordNeededError):
                pw = input("Two-step enabled. Enter your account password: ")
                await client.sign_in(password=pw)
            else:
                print("Sign-in failed:", e)
                return

    print("\nLogin complete.\n")

    # ---- Start spinner for network heavy work ----
    global spinner_running
    spinner_running = True
    t = threading.Thread(target=spinner, args=("Fetching dialogs",))
    t.start()

    # ---- Fetch dialogs ----
    try:
        dialogs = await client.get_dialogs()
    except Exception as e:
        spinner_running = False
        t.join()
        print("Failed to fetch dialogs:", e)
        return

    spinner_running = False
    t.join()
    print(f"Found {len(dialogs)} dialogs.\nProcessing...  ")

    # ---- Prepare helpers & imports used below ----
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.functions.channels import GetFullChannelRequest
    from telethon.tl.functions.messages import GetFullChatRequest
    from telethon.tl.types import User as TlUser, Channel as TlChannel, Chat as TlChat

    results = []

    # ---- Process each dialog ----
    for d in dialogs:
        ent = d.entity

        # decide inclusion
        is_channel = isinstance(ent, TlChannel)
        is_group = isinstance(ent, TlChat)
        is_user = isinstance(ent, TlUser)
        is_bot = is_user and getattr(ent, "bot", False)

        if not (is_channel or is_group or is_bot or (is_user and include_contacts)):
            continue

        # name/title
        name = getattr(ent, "title", None) or \
               (" ".join(filter(None, [getattr(ent, "first_name", ""), getattr(ent, "last_name", "")])).strip() if is_user else None) or \
               getattr(ent, "username", None) or "Unknown"

        username = getattr(ent, "username", None)
        tg_link = f"https://t.me/{username}" if username else None
        fallback_note = "(no public link)"

        # ---- SAFE BIO / DESCRIPTION extraction ----
        bio = ""
        try:
            if is_channel:
                try:
                    full = await client(GetFullChannelRequest(ent))
                    bio = (getattr(full.full_chat, "about", None) or "")  # channels/supergroups
                except:
                    bio = ""
            elif is_group:
                try:
                    full = await client(GetFullChatRequest(ent.id))
                    bio = (getattr(full.full_chat, "about", None) or "")
                except:
                    bio = ""
            elif is_user:
                try:
                    full = await client(GetFullUserRequest(ent))
                    # full_user.bot_info.description exists for bots
                    full_user = getattr(full, "full_user", None)
                    if getattr(full_user, "bot", False) and getattr(full_user, "bot_info", None):
                        # bot_info may contain .description or .description may be nested
                        bot_info = getattr(full_user, "bot_info", None)
                        bio = getattr(bot_info, "description", "") or ""
                    else:
                        bio = getattr(full_user, "about", "") or ""
                except:
                    bio = ""
        except Exception:
            bio = ""

        # ---- Profile photo (embedded base64) ----
        photo_data_uri = None
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"pf_{ent.id}.jpg")
            file = await client.download_profile_photo(ent, file=tmp)
            if file:
                with open(file, "rb") as f:
                    photo_data_uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")
                try:
                    os.remove(file)
                except:
                    pass
        except Exception:
            photo_data_uri = None

        # ---- Create a safe link for HTML clicks (if no username, keep fallback) ----
        html_link = tg_link or "#"  # clicking will open '#' (no-op) for items without public link

        results.append({
            "id": ent.id,
            "name": name,
            "username": username or "",
            "link": tg_link or "",
            "link_available": bool(tg_link),
            "fallback": fallback_note if not tg_link else "",
            "bio": bio or "",
            "type": ("channel" if is_channel else "group" if is_group else "bot" if is_bot else "user"),
            "photo": photo_data_uri
        })

    # ---- Build HTML output ----
    html_parts = []
    html_parts.append(html_header())

    for item in results:
        disp_photo = item["photo"] if item["photo"] else ""
        photo_html = f'<img src="{disp_photo}" alt="avatar" />' if disp_photo else f"<div style='width:54px;height:54px;border-radius:50%;background:#dfe8ee;display:flex;align-items:center;justify-content:center;font-weight:bold;margin-right:14px'>{escape(item['name'][0])}</div>"
        link_for_click = item["link"] if item["link_available"] else "#"

        bio_html = escape(item["bio"]).replace("\n", "<br>") if item["bio"] else ""

        html_parts.append(
            f'''
<div class="item" onclick="if('{link_for_click}'!=='#') window.open('{link_for_click}', '_blank')">
    {photo_html}
    <div>
        <div class="title">{escape(item["name"])}</div>
        <div class="subtitle">{("@"+escape(item["username"])) if item["username"] else "(no username)"}</div>
        <div class="bio">{bio_html if bio_html else ""}</div>
        <div class="subtitle">{escape(item["fallback"]) if item["fallback"] else ""}</div>
    </div>
</div>
'''
        )

    html_parts.append(html_footer())
    html_text = "\n".join(html_parts)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_text)

    print(f"\nHTML saved → {OUTPUT_HTML}")

    # ---- Optional JSON export ----
    if export_json:
        try:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"JSON saved → {OUTPUT_JSON}")
        except Exception as e:
            print("Failed to write JSON:", e)

    # ---- Optional CSV export ----
    if export_csv:
        try:
            with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "name", "username", "link", "bio", "type"])
                for x in results:
                    writer.writerow([x["id"], x["name"], x["username"], x["link"], x["bio"], x["type"]])
            print(f"CSV saved → {OUTPUT_CSV}")
        except Exception as e:
            print("Failed to write CSV:", e)

    # ---- Done ----
    await client.disconnect()



    print("Backup complete.")

# --------------------- RUN APP ---------------------
if __name__ == "__main__":
    asyncio.run(main())
