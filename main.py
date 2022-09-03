import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CallbackContext, CommandHandler, Dispatcher, Filters, MessageHandler, \
    PicklePersistence
from freepik import Freepik
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def inline_handler(msg: str):
    """returns a handler that sends message msg in response to any updates"""
    def handler(update: Update, ctx: CallbackContext):
        update.effective_chat.send_message(msg)
    return handler


def promote_handler(update: Update, ctx: CallbackContext):
    usernames = update.message.text.split(' ')[1:]
    if len(usernames) == 0:
        return update.effective_chat.send_message('You have to specify the username (for example: /promote user123)')
    usernames = [username if not username.startswith('@') else username[1:] for username in usernames]
    ctx.bot_data['members'].update(set(usernames))
    update.effective_chat.send_message('The following users have been promoted:\n' + "\n".join(usernames))


def demote_handler(update: Update, ctx: CallbackContext):
    usernames = update.message.text.split(' ')[1:]
    if len(usernames) == 0:
        return update.effective_chat.send_message('You have to specify the username (for example: /demote user123)')
    usernames = [username if not username.startswith('@') else username[1:] for username in usernames]
    ctx.bot_data['members'].difference_update(set(usernames))
    update.effective_chat.send_message('The following users have been demoted:\n' + "\n".join(usernames))


def user_status_handler(update: Update, ctx: CallbackContext):
    usernames = update.message.text.split(' ')[1:]
    if len(usernames) == 0:
        return update.effective_chat.send_message('You have to specify the username (for example: /user_status user123)')
    usernames = [username if not username.startswith('@') else username[1:] for username in usernames]
    lines = []
    for username in sorted(usernames):
        if username in ctx.bot_data['members']:
            lines.append(f'{username} is a member')
        elif username in ctx.bot_data['admin_usernames']:
            lines.append(f'{username} is an admin')
        else:
            lines.append(f'{username} is a regular user')
    update.effective_chat.send_message('\n'.join(lines))


def members_list_handler(update: Update, ctx: CallbackContext):
    members = [username for username in sorted(list(ctx.bot_data['members']))]
    if members:
        update.effective_chat.send_message('\n'.join(members))
    else:
        update.effective_chat.send_message('There are no members')


def url_handler(update: Update, ctx: CallbackContext):
    input_url = update.message.text
    try:
        download_url = ctx.bot_data['freepik_api'].input_url2download_url(input_url)
        update.effective_chat.send_message(
            'To download the file, use the button below',
            reply_to_message_id=update.message.message_id,
            reply_markup=InlineKeyboardMarkup.from_button(InlineKeyboardButton('Download', url=download_url))
        )
    except AttributeError:
        update.effective_chat.send_message(
            'This is not a valid url',
            reply_to_message_id=update.message.message_id
        )


def main():
    updater = Updater(token=os.environ['TELEGRAM_TOKEN'], use_context=True, persistence=PicklePersistence('persistence.pickle'))
    dispatcher: Dispatcher = updater.dispatcher

    dispatcher.bot_data.setdefault('members', set())

    admin_usernames = os.environ['ADMIN_USERNAMES'].split(' ')
    dispatcher.bot_data['admin_usernames'] = admin_usernames
    dispatcher.bot_data['freepik_api'] = Freepik(os.environ['FREEPIK_GR_TOKEN'])
    dispatcher.bot.set_my_commands([
        ('/promote', 'promotes specified user(s) to member(s)'),
        ('/demote', 'demotes specified user(s) to regular user(s)'),
        ('/user_status', 'prints the status of the specified user(s) (regular, member, admin)'),
        ('/members_list', 'lists all members'),
    ])

    only_admins = Filters.user(username=admin_usernames)
    regular_users = ~only_admins
    private_chat = Filters.chat_type.private
    group_chat = Filters.chat_type.groups
    has_url = Filters.regex(r'^https?://')

    handlers = [
        MessageHandler(private_chat & regular_users, inline_handler('You are not an admin')),

        CommandHandler('start', inline_handler('start'), filters=private_chat & only_admins),
        CommandHandler('promote', promote_handler, filters=private_chat & only_admins),
        CommandHandler('demote', demote_handler, filters=private_chat & only_admins),
        CommandHandler('user_status', user_status_handler, filters=private_chat & only_admins),
        CommandHandler('members_list', members_list_handler, filters=private_chat & only_admins),

        MessageHandler(group_chat & has_url, url_handler),

        MessageHandler(Filters.all, lambda upd, ctx: print('unhandled message:', upd.message.text)),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
