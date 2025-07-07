import os
import datetime
import logging

from psycopg import AsyncConnection
from psycopg.types.json import Json

logger = logging.getLogger(__name__)

DB_URL = os.environ["POSTGRES_URL"]


async def get_connection() -> AsyncConnection:
    return await AsyncConnection.connect(conninfo=DB_URL)


async def ensure_schema_and_table(conn, account_id):
    schema = f"account_{account_id}"
    async with conn.cursor() as cur:
        await cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        await cur.execute(f'SET search_path TO "{schema}"')
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(64) PRIMARY KEY,
                chat_id VARCHAR(64) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                message_type VARCHAR(32),
                event_type VARCHAR(32),
                from_user VARCHAR(128),
                event JSONB
            )
        """)
        await cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id_timestamp
            ON messages (chat_id, timestamp)
        """)
        await conn.commit()


async def add_message(message: dict):
    data = message['data']
    key = data['key']

    event_id = key['id']
    event_type = message['event']
    chat_id = key['remoteJid']
    message_type = data['messageType']
    sent_at_ts = data['messageTimestamp']
    timestamp = datetime.datetime.utcfromtimestamp(sent_at_ts)
    account_id = message['sender']
    from_user = key.get("participant")

    async with await get_connection() as conn:
        await ensure_schema_and_table(conn, account_id)
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO messages (id, chat_id, timestamp, event_type, from_user, message_type, event)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                event_id, chat_id, timestamp, event_type, from_user, message_type, Json(message)
            ))
        await conn.commit()
