import sqlite3
import uuid
import time
from pathlib import Path


class Database:

    def __init__(self, path="data/securelink.db"):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row

        self.create_tables()

    # =========================================================
    # TABLES
    # =========================================================

    def create_tables(self):

        cursor = self.connection.cursor()

        # -----------------------------------------------------
        # Identity
        # -----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS identity (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL
            )
        """)

        # -----------------------------------------------------
        # Contacts
        # -----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                ip TEXT,
                port INTEGER
            )
        """)

        # -----------------------------------------------------
        # Messages
        # -----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                local_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                conversation_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                message_ciphertext TEXT NOT NULL,
                message_nonce TEXT,
                timestamp INTEGER NOT NULL
            )
        """)

        self.connection.commit()

    # =========================================================
    # IDENTITY
    # =========================================================

    def get_identity(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT user_id, username
            FROM identity
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row is None:

            return None

        return dict(row)

    def create_identity(self, username):

        existing = self.get_identity()

        if existing:

            return existing["user_id"]

        user_id = str(
            uuid.uuid4()
        )

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO identity (
                user_id,
                username
            )
            VALUES (?, ?)
        """, (
            user_id,
            username
        ))

        self.connection.commit()

        return user_id

    def update_username(self, username):

        cursor = self.connection.cursor()

        cursor.execute("""
            UPDATE identity
            SET username = ?
        """, (
            username,
        ))

        self.connection.commit()

    # =========================================================
    # CONTACTS
    # =========================================================

    def save_contact(
        self,
        user_id,
        username,
        ip,
        port
    ):

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO contacts (
                user_id,
                username,
                ip,
                port
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                username = excluded.username,
                ip = excluded.ip,
                port = excluded.port
        """, (
            user_id,
            username,
            ip,
            port
        ))

        self.connection.commit()

    def get_contact(self, user_id):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                user_id,
                username,
                ip,
                port
            FROM contacts
            WHERE user_id = ?
        """, (
            user_id,
        ))

        row = cursor.fetchone()

        if row is None:

            return None

        return dict(row)

    def get_contacts(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                user_id,
                username,
                ip,
                port
            FROM contacts
            ORDER BY username
        """)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    # =========================================================
    # MESSAGES
    # =========================================================

    def save_message(
        self,
        conversation_id,
        sender_id,
        message_ciphertext,
        message_nonce=None,
        message_id=None,
        timestamp=None
    ):

        if message_id is None:

            message_id = str(
                uuid.uuid4()
            )

        if timestamp is None:

            timestamp = int(
                time.time()
            )

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO messages (
                message_id,
                conversation_id,
                sender_id,
                message_ciphertext,
                message_nonce,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            conversation_id,
            sender_id,
            message_ciphertext,
            message_nonce,
            timestamp
        ))

        self.connection.commit()

        return message_id

    def get_conversation(
        self,
        conversation_id
    ):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                local_id,
                message_id,
                conversation_id,
                sender_id,
                message_ciphertext,
                message_nonce,
                timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC, local_id ASC
        """, (
            conversation_id,
        ))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    def message_exists(
        self,
        message_id
    ):

        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT 1
            FROM messages
            WHERE message_id = ?
            LIMIT 1
        """, (
            message_id,
        ))

        return cursor.fetchone() is not None

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        self.connection.close()