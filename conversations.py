# -*- coding: utf-8 -*-
import time

from conversation import Conversation
from conversationrequests import ConversationRequests
from conversationrequest import ConversationRequest
from conversationrequest import ConversationType
from user import User


class Conversations(object):
    __instance = None
    _initialized = False
    LIMIT_CONCURRENT_CHATS = 100

    def __init__(self):
        if Conversations._initialized:
            return
        self.conversation_requests = ConversationRequests()
        self.active_conversations = []
        Conversations._initialized = True

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Conversations, cls).__new__(cls)
        return cls.__instance

    def limit_reached(self):
        """Returns True if the number of current active conversations exceed the defined limit"""
        return len(self.active_conversations) >= Conversations.LIMIT_CONCURRENT_CHATS

    def is_user_waiting(self, user_id):
        return self.conversation_requests.has_user_request(user_id)

    def get_waiting_requests(self, waiting_minutes=15):
        """Returns a list of requests waiting for over 15 minutes"""
        return self.conversation_requests.get_waiting_requests(waiting_minutes)

    def has_active_conversation(self, user_id):
        """Checks if a user has active conversations"""
        return self.get_conversation(user_id) is not None

    def get_conversation(self, user_id):
        """Returns the Conversation object for a certain user"""
        for conv in self.active_conversations:
            if conv.worker == user_id or conv.user == user_id:
                return conv

        return None

    def new_conversation(self, worker_id, user_id):
        worker = User(worker_id)
        user = User(user_id)

        req = self.conversation_requests.get_request_by_user(user.user_id)

        conv = Conversation(worker, user, req.type)
        self.active_conversations.append(conv)

        self.conversation_requests.close(req)

    def stop_conversation(self, user_id):
        conv = self.get_conversation(user_id)
        if conv is not None:
            self.active_conversations.remove(conv)

    def request_conversation(self, user_id, first_name, last_name, username, type):
        new_user = User(user_id, first_name, last_name, username)
        req = ConversationRequest(new_user, type)
        self.conversation_requests.add(req)
