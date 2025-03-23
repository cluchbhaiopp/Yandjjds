import os
import asyncio
import sys
import time
import random
import string  

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from bot import Bot
from config import ADMINS, OWNER_ID, FORCE_MSG, START_MSG, CUSTOM_CAPTION, IS_VERIFY, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_URL, TUT_VID, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT
from helper_func import subscribed1, subscribed2, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import add_user, del_user, full_userbase, present_user, is_admin
from shortzy import Shortzy

BOT_USERNAME = "Backbencherstoken_bot"

@Bot.on_message(filters.command('start') & filters.private & subscribed1 & subscribed2)
async def start_command(client: Bot, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass

    verify_status = await get_verify_status(id)
    
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(id, is_verified=False)
        verify_status['is_verified'] = False

    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or Expired.🥲  Try again by clicking /start")
        await update_verify_status(id, is_verified=True, verified_time=time.time())
        reply_markup = None if verify_status["link"] == "" else InlineKeyboardMarkup([[InlineKeyboardButton("Open Link", url=verify_status["link"])]])
        return await message.reply(f"Your token successfully verified and valid for: 24 Hour 😀", reply_markup=reply_markup, protect_content=False, quote=True)

    if verify_status['is_verified']:
        if len(message.text) > 7:
            try:
                base64_string = message.text.split(" ", 1)[1]
                string_decoded = await decode(base64_string)
                argument = string_decoded.split("-")
                
                if len(argument) == 3:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                    ids = range(start, end+1) if start <= end else list(range(start, end-1, -1))
                elif len(argument) == 2:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                else:
                    return

                temp_msg = await message.reply("Please wait...")
                try:
                    messages = await get_messages(client, ids)
                    await temp_msg.delete()
                    for msg in messages:
                        caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name) if bool(CUSTOM_CAPTION) & bool(msg.document) else ("" if not msg.caption else msg.caption.html)
                        reply_markup = None if DISABLE_CHANNEL_BUTTON else msg.reply_markup
                        try:
                            await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                            await asyncio.sleep(0.5)
                        except FloodWait as e:
                            await asyncio.sleep(e.x)
                            await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                        except:
                            pass
                except:
                    await message.reply_text("Something went wrong..!")
                return
            except:
                pass
        
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("About Me", callback_data="about"),
              InlineKeyboardButton("Close", callback_data="close")]]
        )
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
    else:
        if IS_VERIFY:
           # short_url = f"adrinolinks.in"
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(id, verify_token=token, link="")
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{BOT_USERNAME}?start=verify_{token}')
            btn = [
                [InlineKeyboardButton("📥 Click here 📥", url=link)],
                [InlineKeyboardButton('🔰 How to use the bot 🔰', url=TUT_VID)]
            ]
            await message.reply(f"👉 Your Ads token is expired, refresh your token and try again.🔃 \n\n🎟️ <b> Token Timeout:</b> {get_exp_time(VERIFY_EXPIRE)}⏲️\n\n<blockquote><b>What is the token?</b>\n\nThis is an ads token.🎟️ If you pass 1 ad, you can use the bot for 24 Hour⏲️  after passing the ad.</blockquote>", reply_markup=InlineKeyboardMarkup(btn), protect_content=False, quote=True)
        else:
            # Handle the case when verification is not required
            pass

#=====================================================================================##

WAIT_MSG = """"<b>Processing ....</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message with out any spaces.</code>"""

#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Bot, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink),
            InlineKeyboardButton(text="Join Channel", url=client.invitelink2),
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass
    
    


    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private)
async def get_users(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:       
        return
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.command('broadcast') & filters.private)
async def send_text(client: Bot, message: Message):
    user_id = message.from_user.id
    is_user_admin = await is_admin(user_id)
    if not is_user_admin and user_id != OWNER_ID:        
        return
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcast ho rha till then FUCK OFF </i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

@Bot.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot(b, m):
    restarting_message = await m.reply_text(f"⚡️<b><i>Restarting....</i></b>", disable_notification=True)

    # Wait for 3 seconds
    await asyncio.sleep(3)

    # Update message after the delay
    await restarting_message.edit_text("✅ <b><i>Successfully Restarted</i></b>")

    # Restart the bot
    os.execl(sys.executable, sys.executable, *sys.argv)
