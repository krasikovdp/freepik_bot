import telegram
from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters
import datetime
import pytz
import requests
import re

updater = Updater("", use_context=True)
user_limit = 1
total_message_limit = 100

dispatcher = updater.dispatcher
j = updater.job_queue
run_once = 0
total_messages_sent = 0
users = {}
whitelist = ["https://www.freepik.com/", "https://br.freepik.com/", "https://de.freepik.com/", "https://www.freepik.es/", "https://fr.freepik.com/", "https://jp.freepik.com/", "https://pl.freepik.com/", "https://ru.freepik.com/", "https://nl.freepik.com/", "https://it.freepik.com/", "https://kr.freepik.com/", "https://elements.envato.com/", "https://www.flaticon.com/", "https://www.flaticon.es/", "https://www.flaticon.com/de/", "https://www.flaticon.com/br/", "https://www.flaticon.com/fr/", "https://www.flaticon.com/kr/", "https://www.flaticon.com/ru/"]

def daily_handler(context):
    global total_messages_sent, users
    total_messages_sent = 0
    unlock_group(context.job.context)
    for user_id in users.keys():
        print(user_id)
        unlock_user(context.job.context, context, user_id)
    users = {}

def daily(update, context):
    j.run_daily(daily_handler, datetime.time(1, tzinfo=pytz.timezone('Asia/Dubai')), days=(0, 1, 2, 3, 4, 5, 6), context=update)

#modify lock permissions
def lock_perm():
    return telegram.ChatPermissions(
        can_send_messages=False,
        messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False
    )

#modify unlock permissions
def unlock_perm():
    return telegram.ChatPermissions(
        can_send_messages=True,
        messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=True,
        can_invite_users=True,
        can_pin_messages=True
    )

def lock_group(update):
    update.effective_chat.set_permissions(lock_perm())

def unlock_group(update):
    try:
        update.effective_chat.set_permissions(unlock_perm())
    except:
        pass

def lock_user(update, context):
    context.bot.restrict_chat_member(chat_id=update.effective_chat.id, user_id=update.effective_user.id, permissions=lock_perm())

def unlock_user(update, context, user_id=None):
    try:
        if not user_id:
            context.bot.restrict_chat_member(chat_id=update.effective_chat.id, user_id=update.effective_user.id, permissions=unlock_perm())
        else:
            context.bot.restrict_chat_member(chat_id=update.effective_chat.id, user_id=user_id, permissions=unlock_perm())
    except:
        pass

def freepik_general_to_download_url(url: str) -> str:
    if 'download-file' in url:
        return url
    file_id = re.search(r'(\d+)\.htm', url).group(1)
    return f'https://www.freepik.com/download-file/{file_id}'

def download_freepik(url: str) -> (bytes, str):
    url = freepik_general_to_download_url(url)
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError
    content = resp.content
    filename_match = re.search(r'filename=(.+)$', resp.headers['Content-Disposition'])
    if filename_match is None:
        filename = ''
    else:
        filename = filename_match.group(1)
    return content, filename

def welcome(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        #update welcome message here
        msg = f"Hi {member.full_name}\nWelcome to group.\nPlease read the rules in the pinned message.\n[Tutorial](https://www.myvideo.ge/v/4113113)"
        context.bot.send_message(update.message.chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

def message(update: Update, context: CallbackContext):
    global total_messages_sent, run_once, users, user_limit, total_message_limit, whitelist
    uid = update.effective_user.id
    member = context.bot.get_chat_member(update.effective_chat.id, uid)
    if member.status == "creator" or member == "administrator":
        if update.message.text == "/lock all":
            lock_group(update)
        elif update.message.text == "/unlock all":
            total_messages_sent = 0
            unlock_group(update)
            for user_id in users.keys():
                unlock_user(update, context, user_id)
            users = {}
        elif update.message.text[:10] == "/whitelist":
            if update.message.text == "/whitelist":
                link_list = '\n'.join(whitelist)
                context.bot.send_message(update.message.chat_id, text=f"Following site are whitelisted:\n{link_list}")
            else:
                link = update.message.text[11:]
                print(link)
                if link[-1] != "/":
                    link += "/"
                print(link)
                whitelist.append(link)
        elif update.message.text[:12] == "/rmwhitelist":
            if update.message.text == "/rmwhitelist":
                link_list = '\n'.join(whitelist)
                context.bot.send_message(update.message.chat_id, text=f"Following can be removed from whitelist:\n{link_list}")
            else:
                link = update.message.text[13:]
                print(link)
                if link[-1] != "/":
                    link += "/"
                print(link)
                whitelist.remove(link)
    if update.message.text[:8] == "https://" or update.message.text[:7] == "http://":
        #if text in whitelist
        reduced_link = update.message.text.split("/")
        reduced_link = reduced_link[0] + "//" + reduced_link[2] + "/"
        print(reduced_link)
        print(reduced_link in whitelist)
        if reduced_link in whitelist:
            document, filename = download_freepik(update.message.text)
            update.effective_chat.send_document(document, filename=filename)
            if run_once == 0:
                daily(update, context)
                run_once = 1

            total_messages_sent += 1
            print(total_messages_sent)
            if total_messages_sent >= total_message_limit:
                lock_group(update)

            if not users.get(uid):
                users[uid] = 1
            else:
                users[uid] += 1
            try:
                if users[uid] >= user_limit:
                    lock_user(update, context)
            except:
                pass
        else:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
    else:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)

welcome_handler = MessageHandler(Filters.status_update.new_chat_members, welcome)
dispatcher.add_handler(welcome_handler)

message_handler = MessageHandler((Filters.text | Filters.command), message)
dispatcher.add_handler(message_handler)

updater.start_polling()
updater.idle()
