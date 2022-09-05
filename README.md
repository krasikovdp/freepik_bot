# Freepik bot

This is a bot for supergroups that can generate download links for premium content on freepik.com. Admins can assign roles, based on which users are restricted how much they can download per day.

## Environment variables

### TELEGRAM_TOKEN

The token you get from BotFather when you create a bot

### ADMIN_USERNAMES

Usernames of admins, separated with spaces. Admins can change users' roles through private messages

### FREEPIK_GR_TOKEN

Get this from freepik.com cookie GR_TOKEN

### DATABASE_URL

URL of the postgres database. Will be added automatically if you have the heroku add-on
