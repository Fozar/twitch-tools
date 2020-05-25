from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client


class Game:
    """Represents a Twitch Game

        .. container:: operations
            .. describe:: x == y
                Checks if two games are equal.
            .. describe:: x != y
                Checks if two games are not equal.
            .. describe:: str(x)
                Returns the game's name.

    Attributes
    -----------
    client : :class:`Client`
        Current Twitch client
    id : str
        Game ID.
    name : str
        Game name.
    """

    __slots__ = ("client", "_box_art_url", "id", "name")

    def __init__(self, client: "Client", data: dict):
        self.client = client
        self._update(data)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Game) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def _update(self, data: dict):
        self._box_art_url = data["box_art_url"]
        self.id = data["id"]
        self.name = data["name"]

    def box_art_url(self, width: int = 144, height: int = 192):
        """Game’s box art URL. All image URLs have variable width and height.
        You can specify width and height with any values to get that size image.

        Parameters
        ----------
        width : int
            Image width. Defaults to 144.
        height : int
            Image height. Defaults to 192.

        Returns
        -------
        str
            Game’s box art URL

        """
        return self._box_art_url.format(width=width, height=height)
