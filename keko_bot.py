import json
import os

import ts3API.Events as Events
from ts3API.TS3Connection import TS3Connection

settings = None
CONFIG_FILEPATH = 'keko_bot.json'


def load_config():
    global settings

    if os.path.exists(CONFIG_FILEPATH):
        with open(CONFIG_FILEPATH) as json_file:
            settings = json.load(json_file)
    else:
        settings = {'host': '0.0.0.0',
                    'port': 10011,
                    'user': 'serveradmin',
                    'password': 'password',
                    'default_channel': 'Botchannel-or-any-other',
                    'sid': 1,
                    'nickname': 'KeKo Bot'}

        with open(CONFIG_FILEPATH, 'w') as outfile:
            json.dump(settings, outfile, sort_keys=True, indent=4)


def on_event(sender, **kw):
    """
    Event handling method
    """
    # Get the parsed event from the dictionary
    event = kw["event"]
    if type(event) is Events.TextMessageEvent:
        # Prevent the client from sending messages to itself
        if event.invoker_id != int(ts3conn.whoami()["client_id"]):
            ts3conn.sendtextmessage(targetmode=1, target=event.invoker_id, msg="I received your message!")


if __name__ == "__main__":
    load_config()

    user = settings['user']
    password = settings['password']
    host = settings['host']
    port = settings['port']
    nickname = settings['nickname']

    print("KeKo Bot starting")
    print("connecting to", host, "on port", port)
    print("query login as", user, "with password", password)
    print("using nickname", nickname)

    # Connect to the Query Port
    ts3conn = TS3Connection(host, port)
    # Login with query credentials
    ts3conn.login(user, password)
    # Choose a virtual server
    ts3conn.use(sid=settings['sid'])
    # Find the channel to move the query client to
    channel = ts3conn.channelfind(pattern=settings['default_channel'])[0]["cid"]
    # Give the Query Client a name
    ts3conn.clientupdate(["client_nickname=" + nickname])
    # Move the Query client
    ts3conn.clientmove(channel, int(ts3conn.whoami()["client_id"]))
    # Register for server wide events
    ts3conn.register_for_server_events(on_event)
    # Register for private messages
    ts3conn.register_for_private_messages(on_event)
    # Start the loop to send connection keepalive messages
    ts3conn.start_keepalive_loop()
