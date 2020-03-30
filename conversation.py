# -*- coding: utf-8 -*-


class Conversation(object):

    def __init__(self, worker, user, type):
        if worker == user:
            raise ValueError("Worker can't be the same as user")
        self.worker = worker
        self.user = user
        self.type = type

    def __repr__(self):
        return "Conversation(worker: {}, user: {})".format(self.worker, self.user)
