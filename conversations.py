# -*- coding: utf-8 -*-
import time

from conversation import Conversation
from user import User


class Conversations(object):
    __instance = None
    _initialized = False
    LIMIT_CONCURRENT_CHATS = 100

    def __init__(self):
        self.waiting_queue = []
        if Conversations._initialized:
            return
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
        return user_id in self.waiting_queue

    def get_waiting_users(self, waiting_minutes=15):
        """Returns a list of users waiting for over 15 minutes"""
        now = int(time.time())
        tmp_users = []
        for user in self.waiting_queue:
            time_diff = now - user.waiting_since
            if time_diff >= waiting_minutes * 60:
                tmp_users.append(user)

        return tmp_users

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

        conv = Conversation(worker, user)
        self.active_conversations.append(conv)
        self.waiting_queue.remove(user)

    def stop_conversation(self, user_id):
        conv = self.get_conversation(user_id)
        if conv is not None:
            self.active_conversations.remove(conv)

    def new_user(self, user_id, first_name, last_name, username, request_type):
        new_user = User(user_id, first_name, last_name, username, request_type=request_type)
        if new_user not in self.waiting_queue:
            self.waiting_queue.append(new_user)
            return

        raise Exception("User already waiting")
