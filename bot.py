#!/usr/bin/env python3
# coding: utf-8

"""
telegram bot to connect corona-suspects with medical staff

Bot url:
t.me/corona_care_bot

spec: https://notes.status.im/_zy_XbciTQqQDzVrnTJ7TA?edit

groups the bot forwards to: (has to be a member of the group)
https://t.me/humanbios0k

"""

import logging.config
import textwrap
import emoji

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from config import settings


# enable logging
logging.config.dictConfig(settings.LOGGING)


# definitions
FEEL_OK, COUGH_FEVER, STRESSED_ANXIOUS, WANNA_HELP, TELL_FRIENDS = range(5)
yes_no_keyboard = ReplyKeyboardMarkup([["Yes", "No"]])
filter_yes = Filters.regex("^Yes$")
filter_no = Filters.regex("^No$")


# methods & commands
def cancel(update, context):
    TEXT_CANCEL = """
        Bye! I hope we can talk again some day.
        """
    update.message.reply_text(text=textwrap.dedent(TEXT_CANCEL), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def are_you_ok(update, context):
    TEXT_ARE_YOU_OK = f"""
        Hi! {emoji.emojize(':simple_smile:')}
        Are you feeling Ok?
        """
    update.message.reply_text(text=textwrap.dedent(TEXT_ARE_YOU_OK), reply_markup=yes_no_keyboard)
    return FEEL_OK

def cough(update, context):
    TEXT_COUGH = "Oh no, I'm sorry about that! Are you having cough or fever?"
    update.message.reply_text(
        text=textwrap.dedent(TEXT_COUGH), reply_markup=yes_no_keyboard
    )
    return COUGH_FEVER

def stressed(update, context):
    TEXT_STRESSED = f"Good! Are you feeling stressed or anxious? {emoji.emojize(':worried:')}"
    update.message.reply_text(text=textwrap.dedent(TEXT_STRESSED), reply_markup=yes_no_keyboard)
    return STRESSED_ANXIOUS

def wanna_help(update, context):
    TEXT_WANNA_HELP = "That's great! Do you wanna help?"
    update.message.reply_text(text=textwrap.dedent(TEXT_WANNA_HELP), reply_markup=yes_no_keyboard)
    return WANNA_HELP

def bye(update, context):
    TEXT_BYE = "Okay, Bye!"
    update.message.reply_text(text=textwrap.dedent(TEXT_BYE), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def doctors_room(update, context):
    user = update.effective_user
    context.bot.send_message(
        chat_id=settings.TELEGRAM_DOCTOR_ROOM, text=f"A user requested medical help: {user.first_name}"
    )
    update.message.reply_text("Forwarded your request to the doctor's room!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def psychologists_room(update, context):
    user = update.effective_user
    context.bot.send_message(
        chat_id=settings.TELEGRAM_PSYCHOLOGIST_ROOM, text=f"A user requested psychological help: {user.first_name}"
    )
    update.message.reply_text("Forwarded your request to the psychologists' room!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def new_members_room(update, context):
    user = update.effective_user
    context.bot.send_message(
        chat_id=settings.TELEGRAM_NEW_MEMBERS_ROOM, text=f"A user wants to help: {user.first_name}"
    )
    update.message.reply_text("Forwarded your request to the new members' room!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", are_you_ok)],
    states={
        FEEL_OK: [
            MessageHandler(filter_yes, wanna_help),
            MessageHandler(filter_no, cough)
            ],
        WANNA_HELP: [
            MessageHandler(filter_yes, new_members_room),
            MessageHandler(filter_no, bye)
            ],
        COUGH_FEVER: [
            MessageHandler(filter_yes, doctors_room),
            MessageHandler(filter_no, stressed)
            ],
        STRESSED_ANXIOUS: [
            MessageHandler(filter_yes, psychologists_room),
            MessageHandler(filter_no, bye)
            ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


def main():
    """the main event loop"""

    logging.info('Starting corona telegram-bot')

    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
