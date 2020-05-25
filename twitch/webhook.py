"""
MIT License

 Copyright (c) 2020 Fozar

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
 """
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Union, TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING:
    from .client import Client

__all__ = (
    "Topic",
    "ChannelBanChangeEvents",
    "ExtensionTransactionCreated",
    "ModeratorChangeEvents",
    "StreamChanged",
    "SubscriptionEvents",
    "UserChanged",
    "UserFollows",
    "Subscription",
)


class Topic(ABC):
    """Represents subscription's topic

        .. container:: operations
            .. describe:: str(x)
                Returns the topic's uri.
    """

    BASE_URL: str = "https://api.twitch.tv/helix"

    __slots__ = ()

    @property
    def _params(self) -> List[Tuple[str, Union[str, int]]]:
        return [
            (slot, getattr(self, slot))
            for slot in sorted(self.__slots__)
            if getattr(self, slot) is not None
        ]

    def __str__(self):
        return self.uri

    @property
    @abstractmethod
    def uri(self):
        raise NotImplemented


class ChannelBanChangeEvents(Topic):
    """Notifies when a broadcaster bans or un-bans people in their channel.

    Attributes
    -----------
    broadcaster_id : str
        User ID of the broadcaster.
    user_id : Optional[str]
        Specifies the user ID of the moderator added or removed.

    """

    __slots__ = ("broadcaster_id", "first", "user_id")

    def __init__(self, broadcaster_id: str, user_id: Optional[str] = None):
        self.broadcaster_id = broadcaster_id
        self.first = 1
        self.user_id = user_id

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/moderation/banned/events?{urlencode(self._params)}"


class ExtensionTransactionCreated(Topic):
    """Sends a notification when a new transaction is created for an extension.

    Attributes
    -----------
    extension_id : str
        ID of the extension to listen to for transactions.

    """

    __slots__ = ("extension_id", "first")

    def __init__(self, extension_id: str):
        self.extension_id = extension_id
        self.first = 1

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/extensions/transactions?{urlencode(self._params)}"


class ModeratorChangeEvents(Topic):
    """Notifies when a broadcaster adds or removes moderators.

    Attributes
    -----------
    broadcaster_id : str
        User ID of the broadcaster.
    user_id : Optional[str]
        Specifies the user ID of the moderator added or removed.

    """

    __slots__ = ("broadcaster_id", "first", "user_id")

    def __init__(self, broadcaster_id: str, user_id: Optional[str] = None):
        self.broadcaster_id = broadcaster_id
        self.first = 1
        self.user_id = user_id

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/moderation/moderators/events?{urlencode(self._params)}"


class StreamChanged(Topic):
    """Notifies when a stream changes; e.g., stream goes online or offline, the stream
    title changes, or the game changes.

    Attributes
    -----------
    user_id : str
        Specifies the user ID whose stream is monitored.

    """

    __slots__ = ("user_id",)

    def __init__(self, user_id: str):
        self.user_id = user_id

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/streams?{urlencode(self._params)}"


class SubscriptionEvents(Topic):
    """This webhook notifies you when:
        - A payment has been processed for a subscription or unsubscription.
        - A user who is subscribed to a broadcaster notifies the broadcaster of their
            subscription in the chat.

    Note
    ----
    Required OAuth Scope: `channel:read:subscriptions`

    Attributes
    -----------
    broadcaster_id : str
        User ID of the broadcaster. Must match the User ID in the Bearer token.
    user_id : Optional[str]
        ID of the subscribed user.
    gifter_id : Optional[str]
        ID of the user who gifted the sub. `274598607` for anonymous gifts.
    gifter_name	: Optional[str]
        Display name of the user who gifted the sub. `AnAnonymousGifter` for anonymous
        gifts.

    """

    __slots__ = ("broadcaster_id", "first", "user_id", "gifter_id", "gifter_name")

    def __init__(
        self,
        broadcaster_id: str,
        user_id: Optional[str] = None,
        gifter_id: Optional[str] = None,
        gifter_name: Optional[str] = None,
    ):
        self.broadcaster_id = broadcaster_id
        self.first = 1
        self.user_id = user_id
        self.gifter_id = gifter_id
        self.gifter_name = gifter_name

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/subscriptions/events?{urlencode(self._params)}"


class UserChanged(Topic):
    """Notifies when a user changes information about his/her profile.

    Note
    ----
    Requires the `user:read:email` OAuth scope to get notifications of email changes.

    Attributes
    -----------
    id : str
        Specifies the user ID whose data is monitored.

    """

    __slots__ = ("id",)

    def __init__(self, id: str):
        self.id = id

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/users?{urlencode(self._params)}"


class UserFollows(Topic):
    """Notifies when a follows event occurs.

    Note
    ----
    `from_id` and/or `to_id` must be specified.

    Attributes
    -----------
    from_id : Optional[str]
        Specifies the user who starts following someone.
    to_id : Optional[str]
        Specifies the user who has a new follower.

    """

    __slots__ = ("first", "from_id", "to_id")

    def __init__(self, from_id: Optional[int] = None, to_id: Optional[int] = None):
        if from_id is None and to_id is None:
            raise TypeError("'from_id' and/or 'to_id' must be specified.")

        self.first = 1
        self.from_id = from_id
        self.to_id = to_id

    @property
    def uri(self) -> str:
        return f"{self.BASE_URL}/users/follows?{urlencode(self._params)}"


class Subscription:
    """Represents webhook subscription

        .. container:: operations
            .. describe:: str(x)
                Returns the topic's uri.

    Note
    ----
    Subscription requests affect rate limits in the Twitch API.

    Attributes
    -----------
    callback : str
        URL where notifications will be delivered.
    topic : Topic
        Topic to subscribe to or unsubscribe from.
    lease_seconds : int
        Number of seconds until the subscription expires. Default: 0. Maximum: 864000.
        Should be specified to a value greater than 0 otherwise subscriptions will
        expire before any useful notifications can be sent.
    secret : Optional[str]
        Secret used to sign notification payloads. The X-Hub-Signature header is
        generated by sha256(secret, notification_bytes). We strongly encourage you to
        use this, so your application can verify that notifications are genuine.

    """

    __slots__ = ("client", "callback", "topic", "lease_seconds", "secret")

    def __init__(
        self,
        client: "Client",
        callback: str,
        topic: Topic,
        lease_seconds: int = 0,
        secret: Optional[str] = None,
    ):
        self.client = client
        self.callback = callback
        self.topic = topic
        self.lease_seconds = lease_seconds
        self.secret = secret

    def __str__(self):
        return str(self.topic)

    async def extend(self):
        """An alias for :meth:`~Subscription.subscribe`"""
        return await self.subscribe()

    async def subscribe(self):
        """Subscribe to events

        After this, we will make a call to your callback to verify your subscription; see
        the Webhooks Guide for information on how to implement your callback.

        """
        return await self.client.http.subscribe_to_events(
            self.callback, self.topic.uri, self.lease_seconds, self.secret
        )

    async def unsubscribe(self):
        """Unsubscribe from events

        After this, we will make a call to your callback to verify your subscription; see
        the Webhooks Guide for information on how to implement your callback.

        """
        return await self.client.http.unsubscribe_from_events(
            self.callback, self.topic.uri, self.lease_seconds, self.secret
        )
