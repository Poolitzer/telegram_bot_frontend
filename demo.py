# -*- coding: utf-8 -*-
from enum import IntEnum

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler


class DemoDecisions(IntEnum):
    FAVPIC = 1
    FAMILY = 2
    AMAZON = 3
    DURABLE = 4
    DIFFICULT = 5
    MICHAEL = 6
    WINNER = 7


yes_no_keyboard = ReplyKeyboardMarkup([["Yes", "No"]])
filter_yes = Filters.regex("^Yes$")
filter_no = Filters.regex("^No$")


def demo_intro(update, context):
    text = "Send your favorite picture of Covid!"
    update.message.reply_text(text=text, reply_markup=ReplyKeyboardRemove())
    return DemoDecisions.FAVPIC


def demo_family(update, context):
    text = "Do you agree Covid-19 does have neither family or friends?"
    update.message.reply_text(text=text, reply_markup=yes_no_keyboard)
    return DemoDecisions.FAMILY


def demo_family_invalid_input(update, context):
    text = "Please send me a picture!"
    update.message.reply_text(text=text)


def demo_amazon(update, context):
    text = "How likely would you give Covid-19 0 stars on Amazon? (10=most likely)"
    keyboard = ReplyKeyboardMarkup([["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["10"]])
    update.message.reply_text(text=text, reply_markup=keyboard)
    return DemoDecisions.AMAZON


def demo_durable(update, context):
    text = "Mohammed Ali or Covid-19, who's more durable?"
    keyboard = ReplyKeyboardMarkup([["Mohammed Ali", "Covid-19"]])
    update.message.reply_text(text=text, reply_markup=keyboard)
    return DemoDecisions.DURABLE


def demo_difficult(update, context):
    text = "What's more difficult do build?"
    keyboard = ReplyKeyboardMarkup([["Chinese Wall", "Golden-Gate-Bridge"], ["Eiffel Tower", "Colosseum", "Covid-19 vaccine"]])
    update.message.reply_text(text=text, reply_markup=keyboard)
    return DemoDecisions.DIFFICULT


def demo_michael(update, context):
    text = "If Michael was alive, would he know how to heal Covid-19?"
    keyboard = ReplyKeyboardMarkup([["Yes", "No", "Not so sure"]])
    update.message.reply_text(text=text, reply_markup=keyboard)
    return DemoDecisions.MICHAEL


def demo_winner(update, context):
    text = "Who wins eventually?"
    keyboard = ReplyKeyboardMarkup([["Covid-19", "Humanity"]])
    update.message.reply_text(text=text, reply_markup=keyboard)
    return DemoDecisions.WINNER


def demo_bye(update, context):
    text = "Thank you! Stay healthy."
    update.message.reply_text(text=text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def demo_invalid_answer(update, context):
    text = "That's not an answer from the given possibilities. Please use the buttons."
    update.message.reply_text(text=text)


def cancel(update, context):
    text_cancel = "Bye! I hope we can talk again some day."
    update.message.reply_text(text=text_cancel, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


demo_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("demo", demo_intro)],
    states={
        DemoDecisions.FAVPIC: [
            MessageHandler(Filters.photo, demo_family),
            MessageHandler(Filters.all, demo_family_invalid_input)
        ],
        DemoDecisions.FAMILY: [
            MessageHandler(Filters.text & (filter_yes | filter_no), demo_amazon)
        ],
        DemoDecisions.AMAZON: [
            MessageHandler(Filters.text & Filters.regex(r"[0-9]|10"), demo_durable)
        ],
        DemoDecisions.DURABLE: [
            MessageHandler(Filters.text & Filters.regex(r"Mohammed Ali|Covid-19"), demo_difficult)
        ],
        DemoDecisions.DIFFICULT: [
            MessageHandler(Filters.text & Filters.regex(r"Chinese Wall|Golden-Gate-Bridge|Eiffel Tower|Colosseum|Covid-19 vaccine"), demo_michael)
        ],
        DemoDecisions.MICHAEL: [
            MessageHandler(Filters.text & Filters.regex(r"Yes|No|Not so sure"), demo_winner)
        ],
        DemoDecisions.WINNER: [
            MessageHandler(Filters.text & (Filters.regex(r"") | Filters.regex(r"")), demo_bye)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel), MessageHandler(Filters.all, demo_invalid_answer)],
)
