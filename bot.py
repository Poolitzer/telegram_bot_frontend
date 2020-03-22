#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
telegram bot to connect corona-suspects with medical staff

Bot url:
t.me/corona_care_bot

spec: https://notes.status.im/_zy_XbciTQqQDzVrnTJ7TA?edit

groups the bot forwards to: (has to be a member of the group)
https://t.me/humanbios0k

"""

import logging
import textwrap

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.utils import helpers

from config import settings
from conversations import Conversations

conversations = Conversations()

# enable logging
logging.basicConfig(format="{asctime} {name} {levelname} {message}", style="{", level=logging.INFO)
logger = logging.getLogger(__name__)

# definitions
AGE, FEEL_OK, COUGH_FEVER, STRESSED_ANXIOUS, WANNA_HELP, TELL_FRIENDS, CASE_DESC = range(7)
yes_no_keyboard = ReplyKeyboardMarkup([["Yes", "No"]])
filter_yes = Filters.regex("^Yes$")
filter_no = Filters.regex("^No$")


# methods & commands
def cancel(update, context):
    TEXT_CANCEL = "Bye! I hope we can talk again some day."
    update.message.reply_text(text=textwrap.dedent(TEXT_CANCEL), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def are_you_ok(update, context):
    # TODO check if the user is already waiting for a response and tell them to wait
    TEXT_ARE_YOU_OK = "Hi! Are you feeling Ok?"
    update.message.reply_text(text=textwrap.dedent(TEXT_ARE_YOU_OK), reply_markup=yes_no_keyboard)
    return FEEL_OK

def cough(update, context):
    TEXT_COUGH = "Oh no, I'm sorry about that! Are you having cough or fever?"
    context.user_data["symptoms"] = "Cough or fever"
    update.message.reply_text(
        text=textwrap.dedent(TEXT_COUGH), reply_markup=yes_no_keyboard
    )
    return COUGH_FEVER

def stressed(update, context):
    TEXT_STRESSED = "Good! Are you feeling stressed or anxious?"
    context.user_data["symptoms"] = "Feeling stressed or anxious"
    update.message.reply_text(text=textwrap.dedent(TEXT_STRESSED), reply_markup=yes_no_keyboard)
    return STRESSED_ANXIOUS

def wanna_help(update, context):
    TEXT_WANNA_HELP = "That's great! Do you wanna help?"
    update.message.reply_text(text=textwrap.dedent(TEXT_WANNA_HELP), reply_markup=yes_no_keyboard)
    return WANNA_HELP

def desc(update, context):
    print(update)
    if update.effective_user.id in conversations.waiting_queue:
        update.message.reply_text(text="Hey there, you are already waiting for an answer. Please be patient.")
        return ConversationHandler.END

    TEXT_DESC = "Hello there. It seems that you are having medical issues? Please describe your issues in a few words (max. 200)."
    update.message.reply_text(text=textwrap.dedent(TEXT_DESC))
    return CASE_DESC

def bye(update, context):
    TEXT_BYE = "Okay, Bye!"
    update.message.reply_text(text=textwrap.dedent(TEXT_BYE), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def doctors_room(update, context):
    user = update.effective_user
    assign_url = helpers.create_deep_linked_url(context.bot.get_me().username, "doctor_" + str(user.id))
    context.user_data["desc"] = update.message.text

    conversations.new_user(user.id)
    context.bot.send_message(
        chat_id=settings.TELEGRAM_DOCTOR_ROOM, text=f"A user requested medical help!\n\n"
                                                    f"Name: {user.first_name}\n"
                                                    f"Username: @{user.username}\n"
                                                    f"Case description: {update.message.text}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Assign Case to me", url=assign_url),
                                            InlineKeyboardButton(callback_data="report_" + str(user.id), text="Report User")]])
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
        chat_id=settings.TELEGRAM_NEW_MEMBERS_ROOM, text=f"A user wants to help:\n\nName: {user.first_name}\nUsername: @{user.username}"
    )
    update.message.reply_text("Forwarded your request to the new members' room!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", desc)],
    states={
        CASE_DESC: [
            MessageHandler(Filters.text, doctors_room)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

def report_handler(update, context):
    """Handles the reports of workers"""
    query = update.callback_query
    data = update.callback_query.data
    orig_user_id = update.callback_query.from_user.id
    # TODO check if user is doctor or admin
    # TODO logic for reporting users

    query.answer(text="Thank you for your report!")

def deeplink(update, context):
    # TODO check if the user requesting to take over is a registered doctor/psychologist
    # TODO check if the passed user_id is legit
    # TODO check if the case is already assigned
    user_id = int(update.message.text.split("_")[1])
    print(user_id)

    if user_id not in conversations.waiting_queue:
        if user_id not in conversations.active_conversations:
            update.message.reply_text("Sorry, but this case is already closed!")
            return
        update.message.reply_text("Sorry, but this case is assigned to someone else!")
        return

    context.user_data["case"] = user_id
    conversations.new_conversation(update.effective_user.id, user_id)
    update.message.reply_text("Case assigned to you!")

def chat_handler(update, context):
    """Handles chat messages sent to another user"""
    sender = int(update.effective_user.id)
    conversation = conversations.get_conversation(sender)

    if conversation is None:
        return

    if sender == conversation.worker:
        recipient = conversation.user
        prefix = "👨‍⚕️: "
    elif sender == conversation.user:
        recipient = conversation.worker
        prefix = "👤: "

    context.bot.send_message(chat_id=recipient, text=prefix + update.message.text)

def stop_conversation(update, context):
    sender = int(update.effective_user.id)
    conv = conversations.get_conversation(sender)
    if conv is not None:
        update.message.reply_text("I ended the conversation!")
        if conv.worker == sender:
            recp_id = conv.user
        else:
            recp_id = conv.worker
        context.bot.send_message(chat_id=recp_id, text="Your opponent ended the conversation!")
    conversations.stop_conversation(sender)

def forbidden_handler(update, context):
    update.message.reply_text("Sorry but only text is allowed!")

def main():
    """the main event loop"""
    logger.info('Starting corona telegram-bot')

    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"doctor_\d+")))
    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"^psychologist_\d+$")))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(report_handler, pattern=r"^report_\d+$"))
    dispatcher.add_handler(CommandHandler("stop", stop_conversation))

    # Handle chats between workers and users
    dispatcher.add_handler(MessageHandler(Filters.text, chat_handler))
    dispatcher.add_handler(MessageHandler(~Filters.text, forbidden_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
