from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .game import Game
    from .client import Client


class Stream:
    """Represents a Twitch Stream

    .. container:: operations
        .. describe:: x == y
            Checks if two streams are equal.
        .. describe:: x != y
            Checks if two streams are not equal.
        .. describe:: str(x)
            Returns the stream's title.

    Attributes
    -----------
    client : :class:`Client`
        Current Twitch client
    game : Optional[:class:`Game`]
        Game being played on the stream. Initially None. To get it, use the appropriate
        method.
    user : Optional[:class:`User`]
        User who is streaming. Initially None. To get it, use the appropriate method.
    game_id : str
        ID of the game being played on the stream.
    id : str
        Stream ID.
    language : str
        Stream language.
    started_at : :class:`datetime`
        UTC timestamp.
    tag_ids : List[str]
        Shows tag IDs that apply to the stream.
    title : str
        Stream title.
    user_id : str
        ID of the user who is streaming.
    user_name : str
        Display name corresponding to user_id.
    viewer_count : int
        Number of viewers watching the stream at the time of the query.

    """

    __slots__ = (
        "client",
        "game",
        "user",
        "game_id",
        "id",
        "language",
        "started_at",
        "tag_ids",
        "_thumbnail_url",
        "title",
        "_type",
        "user_id",
        "user_name",
        "viewer_count",
    )

    def __init__(self, client: "Client", data: dict):
        self.client = client
        self._update(data)
        self.game = None
        self.user = None

    def __str__(self):
        return self.title

    def __eq__(self, other):
        return isinstance(other, Stream) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def _update(self, data: dict):
        self.game_id = data["game_id"]
        self.id = data["id"]
        self.language = data["language"]
        self.started_at = datetime.strptime(data["started_at"], "%Y-%m-%dT%H:%M:%S%z")
        self.tag_ids = data["tag_ids"]
        self._thumbnail_url = data["thumbnail_url"]
        self.title = data["title"]
        self._type = bool(data["type"])
        self.user_id = data["user_id"]
        self.user_name = data["user_name"]
        self.viewer_count = data["viewer_count"]

    @property
    def live(self) -> bool:
        """True if stream status is "live". False in case of error.

        Returns
        -------
        bool
            Stream status
        """
        return self._type

    def thumbnail_url(self, width: int = 1920, height: int = 1080) -> str:
        """Thumbnail URL of the stream. All image URLs have variable width and height.
        You can specify width and height with any values to get that size image.

        Parameters
        ----------
        width : int
            Image width. Defaults to 1920.
        height : int
            Image height. Defaults to 1080.

        Returns
        -------
        str
            Thumbnail URL
            
        """
        return self._thumbnail_url.format(width=width, height=height)

    async def get_game(self) -> Optional["Game"]:
        """Returns game being played on the stream.

        Returns
        -------
        Optional[:class:`Game`]
            Current game being played
        """
        self.game = await self.client.get_game(self.game_id)
        return self.game

    async def get_user(self) -> Optional["User"]:
        """Returns user who is streaming.

        Returns
        -------
        Optional[:class:`User`]
            User who is streaming
        """
        self.user = await self.client.get_user(self.user_id)
        self.user.stream = self
        return self.user
