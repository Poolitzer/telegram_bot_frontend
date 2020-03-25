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
from enum import IntEnum

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.utils import helpers

from config import settings
from conversations import Conversations

conversations = Conversations()

# enable logging
project_path = os.path.dirname(os.path.abspath(__file__))
logdir_path = os.path.join(project_path, "logs")
logfile_path = os.path.join(logdir_path, "bot.log")

if not os.path.exists(logdir_path):
    os.makedirs(logdir_path)

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logfile_handler])
logging.getLogger("telegram").setLevel(logging.WARNING)



# definitions
class Decisions(IntEnum):
    AGE = 1
    FEEL_OK = 2
    COUGH_FEVER = 3
    STRESSED_ANXIOUS = 4
    WANNA_HELP = 5
    TELL_FRIENDS = 6
    CASE_DESC = 7

yes_no_keyboard = ReplyKeyboardMarkup([["Yes", "No"]])
filter_yes = Filters.regex("^Yes$")
filter_no = Filters.regex("^No$")


# methods & commands
def cancel(update, context):
    text_cancel = "Bye! I hope we can talk again some day."
    update.message.reply_text(text=text_cancel, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def welcome(update, context):
    """Greets users, which use the /start command"""
    if conversations.has_active_conversation(update.effective_user.id):
        update.message.reply_text("You are already having a conversation. You can end it with /stop.")
        return ConversationHandler.END
    elif conversations.is_user_waiting(update.effective_user.id):
        update.message.reply_text("You are already waiting for an answer. Please be patient. We'll handle you request soon.")
        return ConversationHandler.END

    text_greeting = "Hello there. Thank you for contacting HumanbiOS."
    context.user_data["decision"] = None
    update.message.reply_text(text=text_greeting)

    text_are_you_okay = "Are you feeling Ok?"
    update.message.reply_text(text=text_are_you_okay, reply_markup=yes_no_keyboard)
    return Decisions.FEEL_OK

def cough(update, context):
    text_cough = "Oh no, I'm sorry about that! Are you having cough or fever?"
    context.user_data["decision"] = Decisions.COUGH_FEVER
    update.message.reply_text(text=text_cough, reply_markup=yes_no_keyboard)
    return Decisions.COUGH_FEVER


def stressed(update, context):
    text_stressed = "Good! Are you feeling stressed or anxious?"
    context.user_data["decision"] = Decisions.STRESSED_ANXIOUS
    update.message.reply_text(text=text_stressed, reply_markup=yes_no_keyboard)
    return Decisions.STRESSED_ANXIOUS


def wanna_help(update, context):
    # TODO we need some way to invite new members to the group chat
    text_wanna_help = "That's great! Do you wanna help?"
    context.user_data["decision"] = Decisions.WANNA_HELP
    update.message.reply_text(text=text_wanna_help, reply_markup=yes_no_keyboard)
    return Decisions.WANNA_HELP

def desc(update, context):
    decision = context.user_data.get("decision", None)

    if decision is None:
        logger.error("Decision is None")
        return ConversationHandler.END
    elif decision == Decisions.STRESSED_ANXIOUS:
        text = "Please tell us a little about your current situation. How are you feeling? Are you afraid? Take a minute to relax and breath. " \
               "Tell us also about your friends and family"
    elif decision == Decisions.COUGH_FEVER:
        text = "Dear patient, we will try to help you as much as we can. Please tell us about your symptoms. Also what is your current body temperature?"
    elif decision == Decisions.WANNA_HELP:
        text = "Welcome new member. We are so glad you’re here! Please provide a short description of what you would like to help with and what you can do. " \
               "Keep it brief and professional"
    else:
        logger.error("Unknown desicion {}".format(decision))
        return ConversationHandler.END
    update.message.reply_text(text=text, reply_markup=ReplyKeyboardRemove())
    return Decisions.CASE_DESC

def bye(update, context):
    text_bye = "Okay, please tell your friends about humanbios!"
    update.message.reply_text(text=text_bye, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def forward(update, context):
    """Forwards a user's data based on their previous decisions to a certain group"""
    decision = context.user_data.get("decision", None)

    if decision is None:
        logger.error("Decision is None")
        return ConversationHandler.END
    elif decision == Decisions.STRESSED_ANXIOUS:
        psychologists_room(update, context)
    elif decision == Decisions.COUGH_FEVER:
        doctors_room(update, context)
    elif decision == Decisions.WANNA_HELP:
        new_members_room(update, context)

    return ConversationHandler.END

def doctors_room(update, context):
    user = update.effective_user
    assign_url = helpers.create_deep_linked_url(context.bot.get_me().username, "doctor_" + str(user.id))
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
    update.message.reply_text(
        "Forwarded your request to the doctor's room!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def psychologists_room(update, context):
    user = update.effective_user
    assign_url = helpers.create_deep_linked_url(context.bot.get_me().username, "psychologist_" + str(user.id))
    conversations.new_user(user.id)
    context.bot.send_message(
        chat_id=settings.TELEGRAM_PSYCHOLOGIST_ROOM, text=f"A user wants to talk!\n\n"
                                                          f"Name: {user.first_name}\n"
                                                          f"Username: @{user.username}\n"
                                                          f"Case description: {update.message.text}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Assign Case to me", url=assign_url),
                                            InlineKeyboardButton(callback_data="report_" + str(user.id), text="Report User")]])
    )
    update.message.reply_text(
        "Forwarded your request to the psychologists' room!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def new_members_room(update, context):
    # TODO We need something similar to the "assign case to me" button for this case
    user = update.effective_user
    context.bot.send_message(
        chat_id=settings.TELEGRAM_NEW_MEMBERS_ROOM, text=f"A user wants to help:\n\n"
                                                         f"Name: {user.first_name}\n"
                                                         f"Username: @{user.username}\n"
                                                         f"Case description: {update.message.text}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(callback_data="report_" + str(user.id), text="Report User")]])
    )
    update.message.reply_text(
        "Forwarded your request to the new members' room!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

yesfilter = Filters.regex('^Yes$')
nofilter = Filters.regex('^No$')

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", welcome)],
    states={
        Decisions.FEEL_OK: [
            MessageHandler(yesfilter, wanna_help),
            MessageHandler(nofilter, cough)
        ],

        Decisions.WANNA_HELP: [
            MessageHandler(yesfilter, desc),
            MessageHandler(nofilter, bye)
        ],

        Decisions.COUGH_FEVER: [
            MessageHandler(yesfilter, desc),
            MessageHandler(nofilter, stressed)
        ],

        Decisions.STRESSED_ANXIOUS: [
            MessageHandler(yesfilter, desc),
            MessageHandler(nofilter, bye)
        ],

        Decisions.CASE_DESC: [
            MessageHandler(Filters.text, forward)
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
    user_id = int(update.message.text.split("_")[-1])

    if conversations.has_active_conversation(update.effective_user.id):
        update.message.reply_text("Sorry, you are already in a conversation. Please use /stop to end it, before starting a new one.")
        return

    if user_id not in conversations.waiting_queue:
        if user_id not in conversations.active_conversations:
            update.message.reply_text("Sorry, but this case is already closed!")
            return
        update.message.reply_text("Sorry, but this case is assigned to someone else!")
        return

    context.user_data["case"] = user_id
    try:
        conversations.new_conversation(update.effective_user.id, user_id)
    except ValueError:
        update.message.reply_text("You can't talk to yourself! Please wait for someone else to take over your case.")
        return
    update.message.reply_text("Case assigned to you! You are now connected to the patient!")
    context.bot.send_message(chat_id=user_id, text="Hey, we found a doctor who can help you. You are now connected to them - simply send your messages in "
                                                   "here.")

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
    else:
        logger.error("The sender is neither a worker nor a user!")
        return

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
    update.message.reply_text("Sorry, I can only handle text messages for now!")

def main():
    """the main event loop"""
    logger.info('Starting corona telegram-bot')

    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"doctor_\d+$")))
    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"psychologist_\d+$")))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(report_handler, pattern=r"^report_\d+$"))
    dispatcher.add_handler(CommandHandler("stop", stop_conversation))

    # Handle chats between workers and users
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, chat_handler))
    dispatcher.add_handler(MessageHandler(~Filters.text & Filters.private, forbidden_handler))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
