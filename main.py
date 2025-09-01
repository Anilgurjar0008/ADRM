# ------------------------------------------------------------------
#  Unified Saini-TXT-Direct  (File-1  +  File-2  features)
#  Author: nikhilsainiop
#  Drop-in replacement – no other changes needed
# ------------------------------------------------------------------
import os, re, sys, m3u8, json, time, pytz, asyncio, requests, subprocess
import urllib, urllib.parse, yt_dlp, tgcrypto, cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from logs import logging
from bs4 import BeautifulSoup
import saini as helper
import txthtml                      #  NEW  (for /t2h)
from utils import progress_bar
from vars import (
    API_ID, API_HASH, BOT_TOKEN, OWNER,
    CREDIT, AUTH_USERS, TOTAL_USERS
)
from aiohttp import ClientSession
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import random
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp, aiofiles, zipfile, shutil, ffmpeg

# ------------------------------------------------------------------
#  Bot instance
# ------------------------------------------------------------------
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------------------------------------------------------
#  Global state
# ------------------------------------------------------------------
processing_request = False
cancel_requested   = False
cancel_message     = None

# ------------------------------------------------------------------
#  Configurable defaults   (File-2 additions)
# ------------------------------------------------------------------
caption      = '/cc1'          # /cc1 /cc2 /cc3
endfilename  = '/d'           # suffix for file name
thumb        = '/d'           # thumbnail url
CR           = CREDIT         # footer credit
cwtoken      = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbi'
                'I6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOS'
                'IsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05I'
                'TjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk'
                '0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVc'
                'wd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQw'
                'OSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV'
                '90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21v'
                'ZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi'
                '4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6'
                '-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_'
                '7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs'
                '5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRH'
                'hl1U-0hne4-5fF0aouyu71Y6W0eg')
cptoken      = "cptoken"
pwtoken      = "pwtoken"
vidwatermark = '/d'
raw_text2    = '480'
quality      = '480p'
res          = '854x480'
topic        = '/d'

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url           = "http://master-api-v3.vercel.app/"
api_token         = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX"
                     "3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj"
                     "0hBKSghhxJ3k1GTWoBUbivUe1I")
token_cp          = ('eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5'
                     'SWQiOm51bGx9r')
adda_token        = ("eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkcGthNTQ3MEBnbWFpbC5jb20iLCJhdWQiOiIxNzg2OTYw"
                     "NSIsImlhdCI6MTc0NDk0NDQ2NCwiaXNzIjoiYWRkYTI0Ny5jb20iLCJuYW1lIjoiZHBrYSIsImVtYWls"
                     "IjoiZHBrYTU0NzBAZ21haWwuY29tIiwicGhvbmUiOiI3MzUyNDA0MTc2IiwidXNlcklkIjoiYWRkYS52"
                     "MS41NzMyNmRmODVkZDkxZDRiNDkxN2FiZDExN2IwN2ZjOCIsImxvZ2luQXBpVmVyc2lvbiI6MX0.0QOu"
                     "YFMkCEdVmwMVIPeETa6Kxr70zEslWOIAfC_ylhbku76nDcaBoNVvqN4HivWNwlyT0jkUKjWxZ8AbdorMLg")

photologo = ('https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png')
photoyt   = ('https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png')
photocp   = ('https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg')
photozip  = ('https://envs.sh/cD_.jpg')

# ------------------------------------------------------------------
#  Keyboard helpers
# ------------------------------------------------------------------
BUTTONSCONTACT = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="📞 Contact", url="https://t.me/saini_contact_bot")]]
)
keyboard = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton(text="🛠️ Help", url="https://t.me/+3k-1zcJxINYwNGZl"),
        InlineKeyboardButton(text="🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")
    ]]
)

image_urls = [
    "https://tinypic.host/images/2025/02/07/IMG_20250207_224444_975.jpg",
    "https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png"
]

# ------------------------------------------------------------------
#  AUTH / USER management   (UNCHANGED from File-1 / File-2)
# ------------------------------------------------------------------
@bot.on_message(filters.command("addauth") & filters.private)
async def add_auth_user(c, m):
    if m.chat.id != OWNER:
        return
    try:
        uid = int(m.command[1])
        if uid in AUTH_USERS:
            return await m.reply("**User already authorised.**")
        AUTH_USERS.append(uid)
        await m.reply(f"**Added `{uid}` ✔**")
        await bot.send_message(uid, "<b>Premium granted 🎉</b>")
    except (IndexError, ValueError):
        await m.reply("**Send /addauth user_id**")

@bot.on_message(filters.command("rmauth") & filters.private)
async def rm_auth_user(c, m):
    if m.chat.id != OWNER:
        return
    try:
        uid = int(m.command[1])
        if uid not in AUTH_USERS:
            return await m.reply("**User not found.**")
        AUTH_USERS.remove(uid)
        await m.reply(f"**Removed `{uid}` ✔**")
        await bot.send_message(uid, "<b>Premium revoked ❌</b>")
    except (IndexError, ValueError):
        await m.reply("**Send /rmauth user_id**")

@bot.on_message(filters.command("users") & filters.private)
async def list_auth(c, m):
    if m.chat.id != OWNER:
        return
    ulist = '\n'.join(map(str, AUTH_USERS))
    await m.reply(f"**Authorised Users:**\n{ulist}")

# ------------------------------------------------------------------
#  Broadcast helpers
# ------------------------------------------------------------------
@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast(c, m):
    if m.chat.id != OWNER:
        return
    if not m.reply_to_message:
        return await m.reply("**Reply to any message to broadcast.**")
    ok, fail = 0, 0
    for uid in list(set(TOTAL_USERS)):
        try:
            await m.reply_to_message.copy(uid)
            ok += 1
        except Exception:
            fail += 1
    await m.reply(f"**Broadcast done ✅\nSuccess: {ok}\nFailed: {fail}**")

@bot.on_message(filters.command("broadusers") & filters.private)
async def broadusers(c, m):
    if m.chat.id != OWNER:
        return
    if not TOTAL_USERS:
        return await m.reply("**No users yet.**")
    infos = []
    for uid in list(set(TOTAL_USERS)):
        try:
            u = await c.get_users(uid)
            infos.append(f"[{u.id}](tg://user?id={u.id}) | `{u.first_name}`")
        except:
            infos.append(f"[{uid}](tg://user?id={uid})")
    await m.reply("**Total: {}**\n\n{}".format(len(infos), '\n'.join(infos)))

# ------------------------------------------------------------------
#  Cookies
# ------------------------------------------------------------------
@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(c, m):
    e = await m.reply("**Send the YT cookies .txt file.**")
    msg = await c.listen(m.chat.id)
    if not (msg.document and msg.document.file_name.endswith(".txt")):
        return await m.reply("**Invalid file.**")
    path = await msg.download()
    with open(path) as f, open(cookies_file_path, "w") as t:
        t.write(f.read())
    os.remove(path)
    await e.delete()
    await msg.delete()
    await m.reply("✅ Cookies updated!")

# ------------------------------------------------------------------
#  Text → .txt  (/t2t)
# ------------------------------------------------------------------
@bot.on_message(filters.command("t2t"))
async def text_to_txt(c, m):
    e = await m.reply("**Send text to convert → .txt**")
    inp = await c.listen(m.chat.id)
    if not inp.text:
        return await m.reply("**No text found.**")
    data = inp.text.strip()
    await inp.delete()
    await e.edit("**Send file name or /d**")
    name_msg = await c.listen(m.chat.id)
    fname = name_msg.text if name_msg.text != '/d' else 'txt_file'
    await name_msg.delete()
    await e.delete()
    os.makedirs("downloads", exist_ok=True)
    fpath = f"downloads/{fname}.txt"
    with open(fpath, "w") as f:
        f.write(data)
    await m.reply_document(fpath, caption=f"`{fname}.txt`")
    os.remove(fpath)

# ------------------------------------------------------------------
#  YouTube → .txt  (/y2t)
# ------------------------------------------------------------------
@bot.on_message(filters.command("y2t"))
async def youtube_to_txt(c, m):
    e = await m.reply("**Send YouTube playlist / video link.**")
    msg = await c.listen(m.chat.id)
    link = msg.text.strip()
    await msg.delete()
    await e.delete()
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': cookies_file_path
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(link, download=False)
        title = res.get('title', 'youtube_list')
        out = '\n'.join(f"{e.get('title','No title')}: https://youtu.be/{e['url']}"
                        for e in res.get('entries', [res]))
        fpath = f"downloads/{title}.txt"
        os.makedirs("downloads", exist_ok=True)
        with open(fpath, "w") as f:
            f.write(out)
        await m.reply_document(fpath, caption=f"[Open playlist]({link})")
        os.remove(fpath)
    except Exception as ex:
        await m.reply(f"**Error:** `{ex}`")

# ------------------------------------------------------------------
#  YouTube → .mp3  (/ytm)
# ------------------------------------------------------------------
@bot.on_message(filters.command("ytm"))
async def ytm_handler(c, m):
    global processing_request, cancel_requested
    processing_request = True
    cancel_requested = False
    e = await m.reply("**Send .txt with YouTube links or paste links.**")
    msg = await c.listen(m.chat.id)
    links = []
    if msg.document and msg.document.file_name.endswith(".txt"):
        path = await msg.download()
        with open(path) as f:
            links = [l.strip() for l in f if l.strip()]
        os.remove(path)
    elif msg.text:
        links = [l.strip() for l in msg.text.splitlines() if l.strip()]
    await msg.delete()
    await e.delete()
    if not links:
        return await m.reply("**No valid links.**")
    count = 1
    for url in links:
        if cancel_requested:
            await m.reply("🚦 **Stopped**")
            break
        try:
            oembed = requests.get(f"https://www.youtube.com/oembed?url={url}&format=json").json()
            title = oembed.get('title', 'song').replace("_", " ")
            fname = f"{title[:60]} {CREDIT}"
            prog = await m.reply(f"**[{count:03d}] Downloading → {title}**")
            os.system(f'yt-dlp -x --audio-format mp3 --cookies {cookies_file_path} "{url}" -o "{fname}.mp3"')
            if os.path.exists(f"{fname}.mp3"):
                await m.reply_document(f"{fname}.mp3",
                                       caption=f"**[{count:03d}] {fname}.mp3**\n🔗 {url}\n🌟 {CREDIT}")
                os.remove(f"{fname}.mp3")
            await prog.delete()
        except Exception as ex:
            await m.reply(f"**Failed:** `{ex}`")
        count += 1
    processing_request = False

# ------------------------------------------------------------------
#  .txt → .html  (/t2h)   (NEW from File-2)
# ------------------------------------------------------------------
@bot.on_message(filters.command("t2h"))
async def txt_to_html(c, m):
    e = await m.reply("**Send .txt file for HTML conversion.**")
    msg = await c.listen(m.chat.id)
    if not (msg.document and msg.document.file_name.endswith(".txt")):
        return await m.reply("**Invalid file.**")
    path = await msg.download()
    with open(path) as f:
        urls = txthtml.extract_names_and_urls(f.read())
    videos, pdfs, others = txthtml.categorize_urls(urls)
    html = txthtml.generate_html(os.path.splitext(os.path.basename(path))[0], videos, pdfs, others)
    html_path = path.replace(".txt", ".html")
    with open(html_path, "w") as f:
        f.write(html)
    await m.reply_document(html_path, caption="✅ HTML generated!")
    os.remove(path)
    os.remove(html_path)

# ------------------------------------------------------------------
#  Universal handler (File-2 style)  –  /drm merged here
# ------------------------------------------------------------------
@bot.on_message(filters.private & (filters.document | filters.text))
async def universal_drm(c, m):
    global processing_request, cancel_requested, caption, endfilename, thumb, CR
    processing_request = True
    cancel_requested = False
    uid = m.from_user.id
    lines = []

    if m.document and m.document.file_name.endswith(".txt"):
        if uid not in AUTH_USERS:
            await m.reply("**You are not premium.**")
            return
        path = await m.download()
        with open(path) as f:
            lines = [l.strip() for l in f if l.strip()]
        os.remove(path)
    elif m.text and "://" in m.text:
        lines = [m.text.strip()]
    else:
        return

    links = []
    for l in lines:
        if "://" in l:
            name, url = l.split("://", 1)
            links.append([name.strip(), "https://" + url])

    if not links:
        return await m.reply("**No valid links.**")

    # Ask start index
    e = await m.reply(f"**Found {len(links)} links.**\nSend start index or /d")
    try:
        idx_msg = await c.listen(m.chat.id, timeout=20)
        start = int(idx_msg.text) if idx_msg.text.isdigit() else 1
        await idx_msg.delete()
    except asyncio.TimeoutError:
        start = 1

    # Ask batch name
    await e.edit("**Send batch name or /d**")
    try:
        bn_msg = await c.listen(m.chat.id, timeout=20)
        b_name = bn_msg.text.replace('_', ' ') if bn_msg.text != '/d' else "Batch"
        await bn_msg.delete()
    except asyncio.TimeoutError:
        b_name = "Batch"

    # Ask channel
    await e.edit("**Send channel id or /d**")
    try:
        ch_msg = await c.listen(m.chat.id, timeout=20)
        ch = int(ch_msg.text) if ch_msg.text.lstrip('-').isdigit() else m.chat.id
        await ch_msg.delete()
    except asyncio.TimeoutError:
        ch = m.chat.id
    await e.delete()

    # Pin batch
    if start == 1 and ch != m.chat.id:
        try:
            pin_msg = await c.send_message(ch, f"🎯 **{b_name}**")
            await pin_msg.pin()
        except:
            pass

    # Begin loop
    count = start
    failed = 0
    for i in range(start - 1, len(links)):
        if cancel_requested:
            await m.reply("🚦 **Stopped**")
            break
        name_raw, url = links[i]
        safe_name = re.sub(r'[^\w\s-]', '', name_raw)[:60]
        if endfilename == '/d':
            fname = f"{count:03d} {safe_name}"
        else:
            fname = f"{count:03d} {safe_name} {endfilename}"

        # Build caption
        if topic == '/yes':
            t_match = re.search(r'[\(\[](.*?)[\)\]]', name_raw)
            t_name = t_match.group(1) if t_match else "Topic"
            v_name = re.sub(r'[\(\[].*?[\)\]]', '', name_raw).strip()
            v_name = re.sub(r':.*', '', v_name).strip()
            if caption == '/cc1':
                cap = (f"[🎥]Vid Id : {count:03d}\n**Video Title :** `{v_name} [{quality}].mkv`\n"
                       f"**Batch :** {b_name}\n**Topic :** {t_name}\n**Extracted by** {CR}")
            elif caption == '/cc2':
                cap = (f"——— ✦ {count:03d} ✦ ———\n\n🎞️ **Title :** {v_name}\n"
                       f"**├── Extension : {CR}.mkv**\n**├── Resolution : [{quality}]**\n"
                       f"**📚 Course : {b_name}**\n\n🌟 **Extracted By : {CR}**")
            else:
                cap = f"{count:03d}. {v_name} [{quality}].mkv"
        else:
            cap = f"{count:03d}. {safe_name} [{quality}].mkv"

        # Download & send
        try:
            if "drive.google.com" in url:
                file = await helper.download(url, fname)
                await c.send_document(ch, file, caption=cap)
                os.remove(file)
            elif ".pdf" in url:
                file = f"{fname}.pdf"
                os.system(f'yt-dlp -o "{file}" "{url}"')
                await c.send_document(ch, file, caption=cap)
                os.remove(file)
            elif any(x in url for x in ["mpd", "m3u8", "encrypted", "drm"]):
                # DRM handled by helper
                file = await helper.download_video(url,
                                                   f'yt-dlp -f "best[height<={raw_text2}]" -o "{fname}.mp4" "{url}"',
                                                   fname)
                await helper.send_vid(c, m, cap, file, vidwatermark, thumb, fname, None, ch)
            else:
                file = await helper.download_video(url,
                                                   f'yt-dlp -f "best[height<={raw_text2}]" -o "{fname}.mp4" "{url}"',
                                                   fname)
                await c.send_video(ch, file, caption=cap)
                os.remove(file)
        except Exception as ex:
            await c.send_message(ch, f"**Failed:** {fname}\n`{ex}`")
            failed += 1
        count += 1

    processing_request = False
    await c.send_message(
        ch,
        f"✅ **{b_name} finished**\n"
        f"Total: {len(links)}\n"
        f"Failed: {failed}\n"
        f"Success: {len(links) - failed}"
    )

# ------------------------------------------------------------------
#  Owner restart
# ------------------------------------------------------------------
@bot.on_message(filters.command("reset") & filters.private)
async def reset_bot(c, m):
    if m.chat.id != OWNER:
        return
    await m.reply("🔁 Restarting…")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ------------------------------------------------------------------
#  Stop running task
# ------------------------------------------------------------------
@bot.on_message(filters.command("stop") & filters.private)
async def stop_task(c, m):
    global cancel_requested
    if m.chat.id not in AUTH_USERS:
        return await m.reply("**Not authorised.**")
    cancel_requested = True
    await m.reply("🚦 **Cancellation requested.**")

# ------------------------------------------------------------------
#  Basic info commands
# ------------------------------------------------------------------
@bot.on_message(filters.command("id"))
async def id_cmd(c, m):
    await m.reply(f"**Chat ID:** `{m.chat.id}`")

@bot.on_message(filters.command("info") & filters.private)
async def info_cmd(c, m):
    await m.reply(
        f"╭───✨ **Your Info** ✨\n"
        f"├ Name: `{m.from_user.first_name}`\n"
        f"├ ID: `{m.from_user.id}`\n"
        f"╰ Username: @{m.from_user.username or 'None'}"
    )

@bot.on_message(filters.command("logs") & filters.private)
async def send_logs(c, m):
    try:
        await m.reply_document("logs.txt")
    except Exception as e:
        await m.reply(f"**Error:** `{e}`")

# ------------------------------------------------------------------
#  Settings panel   (File-2 additions)
# ------------------------------------------------------------------
@bot.on_callback_query(filters.regex("setttings"))
async def settings_panel(_, q):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Caption Style", "caption_style_command"),
         InlineKeyboardButton("🖋️ File Name", "file_name_command")],
        [InlineKeyboardButton("🌅 Thumbnail", "thummbnail_command")],
        [InlineKeyboardButton("✍️ Credit", "add_credit_command"),
         InlineKeyboardButton("🔏 Token", "set_token_command")],
        [InlineKeyboardButton("💧 Watermark", "wattermark_command")],
        [InlineKeyboardButton("📽️ Quality", "quality_command"),
         InlineKeyboardButton("🏷️ Topic", "topic_command")],
        [InlineKeyboardButton("🔄 Reset Settings", "resset_command")],
        [InlineKeyboardButton("🔙 Back", "back_to_main_menu")]
    ])
    await q.message.edit_media(
        InputMediaPhoto("https://envs.sh/GVI.jpg", caption="⚙️ **Settings Panel**"),
        reply_markup=kb
    )

@bot.on_callback_query(filters.regex("caption_style_command"))
async def set_caption(_, q):
    global caption
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send /cc1 /cc2 /cc3 or custom text**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    if m.text.lower() in ("/cc1", "/cc2", "/cc3"):
        caption = m.text.lower()
    else:
        caption = m.text
    await m.delete()
    await q.message.edit(f"✅ Caption set to **{caption}**",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("file_name_command"))
async def set_endfname(_, q):
    global endfilename
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send suffix or /d to disable**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    endfilename = '/d' if m.text == '/d' else m.text
    await m.delete()
    await q.message.edit(f"✅ Suffix: `{endfilename}`",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("thummbnail_command"))
async def set_thumb(_, q):
    global thumb
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send thumbnail URL or /d**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    thumb = '/d' if m.text == '/d' else m.text
    await m.delete()
    await q.message.edit("✅ Thumbnail updated.",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("add_credit_command"))
async def set_credit(_, q):
    global CR
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send credit text or /d**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    CR = CREDIT if m.text == '/d' else m.text
    await m.delete()
    await q.message.edit(f"✅ Credit: `{CR}`",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("quality_command"))
async def set_quality(_, q):
    global raw_text2, quality, res
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send 144/240/360/480/720/1080 or /d**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    if m.text.isdigit():
        raw_text2 = m.text
        quality = f"{raw_text2}p"
        res = {"144": "256x144", "240": "426x240", "360": "640x360",
               "480": "854x480", "720": "1280x720", "1080": "1920x1080"}.get(raw_text2, "854x480")
    else:
        raw_text2, quality, res = '480', '480p', '854x480'
    await m.delete()
    await q.message.edit(f"✅ Quality: **{quality}**",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("topic_command"))
async def set_topic(_, q):
    global topic
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send /yes to enable topic or /d**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    topic = '/yes' if m.text == '/yes' else '/d'
    await m.delete()
    await q.message.edit(f"✅ Topic: **{topic}**",
                         reply_markup=InlineKeyboardMarkup(kb))

@bot.on_callback_query(filters.regex("resset_command"))
async def reset_settings(_, q):
    global caption, endfilename, thumb, CR, cwtoken, cptoken, pwtoken, vidwatermark, raw_text2, quality, res, topic
    kb = [[InlineKeyboardButton("🔙 Back", "setttings")]]
    await q.message.edit("**Send /yes to reset or /no**",
                         reply_markup=InlineKeyboardMarkup(kb))
    m = await bot.listen(q.from_user.id)
    if m.text == '/yes':
        caption, endfilename, thumb = '/cc1', '/d', '/d'
        CR = CREDIT
        cwtoken = ('eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpm'
                   'YWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFB'
                   'NblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRk'
                   'F5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWb'
                   'XRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDki'
                   'LCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJO'
                   'alZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZ'
                   'V92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsIn'
                   'JlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0'
                   'VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72'
                   '-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0'
                   'ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvz'
                   'EhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg')
        cptoken = pwtoken = "cptoken"
        vidwatermark = '/d'
        raw_text2, quality, res, topic = '480', '480p', '854x480', '/d'
        await q.message.edit("✅ Settings reset!",
                             reply_markup=InlineKeyboardMarkup(kb))
    await m.delete()

# ------------------------------------------------------------------
#  Start & callback menus   (File-2 style)
# ------------------------------------------------------------------
@bot.on_message(filters.command("start"))
async def start(c, m):
    if m.from_user.id not in TOTAL_USERS:
        TOTAL_USERS.append(m.from_user.id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
        [InlineKeyboardButton("💎 Features", callback_data="feat_command"),
         InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
        [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
        [InlineKeyboardButton("📞 Contact", url=f"tg://user?id={OWNER}"),
         InlineKeyboardButton("🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")]
    ])
    if m.from_user.id in AUTH_USERS:
        text = (f"🌟 **Welcome {m.from_user.first_name}!**\n"
                f"You are **Premium** ✨\n\n"
                f"Use **Commands** to get started!")
    else:
        text = (f"🎉 **Welcome {m.from_user.first_name}!**\n\n"
                f"You are using the **free version**. "
                f"Contact [{CREDIT}](tg://user?id={OWNER}) to upgrade.")
    await m.reply_photo("https://envs.sh/GVI.jpg", caption=text, reply_markup=kb)

@bot.on_callback_query(filters.regex("back_to_main_menu"))
async def back_main(_, q):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
        [InlineKeyboardButton("💎 Features", callback_data="feat_command"),
         InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
        [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
        [InlineKeyboardButton("📞 Contact", url=f"tg://user?id={OWNER}"),
         InlineKeyboardButton("🛠️ Repo", url="https://github.com/nikhilsainiop/saini-txt-direct")]
    ])
    await q.message.edit_media(
        InputMediaPhoto("https://envs.sh/GVI.jpg",
                        caption=f"✨ **Welcome {q.from_user.first_name}!**"),
        reply_markup=kb
    )

@bot.on_callback_query(filters.regex("cmd_command"))
async def cmd(_, q):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚻 User", callback_data="user_command"),
         InlineKeyboardButton("🚹 Owner", callback_data="owner_command")],
        [InlineKeyboardButton("🔙 Back", "back_to_main_menu")]
    ])
    await q.message.edit_media(
        InputMediaPhoto("https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
                        caption="**Choose command list:**"),
        reply_markup=kb
    )

@bot.on_callback_query(filters.regex("user_command"))
async def user_cmds(_, q):
    kb = [[InlineKeyboardButton("🔙 Back", "cmd_command")]]
    txt = ("💥 **User Commands**\n\n"
           "➥ /start – Bot check\n"
           "➥ /y2t – YouTube → .txt\n"
           "➥ /ytm – YouTube → .mp3\n"
           "➥ /t2t – Text → .txt\n"
           "➥ /t2h – .txt → .html\n"
           "➥ /stop – Cancel task\n"
           "➥ /cookies – Update cookies\n"
           "➥ /id – Get ID\n"
           "➥ /info – User info\n"
           "➥ /logs – Bot logs")
    await q.message.edit_media(
        InputMediaPhoto("https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
                        caption=txt),
        reply_markup=InlineKeyboardMarkup(kb)
    )

@bot.on_callback_query(filters.regex("owner_command"))
async def owner_cmds(_, q):
    kb = [[InlineKeyboardButton("🔙 Back", "cmd_command")]]
    txt = ("👤 **Owner Commands**\n\n"
           "➥ /addauth – Add user\n"
           "➥ /rmauth – Remove user\n"
           "➥ /users – List users\n"
           "➥ /broadcast – Mass message\n"
           "➥ /broadusers – Broadcast users\n"
           "➥ /reset – Restart bot")
    await q.message.edit_media(
        InputMediaPhoto("https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
                        caption=txt),
        reply_markup=InlineKeyboardMarkup(kb)
    )

@bot.on_callback_query(filters.regex("feat_command"))
async def feat(_, q):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Auto Pin", callback_data="pin_command")],
        [InlineKeyboardButton("💧 Watermark", callback_data="watermark_command"),
         InlineKeyboardButton("🔄 Reset", callback_data="reset_command")],
        [InlineKeyboardButton("🖨️ Logs", callback_data="logs_command")],
        [InlineKeyboardButton("🖋️ File Name", callback_data="custom_command"),
         InlineKeyboardButton("🏷️ Title", callback_data="titlle_command")],
        [InlineKeyboardButton("🎥 YouTube", callback_data="yt_command")],
        [InlineKeyboardButton("🌐 HTML", callback_data="html_command")],
        [InlineKeyboardButton("📝 Text File", callback_data="txt_maker_command"),
         InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_command")],
        [InlineKeyboardButton("🔙 Back", "back_to_main_menu")]
    ])
    await q.message.edit_media(
        InputMediaPhoto("https://tinypic.host/images/2025/07/14/file_000000002d44622f856a002a219cf27aconversation_id68747543-56d8-800e-ae47-bb6438a09851message_id8e8cbfb5-ea6c-4f59-974a-43bdf87130c0.png",
                        caption="**✨ Bot Features**"),
        reply_markup=kb
    )

@bot.on_callback_query(filters.regex("upgrade_command"))
async def upgrade(_, q):
    kb = [[InlineKeyboardButton("🔙 Back", "back_to_main_menu")]]
    txt = ("🎉 **Upgrade to Premium**\n\n"
           "Unlock DRM + AES decryption, classplus, PW, etc.\n\n"
           "💵 100 INR / month\n"
           f"Contact [{CREDIT}](tg://user?id={OWNER})")
    await q.message.edit_media(
        InputMediaPhoto("https://envs.sh/GVI.jpg", caption=txt),
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ------------------------------------------------------------------
#  Run
# ------------------------------------------------------------------
def notify_owner():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": OWNER, "text": "🔄 Bot restarted successfully ✅"})

def set_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    cmds = [
        {"command": "start", "description": "✅ Check bot"},
        {"command": "stop", "description": "🚫 Stop task"},
        {"command": "reset", "description": "🔁 Restart bot"},
        {"command": "id", "description": "🆔 Get ID"},
        {"command": "info", "description": "ℹ️ User info"},
        {"command": "cookies", "description": "📁 Upload YT cookies"},
        {"command": "y2t", "description": "🔪 YT → .txt"},
        {"command": "ytm", "description": "🎶 YT → .mp3"},
        {"command": "t2t", "description": "📟 Text → .txt"},
        {"command": "t2h", "description": "🌐 .txt → .html"},
        {"command": "logs", "description": "👁️ Bot logs"},
        {"command": "broadcast", "description": "📢 Broadcast"},
        {"command": "broadusers", "description": "👥 Broadcast users"},
        {"command": "addauth", "description": "➕ Add user"},
        {"command": "rmauth", "description": "➖ Remove user"},
        {"command": "users", "description": "👑 Premium users"}
    ]
    requests.post(url, json={"commands": cmds})

if __name__ == "__main__":
    set_commands()
    notify_owner()
    bot.run()
