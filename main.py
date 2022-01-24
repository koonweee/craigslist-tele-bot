import datetime
from telegram.ext import Updater, CommandHandler
from sheets import *
import pytz
from pytz import timezone
import logging

updater = Updater(token='5138358228:AAF50OgNglW72Y69TFmeRTHGqQ9n1HVdsVo',
    use_context=True) # receives updates from Telegram
dispatcher = updater.dispatcher # dispatches updates to appropriate handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO) # config for logger

# chores handler
def chores(update, context):
    today = datetime.datetime.now(tz=pytz.utc)
    today = today.astimezone(timezone('US/Pacific'))
    todayString = today.strftime("%B %d, %Y")
    message = 'Retrieving chores for week of %s...' % todayString
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    chores = getWeekChores(today)
    if not chores:
        message = 'No chores found for this week, retrieving next weeks...'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        chores = getWeekChores(today + datetime.timedelta(7))
    message = (
            '🗑️ Trash: %s\n'
            '🚽 Upstairs toilet: %s\n'
            '🚽 Downstairs toilet: %s\n'
            '🚽 Common toilet: %s\n'
            '🧹 Common floor: %s'
        ) % (chores[0], chores[1], chores[2], chores[3], chores[4])
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


start_handler = CommandHandler('chores', chores) # associate /start with above fn
dispatcher.add_handler(start_handler)
updater.start_polling()
