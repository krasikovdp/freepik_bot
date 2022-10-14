# Freepik bot

This is a bot for supergroups that can generate download links for premium content on freepik.com. Admins can assign roles, based on which users are restricted how much they can download per day.

## Environment variables

### TELEGRAM_TOKEN

The token you get from BotFather when you create a bot

### ADMIN_USERNAMES

Usernames of admins, separated with spaces. Admins can change users' roles through private messages

### FREEPIK_USERNAME

Your freepik account's e-mail

### FREEPIK_PASSWORD

Your freepik account's password

### 2CAPTCHA_API_KEY

2captcha api key from the developer or customer tab

### DATABASE_URL

URL of the postgres database. Will be added automatically if you have the heroku add-on
