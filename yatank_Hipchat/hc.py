# -*- coding: utf-8 -*-

import ConfigParser
from os.path import expanduser
from hypchat import HypChat
from hypchat.restobject import User, Room


class HipChatBot(object):

    def __init__(self, options):
        self.options = options
        self.hc = HypChat(options["token"])
        self.hc.capabilities.url = "{hipchat}/capabilities".format(hipchat=self.options["server"])
        self.hc.emoticons.url = "{hipchat}/emoticon".format(hipchat=self.options["server"])
        self.hc.rooms.url = "{hipchat}/room".format(hipchat=self.options["server"])
        self.hc.users_url = "{hipchat}/user".format(hipchat=self.options["server"])

    def msg_to_rooms(self, text, format="text", color="gray"):
        for name in self.options["rooms"]:
            url = "{hipchat}/room/{room}".format(hipchat=self.options["server"],
                                                 room=name)
            room = Room(self.hc.fromurl(url))
            room._requests = self.hc._requests
            room.message(message=text, format=format, notify="0", color=color)

    def msg_to_users(self, text):
        for name in self.options["users"]:
            full_name = "%s@%s" % (name, self.options["domain"])
            url = "{hipchat}/user/{user}".format(hipchat=self.options["server"],
                                                 user=full_name)
            user = User(self.hc.fromurl(url))
            user._requests = self.hc._requests
            user.message(text)
