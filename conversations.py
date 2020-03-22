# -*- coding: utf-8 -*-
from conversation import Conversation


class Conversations(object):

    def __init__(self):
        self.waiting_queue = []
        self.active_conversations = []

    def get_conversation(self, user):
        if user is not None:
            user = int(user)

        for conv in self.active_conversations:
            if conv.worker == user or conv.user == user:
                return conv

        return None

    def new_conversation(self, worker, user):
        worker = int(worker)
        user = int(user)

        conv = Conversation(worker, user)
        self.active_conversations.append(conv)
        self.waiting_queue.remove(user)

    def stop_conversation(self, user):
        conv = self.get_conversation(user)
        if conv is not None:
            self.active_conversations.remove(conv)

    def new_user(self, user):
        if user not in self.waiting_queue:
            self.waiting_queue.append(int(user))
            return

        raise Exception("User already waiting")

