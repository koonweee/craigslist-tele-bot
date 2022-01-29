import datetime
import config
import craigslist
import telegram
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler,  MessageHandler, Filters, ConversationHandler, MessageFilter
import pytz
from pytz import timezone
import logging
import db
import math
import schedule
import time

updater = Updater(token=config.telegramAPIKey,
    use_context=True) # receives updates from Telegram
dispatcher = updater.dispatcher # dispatches updates to appropriate handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO) # config for logger
db.init_users()

def start(update, context):
    message = (
        '<b>To start using the bot, please use /update_url to register a Craigslist URL to track</b>\n\n'
        '/all - retrieves all listings from the specified URL\n'
        '/new - retrieves new (unseen) listings from the specified URL\n\n'
        'The bot will automatically send new listings every 10 minutes\n\n'
        'Use /help at anytime to read these instructions again'
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)
def help(update, context):
    return start(update, context)

start_handler = CommandHandler('start', start) # associate /start with above fn
dispatcher.add_handler(start_handler)

help_handler = CommandHandler('help', help) # associate /help with above fn
dispatcher.add_handler(help_handler)

# helper/setup functions
def get_user_url(context, handle):
    if (db.user_exists(handle)):
        context.user_data["url"] = db.get_userURL(handle)
        return context
    else:
        return context

def epoch_duration_to_pretty(epoch_seconds):
    minutes = math.floor(epoch_seconds/60)
    remainder_seconds = epoch_seconds % 60

    hours = math.floor(minutes/60)
    remainder_minutes = minutes % 60

    return f'{hours}h {remainder_minutes}m {remainder_seconds}s'

def send_formatted_results(update, context, notify):
    results = context.user_data["results"]
    for result in reversed(results):
        now = datetime.datetime.now(tz=pytz.utc)
        now = now.astimezone(timezone('US/Pacific'))
        now_epoch = int(now.strftime('%s'))
        caption = (
            f'🚗 <a href=\'{result.url}\'>{result.title}</a> - <b>{result.price}</b>\n'
            f'📍 {result.distance} away\n'
            f'⏱️ Listed {epoch_duration_to_pretty(now_epoch - result.epoch)} ago'
        )
        img_404_url = 'https://github.com/koonweee/craigslist-tele-bot/raw/main/404.jpeg'
        img_url = result.img_url if result.img_url else img_404_url
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            disable_notification=not notify
        )

def new(update, context):
    handle = update.effective_user.username
    if db.user_exists(handle):
        context = get_user_url(context, handle)
        message = 'Retrieving new listings...'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message, disable_notification=True)
        latest_epoch = db.get_latest_result_epoch(handle)
        results = craigslist.getListings(base_url=context.user_data["url"], latest_epoch=latest_epoch)
        context.user_data["results"] = results
        if len(results) > 0:
            send_formatted_results(update, context, notify=False)
            for result in results:
                db.add_user_result(handle, result)
        else:
            message = 'No new listings found'
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        message = 'Please set a Craigslist URL using /update_url first'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

new_handler = CommandHandler('new', new) # associate /start with above fn
dispatcher.add_handler(new_handler)

def all(update, context):
    handle = update.effective_user.username
    if db.user_exists(handle):
        context = get_user_url(context, handle)
        message = 'Retrieving all listings...'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message, disable_notification=True)
        results = craigslist.getListings(base_url=context.user_data["url"])
        context.user_data["results"] = results
        send_formatted_results(update, context, notify=False)
        for result in results:
            db.add_user_result(handle, result)
    else:
        message = 'Please set a Craigslist URL using /update_url first'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

all_handler = CommandHandler('all', all) # associate /start with above fn
dispatcher.add_handler(all_handler)

def clear(update, context):
    handle = update.effective_user.username
    message = 'Clearing all listings in database'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, disable_notification=True)
    db.delete_user_results(handle)
clear_handler = CommandHandler('clear', clear) # associate /start with above fn
dispatcher.add_handler(clear_handler)
# conversation to get craigslist URL

URL_UPDATE_DECISION, URL_UPDATED = range(2)

def update_url_start_handler(update, context):
    context = get_user_url(context, update.effective_user.username)
    if "url" in context.user_data:
        reply_keyboard = [['Yes', 'No']]
        message = f'The current Craigslist URL is: {context.user_data["url"]}'
        update.message.reply_text(
            message
        )
        message = "Would you like to change this URL?"
        update.message.reply_text(
            message,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            )
        )
        return URL_UPDATE_DECISION
    return update_url_prompt_handler(update, context)

def update_url_decision_handler(update, context):
    decision = update.message.text
    if decision == "Yes":
        return update_url_prompt_handler(update, context)
    else:
        message = f'The URL was not updated'
        update.message.reply_text(
            message
        )
        return ConversationHandler.END

def update_url_prompt_handler(update, context):
    message = 'Please send me the Craigslist URL to monitor'
    update.message.reply_text(
        message
    )
    return URL_UPDATED

def update_url_updated_handler(update, context):
    new_url = update.message.text
    context.user_data["url"] = new_url
    handle = update.effective_user.username
    if db.user_exists(handle):
        db.update_userURL(handle, new_url)
    else:
        db.add_userURL(handle, new_url, update.effective_chat.id)
    db.init_user_results(handle)
    db.delete_user_results(handle)
    message = f'The URL was updated'
    update.message.reply_text(
        message
    )
    return ConversationHandler.END

def cancel_handler(update, context) -> int:
    message = 'The last action was cancelled'
    update.message.reply_text(
        message
    )
    return ConversationHandler.END

target_url_handler = ConversationHandler(
    entry_points=[CommandHandler('update_url', update_url_start_handler)],
    states = {
        URL_UPDATE_DECISION: [MessageHandler(Filters.regex('^(Yes|No)$'), update_url_decision_handler)],
        URL_UPDATED: [MessageHandler(Filters.text, update_url_updated_handler)]
    },
    fallbacks=[CommandHandler('cancel', cancel_handler)]
)

dispatcher.add_handler(target_url_handler)

def scheduled_new_send(handle):
    # init bot
    bot = telegram.Bot(token=config.telegramAPIKey)
    # get the chat_id of this handle
    chat_id = db.get_userID(handle)
    # get the URL of this handle
    url = db.get_userURL(handle)
    # retrieve new listings if they exists, and send them
    latest_epoch = db.get_latest_result_epoch(handle)
    results = craigslist.getListings(base_url=url, latest_epoch=latest_epoch)
    if len(results) > 0:
        for result in reversed(results):
            now = datetime.datetime.now(tz=pytz.utc)
            now = now.astimezone(timezone('US/Pacific'))
            now_epoch = int(now.strftime('%s'))
            caption = (
                f'🚗 <a href=\'{result.url}\'>{result.title}</a> - <b>{result.price}</b>\n'
                f'📍 {result.distance} away\n'
                f'⏱️ Listed {epoch_duration_to_pretty(now_epoch - result.epoch)} ago'
            )
            img_404_url = 'https://github.com/koonweee/craigslist-tele-bot/raw/main/404.jpeg'
            img_url = result.img_url if result.img_url else img_404_url
            bot.send_photo(
                chat_id=chat_id,
                photo=img_url,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            db.add_user_result(handle, result)
    else:
        message = 'No new listings found'
        bot.send_message(chat_id=chat_id, text=message, disable_notification=True)

def scheduled_new():
    # get all handles from db
    handles = db.get_all_handles()
    #print(handles)
    if handles:
        for handle in handles:
            handle = handle[0]
            #print(f'Sending scheduled update for {handle}')
            scheduled_new_send(handle)

schedule.every(10).minutes.do(scheduled_new)
updater.start_polling()
while True:
    schedule.run_pending()
    time.sleep(1)

