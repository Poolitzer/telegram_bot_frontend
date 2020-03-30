#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
telegram bot to connect corona-suspects with medical staff

Bot url:
t.me/HumanbiOS_bot

Specification: https://hackmd.io/p0vKHdtAR4C1ygXadeTncA?view

Bot currently forwards all cases to:  https://t.me/humanbios (Bot has to be a member of the group)

"""

import logging
import os
from enum import IntEnum
from functools import wraps

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, CallbackContext as Context
from telegram.utils import helpers

from config import settings
from conversationrequest import ConversationType
from conversations import Conversations
from demo import demo_conv_handler
from requesttype import RequestType

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
logger = logging.getLogger(__name__)


def chat_conversation(func):
    @wraps(func)
    def wrapper(update: Update, context: Context):
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
            logger.error("Sender is neither worker, nor user!")
            return

        func(update, context, sender, recipient, prefix, conversation)

    return wrapper


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


# methods & commands
def cancel(update, context):
    text_cancel = "Bye! I hope we can talk again some day."
    update.message.reply_text(text=text_cancel, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def welcome(update, context):

    """Greets users, which use the /start command"""
    if conversations.limit_reached():
        update.message.reply_text("Hello there. Sorry but the queue of waiting users is currently just too long. In order to prevent users from becoming "
                                  "frustrated, because of long waiting times, we decided to not accept new users for now. Please try again soon. Bye.")
        return ConversationHandler.END

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
    conversations.request_conversation(user_id=user.id,
                                       first_name=user.first_name,
                                       last_name=user.last_name,
                                       username=user.username,
                                       type=ConversationType.MEDICAL)
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
    conversations.request_conversation(user_id=user.id,
                                       first_name=user.first_name,
                                       last_name=user.last_name,
                                       username=user.username,
                                       type=ConversationType.SOCIAL)
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

    if not conversations.conversation_requests.has_user_request(user_id):
        if not conversations.has_active_conversation(user_id):
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


@chat_conversation
def chat_text_handler(update, context, sender, recipient, prefix, conversation):
    """Handles chat messages sent to another user"""
    context.bot.send_message(chat_id=recipient.user_id, text=prefix + update.message.text)


@chat_conversation
def chat_media_handler(update, context, sender, recipient, prefix, conversation):
    logger.info(update.message)


@chat_conversation
def chat_audio_handler(update, context, sender, recipient, prefix, conversation):
    context.bot.send_audio(chat_id=recipient.user_id, audio=update.message.audio.file_id)


@chat_conversation
def chat_voice_handler(update, context, sender, recipient, prefix, conversation):
    context.bot.send_voice(chat_id=recipient.user_id, voice=update.message.voice.file_id)


@chat_conversation
def chat_sticker_handler(update, context, sender, recipient, prefix, conversation):
    context.bot.send_message(chat_id=recipient.user_id, text=prefix + "sent a sticker")
    context.bot.send_sticker(chat_id=recipient.user_id, sticker=update.message.sticker.file_id)

@chat_conversation
def chat_photo_handler(update, context, sender, recipient, prefix, conversation):
    photo = update.message.photo[-1]
    context.bot.send_photo(chat_id=recipient.user_id, photo=photo.file_id)


def stop_conversation(update: Update, context: Context):
    sender = int(update.effective_user.id)
    conv = conversations.get_conversation(sender)
    if conv is not None:
        update.message.reply_text("I ended the conversation!")
        if conv.worker == sender:
            recipient = conv.user
        else:
            recipient = conv.worker
        context.bot.send_message(chat_id=recipient.user_id, text="Your opponent ended the conversation!")
    conversations.stop_conversation(sender)


def forbidden_handler(update: Update, context: Context):
    update.message.reply_text("Sorry, I can't handle that type of messages!")


def check_waiting_conversations(context):
    """Check for all users waiting for >15 minutes to notify workers about waiting cases"""
    long_waiting_reqs = conversations.get_waiting_requests()

    for req in long_waiting_reqs:
        user = req.user
        text = "User {} (@{}) is waiting for > 15 minutes!".format(user.first_name, user.username)
        if req.type == ConversationType.MEDICAL:
            context.bot.send_message(settings.TELEGRAM_DOCTOR_ROOM, text=text)
        elif req.type == ConversationType.SOCIAL:
            context.bot.send_message(settings.TELEGRAM_PSYCHOLOGIST_ROOM, text=text)


def main():
    """the main event loop"""
    logger.info('Starting corona telegram-bot')

    updater = Updater(token=settings.TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"doctor_\d+$")))
    dispatcher.add_handler(CommandHandler("start", deeplink, Filters.regex(r"psychologist_\d+$")))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(demo_conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(report_handler, pattern=r"^report_\d+$"))
    dispatcher.add_handler(CommandHandler("stop", stop_conversation))

    # Handle chats between workers and users
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, chat_text_handler))

    if settings.CHAT_MEDICAL_ENABLE_PHOTOS:
        dispatcher.add_handler(MessageHandler(Filters.private & Filters.photo, chat_photo_handler))

    if settings.CHAT_SOCIAL_ENABLE_GIFS:
        dispatcher.add_handler(MessageHandler(Filters.private & Filters.sticker, chat_sticker_handler))
        dispatcher.add_handler(MessageHandler(Filters.private & Filters.audio, chat_audio_handler))
        dispatcher.add_handler(MessageHandler(Filters.private & Filters.voice, chat_voice_handler))

    dispatcher.add_handler(MessageHandler(~Filters.text & Filters.private, forbidden_handler))

    # Schedule jobs to run periodically in the background
    job_queue = updater.job_queue
    job_queue.run_repeating(callback=check_waiting_conversations, interval=60, first=60)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
