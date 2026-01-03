import json
import logging
import os
import random
import string
from datetime import datetime, timedelta

import requests
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from .model import SquadXmlEntry, TeamspeakAccount, TeamspeakAuthkey, TeamspeakMessage

CONFIG_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database_config.json')


class Database:
    def __init__(self):
        self._load_config()
        self._setup_engines()
        self._insert_default_welcome_messages()

    def _load_config(self):
        logging.info(f'Loading Database config from {CONFIG_FILEPATH}')

        if os.path.exists(CONFIG_FILEPATH):
            with open(CONFIG_FILEPATH) as json_file:
                self._settings = json.load(json_file)
        else:
            self._settings = {
                'db_host': 'localhost',
                'db_name_teamspeak': 'arma3',
                'db_username_teamspeak': 'username',
                'db_password_teamspeak': 'password',
                'db_name_webpage': 'arma3',
                'db_username_webpage': 'username',
                'db_password_webpage': 'password',
            }

            with open(CONFIG_FILEPATH, 'w') as outfile:
                json.dump(self._settings, outfile, sort_keys=True, indent=4)

    def _setup_engines(self):
        ts_url = (
            f"mariadb+mariadbconnector://{self._settings['db_username_teamspeak']}:"
            f"{self._settings['db_password_teamspeak']}@"
            f"{self._settings['db_host']}/{self._settings['db_name_teamspeak']}"
        )
        wp_url = (
            f"mariadb+mariadbconnector://{self._settings['db_username_webpage']}:"
            f"{self._settings['db_password_webpage']}@"
            f"{self._settings['db_host']}/{self._settings['db_name_webpage']}"
        )
        self._engine_teamspeak = create_engine(ts_url)
        self._engine_webpage = create_engine(wp_url)

    def _insert_default_welcome_messages(self):
        with open('../../default_guest_welcome_message.txt', 'r') as fp:
            message = fp.read()

        with Session(self._engine_teamspeak) as session:
            existing = session.get(TeamspeakMessage, "GUEST_MSG")
            if existing is None:
                msg = TeamspeakMessage(message_type="GUEST_MSG", message_text=message)
                session.add(msg)
                session.commit()

    def get_guest_welcome_message(self) -> str | None:
        with Session(self._engine_teamspeak) as session:
            msg = session.get(TeamspeakMessage, "GUEST_MSG")
            return msg.message_text if msg else None

    def get_user_id(self, teamspeak_uid: str) -> int | None:
        with Session(self._engine_teamspeak) as session:
            stmt = select(TeamspeakAccount.user_id).where(
                TeamspeakAccount.teamspeak_uid == teamspeak_uid
            )
            return session.scalar(stmt)

    def get_steam_id(self, teamspeak_uid: str) -> str | None:
        with Session(self._engine_teamspeak) as session:
            stmt = select(TeamspeakAccount.steam_id).where(
                TeamspeakAccount.teamspeak_uid == teamspeak_uid
            )
            return session.scalar(stmt)

    def has_user_id(self, teamspeak_uid: str) -> bool:
        return self.get_user_id(teamspeak_uid) is not None

    @staticmethod
    def _generate_authkey() -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(random.choice(alphabet) for _ in range(32))

    def _get_authkeys(self) -> list[str]:
        with Session(self._engine_teamspeak) as session:
            stmt = select(TeamspeakAuthkey.authkey)
            return list(session.scalars(stmt))

    def generate_authkey(self, teamspeak_uid: str) -> str:
        authkeys = self._get_authkeys()
        authkey = self._generate_authkey()
        while authkey in authkeys:
            authkey = self._generate_authkey()

        with Session(self._engine_teamspeak) as session:
            # delete previous authkeys for this user
            stmt = delete(TeamspeakAuthkey).where(
                TeamspeakAuthkey.teamspeak_uid == teamspeak_uid
            )
            session.execute(stmt)

            # delete outdated authkeys
            cutoff = datetime.now() - timedelta(minutes=10)
            stmt = delete(TeamspeakAuthkey).where(
                TeamspeakAuthkey.generated_date < cutoff
            )
            session.execute(stmt)

            # insert new authkey
            new_authkey = TeamspeakAuthkey(
                authkey=authkey,
                teamspeak_uid=teamspeak_uid,
                generated_date=datetime.now(),
            )
            session.add(new_authkey)
            session.commit()

        return "https://kellerkompanie.com/teamspeak/link_account.php?authkey=" + authkey

    def has_squad_xml_entry(self, steam_id: str) -> bool:
        with Session(self._engine_webpage) as session:
            entry = session.get(SquadXmlEntry, steam_id)
            return entry is not None

    def create_squad_xml_entry(self, steam_id: str, nick: str):
        with Session(self._engine_webpage) as session:
            entry = SquadXmlEntry(player_id=steam_id, nick=nick)
            session.add(entry)
            session.commit()

        # call webpage to actually write the new squad.xml file
        requests.get("https://kellerkompanie.com/profile.php?update_squad_xml=true")
