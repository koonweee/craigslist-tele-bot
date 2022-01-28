import datetime
import config
import craigslist
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, PollHandler, MessageHandler, Filters, ConversationHandler, MessageFilter
import pytz
from pytz import timezone
import logging
import db

updater = Updater(token=config.telegramAPIKey,
    use_context=True) # receives updates from Telegram
dispatcher = updater.dispatcher # dispatches updates to appropriate handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO) # config for logger
db.init_users()

# helper/setup functions
def get_user_url(context, handle):
    if (db.user_exists(handle)):
        context.user_data["url"] = db.get_userURL(handle)
        return context
    else:
        return context

def refresh(update, context):
    now = datetime.datetime.now(tz=pytz.utc)
    now = now.astimezone(timezone('US/Pacific'))
    nowString = now.strftime("%B %d, %Y %H:%M")
    message = 'Retrieving cars as of %s...' % nowString
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    results = craigslist.getListings(base_url=context.user_data["url"])
    print(results[0])

refresh_handler = CommandHandler('refresh', refresh) # associate /start with above fn
dispatcher.add_handler(refresh_handler)

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
        db.add_userURL(handle, new_url)
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

updater.start_polling()
