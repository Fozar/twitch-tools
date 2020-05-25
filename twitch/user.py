from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .stream import Stream
    from .client import Client


class User:
    """Represents a Twitch User

    .. container:: operations
        .. describe:: x == y
            Checks if two users are equal.
        .. describe:: x != y
            Checks if two users are not equal.
        .. describe:: str(x)
            Returns the user's display name.

    Attributes
    -----------
    client : :class:`Client`
        Current Twitch client
    stream : Optional[:class:`Stream`]
        User's current stream. Initially None. To get it, use the appropriate method.
    broadcaster_type : Optional[str]
        User’s broadcaster type: "partner", "affiliate", or None.
    description : Optional[str]
        User’s channel description.
    display_name : str
        User’s display name.
    email : Optional[str]
        User’s email address. Returned if the request includes the user:read:email scope.
    id : str
        User’s ID.
    login : str
        User’s login name.
    offline_image_url : str
        URL of the user’s offline image.
    profile_image_url : str
        URL of the user’s profile image.
    type : Optional[str]
        User’s type: "staff", "admin", "global_mod", or None.
    view_count : int
        Total number of views of the user’s channel.

    """

    __slots__ = (
        "client",
        "stream",
        "broadcaster_type",
        "description",
        "display_name",
        "email",
        "id",
        "login",
        "offline_image_url",
        "profile_image_url",
        "type",
        "view_count",
    )

    def __init__(self, client: "Client", data: dict):
        self.client = client
        self._update(data)
        self.stream = None

    def __str__(self):
        return self.display_name

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def _update(self, data: dict):
        self.broadcaster_type = data["broadcaster_type"] or None
        self.description = data["description"] or None
        self.display_name = data["display_name"]
        self.email = data.get("email")
        self.id = data["id"]
        self.login = data["login"]
        self.offline_image_url = data["offline_image_url"]
        self.profile_image_url = data["profile_image_url"]
        self.type = data["type"] or None
        self.view_count = data["view_count"]

    async def get_stream(self) -> Optional["Stream"]:
        """Returns current user's stream.

        Returns
        -------
        Optional[:class:`Stream`]
            Current user's stream. None if no active stream.
        """
        self.stream = await self.client.get_stream(self.id)
        self.stream.user = self
        return self.stream
