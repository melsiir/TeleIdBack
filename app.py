"""
Backup your Telegram joined channels/groups/bots to a single HTML file.
NO messages, NO media (except profile photos), ONLY:
    - profile image
    - name
    - username (if exists)
    - telegram link

Requirements:
    pip install telethon
"""

import os
import asyncio
import tempfile
import base64
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from html import escape

API_ID = 27757051               # <-- replace
API_HASH = "bce7f73b5e5bb1f36b15781639a91aa5"    # <-- replace
SESSION_NAME = "tg_entities_backup"
OUTPUT_HTML = "telegram_entities_backup.html"


def bytes_to_data_uri(data: bytes, mime="image/jpeg"):
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def html_header():
    return """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Telegram Entities Backup</title>
<style>
body { font-family: sans-serif; background:#e6ecf0; margin:0; padding:20px; }
.container { max-width:800px; margin:auto; }
.item { background:white; padding:14px; border-radius:12px; display:flex; align-items:center;
        margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,.1); }
.item img { width:54px; height:54px; border-radius:50%; margin-right:14px; object-fit:cover; }
.title { font-size:16px; font-weight:600; }
.subtitle { font-size:13px; color:#8899a6; }
.link { font-size:13px; margin-top:4px; display:block; text-decoration:none; color:#1181d6; }
</style>
</head>
<body>
<div class="container">
<h2>Your Telegram Joined Entities</h2>
"""


def html_footer():
    return "</div></body></html>"




async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    print("Logged in as:", await client.get_me())

    dialogs = await client.get_dialogs()

    html = [html_header()]

    for d in dialogs:
        ent = d.entity

        # Only include channels, groups & bots
        is_channel = isinstance(ent, Channel)
        is_group = isinstance(ent, Chat)
        is_user_bot = isinstance(ent, User) and ent.bot

        if not (is_channel or is_group or is_user_bot):
            continue

        name = (
            getattr(ent, "title", None)
            or f"{ent.first_name or ''} {ent.last_name or ''}".strip()
            or ent.username
            or "Unknown"
        )

        username = getattr(ent, "username", None)
        link = f"https://t.me/{username}" if username else None

        # Download profile photo
        photo_data_uri = None
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"pf_{ent.id}.jpg")
            file = await client.download_profile_photo(ent, file=tmp)
            if file:
                with open(file, "rb") as f:
                    b = f.read()
                photo_data_uri = bytes_to_data_uri(b)
                os.remove(tmp)
        except:
            pass

        # Build HTML block
        html.append('<div class="item">')
        if photo_data_uri:
            html.append(f'<img src="{photo_data_uri}"/>')
        else:
            # fallback colored circle
            html.append(
                '<div style="width:54px;height:54px;border-radius:50%;'
                'background:#dfe8ee;margin-right:14px;display:flex;'
                'align-items:center;justify-content:center;font-weight:bold;">'
                f'{escape(name[0])}</div>'
            )

        html.append('<div>')
        html.append(f'<div class="title">{escape(name)}</div>')
        if username:
            html.append(f'<div class="subtitle">@{escape(username)}</div>')
        if link:
            html.append(f'<a class="link" href="{link}" target="_blank">{link}</a>')
        html.append('</div></div>')

    html.append(html_footer())

    # Write file
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print("Backup saved:", OUTPUT_HTML)


if __name__ == "__main__":
    asyncio.run(main())
