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

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, CallbackContext as Context
from telegram.utils import helpers

import filters
from config import settings
from conversationrequest import ConversationType
from conversations import Conversations
from demo import demo_conv_handler
import graph
from questions_and_answers import Strings

conversations = Conversations()
qa_strings = Strings()


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
    """Decorator that performs checks and prepares data for the called function"""

    @wraps(func)
    def wrapper(update: Update, context: Context):
        sender = int(update.effective_user.id)
        conversation = conversations.get_conversation(sender)

        if conversation is None:
            return

        if conversation.type == ConversationType.MEDICAL:
            prefix = "👩🏻‍⚕️: "
        elif conversation.type == ConversationType.SOCIAL:
            prefix = "🧔🏻: "
        else:
            logger.error("Conversation is neither social or medical!")
            return

        if sender == conversation.worker:
            recipient = conversation.user
        elif sender == conversation.user:
            recipient = conversation.worker
        else:
            logger.error("Sender is neither worker, nor user!")
            return

        func(update, context, sender, recipient, prefix, conversation)

    return wrapper


# definitions
class Decisions(IntEnum):
    AGE = 1
    FEEL_OK = 2
    MEDICAL = 3
    STRESSED_ANXIOUS = 4
    WANNA_HELP = 5
    TELL_FRIENDS = 6
    CASE_DESC = 7
    ANSWER_LOOP = 8
    DISCLAIMER = 9


yes_no_keyboard = ReplyKeyboardMarkup([["Yes", "No"]])

REPEAT_INTERVAL = 10


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

    text_disclaimer = "Legal notice:\nThe use of this software does not replace medical treatment and does not provide diagnostic services. If you currently" \
                      " feel seriously ill, call a doctor immediately.\n\nThe involved parties act in good faith to fulfill the first aid obligation and the duty " \
                      "to care on a best effort basis.\n\n\nBy using this software, you agree not to hold liable any of the involved parties (specifically " \
                      "including negligent homicide/assault).\n\nThe involved parties include but are not limited to:\n\n- the individuals or organizations " \
                      "you interact with via this software (specifically including personnel with official medical training or expertise)\n- the developers " \
                      "and maintainers of this software\n\n\nAre you agreeing to this disclaimer?"
    update.message.reply_text(text=text_disclaimer, reply_markup=yes_no_keyboard)
    return Decisions.DISCLAIMER


def how_are_you(update, context):
    text_are_you_okay = "Are you feeling Ok?"
    update.message.reply_text(text=text_are_you_okay, reply_markup=yes_no_keyboard)
    return Decisions.FEEL_OK


def medical_issue(update, context):
    text_medical = "Oh no, I'm sorry about that! Can we help you, medical?"
    context.user_data["decision"] = Decisions.MEDICAL
    update.message.reply_text(text=text_medical, reply_markup=yes_no_keyboard)
    return Decisions.MEDICAL


def stressed(update, context):
    text_stressed = "Okay. Are you feeling stressed or anxious?"
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
    elif decision == Decisions.MEDICAL:
        questions(update, context)
        return Decisions.ANSWER_LOOP
    elif decision == Decisions.WANNA_HELP:
        text = "Welcome new member. We are so glad you’re here! Please provide a short description of what you would like to help with and what you can do. " \
               "Keep it brief and professional"
    else:
        logger.error("Unknown decision {}".format(decision))
        return ConversationHandler.END
    update.message.reply_text(text=text, reply_markup=ReplyKeyboardRemove())
    return Decisions.CASE_DESC


def bye(update, context):

    text_bye = "Okay, please tell your friends about humanbios!"
    update.message.reply_text(text=text_bye, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def questions(update, context):
    """Puts users in a question loop, based on the graph data"""
    # getting the node_id from user_data
    node_id = context.user_data.get("node_id", None)
    # here would be an call or the actual user
    user_language = "english"
    if not node_id:
        # means first time entering this loop
        context.user_data["node_id"] = "0"
        # we add the answers to this dictionary. this way, we dont have keyerrors
        context.user_data["answers"] = {}
        question = qa_strings.get_string(user_language, graph.get_next_question("0"))
        text = "Dear patient, we will try to help you as much as we can. This bot will ask a series of question now which will help understanding your case. First one: " + question
        # this means we get a dictionary. The key is the next nod id, the value another dict
        neighbors = graph.get_next_answer("0")
        logger.error(neighbors)
        keyboard_list = []
        for neighbor_id in neighbors:
            # now we have access to the dicts, each of them representing possible answers and leading to different
            # questions. We are storing the answer_id as label attribute of edges
            answer_id = neighbors[neighbor_id]["label"]
            # now we translate
            keyboard_list.append(qa_strings.get_string(user_language, answer_id))
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard_list))
        return Decisions.ANSWER_LOOP
    # as explained above. We are doing this with the old answers to have them available for errors
    neighbors = graph.get_next_answer(node_id)
    keyboard = []
    for neighbor_id in neighbors:
        # now we have access to the dicts, each of them representing possible answers and leading to different
        # questions. We are storing the answer_id as label attribute of edges
        answer_id = neighbors[neighbor_id]["label"]
        # now we translate
        keyboard.append(qa_strings.get_string(user_language, answer_id))
    # this results in one row per egde/possible answer path. later one, we could replace this with math to make it
    # look more consistence
    # this is going to be the node id of the next node, if it exists
    next_id = False
    for neighbor_id in neighbors:
        answer_id = neighbors[neighbor_id]["label"]
        if update.message.text in qa_strings.get_string(user_language, answer_id):
            next_id = neighbor_id
            break
    # this checks if the current node id is a multi choice one
    multi = graph.get_multichoice(node_id)
    # the keyword gets appended with the Finish word in the original language
    finish = qa_strings.get_string(user_language, "FINISH")
    # needs to be implemented here since finish doesnt match the answers, we have the ending of the multi selection
    if multi and update.message.text == finish:
        # we set the message text to all the answers given so far
        update.message.text = context.user_data["answers"][node_id]
        # we can do [0] since multiple choices are not allowed to have several edges
        next_id = list(neighbors)[0]
        # this so the multi handler  doesnt handle the input anymore
        multi = False
    if not next_id:
        # this means the send message was not one of the buttons
        text = "I am sorry, you need to press one of the buttons."
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard))
        return Decisions.ANSWER_LOOP
    if multi:
        # we have an active multichoice questions
        if node_id in context.user_data["answers"]:
            # user could send manually a text from an old button we already have saved
            if update.message.text in context.user_data["answers"][node_id]:
                text = "I am sorry, you need to press one of the buttons."
                new_keyboard = [word for word in keyboard[0] if word not in context.user_data["answers"][node_id]]
                new_keyboard.append(finish)
                update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup([new_keyboard]))
                return Decisions.ANSWER_LOOP
            # storing the answers in a string, separated with a ,
            context.user_data["answers"][node_id] += f", {update.message.text}"
        else:
            # first time saving the answers in user data
            context.user_data["answers"][node_id] = update.message.text
        # we can do 0] since multiple choices are not allowed to have several edges
        new_keyboard = [word for word in keyboard[0] if word not in context.user_data["answers"][node_id]]
        new_keyboard.append(finish)
        text = f"Since this is a multiple choice question, please press more options if you want to. Otherwise, " \
               f"press {finish}"
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup([new_keyboard]))
        return Decisions.ANSWER_LOOP
    # saving the answer as value to the node id of the question as key
    context.user_data["answers"][node_id] = update.message.text
    # we have to separate here since it can be false if we reached the end
    next_question_id = graph.get_next_question(next_id)
    if not next_question_id:
        # this means we have reached an end of the graph
        result = ""
        for answer_id in context.user_data["answers"]:
            # answer_id is actually the node_id of the question
            question = qa_strings.get_string(user_language, graph.get_next_question(answer_id))
            answer = context.user_data["answers"][answer_id]
            # possibility to add markdown if needed
            result += f"{question}: {answer}\n"
        # we are overriding update.message.text so the doctor handler just works
        update.message.text = result
        doctors_room(update, context)
        return ConversationHandler.END
    # this means we have to ask a question, so we get the answers to display them as keyboard
    text = qa_strings.get_string(user_language, next_question_id)
    new_neighbors = graph.get_next_answer(next_id)
    keyboard = []
    for neighbor_id in new_neighbors:
        # now we have access to the dicts, each of them representing possible answers and leading to different
        # questions. We are storing the answer_id as label attribute of edges
        answer_id = new_neighbors[neighbor_id]["label"]
        # now we translate
        keyboard.append(qa_strings.get_string(user_language, answer_id))
    # this results in one row per egde/possible answer path. later one, we could replace this with math to make it
    # look more consistence
    # sending the question
    update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard))
    # saving the new node id in user data
    context.user_data["node_id"] = next_id
    return Decisions.ANSWER_LOOP


def forward(update, context):

    """Forwards a user's data based on their previous decisions to a certain group"""
    decision = context.user_data.get("decision", None)

    if decision is None:
        logger.error("Decision is None")
        return ConversationHandler.END
    elif decision == Decisions.STRESSED_ANXIOUS:
        psychologists_room(update, context)
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
                                                    f"Q&A:\n{update.message.text}",
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


def invalid_answer(update: Update, context: Context):
    text = "Sorry, but that's not any of the expected answers."
    update.message.reply_text(text=text)


yesfilter = Filters.regex('^Yes$')
nofilter = Filters.regex('^No$')

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", welcome)],
    states={
        Decisions.DISCLAIMER: [
            MessageHandler(yesfilter, how_are_you),
            MessageHandler(nofilter, bye)
        ],
        Decisions.FEEL_OK: [
            MessageHandler(yesfilter, wanna_help),
            MessageHandler(nofilter, medical_issue)
        ],

        Decisions.WANNA_HELP: [
            MessageHandler(yesfilter, desc),
            MessageHandler(nofilter, bye)
        ],

        Decisions.MEDICAL: [
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
        Decisions.ANSWER_LOOP: [
            MessageHandler(Filters.text & (~Filters.command), questions)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel), MessageHandler(Filters.all, invalid_answer)],
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

    room_type = context.args[0].split("_")[0]
    logger.setLevel(logging.DEBUG)
    logger.debug("Room type: {}".format(room_type))

    worker_id = update.effective_user.id

    if conversations.has_active_conversation(worker_id):
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
        conversations.new_conversation(worker_id, user_id)

        if context.bot_data.get(worker_id):
            context.bot_data[worker_id] += 1
        else:
            context.bot_data[worker_id] = 1
    except ValueError:
        update.message.reply_text("You can't talk to yourself! Please wait for someone else to take over your case.")
        return
    update.message.reply_text("Case assigned to you! You are now connected to the patient!")

    if room_type == "psychologist":
        update.message.reply_text(
            "[How do you calm someone down?](https://medium.com/@humanbios/how-do-you-calm-someone-down-b178c5a2a3c8)", parse_mode=ParseMode.MARKDOWN)
    if room_type == "doctor" and context.bot_data[worker_id] % REPEAT_INTERVAL == 1:
        update.message.reply_text(
            "[Emergency Heuristics](https://medium.com/@humanbios/emergency-heuristics-2f62e58aa567)", parse_mode=ParseMode.MARKDOWN)
        update.message.reply_text(
            "[WHO treatment recommendations](https://apps.who.int/iris/rest/bitstreams/1272288/retrieve)", parse_mode=ParseMode.MARKDOWN)

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


@chat_conversation
def chat_gif_handler(update, context, sender, recipient, prefix, conversation):
    animation = update.message.animation
    context.bot.send_animation(chat_id=recipient.user_id, animation=animation.file_id)


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
        dispatcher.add_handler(MessageHandler(filters.medical & Filters.private & Filters.photo, chat_photo_handler))
    if settings.CHAT_MEDICAL_ENABLE_GIFS:
        dispatcher.add_handler(MessageHandler(filters.medical & Filters.private & Filters.animation, chat_gif_handler))
    if settings.CHAT_MEDICAL_ENABLE_VOICE:
        dispatcher.add_handler(MessageHandler(filters.medical & Filters.private & Filters.voice, chat_voice_handler))

    if settings.CHAT_SOCIAL_ENABLE_PHOTOS:
        dispatcher.add_handler(MessageHandler(filters.social & Filters.private & Filters.photo, chat_photo_handler))
    if settings.CHAT_SOCIAL_ENABLE_GIFS:
        dispatcher.add_handler(MessageHandler(filters.social & Filters.private & Filters.animation, chat_gif_handler))
    if settings.CHAT_SOCIAL_ENABLE_VOICE:
        dispatcher.add_handler(MessageHandler(filters.social & Filters.private & Filters.voice, chat_voice_handler))

    # Handle all the message types, which are not allowed:
    dispatcher.add_handler(MessageHandler(~Filters.text & Filters.private, forbidden_handler))

    # Schedule jobs to run periodically in the background
    job_queue = updater.job_queue
    job_queue.run_repeating(callback=check_waiting_conversations, interval=60, first=60)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
