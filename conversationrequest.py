# -*- coding: utf-8 -*-
from enum import IntEnum
import time


class ConversationType(IntEnum):
    SOCIAL = 1
    MEDICAL = 2


class ConversationRequest(object):

    def __init__(self, user, type: ConversationType):
        self.user = user
        self.type = type
        self.waiting_since = int(time.time())

    def __eq__(self, other):
        if isinstance(other, ConversationRequest):
            return self.user.user_id == other.user.user_id
        if isinstance(other, int):
            return self.user.user_id == other
        return False

    def __repr__(self):
        return "ConversationRequest: (user: {}, type: {}, waiting_since: {})".format(self.user, self.type, self.waiting_since)
