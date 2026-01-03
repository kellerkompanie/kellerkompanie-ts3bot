import asyncio
import json
import logging
import os

import requests

from keko.ts3api import (
    ClientEnteredEvent,
    ClientLeftEvent,
    ClientMovedEvent,
    ClientMovedSelfEvent,
    TextMessageEvent,
    TS3Connection,
    TS3Event,
    TS3QueryError,
)
from keko.ts3bot.database import Database

CONFIG_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keko_bot.json')

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, client_id: int, client_uid: str, client_name: str, client_dbid: int):
        self.client_id = client_id
        self.client_uid = client_uid
        self.client_name = client_name
        self.client_dbid = client_dbid

    def __repr__(self) -> str:
        return f"{self.client_name} [id:{self.client_id} uid:{self.client_uid}]"


class KeKoBot:
    def __init__(self) -> None:
        self.connected_clients: dict[int, Client] = {}
        self.ts3conn: TS3Connection | None = None
        self.user = 'serveradmin'
        self.password = 'password'
        self.host = '0.0.0.0'
        self.port = 10011
        self.nickname = 'Kellerkompanie Bot'
        self.default_channel = 'Botchannel'
        self.server_id = 1
        self.client_id: int | None = None
        self.load_settings()
        self.database = Database()

    def load_settings(self) -> None:
        logger.info(f'Loading KeKoBot config from {CONFIG_FILEPATH}')

        if os.path.exists(CONFIG_FILEPATH):
            with open(CONFIG_FILEPATH) as json_file:
                settings = json.load(json_file)
        else:
            settings = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'default_channel': self.default_channel,
                'server_id': self.server_id,
                'nickname': self.nickname,
            }

            with open(CONFIG_FILEPATH, 'w') as outfile:
                json.dump(settings, outfile, sort_keys=True, indent=4)

        self.user = settings['user']
        self.password = settings['password']
        self.host = settings['host']
        self.port = settings['port']
        self.nickname = settings['nickname']
        self.server_id = settings['server_id']
        self.default_channel = settings['default_channel']

    async def current_channel_id(self) -> int:
        assert self.ts3conn is not None
        whoami = await self.ts3conn.whoami()
        return int(whoami["client_channel_id"])

    def get_client(self, client_id: int) -> Client:
        return self.connected_clients[int(client_id)]

    def set_client(self, client_id: int, client: Client) -> None:
        self.connected_clients[int(client_id)] = client

    async def on_event(self, event: TS3Event) -> None:
        """Event handling method."""
        match event:
            case TextMessageEvent():
                await self.on_text_message(event)
            case ClientEnteredEvent():
                await self.on_client_entered(event)
            case ClientLeftEvent():
                await self.on_client_left(event)
            case ClientMovedEvent() | ClientMovedSelfEvent():
                await self.on_client_moved(event)
            case _:
                logger.debug(f"unhandled event: {event}")

    async def on_client_moved(self, event: ClientMovedEvent | ClientMovedSelfEvent) -> None:
        moved_client = self.get_client(event.client_id)
        target_channel_id = event.target_channel_id
        if target_channel_id == await self.current_channel_id():
            self.on_client_moved_to_own_channel(moved_client)

    async def on_text_message(self, event: TextMessageEvent) -> None:
        assert self.ts3conn is not None
        chat_partner = self.get_client(event.invoker_id)

        # Prevent the client from sending messages to itself
        if chat_partner.client_id != self.client_id:
            if event.message.startswith("!hi"):
                await self.ts3conn.sendtextmessage(
                    targetmode=1,
                    target=chat_partner.client_id,
                    msg=f"Hallo {chat_partner.client_name}!",
                )
            elif event.message.startswith("!edit"):
                await self.ts3conn.sendtextmessage(
                    targetmode=1,
                    target=chat_partner.client_id,
                    msg="OK! Und los...",
                )
            elif event.message.startswith("!link"):
                teamspeak_uid = chat_partner.client_uid
                has_user_id = self.database.has_user_id(teamspeak_uid)
                user_id = self.database.get_user_id(teamspeak_uid)
                await self.ts3conn.sendtextmessage(
                    targetmode=1,
                    target=chat_partner.client_id,
                    msg=f"has_user_id: {has_user_id}",
                )
                await self.ts3conn.sendtextmessage(
                    targetmode=1,
                    target=chat_partner.client_id,
                    msg=f"user_id: {user_id}",
                )
                authkey_link = self.database.generate_authkey(teamspeak_uid)
                await self.ts3conn.sendtextmessage(
                    targetmode=1,
                    target=chat_partner.client_id,
                    msg=authkey_link,
                )

    async def on_client_entered(self, event: ClientEnteredEvent) -> None:
        assert self.ts3conn is not None
        client_name = event.client_name
        client_uid = event.client_uid
        client_id = event.client_id
        client_dbid = event.client_dbid
        client = Client(
            client_id=client_id,
            client_uid=client_uid,
            client_name=client_name,
            client_dbid=client_dbid,
        )
        self.set_client(client_id, client)

        print("client entered", client)

        if await self.is_guest(client_id):
            message = self.database.get_guest_welcome_message()
            await self.ts3conn.sendtextmessage(targetmode=1, target=client_id, msg=message)
        elif not self.database.has_user_id(client_uid):
            await self.send_link_account_message(client)
        else:
            await self.update_squad_xml_entry(client)
            await self.update_stammspieler_status(client)

    async def is_guest(self, client_id: int) -> bool:
        return await self.is_client_in_group(client_id, 'Guest')

    async def get_server_group_by_name(self, group_name: str) -> int:
        assert self.ts3conn is not None
        server_groups = await self.ts3conn.servergrouplist()

        for server_group in server_groups:
            if server_group['type'] == '1' and server_group['name'] == group_name:
                return int(server_group['sgid'])

        raise ValueError(f"No group found for name '{group_name}'")

    async def is_client_in_group(self, client_id: int, group_name: str) -> bool:
        group_id = await self.get_server_group_by_name(group_name)
        client_groups = await self.get_client_groups(client_id)
        return group_id in client_groups

    async def get_client_groups(self, client_id: int) -> list[int]:
        assert self.ts3conn is not None
        client_info = await self.ts3conn.clientinfo(client_id)
        client_group_ids = [int(x) for x in client_info['client_servergroups'].split(',')]
        return client_group_ids

    async def update_squad_xml_entry(self, client: Client) -> None:
        steam_id = self.database.get_steam_id(client.client_uid)

        if not self.database.has_squad_xml_entry(steam_id):
            username_url = f"http://server.kellerkompanie.com:5000/username/{steam_id}"
            nick = requests.get(username_url).text
            if nick and len(nick) > 0:
                self.database.create_squad_xml_entry(steam_id, nick)

    async def update_stammspieler_status(self, client: Client) -> None:
        assert self.ts3conn is not None
        stammspieler_sgid = await self.get_server_group_by_name("Stammspieler")
        steam_id = self.database.get_steam_id(client.client_uid)
        stammspieler_url = f"http://server.kellerkompanie.com:5000/stammspieler/{steam_id}"
        response = requests.get(stammspieler_url)
        stammspieler_status = bool(json.loads(response.text)['stammspieler'])

        client_is_in_group = await self.is_client_in_group(client.client_id, "Stammspieler")

        if stammspieler_status and not client_is_in_group:
            print(f"adding user {client.client_name} to server group stammspieler")
            await self.ts3conn.servergroupaddclient(sgid=stammspieler_sgid, cldbid=client.client_dbid)
        elif not stammspieler_status and client_is_in_group:
            print(f"removing user {client.client_name} from server group stammspieler")
            await self.ts3conn.servergroupdelclient(sgid=stammspieler_sgid, cldbid=client.client_dbid)

    async def on_client_left(self, event: ClientLeftEvent) -> None:
        client_id = event.client_id
        client = self.get_client(client_id)
        del self.connected_clients[int(client_id)]
        print("client left", client)

    @staticmethod
    def on_client_moved_to_own_channel(client: Client) -> None:
        print("client entered own channel:", client)

    async def send_link_account_message(self, client: Client) -> None:
        assert self.ts3conn is not None
        authkey_link = self.database.generate_authkey(client.client_uid)
        message = (
            f"Hallo {client.client_name}! Deine Teamspeak Identität ist nicht mit der "
            f"Kellerkompanie Webseite verknüpft. Klicke auf folgenden Link um die Accounts "
            f"zu verknüpfen:\n\n{authkey_link}"
        )
        await self.ts3conn.sendtextmessage(targetmode=1, target=client.client_id, msg=message)

    async def start_bot(self) -> None:
        print("Kellerkompanie Bot starting")
        print(f"connecting to {self.host}:{self.port} as {self.nickname}")

        async with TS3Connection(self.host, self.port) as conn:
            self.ts3conn = conn

            # Login with query credentials
            await conn.login(self.user, self.password)

            # Choose a virtual server
            await conn.use(self.server_id)

            # Find the channel to move the query client to
            channels = await conn.channelfind(pattern=self.default_channel)
            channel = int(channels[0]["cid"])

            # Give the Query Client a name
            try:
                await conn.clientupdate(client_nickname=self.nickname)
            except TS3QueryError:
                pass

            # Find own client id
            whoami = await conn.whoami()
            self.client_id = int(whoami["client_id"])

            # Iterate through all currently connected clients
            print("currently connected clients:")
            for client_data in await conn.clientlist():
                client_id = int(client_data["clid"])
                client_name = client_data["client_nickname"]
                client_info = await conn.clientinfo(client_id)
                client_uid = client_info["client_unique_identifier"]
                client_dbid = int(client_info["client_database_id"])
                client = Client(
                    client_id=client_id,
                    client_uid=client_uid,
                    client_name=client_name,
                    client_dbid=client_dbid,
                )
                self.set_client(client_id, client)
                print("\t", client)

                if client_id == self.client_id:
                    continue

                if await self.is_guest(client_id):
                    message = self.database.get_guest_welcome_message()
                    await conn.sendtextmessage(targetmode=1, target=client_id, msg=message)
                elif not self.database.has_user_id(client_uid):
                    await self.send_link_account_message(client=client)
                else:
                    await self.update_squad_xml_entry(client=client)
                    await self.update_stammspieler_status(client=client)

            # Move the Query client
            await conn.clientmove(channel, self.client_id)

            # Register for events
            await conn.register_for_server_events()
            await conn.register_for_server_messages()
            await conn.register_for_channel_events(channel_id=channel)
            await conn.register_for_channel_messages()
            await conn.register_for_private_messages()

            # Start keepalive
            await conn.start_keepalive()

            # Event loop
            async for event in conn.events():
                await self.on_event(event)


def main() -> None:
    keko_bot = KeKoBot()
    asyncio.run(keko_bot.start_bot())


if __name__ == "__main__":
    main()
