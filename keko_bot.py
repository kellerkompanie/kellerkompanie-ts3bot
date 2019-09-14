import teamspeak3-python-api as ts3API

from ts3API.TS3Connection import TS3Connection
import ts3API.Events as Events

HOST = "serverhost"
PORT = 10011 # Default Port
USER = 'serveradmin' # Default login
PASS = 'password'
DEFAULTCHANNEL = 'Botchannel-or-any-other'
SID = 1 # Virtual server id
NICKNAME = "aName"

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

# Connect to the Query Port
ts3conn = TS3Connection(HOST, PORT)
# Login with query credentials
ts3conn.login(USER, PASS)
# Choose a virtual server
ts3conn.use(sid=SID)
# Find the channel to move the query client to
channel = ts3conn.channelfind(pattern=DEFAULTCHANNEL)[0]["cid"]
# Give the Query Client a name
ts3conn.clientupdate(["client_nickname="+NICKNAME])
# Move the Query client
ts3conn.clientmove(channel, int(ts3conn.whoami()["client_id"]))
# Register for server wide events
ts3conn.register_for_server_events(on_event)
# Register for private messages
ts3conn.register_for_private_messages(on_event)
# Start the loop to send connection keepalive messages
ts3conn.start_keepalive_loop()