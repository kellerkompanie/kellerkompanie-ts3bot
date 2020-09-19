#! /usr/bin/python3
# -*- coding:utf-8 -*-
import json
import os
import random
import string

import pymysql

CONFIG_FILEPATH = 'database_config.json'


class Database:
    def __init__(self):
        self._load_config()
        self._insert_default_welcome_messages()

    def create_connection(self):
        return pymysql.connect(host=self._settings['db_host'],
                               database=self._settings['db_name'],
                               user=self._settings['db_username'],
                               password=self._settings['db_password'])

    def _load_config(self):
        if os.path.exists(CONFIG_FILEPATH):
            with open(CONFIG_FILEPATH) as json_file:
                self._settings = json.load(json_file)
        else:
            self._settings = {'db_host': 'localhost',
                              'db_name': 'arma3',
                              'db_username': 'username',
                              'db_password': 'password'}

            with open(CONFIG_FILEPATH, 'w') as outfile:
                json.dump(self._settings, outfile, sort_keys=True, indent=4)

    def _insert_default_welcome_messages(self):
        with open('default_guest_welcome_message.txt', 'r') as fp:
            message = fp.read()

        connection = self.create_connection()
        cursor = connection.cursor()

        query = "INSERT IGNORE INTO teamspeak_messages (message_type, message_text) VALUES(%s, %s);"
        cursor.execute(query, ("GUEST_MSG", message,))

        connection.commit()
        cursor.close()
        connection.close()

    def get_guest_welcome_message(self):
        connection = self.create_connection()
        cursor = connection.cursor()

        sql = "SELECT message_text FROM teamspeak_messages WHERE message_type=%s;"
        cursor.execute(sql, ("GUEST_MSG",))
        row = cursor.fetchone()
        cursor.close()
        connection.close()

        if row:
            return row[0]
        else:
            return None

    def get_user_id(self, teamspeak_uid):
        connection = self.create_connection()
        cursor = connection.cursor()

        sql = "SELECT user_id FROM teamspeak_accounts WHERE teamspeak_uid=%s;"
        cursor.execute(sql, (teamspeak_uid,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()

        if row:
            return row[0]
        else:
            return None

    def get_steam_id(self, teamspeak_uid):
        connection = self.create_connection()
        cursor = connection.cursor()

        sql = "SELECT steam_id FROM teamspeak_accounts WHERE teamspeak_uid=%s;"
        cursor.execute(sql, (teamspeak_uid,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()

        if row:
            return row[0]
        else:
            return None

    def has_user_id(self, teamspeak_uid):
        return self.get_user_id(teamspeak_uid) is not None

    @staticmethod
    def _generate_authkey():
        alphabet = string.ascii_letters + string.digits
        return ''.join(random.choice(alphabet) for i in range(32))

    def _get_authkeys(self):
        connection = self.create_connection()
        cursor = connection.cursor()

        sql = "SELECT authkey FROM teamspeak_authkeys;"
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        authkeys = []
        for row in rows:
            authkeys.append(row[0])

        return authkeys

    def generate_authkey(self, teamspeak_uid):
        authkeys = self._get_authkeys()
        authkey = self._generate_authkey()
        while authkey in authkeys:
            authkey = self._generate_authkey()

        connection = self.create_connection()

        # delete previous authkeys for this user
        cursor = connection.cursor()
        query = "DELETE FROM teamspeak_authkeys WHERE teamspeak_uid=%s;"
        cursor.execute(query, (teamspeak_uid,))
        connection.commit()
        cursor.close()

        # delete outdated authkeys
        cursor = connection.cursor()
        query = "DELETE FROM teamspeak_authkeys WHERE generated_date < (NOW() - INTERVAL 10 MINUTE);"
        cursor.execute(query)
        connection.commit()
        cursor.close()

        cursor = connection.cursor()
        query = "INSERT INTO teamspeak_authkeys (authkey, teamspeak_uid, generated_date) VALUES(%s, %s, NOW());"
        cursor.execute(query, (authkey, teamspeak_uid,))
        connection.commit()

        cursor.close()
        connection.close()

        return "https://kellerkompanie.com/teamspeak/link_account.php?authkey=" + authkey
