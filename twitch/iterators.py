#  MIT License
#
#  Copyright (c) 2020 Fozar
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import asyncio
from abc import abstractmethod
from collections import AsyncIterator
from itertools import zip_longest
from typing import Any, Optional, List

from .errors import NoMoreItems
from .game import Game
from .stream import Stream
from .user import User
from .utils import chunks


class _AsyncIterator(AsyncIterator):
    async def __anext__(self) -> Any:
        try:
            msg = await self.next()
        except NoMoreItems:
            raise StopAsyncIteration()
        else:
            return msg

    @abstractmethod
    async def next(self):
        raise NotImplemented


class GameIterator(_AsyncIterator):
    def __init__(
        self,
        client,
        ids: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
    ):
        if ids is None and names is None:
            raise TypeError("Missing one of positional arguments: 'ids', 'names'")
        self.client = client
        self.ids = chunks(list(set(ids)) if ids else [], 100)
        self.names = chunks(list(set(names)) if names else [], 100)

        self.get_games = self.client.http.get_games
        self.games = asyncio.Queue()

    async def next(self) -> Game:
        if self.games.empty():
            await self.fill_games()

        try:
            return self.games.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    async def fill_games(self):
        ids = next(self.ids, None)
        names = next(self.names, None)
        if ids is None and names is None:
            return

        resp = await self.get_games(ids, names)
        data = resp["data"]
        if not data:
            return

        for element in data:
            await self.games.put(Game(self.client, element))


class StreamIterator(_AsyncIterator):
    def __init__(self, client, limit: int = 100):
        self.client = client
        self.limit = limit

        self._cursor = None
        self._filter = {}

        self.get_streams = self.client.http.get_streams
        self.streams = asyncio.Queue()

    async def next(self) -> Stream:
        if self.streams.empty():
            await self.fill_streams()

        try:
            return self.streams.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        limit = self.limit
        if limit is None or limit > 100:
            retrieve = 100
        else:
            retrieve = limit

        self.retrieve = retrieve
        return retrieve > 0

    def filter(
        self,
        user_ids: Optional[List[str]] = None,
        user_logins: Optional[List[str]] = None,
        game_ids: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
    ):
        if user_ids and len(user_ids) > 100:
            raise OverflowError("Too many user IDs. Maximum: 100")
        if user_logins and len(user_logins) > 100:
            raise OverflowError("Too many user logins. Maximum: 100")
        if game_ids and len(game_ids) > 10:
            raise OverflowError("Too many game IDs. Maximum: 10")
        if languages and len(languages) > 100:
            raise OverflowError("Too many languages. Maximum: 100")
        self._filter.update({k: v for k, v in locals().items() if isinstance(v, list)})
        return self

    async def fill_streams(self):
        if self._get_retrieve():
            resp = await self.get_streams(
                first=self.retrieve, after=self._cursor, **self._filter
            )
            data = resp["data"]
            if len(data) < 100:
                self.limit = 0
            elif self.limit is not None:
                self.limit -= len(data)
            if resp["pagination"].get("cursor"):
                self._cursor = resp["pagination"]["cursor"]

            for element in data:
                await self.streams.put(Stream(self.client, element))


class UserIterator(_AsyncIterator):
    def __init__(
        self,
        client,
        ids: Optional[List[str]] = None,
        logins: Optional[List[str]] = None,
    ):
        self.client = client
        self.ids = chunks(list(set(ids)), 100) if ids else None
        self.logins = chunks(list(set(logins)), 100) if logins else None

        self.get_users = self.client.http.get_users
        self.users = asyncio.Queue()

    async def next(self) -> User:
        if self.users.empty():
            await self.fill_users()

        try:
            return self.users.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    async def fill_users(self):
        if self.ids is None and self.logins is None:
            return await self._get_elements(self.ids, self.logins)

        ids = next(self.ids, None) if self.ids else None
        logins = next(self.logins, None) if self.logins else None
        if ids is None and logins is None:
            return

        if ids and logins and len(ids) + len(logins) > 100:
            for ids, logins in zip_longest(chunks(ids, 50), chunks(logins, 50)):
                await self._get_elements(ids, logins)
            return

        await self._get_elements(ids, logins)

    async def _get_elements(self, ids, logins):
        resp = await self.get_users(ids, logins)
        data = resp["data"]
        if not data:
            return

        for element in data:
            await self.users.put(User(self.client, element))
