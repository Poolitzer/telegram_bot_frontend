# -*- coding: utf-8 -*-
import time

from conversationrequest import ConversationRequest


class ConversationRequests(object):
    _requests = list()

    def __init__(self):
        pass

    def add(self, req: ConversationRequest):
        if req in self._requests:
            raise Exception("User already waiting")
        self._requests.append(req)

    def get_request_by_user(self, user_id):
        for req in self._requests:
            if req.user.user_id == user_id:
                return req
        return None

    def has_user_request(self, user_id):
        return self.get_request_by_user(user_id) is not None

    def close(self, req):
        try:
            self._requests.remove(req)
        except ValueError:
            pass

    def close_by_user(self, user_id):
        try:
            req = self.get_request_by_user(user_id)
            if req is not None:
                self._requests.remove(req)
        except ValueError:
            pass

    def get_waiting_requests(self, waiting_minutes=15):
        now = int(time.time())
        tmp_reqs = list()
        for req in self._requests:
            time_diff = now - req.waiting_since
            if time_diff >= waiting_minutes * 60:
                tmp_reqs.append(req)

        return tmp_reqs
