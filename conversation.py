# -*- coding: utf-8 -*-


class Conversation(object):

    def __init__(self, worker, user):
        if int(worker) == int(user):
            raise ValueError("Worker can't be the same as user")
        self.worker = int(worker)
        self.user = int(user)

    def __repr__(self):
        return "Conversation(worker: {}, user: {})".format(self.worker, self.user)
