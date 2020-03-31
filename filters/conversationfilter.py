# -*- coding: utf-8 -*-

from telegram.ext import BaseFilter

from conversationrequest import ConversationType
from conversations import Conversations


class ConversationFilter(BaseFilter):
    def filter(self, message):
        """Returns True if the sender of the message is in a conversation"""
        conversations = Conversations()
        return conversations.get_conversation(message.from_user.id) is not None


class ConversationTypeFilter(BaseFilter):

    def __init__(self, conversation_type):
        self.conversation_type = conversation_type

    def filter(self, message):
        """Returns True if the sender of the message is in a conversation"""
        conversations = Conversations()
        conversation = conversations.get_conversation(message.from_user.id)
        if conversation is None:
            return False

        return conversation.type == self.conversation_type


# Remember to initialize the class.
conversation_filter = ConversationFilter()
social = ConversationTypeFilter(ConversationType.SOCIAL)
medical = ConversationTypeFilter(ConversationType.MEDICAL)
