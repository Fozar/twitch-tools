class TwitchException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = ""

    def __str__(self):
        return self.message


class HTTPException(TwitchException):
    def __init__(self, response, data, *args):
        self.response = response
        self.data = data
        super().__init__(*args)

    def __str__(self):
        return f"Status code: {self.response.status}. {self.message}"


class NoMoreItems(TwitchException):
    pass
