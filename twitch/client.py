import asyncio
from contextlib import suppress
from typing import List, Optional

import aiohttp

from .errors import NoMoreItems
from .game import Game
from .http import HTTPClient
from .iterators import GameIterator, UserIterator, StreamIterator
from .stream import Stream
from .user import User
from .webhook import *


class Client:
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(
        self,
        client_id: str,
        token: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self.loop = asyncio.get_event_loop()
        session = session or aiohttp.ClientSession()
        self.http = HTTPClient(client_id, token, session)

    def get_games(
        self, ids: Optional[List[str]] = None, names: Optional[List[str]] = None,
    ) -> GameIterator:
        """Gets games information by game IDs or names.

        Note
        ----
        For a query to be valid, name and/or id must be specified.

        Parameters
        ----------
        ids : Optional[List[str]]
            Game IDs.
        names : Optional[List[str]]
            Game names. The name must be an exact match. For instance, “Pokemon” will not
            return a list of Pokemon games; instead, query the specific Pokemon game(s)
            in which you are interested.

        Returns
        -------
        GameIterator
            Asynchronous iterator of found games

        """
        return GameIterator(self, ids, names)

    async def get_game(
        self, id: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[Game]:
        """Gets game information by game ID or name.

        Parameters
        ----------
        id : str
            Game ID.
        name : str
            Game name. The name must be an exact match. For instance, “Pokemon” will not
            return a list of Pokemon games; instead, query the specific Pokemon game(s)
            in which you are interested.
        Returns
        -------
        Optional[Game]
            Found game. None if not found

        """
        if id and name:
            raise TypeError("You must specify only ID or only name.")
        with suppress(NoMoreItems):
            if id:
                return await self.get_games(ids=[id]).next()
            elif name:
                return await self.get_games(names=[name]).next()
        return None

    def get_streams(self, limit: Optional[int] = 100) -> StreamIterator:
        """Gets information about active streams. Streams are returned sorted by number
        of current viewers, in descending order. Across multiple pages of results, there
        may be duplicate or missing streams, as viewers join and leave streams.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of objects to retrieve. If ``None`` it retrieves without
            limits.

        Returns
        -------
        StreamIterator
            Asynchronous iterator of found streams

        """
        return StreamIterator(self, limit)

    async def get_stream(
        self, user_id: Optional[str] = None, user_login: Optional[str] = None
    ) -> Optional[Stream]:
        """Gets information about active stream.

        Parameters
        ----------
        user_id : Optional[str]
            Returns stream broadcast by one specified user ID.
        user_login : Optional[str]
            Returns stream broadcast by one specified user login.

        Returns
        -------
        Optional[Stream]
            Found stream

        """
        if user_id and user_login:
            raise TypeError("You must specify only id or only login.")
        with suppress(NoMoreItems):
            if user_id:
                return await self.get_streams(limit=1).filter(user_ids=[user_id]).next()
            elif user_login:
                return (
                    await self.get_streams(limit=1)
                    .filter(user_logins=[user_login])
                    .next()
                )
        return None

    def get_users(
        self, ids: Optional[List[str]] = None, logins: Optional[List[str]] = None
    ) -> UserIterator:
        """Gets information about one or more specified Twitch users. Users are
        identified by optional user IDs and/or login name. If neither a user ID nor a
        login name is specified, the user is looked up by Bearer token.

        Parameters
        ----------
        ids : Optional[List[str]]
            User IDs. Multiple user IDs can be specified.
        logins : Optional[List[str]]
            User login names. Multiple login names can be specified.

        Returns
        -------
        UserIterator
            Asynchronous iterator of found users

        """
        return UserIterator(self, ids, logins)

    async def get_user(
        self, id: Optional[str] = None, login: Optional[str] = None
    ) -> Optional[User]:
        """Gets information about one specified Twitch user.

        Parameters
        ----------
        id : Optional[str]
            User ID.
        login : Optional[str]
            User login name.
        Returns
        -------
        Optional[User]
            Found user

        """
        if id and login:
            raise TypeError("You must specify only ID or only name.")
        with suppress(NoMoreItems):
            if id:
                return await self.get_users(ids=[id]).next()
            elif login:
                return await self.get_users(logins=[login]).next()
        return None

    def create_subscription(
        self,
        callback: str,
        topic: Topic,
        lease_seconds: int = 0,
        secret: Optional[str] = None,
    ):
        """Subscribe to events for a specified topic.

        After this, we will make a call to your callback to verify your subscription; see
        the Webhooks Guide for information on how to implement your callback.

        Note
        ----
        Subscription requests affect rate limits in the Twitch API.

        Parameters
        ----------
        callback : str
            URL where notifications will be delivered.
        topic : str
            URL for the topic to subscribe to or unsubscribe from. `topic` maps to a new
            Twitch API endpoint.
        lease_seconds : int
            Number of seconds until the subscription expires. Default: 0. Maximum: 864000.
            Should be specified to a value greater than 0 otherwise subscriptions will
            expire before any useful notifications can be sent.
        secret : str
            Secret used to sign notification payloads. The X-Hub-Signature header is
            generated by sha256(secret, notification_bytes). We strongly encourage you to
            use this, so your application can verify that notifications are genuine.

        """
        return Subscription(self, callback, topic, lease_seconds, secret)

    async def unsubscribe_from_events(
        self,
        callback: str,
        topic: str,
        lease_seconds: int = 0,
        secret: Optional[str] = None,
    ):
        """Unsubscribe from events for a specified topic.

        After this, we will make a call to your callback to verify your subscription; see
        the Webhooks Guide for information on how to implement your callback.

        Note
        ----
        Subscription requests affect rate limits in the Twitch API.

        Parameters
        ----------
        callback : str
            URL where notifications will be delivered.
        topic : str
            URL for the topic to subscribe to or unsubscribe from. `topic` maps to a new
            Twitch API endpoint.
        lease_seconds : int
            Number of seconds until the subscription expires. Default: 0. Maximum: 864000.
            Should be specified to a value greater than 0 otherwise subscriptions will
            expire before any useful notifications can be sent.
        secret : Optional[str]
            Secret used to sign notification payloads. The X-Hub-Signature header is
            generated by sha256(secret, notification_bytes). We strongly encourage you to
            use this, so your application can verify that notifications are genuine.

        """
        return await self.http.unsubscribe_from_events(
            callback, topic, lease_seconds, secret
        )
