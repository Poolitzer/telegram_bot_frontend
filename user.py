# -*- coding: utf-8 -*-
import time


class User(object):

    def __init__(self, user_id, first_name=None, last_name=None, username=None):
        self.user_id = int(user_id)
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        if isinstance(other, int):
            return self.user_id == other
        return False

    def __repr__(self):
        return str(self.user_id)
