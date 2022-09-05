import datetime as dt
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import Updater, CallbackContext, CommandHandler, Dispatcher, Filters, MessageHandler, \
    PicklePersistence, JobQueue, Defaults
from freepik import *
from flaticon import *
import logging
import pytz
from roles import roles
from ptbcontrib.postgres_persistence import PostgresPersistence

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DEFAULT_TZINFO = pytz.FixedOffset(5 * 60 + 30)


def inline_handler(msg: str):
    """returns a handler that sends message msg in response to any updates"""
    def handler(update: Update, ctx: CallbackContext):
        update.effective_chat.send_message(msg)
    return handler


def set_role_handler(update: Update, ctx: CallbackContext):
    if len(ctx.args) < 2:
        return update.message.reply_text('You have to specify the role and the username(s) like this: /set_role role_name username\n'
                                         'You can see all roles with /roles_list')
    role = ctx.args[0]
    usernames = [username if not username.startswith('@') else username[1:] for username in ctx.args[1:]]
    for username in usernames:
        ctx.bot_data['users'][username] = default_user(role)
    update.message.reply_text(f'The following users have been promoted to {role}:\n' + "\n".join(usernames))


def roles_list_handler(update: Update, ctx: CallbackContext):
    lines = []
    indent = 2
    for role, params in roles.items():
        lines.append(role)
        lines.append('\n'.join(f'{" " * indent}{k} = {v}' for k, v in params.items()))
    msg = '\n'.join(lines)
    if not msg:
        msg = 'There are no roles'
    update.message.reply_text(msg)


def members_list_handler(update: Update, ctx: CallbackContext):
    lines = [f'{user_data["role"]} - {username}' for username, user_data in ctx.bot_data['users'].items()]
    msg = '\n'.join(sorted(lines))
    if not msg:
        msg = 'There are no members'
    update.message.reply_text(msg)


def restrict_if_necessary(update: Update, ctx: CallbackContext):
    user_data = ctx.bot_data['users'][update.effective_user.username]
    if user_data['uses'] <= 0:
        print(f'retstricting user @{update.effective_user.username}')
        today_12am = dt.datetime.now(DEFAULT_TZINFO).replace(hour=0, minute=0, second=0, microsecond=0)
        print(today_12am)
        print(dt.timedelta(days=user_data['restrict_days']))
        user_data['unrestrict_date'] = (today_12am + dt.timedelta(days=user_data['restrict_days'])).isoformat()
        permissions = ChatPermissions(*([False] * 8))  # set all 8 arguments to False
        ctx.bot.restrict_chat_member(update.effective_chat.id, update.effective_user.id,
                                     permissions, today_12am + dt.timedelta(days=user_data['restrict_days']))


def input_url2download_url(input_url: str):
    if 'freepik' in input_url:
        return freepik_input_url2download_url(input_url)
    if 'flaticon' in input_url:
        return flaticon_input_url2download_url(input_url)
    raise AttributeError


def url_handler(update: Update, ctx: CallbackContext):
    input_url = update.message.text
    user_data = ctx.bot_data['users'].setdefault(update.effective_user.username, default_user())
    if user_data['uses'] > 0:
        download_url_sent = False
        try:
            download_url = input_url2download_url(input_url)
            update.message.reply_text(
                'To download the file, use the button below',
                reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton('Download', url=download_url)))
            download_url_sent = True
        except AttributeError:
            update.message.reply_text('This is not a valid url')
        except Exception as e:
            update.message.reply_text('Something went wrong with the request')
            print(e)
        if download_url_sent:
            user_data['uses'] -= 1
    else:
        update.message.delete()
    restrict_if_necessary(update, ctx)


def default_user(role: str = 'regular'):
    user_data = roles[role]
    user_data['role'] = role
    today_12am = dt.datetime.now(DEFAULT_TZINFO).replace(hour=0, minute=0, second=0, microsecond=0)
    user_data['unrestrict_date'] = (today_12am + dt.timedelta(days=user_data['restrict_days'])).isoformat()
    return user_data


def unrestrict_everyone_necessary(ctx: CallbackContext):
    now = dt.datetime.now(DEFAULT_TZINFO)
    for username, user_data in ctx.bot_data['users'].items():
        if now >= dt.datetime.fromisoformat(user_data['unrestrict_date']):
            for k, v in default_user(user_data['role']).items():
                user_data[k] = v


def main():
    defaults = Defaults(tzinfo=DEFAULT_TZINFO)
    persistence = PostgresPersistence(os.environ['POSTGRES_URL'].replace('postgres://', 'postgresql://'))  # PicklePersistence('persistence.pickle')
    updater = Updater(token=os.environ['TELEGRAM_TOKEN'], use_context=True, persistence=persistence, defaults=defaults)
    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.bot_data.setdefault('users', dict())

    jq: JobQueue = dispatcher.job_queue
    jq.run_once(unrestrict_everyone_necessary, 1)
    jq.run_daily(unrestrict_everyone_necessary, dt.time(0, 0, 0, 0))
    jq.start()

    admin_usernames = os.environ['ADMIN_USERNAMES'].split(' ')
    dispatcher.bot_data['admin_usernames'] = admin_usernames
    dispatcher.bot.set_my_commands([
        ('/set_role', 'assigns a role to user(s), usage: /set_role role username'),
        ('/roles_list', 'prints all roles and their perks'),
        ('/members_list', 'lists all members in the format role - username'),
    ])

    only_admins = Filters.user(username=admin_usernames)
    regular_users = ~only_admins
    private_chat = Filters.chat_type.private
    group_chat = Filters.chat_type.groups
    has_url = Filters.regex(r'^https?://')

    handlers = [
        MessageHandler(private_chat & regular_users, inline_handler('You are not an admin')),

        CommandHandler('start', inline_handler('start'), filters=private_chat & only_admins),
        CommandHandler('set_role', set_role_handler, filters=private_chat & only_admins, pass_args=True),
        CommandHandler('roles_list', roles_list_handler, filters=private_chat & only_admins, pass_args=True),
        CommandHandler('members_list', members_list_handler, filters=private_chat & only_admins, pass_args=True),

        MessageHandler(group_chat & has_url, url_handler),
        MessageHandler(group_chat & ~has_url & ~only_admins, lambda upd, ctx: upd.message.delete()),

        MessageHandler(Filters.all, lambda upd, ctx: print('unhandled message:', upd.message.text)),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
