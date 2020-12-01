#  MIT License
#
#  Copyright (c) 2015-2020 Rapptz
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
import atexit
import datetime as dt
import json
import weakref
from contextlib import suppress
from typing import List, Optional
from urllib.parse import quote

import aiohttp

from .errors import HTTPException


async def json_or_text(response):
    text = await response.text(encoding="utf-8")
    with suppress(KeyError):
        if "application/json" in response.headers["content-type"]:
            return json.loads(text)

    return text


class Route:
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(self, method: str, path: str, params: list = None):
        self.method = method
        self.path = path
        self.url = self.BASE_URL + self.path
        self.params = [(k, quote(v) if isinstance(v, str) else v) for k, v in params]

    def __repr__(self):
        params = tuple(sorted(self.params))
        return f"{self.method}:{self.path}:{params}"

    def __hash__(self):
        return hash(repr(self))


class MaybeUnlock:
    def __init__(self, lock):
        self.lock = lock
        self._unlock = True

    def __enter__(self):
        return self

    def defer(self):
        self._unlock = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._unlock:
            self.lock.release()


class HTTPClient:
    def __init__(self, client_id: str, session: aiohttp.ClientSession, token: str = None):
        self.client_id = client_id
        self.token = token
        self.loop = asyncio.get_event_loop()
        self._session = session or aiohttp.ClientSession()
        self._locks = weakref.WeakValueDictionary()
        atexit.register(self._close)

    def _close(self):
        self.loop.run_until_complete(self._session.close())

    async def get_token(self, client_secret: str):
        response = await self._session.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": self.client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
        response_body = await response.json()
        self.token = response_body["access_token"]
        return self.token

    async def request(self, route: Route, **kwargs):
        method = route.method
        url = route.url
        route_hash = hash(route)
        lock = self._locks.get(route_hash)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[route_hash] = lock

        headers = {"Client-ID": self.client_id}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        kwargs["headers"] = headers
        kwargs["params"] = route.params

        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for attempt in range(5):
                async with self._session.request(method, url, **kwargs) as r:
                    data = await json_or_text(r)
                    remaining = r.headers.get("Ratelimit-Remaining")
                    if remaining == "0" and r.status != 429:
                        now = dt.datetime.utcnow()
                        reset = dt.datetime.utcfromtimestamp(float(r.headers["Ratelimit-Reset"]))
                        delta = (reset - now).total_seconds()
                        maybe_lock.defer()
                        self.loop.call_later(delta, lock.release)

                    if 300 > r.status >= 200:
                        return data
                    elif r.status in {429, 500, 502, 503}:
                        await asyncio.sleep(1 + attempt * 2)
                        continue
                    else:
                        raise HTTPException(r, data)

            raise HTTPException(r, data)

    def get_games(self, game_ids: List[str] = None, game_names: List[str] = None):
        params = []
        if game_ids:
            params.extend(("id", game_id) for game_id in game_ids)
        if game_names:
            params.extend(("name", game_name) for game_name in game_names)
        return self.request(Route("GET", "/games", params))

    def get_streams(
        self,
        user_ids: List[str] = None,
        user_logins: List[str] = None,
        game_ids: List[str] = None,
        languages: List[str] = None,
        first: int = 20,
        after: str = None,
        before: str = None,
    ):
        params = [("first", first)]
        if user_ids:
            params.extend(("user_id", user_id) for user_id in user_ids)
        if user_logins:
            params.extend(("user_login", user_login) for user_login in user_logins)
        if game_ids:
            params.extend(("game_id", game_id) for game_id in game_ids)
        if languages:
            params.extend(("language", language) for language in languages)
        if after:
            params.append(("after", after))
        if before:
            params.append(("before", before))
        return self.request(Route("GET", "/streams", params))

    def get_users(self, user_ids: List[str] = None, user_logins: List[str] = None):
        params = []
        if user_ids:
            params.extend(("id", user_id) for user_id in user_ids)
        if user_logins:
            params.extend(("login", user_login) for user_login in user_logins)
        return self.request(Route("GET", "/users", params))

    def subscribe_to_events(
        self, callback: str, topic: str, lease_seconds: int, secret: Optional[str] = None,
    ):
        params = {
            "hub.callback": callback,
            "hub.mode": "subscribe",
            "hub.topic": topic,
            "hub.lease_seconds": lease_seconds,
        }
        if secret:
            params["hub.secret"] = secret
        return self.request(Route("POST", "/webhooks/hub", list(params.items())))

    def unsubscribe_from_events(
        self, callback: str, topic: str, lease_seconds: int, secret: Optional[str] = None,
    ):
        params = {
            "hub.callback": callback,
            "hub.mode": "unsubscribe",
            "hub.topic": topic,
            "hub.lease_seconds": lease_seconds,
        }
        if secret:
            params["hub.secret"] = secret
        return self.request(Route("POST", "/webhooks/hub", list(params.items())))
