from __future__ import annotations as _annotations
import os
import asyncio
import sqlite3
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable, TypeVar

import logfire
from typing_extensions import LiteralString, ParamSpec

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


P = ParamSpec('P')
R = TypeVar('R')


@dataclass
class Database:
    """Rudimentary database to store chat messages in SQLite.

    The SQLite standard library package is synchronous, so we
    use a thread pool executor to run queries asynchronously.
    """

    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = os.path.join(THIS_DIR, '../.chat_app_messages.sqlite')
    ) -> AsyncIterator[Database]:
        with logfire.span('connect to DB'):
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            con = await loop.run_in_executor(executor, cls._connect, file)
            slf = cls(con, loop, executor)
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        con = sqlite3.connect(str(file))
        con = logfire.instrument_sqlite3(con)
        cur = con.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                session_id TEXT NOT NULL,
                message_list TEXT NOT NULL
            );
            '''
        )
        con.commit()
        return con

    async def add_messages(self, username: str, session_id: str, messages: bytes):
        await self._asyncify(
            self._execute,
            'INSERT INTO messages (username, session_id, message_list) VALUES (?, ?, ?);',
            username,
            session_id,
            messages,
            commit=True,
        )

    async def get_messages(self, username: str, session_id: str) -> list[ModelMessage]:
        c = await self._asyncify(
            self._execute,
            'SELECT message_list FROM messages WHERE username = ? AND session_id = ? ORDER BY id;',
            username,
            session_id
        )
        rows = await self._asyncify(c.fetchall)
        messages: list[ModelMessage] = []
        for row in rows:
            messages.extend(ModelMessagesTypeAdapter.validate_json(row[0]))
        return messages

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        return await self._loop.run_in_executor(  # type: ignore
            self._executor,
            partial(func, **kwargs),
            *args,  # type: ignore
        )
