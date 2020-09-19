#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os

import ts3API.Events as Events
import ts3API.TS3Connection
from database import Database
from ts3API.TS3Connection import TS3Connection

CONFIG_FILEPATH = 'keko_bot.json'


class Client:
    def __init__(self, client_id, client_uid, client_name):
        self.client_id = client_id
        self.client_uid = client_uid
        self.client_name = client_name

    def __repr__(self):
        return "{} [id:{} uid:{}]".format(self.client_name, self.client_id, self.client_uid)


class KeKoBot:
    def __init__(self):
        self.connected_clients = dict()
        self.ts3conn = None
        self.user = 'serveradmin'
        self.password = 'password'
        self.host = '0.0.0.0'
        self.port = 10011
        self.nickname = 'Kellerkompanie Bot'
        self.default_channel = 'Botchannel'
        self.server_id = 1
        self.client_id = None
        self.load_settings()
        self.database = Database()

    def load_settings(self):
        if os.path.exists(CONFIG_FILEPATH):
            with open(CONFIG_FILEPATH) as json_file:
                settings = json.load(json_file)
        else:
            settings = {'host': self.host,
                        'port': self.port,
                        'user': self.user,
                        'password': self.password,
                        'default_channel': self.default_channel,
                        'server_id': self.server_id,
                        'nickname': self.nickname}

            with open(CONFIG_FILEPATH, 'w') as outfile:
                json.dump(settings, outfile, sort_keys=True, indent=4)

        self.user = settings['user']
        self.password = settings['password']
        self.host = settings['host']
        self.port = settings['port']
        self.nickname = settings['nickname']
        self.server_id = settings['server_id']
        self.default_channel = settings['default_channel']

    def current_channel_id(self):
        return int(self.ts3conn.whoami()["client_channel_id"])

    def get_client(self, client_id):
        return self.connected_clients[int(client_id)]

    def set_client(self, client_id, client):
        self.connected_clients[int(client_id)] = client

    def on_event(self, sender, **kwargs):
        """
        Event handling method
        """
        # Get the parsed event from the dictionary
        event = kwargs["event"]
        if type(event) is Events.TextMessageEvent:
            self.on_text_message(event)
        elif type(event) is Events.ClientEnteredEvent:
            self.on_client_entered(event)
        elif type(event) is Events.ClientLeftEvent:
            self.on_client_left(event)
        elif type(event) is Events.ClientMovedEvent:
            self.on_client_moved(event)
        elif type(event) is Events.ClientMovedSelfEvent:
            self.on_client_moved(event)
        else:
            print("unhandled event:", event)

    def on_client_moved(self, event):
        moved_client = self.get_client(event.client_id)
        target_channel_id = event.target_channel_id
        if target_channel_id == self.current_channel_id():
            self.on_client_moved_to_own_channel(moved_client)

    def on_text_message(self, event):
        chat_partner = self.get_client(event.invoker_id)

        # Prevent the client from sending messages to itself
        if chat_partner.client_id != self.client_id:
            # Bot hört nur noch auf bestimmte commands
            if event.message.startswith("!hi"):
                self.ts3conn.sendtextmessage(targetmode=1, target=chat_partner.client_id,
                                             msg="Hallo " + chat_partner.client_name + "!")
            elif event.message.startswith("!edit"):
                self.ts3conn.sendtextmessage(targetmode=1, target=chat_partner.client_id, msg="OK! Und los...")
                # Channel mit Datum+Missionsname wird umbenannt
                # ts3conn.channeledit(cid=34, channel_name="Datum 19:30 - Mission")
            elif event.message.startswith("!link"):
                teamspeak_uid = chat_partner.client_uid
                has_user_id = self.database.has_user_id(teamspeak_uid)
                user_id = self.database.get_user_id(teamspeak_uid)
                self.ts3conn.sendtextmessage(targetmode=1, target=chat_partner.client_id,
                                             msg="has_user_id: " + str(has_user_id))
                self.ts3conn.sendtextmessage(targetmode=1, target=chat_partner.client_id,
                                             msg="user_id: " + str(user_id))
                authkey_link = self.database.generate_authkey(teamspeak_uid)
                self.ts3conn.sendtextmessage(targetmode=1, target=chat_partner.client_id, msg=authkey_link)

    def on_client_entered(self, event):
        client_name = event.client_name
        client_uid = event.client_uid
        client_id = event.client_id
        client = Client(client_id=client_id, client_uid=client_uid, client_name=client_name)
        self.set_client(client_id, client)

        print("client entered", client)

        if self.is_guest(client_id):
            with open('guest_welcome_message.txt', 'r') as fp:
                message = fp.read()
            self.ts3conn.sendtextmessage(targetmode=1, target=client_id, msg=message)
        elif not self.database.has_user_id(client_uid):
            self.send_link_account_message(client_id, client_uid, client_name)

    def is_guest(self, client_id):
        return self.is_client_in_group(client_id, 'Guest')

    def is_client_in_group(self, client_id, group_name):
        server_groups = self.ts3conn.servergrouplist()

        group_id = None
        for server_group in server_groups:
            if server_group['name'] == group_name:
                group_id = int(server_group['sgid'])
                break

        if not group_id:
            raise ValueError("No group found for name '{}'".format(group_name))

        print("found group_id for '{}': {}".format(group_id, group_name))

        return group_id in self.get_client_groups(client_id)

    def get_client_groups(self, client_id):
        client_info = self.ts3conn.clientinfo(client_id=client_id)
        client_group_ids = [int(x) for x in client_info['client_servergroups'].split(',')]
        print('client_group_ids:', client_group_ids)
        return client_group_ids

    def on_client_left(self, event):
        client_id = event.client_id
        client = self.get_client(client_id)
        del self.connected_clients[int(client_id)]
        print("client left", client)

    def on_client_moved_to_own_channel(self, client):
        print("client entered own channel:", client)
        # Idee: Bot reagiert wenn jmd in seinen Channel geht und öffnet chat:
        self.ts3conn.sendtextmessage(targetmode=1, target=client.client_id, msg="Hallo, I bims 1 KeKo Bot!")

    def send_link_account_message(self, client_id, client_uid, client_name):
        authkey_link = self.database.generate_authkey(client_uid)
        message = "Hallo {}! Es scheint als wäre dein Teamspeak User nicht mit der Kellerkompanie Webseite verknüpft. " \
                  "Klicke auf folgenden Link um die Accounts zu verknüpfen:\n\n{}".format(client_name, authkey_link)
        self.ts3conn.sendtextmessage(targetmode=1, target=client_id, msg=message)

    def start_bot(self):
        print("Kellerkompanie Bot starting")
        print("connecting to {}:{} as {}".format(self.host, self.port, self.nickname))

        # Connect to the Query Port
        self.ts3conn = TS3Connection(self.host, self.port)

        # Login with query credentials
        self.ts3conn.login(self.user, self.password)

        # Choose a virtual server
        self.ts3conn.use(self.server_id)

        # Find the channel to move the query client to
        channel = int(self.ts3conn.channelfind(pattern=self.default_channel)[0]["cid"])

        # Give the Query Client a name
        try:
            self.ts3conn.clientupdate(["client_nickname=" + self.nickname])
        except ts3API.TS3Connection.TS3QueryException:
            pass

        # Find own client id
        self.client_id = int(self.ts3conn.whoami()["client_id"])

        # Iterate through all currently connected clients
        print("currently connected clients:")
        for client in self.ts3conn.clientlist():
            client_id = int(client["clid"])
            client_name = client["client_nickname"]
            client_info = self.ts3conn.clientinfo(client_id)
            client_uid = client_info["client_unique_identifier"]
            client = Client(client_id=client_id, client_uid=client_uid, client_name=client_name)
            self.set_client(client_id, client)
            print("\t", client)

            if client_id == self.client_id:
                continue

            if self.is_guest(client_id):
                with open('guest_welcome_message.txt', 'r') as fp:
                    message = fp.read()
                self.ts3conn.sendtextmessage(targetmode=1, target=client_id, msg=message)
            elif not self.database.has_user_id(client_uid):
                self.send_link_account_message(client_id, client_uid, client_name)

        # Move the Query client
        self.ts3conn.clientmove(channel, self.client_id)

        # Register for server wide events
        self.ts3conn.register_for_server_events(self.on_event)

        # Register for server messages
        self.ts3conn.register_for_server_messages(self.on_event)

        # Register for channel events
        self.ts3conn.register_for_channel_events(channel_id=str(channel), event_listener=self.on_event)

        # Register for channel messages
        self.ts3conn.register_for_channel_messages(self.on_event)

        # Register for private messages
        self.ts3conn.register_for_private_messages(self.on_event)

        # Start the loop to send connection keepalive messages
        self.ts3conn.start_keepalive_loop()


if __name__ == "__main__":
    keko_bot = KeKoBot()
    keko_bot.start_bot()
