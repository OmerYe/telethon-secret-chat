import datetime
import os

from telethon.tl.types import InputEncryptedChat

from telethon_secret_chat.secret_methods import SecretChat
from .memory import SecretMemorySession

try:
    import sqlite3

    sqlite3_err = None
except ImportError as e:
    sqlite3 = None
    sqlite3_err = type(e)

TABLE_NAME = "plugin_secret_chats"


class SQLiteSession(SecretMemorySession):
    """This session contains the required information to login into your
       Telegram account. NEVER give the saved session file to anyone, since
       they would gain instant access to all your messages and contacts.

       If you think the session has been compromised, close all the sessions
       through an official Telegram client to revoke the authorization.
    """

    def __init__(self, sqlite_connection):
        if sqlite3 is None:
            raise sqlite3_err
        if not isinstance(sqlite_connection, sqlite3.Connection):
            raise ConnectionError("Please pass an sqlite3 connection")
        super().__init__()

        self._conn = sqlite_connection
        c = self._conn.cursor()
        c.execute("select name from sqlite_master "
                  f"where type='table' and name={TABLE_NAME}")
        if not c.fetchone():
            # Tables don't exist, create new ones
            self._create_table(
                c,
                f"""{TABLE_NAME} (
                  id integer primary key,
                  access_hash integer,
                  auth_key blob,
                  admin integer,
                  user_id integer,
                  in_seq_no_x integer,
                  out_seq_no_x integer,
                  in_seq_no integer,
                  out_seq_no integer,
                  layer integer,
                  ttl integer,
                  ttr integer,
                  updated integer,
                  created integer,
                  mtproto integer,
                )"""
            )

            c.close()
            self.save()

    @staticmethod
    def _create_table(c, *definitions):
        for definition in definitions:
            c.execute('create table {}'.format(definition))

    def save(self):
        """Saves the current session object as session_user_id.session"""
        # This is a no-op if there are no changes to commit, so there's
        # no need for us to keep track of an "unsaved changes" variable.
        if self._conn is not None:
            self._conn.commit()

    def _execute(self, stmt, *values):
        """
        Gets a cursor, executes `stmt` and closes the cursor,
        fetching one row afterwards and returning its result.
        """
        c = self._conn.cursor()
        try:
            return c.execute(stmt, values).fetchone()
        finally:
            c.close()

    def close(self):
        """Closes the connection unless we're working in-memory"""
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def get_temp_secret_chat_by_id(self, id):
        row = self._execute(
            f"select * from {TABLE_NAME} where type='temp' and id = ?", id)
        if row:
            input_chat = InputEncryptedChat(chat_id=row[0], access_hash=row[1])
            return SecretChat(id=row[0], access_hash=row[1], auth_key=row[2], admin=True if row[3] else False,
                              user_id=row[4], in_seq_no_x=row[5], out_seq_no_x=row[6], in_seq_no=row[7],
                              out_seq_no=row[8], layer=row[9], ttl=row[10], ttr=row[11], updated=row[12],
                              created=row[13], mtproto=row[14], input_chat=input_chat)

    def get_secret_chat_by_id(self, id):
        row = self._execute(
            f"select * from {TABLE_NAME} where type='normal' and id = ?", id)

        if row:
            input_chat = InputEncryptedChat(chat_id=row[0], access_hash=row[1])
            return SecretChat(id=row[0], access_hash=row[1], auth_key=row[2], admin=True if row[3] else False,
                              user_id=row[4], in_seq_no_x=row[5], out_seq_no_x=row[6], in_seq_no=row[7],
                              out_seq_no=row[8], layer=row[9], ttl=row[10], ttr=row[11], updated=row[12],
                              created=row[13], mtproto=row[14], input_chat=input_chat)
